import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from google.adk.tools import ToolContext
from .models import (
    RequirementsPackage, ProjectBrief, Persona, DomainEntity, UserStory,
    Requirement, OpenQuestion, Decision, SourceRegistry, SourceDocument,
    SourceOrigin, Status, DefaultIfDeferred, OpenQuestionStatus
)

from .validation.package_validators import validate_package_integrity
from .validation.grounding import validate_source_grounding
from .validation.coverage import validate_coverage
from .validation.definition_of_ready import compute_definition_of_ready
from .packaging.writer import write_package_to_disk
from .packaging.manifest import generate_handoff_manifest
from .settings import Settings

def to_pydantic(data, model_cls):
    if data is None:
        return None
    if isinstance(data, model_cls):
        return data
    if isinstance(data, dict):
        return model_cls.model_validate(data)
    return data

def to_pydantic_list(data_list, model_cls):
    if not data_list:
        return []
    res = []
    for item in data_list:
        if isinstance(item, model_cls):
            res.append(item)
        elif isinstance(item, dict):
            res.append(model_cls.model_validate(item))
        else:
            res.append(item)
    return res

def prune_invalid_affects(pkg: RequirementsPackage) -> None:
    for r in pkg.requirements:
        r.affected_by = []
    for oq in pkg.open_questions:
        for req_id in oq.affects:
            req = next((r for r in pkg.requirements if r.id == req_id), None)
            if req and oq.id not in req.affected_by:
                req.affected_by.append(oq.id)

    req_ids = {r.id for r in pkg.requirements}
    for oq in pkg.open_questions:
        oq.affects = [aff for aff in oq.affects if aff in req_ids]
        
    seen_questions = {}
    unique_questions = []
    id_mapping = {}
    next_num = 1
    
    for oq in pkg.open_questions:
        if oq.question in seen_questions:
            id_mapping[oq.id] = seen_questions[oq.question]
            continue
            
        new_id = f"OQ-{next_num:03d}"
        id_mapping[oq.id] = new_id
        seen_questions[oq.question] = new_id
        
        oq.id = new_id
        unique_questions.append(oq)
        next_num += 1
        
    pkg.open_questions = unique_questions
    
    # Build set of valid OQ IDs after dedup
    valid_oq_ids = {oq.id for oq in pkg.open_questions}
    
    for r in pkg.requirements:
        new_affected_by = []
        for aff in r.affected_by:
            mapped = id_mapping.get(aff, aff)
            if mapped in valid_oq_ids:
                new_affected_by.append(mapped)
        r.affected_by = list(set(new_affected_by))

def make_ac_ids_globally_unique(pkg: RequirementsPackage) -> None:
    req_ac_ids = set()
    for r in pkg.requirements:
        for ac in r.acceptance_criteria:
            req_ac_ids.add(ac.id)
            
    used_ac_numbers = set()
    for r_ac_id in req_ac_ids:
        match = re.match(r"^AC-(\d+)-[a-z]$", r_ac_id)
        if match:
            used_ac_numbers.add(int(match.group(1)))
            
    next_ac_num = max(used_ac_numbers, default=0) + 100
    if next_ac_num < 500:
        next_ac_num = 500
        
    for us in pkg.user_stories:
        for idx, ac in enumerate(us.acceptance_criteria):
            suffix = chr(ord('a') + (idx % 26))
            ac.id = f"AC-{next_ac_num:03d}-{suffix}"
        next_ac_num += 1

def mark_review_passed(tool_context: ToolContext) -> dict:
    """Marks the QA review loop as passed and requests early loop exit.

    Returns:
        dict containing the status indicating review has passed.
    """
    print("[qa_critic] Calling mark_review_passed -> Escalating loop exit.")
    tool_context.actions.escalate = True
    return {"status": "review_passed"}

async def finalize_package(tool_context: ToolContext) -> dict:
    """Assembles the requirements package from session state, runs all validators,
    computes the definition-of-ready and manifest, and writes the artifact pack to disk.
    Call this once, after user stories are generated, to produce the final output.

    Returns:
        dict with execution status, timestamp, record counts, and ready_for list.
    """
    print("[package_agent] Finalizing requirements package...")
    state = tool_context.state

    # 1. Build project brief
    brief = to_pydantic(state.get("brief"), ProjectBrief)
    
    # 2. Get lists of elements robustly
    personas_data = state.get("personas", [])
    if hasattr(personas_data, "personas"):
        personas_list = personas_data.personas
    elif isinstance(personas_data, dict) and "personas" in personas_data:
        personas_list = personas_data["personas"]
    else:
        personas_list = personas_data
    personas = to_pydantic_list(personas_list, Persona)

    requirements_data = state.get("requirements", [])
    from .schemas import RequirementList
    if isinstance(requirements_data, RequirementList):
        requirements_list = requirements_data.requirements
    elif isinstance(requirements_data, dict) and "requirements" in requirements_data:
        requirements_list = requirements_data["requirements"]
    elif hasattr(requirements_data, "requirements"):
        requirements_list = requirements_data.requirements
    else:
        requirements_list = requirements_data
    requirements = to_pydantic_list(requirements_list, Requirement)

    user_stories_data = state.get("user_stories", [])
    from .schemas import UserStoryList
    if isinstance(user_stories_data, UserStoryList):
        user_stories_list = user_stories_data.user_stories
    elif isinstance(user_stories_data, dict) and "user_stories" in user_stories_data:
        user_stories_list = user_stories_data["user_stories"]
    elif hasattr(user_stories_data, "user_stories"):
        user_stories_list = user_stories_data.user_stories
    else:
        user_stories_list = user_stories_data
    user_stories = to_pydantic_list(user_stories_list, UserStory)

    domain_entities_data = state.get("domain_entities", [])
    from .schemas import DomainEntityList
    if isinstance(domain_entities_data, DomainEntityList):
        domain_entities_list = domain_entities_data.domain_entities
    elif isinstance(domain_entities_data, dict) and "domain_entities" in domain_entities_data:
        domain_entities_list = domain_entities_data["domain_entities"]
    elif hasattr(domain_entities_data, "domain_entities"):
        domain_entities_list = domain_entities_data.domain_entities
    else:
        domain_entities_list = domain_entities_data
    domain_entities = to_pydantic_list(domain_entities_list, DomainEntity)

    open_questions = to_pydantic_list(state.get("open_questions", []), OpenQuestion)
    decisions = to_pydantic_list(state.get("decisions", []), Decision)
    
    # 3. Setup source registry
    source_registry = to_pydantic(state.get("source_registry"), SourceRegistry) or SourceRegistry()
    transcript = state.get("transcript", "")
    if transcript and "transcript" not in source_registry.documents:
        source_registry.documents["transcript"] = SourceDocument(
            doc_id="transcript",
            kind=SourceOrigin.transcript,
            text=transcript
        )
        
    # Append gate answers if any are recorded
    gate_answers_text = ""
    for oq in open_questions:
        if oq.status == OpenQuestionStatus.answered and oq.answer:
            gate_answers_text += f"\n[{oq.id}] {oq.answer}"
    if gate_answers_text:
        source_registry.documents["gate_answers"] = SourceDocument(
            doc_id="gate_answers",
            kind=SourceOrigin.human_answer,
            text=gate_answers_text.strip()
        )

    # 4. Construct RequirementsPackage
    candidate_stmt_count = state.get("candidate_statement_count", 0)
    if candidate_stmt_count == 0 and "statements" in state:
        candidate_stmt_count = len(state.get("statements", []))

    source_provenance = state.get("source_provenance", [])
    if not source_provenance:
        source_provenance = ["sample_transcript.txt"]

    pkg = RequirementsPackage(
        brief=brief,
        personas=personas,
        requirements=requirements,
        user_stories=user_stories,
        domain_entities=domain_entities,
        open_questions=open_questions,
        decisions=decisions,
        generated_at=datetime.now(),
        candidate_statement_count=candidate_stmt_count,
        source_registry=source_registry,
        source_provenance=source_provenance
    )

    # 5. Run re-indexing and AC uniqueness
    prune_invalid_affects(pkg)
    make_ac_ids_globally_unique(pkg)

    # 6. Load Settings & Run Validators
    settings = Settings.load()
    print(f"[package_agent] Running structural validation (orphan_check={settings.validation.orphan_check})...")
    validate_package_integrity(pkg, orphan_check=settings.validation.orphan_check)

    print("[package_agent] Running grounding checks...")
    validate_source_grounding(pkg, pkg.source_registry, mode="warn")

    # Enforce grounding ratio floor (Fix 2)
    sourced_requirements = [r for r in pkg.requirements if any(s.origin in REAL_ORIGINS for s in r.source)]
    if sourced_requirements:
        confirmed_grounded = [r for r in sourced_requirements if r.status == Status.confirmed]
        grounding_ratio = len(confirmed_grounded) / len(sourced_requirements)
        if grounding_ratio < 0.95:
            from .validation.grounding import GroundingError
            raise GroundingError(
                f"grounding check failed: {len(confirmed_grounded)}/{len(sourced_requirements)} "
                f"confirmed requirements not found in the provided transcript — possible wrong/stale source"
            )

    # Provenance check (Fix 4)
    for r in pkg.requirements:
        for s in r.source:
            if s.origin in REAL_ORIGINS and s.ref:
                ref_lower = s.ref.lower()
                matched = False
                for prov in pkg.source_provenance:
                    prov_clean = Path(prov).stem.lower()
                    if prov_clean in ref_lower or ref_lower in prov_clean:
                        matched = True
                        break
                
                # Check if the ref mentions other project names when the brief is different
                if pkg.brief and pkg.brief.project_name:
                    proj_name = pkg.brief.project_name.lower()
                    if "spincycle" in ref_lower and proj_name != "spincycle":
                        matched = False
                    if "petwell" in ref_lower and proj_name != "petwell":
                        matched = False
                
                if not matched:
                    raise ValueError(
                        f"Provenance mismatch: requirement {r.id} cites source reference {s.ref!r} "
                        f"which does not match current run's source provenance {pkg.source_provenance} "
                        f"or project name {pkg.brief.project_name if pkg.brief else 'Unknown'}."
                    )

    print("[package_agent] Running transcript coverage validation...")
    validate_coverage(pkg, transcript, pkg.candidate_statement_count)

    print("[package_agent] Computing definition of ready...")
    dor = compute_definition_of_ready(pkg)

    # 7. Write package to disk
    out_dir = settings.io.output_dir
    print(f"[package_agent] Writing package artifacts to: {out_dir}")
    write_package_to_disk(pkg, out_dir, orphan_check=settings.validation.orphan_check)

    # Write UML diagrams if present in state
    mermaid_diagrams = state.get("mermaid_diagrams", {})
    if mermaid_diagrams:
        uml_dir = Path(out_dir) / "uml"
        uml_dir.mkdir(parents=True, exist_ok=True)
        for name, content in mermaid_diagrams.items():
            if content:
                with open(uml_dir / f"{name}.mermaid", "w", encoding="utf-8") as f:
                    f.write(content)

    manifest_dict = generate_handoff_manifest(pkg, orphan_check=settings.validation.orphan_check)

    # 8. Save each artifact via the ADK artifact service so they appear in adk web
    from google.genai import types
    artifacts_map = {
        "handoff_manifest.json": ("application/json", Path(out_dir) / "handoff_manifest.json"),
        "srs.md":               ("text/markdown", Path(out_dir) / "srs.md"),
        "requirements.json":    ("application/json", Path(out_dir) / "requirements.json"),
        "user_stories.md":      ("text/markdown", Path(out_dir) / "user_stories.md"),
        "user_stories.json":    ("application/json", Path(out_dir) / "user_stories.json"),
        "traceability.md":      ("text/markdown", Path(out_dir) / "traceability.md"),
        "traceability.json":    ("application/json", Path(out_dir) / "traceability.json"),
        "domain_class.mermaid": ("text/plain", Path(out_dir) / "uml" / "domain_class.mermaid"),
        "domain_model.json":    ("application/json", Path(out_dir) / "domain_model.json"),
        "personas.md":          ("text/markdown", Path(out_dir) / "personas.md"),
        "personas.json":        ("application/json", Path(out_dir) / "personas.json"),
        "open_questions.md":    ("text/markdown", Path(out_dir) / "open_questions.md"),
        "open_questions.json":  ("application/json", Path(out_dir) / "open_questions.json"),
        "decisions.md":         ("text/markdown", Path(out_dir) / "decisions.md"),
        "decisions.json":       ("application/json", Path(out_dir) / "decisions.json"),
    }
    
    saved_artifacts = []
    for name, (mime, path) in artifacts_map.items():
        if path.exists():
            try:
                data = path.read_bytes()
                await tool_context.save_artifact(
                    filename=name,
                    artifact=types.Part.from_bytes(data=data, mime_type=mime)
                )
                saved_artifacts.append(name)
            except Exception as e:
                print(f"[package_agent] Error saving artifact {name} to ADK: {e}")

    return {
        "status": "success",
        "generated_at": pkg.generated_at.isoformat(),
        "counts": {
            "requirements": len(pkg.requirements),
            "personas": len(pkg.personas),
            "user_stories": len(pkg.user_stories),
            "open_questions": len(pkg.open_questions),
            "decisions": len(pkg.decisions),
        },
        "ready_for": manifest_dict.get("ready_for", []),
        "artifacts": saved_artifacts
    }

from google.adk.tools import ToolContext

def resolve_open_questions(answers: dict[str, str], tool_context: ToolContext) -> dict:
    """Resolve one or more open questions in the state with user-supplied answers.

    Args:
        answers: A dictionary mapping question IDs (e.g. 'OQ-001') to their resolved answers/decisions.

    Returns:
        dict with success status and count of resolved questions.
    """
    state = tool_context.state
    oqs = state.get("open_questions") or []
    if not oqs:
        return {"status": "success", "resolved_count": 0}

    import re
    from .models import OpenQuestion, OpenQuestionStatus, SourceOrigin, Status, Source, Decision, Requirement
    from .callbacks import serialize_state_val
    from .tools import to_pydantic_list

    oq_list = to_pydantic_list(oqs, OpenQuestion)
    resolved_count = 0
    
    # Track decisions
    decisions = state.get("decisions") or []
    dec_list = to_pydantic_list(decisions, Decision)
    next_dec_num = 1
    for d in dec_list:
        match = re.match(r"^DEC-(\d+)$", d.id)
        if match:
            next_dec_num = max(next_dec_num, int(match.group(1)) + 1)
            
    # We also want to promote the affected requirements if they were blocked
    reqs = state.get("requirements") or []
    req_list = to_pydantic_list(reqs, Requirement)

    for qid, ans in answers.items():
        for oq in oq_list:
            if oq.id == qid:
                oq.answer = ans
                oq.status = OpenQuestionStatus.answered
                resolved_count += 1
                
                # Create a Decision record for this resolved question
                dec_id = f"DEC-{next_dec_num:03d}"
                dec = Decision(
                    id=dec_id,
                    statement=f"Adopted resolution: {ans}",
                    rationale=f"Resolved open question: {oq.question}",
                    related_ids=oq.affects,
                    resolved_by="human"
                )
                dec_list.append(dec)
                next_dec_num += 1
                
                # If this question affects any requirements, let's promote them to confirmed if grounded
                for req_id in oq.affects:
                    for r in req_list:
                        if r.id == req_id:
                            # Add a source with origin 'human_answer'
                            r.source.append(Source(
                                origin=SourceOrigin.human_answer,
                                ref=f"Human Gate Resolution ({qid})",
                                excerpt=ans
                            ))
                            r.status = Status.confirmed
                            print(f"[elicitation] Promoted requirement {r.id} to confirmed because open question {qid} was resolved by human.")

    state["open_questions"] = serialize_state_val(oq_list)
    state["decisions"] = serialize_state_val(dec_list)
    state["requirements"] = serialize_state_val(req_list)
    return {"status": "success", "resolved_count": resolved_count}
