import os
import re
from pathlib import Path
from google.adk.agents.callback_context import CallbackContext
from .models import (
    SourceOrigin, Status, REAL_ORIGINS, Priority, Requirement, UserStory, 
    RequirementType, AcceptanceCriterion, OpenQuestion, OpenQuestionStatus, 
    DefaultIfDeferred
)
from .validation.grounding import check_confirmed_grounding, _norm
from .schemas import RequirementList, UserStoryList, QaReviewFindings, QAFinding, DomainEntityList, MermaidDiagramList
from .tools import to_pydantic_list

def serialize_state_val(val):
    """Recursively converts Pydantic objects and nested structures to JSON-serializable types."""
    if val is None:
        return None
    if hasattr(val, "model_dump"):
        return val.model_dump(mode="json")
    if isinstance(val, list):
        return [serialize_state_val(item) for item in val]
    if isinstance(val, dict):
        return {k: serialize_state_val(v) for k, v in val.items()}
    return val

async def init_state(callback_context: CallbackContext) -> None:
    """Initializes all required session state keys, resets working state, seeds the transcript, and wipes outputs."""
    state = callback_context.state
    if state.get("_initialized"):
        print("[callback] Session already initialized. Skipping state reset.")
        return
        
    print("[callback] Resetting state keys for a fresh run...")
    # Initialize basic state keys (always clear them at start of run to avoid cross-project contamination)
    keys = [
        "brief", "personas", "statements", "requirements", "user_stories", 
        "open_questions", "decisions", "domain_entities", "srs_review", 
        "intake_result", "candidate_statement_count", "source_registry", "mermaid_diagrams"
    ]
    for key in keys:
        state[key] = [] if key in ["personas", "statements", "requirements", "user_stories", "open_questions", "decisions", "domain_entities"] else ""
            
    # Check if there is user-provided input message in the UI
    user_input_text = ""
    try:
        inv_ctx = callback_context.get_invocation_context()
        if inv_ctx and inv_ctx.user_content and inv_ctx.user_content.parts:
            parts = [p.text for p in inv_ctx.user_content.parts if getattr(p, "text", None)]
            user_input_text = "".join(parts).strip()
    except Exception as e:
        print(f"[callback] Error checking user input: {e}")

    # Seed transcript: prioritize user UI input, then fall back to disk or pre-existing state
    if user_input_text:
        state["transcript"] = user_input_text
        state["source_provenance"] = ["ui_input"]
        print(f"[callback] Fresh run: loaded transcript from user UI input (length={len(state['transcript'])})")
    elif not state.get("transcript"):
        transcript_path = Path("sample_transcript.txt")
        if not transcript_path.exists():
            # Try to resolve relative to this file
            transcript_path = Path(__file__).resolve().parent.parent / "sample_transcript.txt"
            
        if transcript_path.exists():
            try:
                with open(transcript_path, "r", encoding="utf-8") as f:
                    state["transcript"] = f.read()
                state["source_provenance"] = [transcript_path.name]
                print(f"[callback] Fresh run: loaded transcript from disk: {transcript_path} (length={len(state['transcript'])})")
            except Exception as e:
                print(f"[callback] Error loading transcript: {e}")
        else:
            print("[callback] Warning: sample_transcript.txt not found.")
    else:
        print(f"[callback] Transcript already present in state (length={len(state['transcript'])}). Skipping seeding from disk.")
        if "source_provenance" not in state or not state["source_provenance"]:
            state["source_provenance"] = ["transcript"]

    # Wipe output directory at run start (Fix 3)
    try:
        from .settings import Settings
        settings = Settings.load()
        out_dir = Path(settings.io.output_dir)
        if out_dir.exists():
            print(f"[callback] Wiping output directory: {out_dir}")
            import shutil
            for item in out_dir.iterdir():
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
    except Exception as e:
        print(f"[callback] Error wiping output directory: {e}")

    state["_initialized"] = True

async def before_intake_log(callback_context: CallbackContext) -> None:
    transcript = callback_context.state.get("transcript", "")
    prefix = transcript[:150].replace("\n", " ")
    print(f"[TRACE] Intake Agent: transcript length={len(transcript)}, prefix={prefix!r}")

async def before_requirements_log(callback_context: CallbackContext) -> None:
    transcript = callback_context.state.get("transcript", "")
    prefix = transcript[:150].replace("\n", " ")
    print(f"[TRACE] Requirements Agent: transcript length={len(transcript)}, prefix={prefix!r}")

async def before_writer_log(callback_context: CallbackContext) -> None:
    transcript = callback_context.state.get("transcript", "")
    prefix = transcript[:150].replace("\n", " ")
    print(f"[TRACE] SRS Writer Agent: transcript length={len(transcript)}, prefix={prefix!r}")

async def unpack_intake(callback_context: CallbackContext) -> None:
    """Unpacks the IntakeResult output into separate state keys as JSON-serializable dicts."""
    print("[callback] Unpacking intake result...")
    res = callback_context.state.get("intake_result")
    if res:
        if hasattr(res, "brief"):
            callback_context.state["brief"] = serialize_state_val(res.brief)
            callback_context.state["personas"] = serialize_state_val(res.personas)
            callback_context.state["statements"] = serialize_state_val(res.statements)
            callback_context.state["open_questions"] = serialize_state_val(getattr(res, "open_questions", []))
            callback_context.state["candidate_statement_count"] = len(res.statements)
        elif isinstance(res, dict):
            callback_context.state["brief"] = serialize_state_val(res.get("brief"))
            callback_context.state["personas"] = serialize_state_val(res.get("personas", []))
            callback_context.state["statements"] = serialize_state_val(res.get("statements", []))
            callback_context.state["open_questions"] = serialize_state_val(res.get("open_questions", []))
            callback_context.state["candidate_statement_count"] = len(res.get("statements", []))
    
    check_stage_emptiness_warning("personas", "Persona Building (Intake)", callback_context)
    check_stage_emptiness_warning("statements", "Statement Extraction (Intake)", callback_context)
    return None

async def ground_requirements(callback_context: CallbackContext) -> None:
    """Post-agent callback for requirements_agent and srs_writer.
    
    Verifies that all requirements with real human sources are strictly grounded
    with verbatim excerpts in the transcript. Promotes grounded requirements to 'confirmed'
    and demotes ungrounded ones to 'open' with recorded warnings.
    """
    print("[callback] Running ground_requirements callback...")
    
    req_list_data = callback_context.state.get("requirements")
    if not req_list_data:
        print("[callback] No requirements found in state to ground.")
        return None

    if isinstance(req_list_data, dict):
        req_list = RequirementList.model_validate(req_list_data)
    elif isinstance(req_list_data, RequirementList):
        req_list = req_list_data
    else:
        req_list = RequirementList(requirements=to_pydantic_list(req_list_data, Requirement))

    transcript = callback_context.state.get("transcript", "")
    if not transcript:
        print("[callback] Warning: No transcript found in state for grounding.")
        return None

    haystack = _norm(transcript)
    promotions_count = 0
    demotions_count = 0

    for r in req_list.requirements:
        real_sources = [s for s in r.source if s.origin in REAL_ORIGINS]
        if real_sources:
            # Check if all real sources are grounded verbatim
            all_grounded = True
            for s in real_sources:
                if not s.excerpt or not check_confirmed_grounding(s.excerpt, haystack):
                    all_grounded = False
                    print(f"[callback] WARNING: Grounding failed for source excerpt on {r.id}: {s.excerpt!r}")
            
            if all_grounded:
                if r.status != Status.confirmed:
                    print(f"[callback] Promoting requirement {r.id} to confirmed (grounded and has real human source).")
                    r.status = Status.confirmed
                    promotions_count += 1
                
                # Safety fallback: ensure confirmed functional requirement has at least one AC
                if r.type == RequirementType.functional and not r.acceptance_criteria:
                    print(f"[callback] Safety fallback: Adding default acceptance criteria for confirmed requirement {r.id}.")
                    match = re.match(r"^REQ-(\d+)$", r.id)
                    req_num = match.group(1) if match else "000"
                    r.acceptance_criteria = [
                        AcceptanceCriterion(
                            id=f"AC-{req_num}-a",
                            given="The system is running",
                            when="The stakeholder's requirement is exercised",
                            then="The system behaves exactly as described in the requirement statement"
                        )
                    ]
            else:
                # real origin but excerpt not found -> open + warn
                print(f"[callback] WARNING: Requirement {r.id} has real origin but failed grounding. Setting to open.")
                if r.status != Status.open:
                    r.status = Status.open
                    r.rationale = (r.rationale or "") + " [Grounding Callback Alert: Set to open because excerpt was not verbatim in transcript.]"
                    demotions_count += 1
        else:
            # Synthetic or no sources -> assumed/open per existing rules
            if r.status == Status.confirmed:
                has_synthetic = any(s.origin not in REAL_ORIGINS for s in r.source)
                target_status = Status.assumed if has_synthetic else Status.open
                print(f"[callback] SECURITY CONTROL: Requirement {r.id} marked confirmed but has no real human source. Demoting to {target_status.value}.")
                r.status = target_status
                r.rationale = (r.rationale or "") + f" [Grounding Callback Alert: Demoted from confirmed because it lacks a real human source.]"
                demotions_count += 1

    print(f"[callback] Grounding check complete. Promotions: {promotions_count}, Demotions: {demotions_count}.")
    
    # Store list of Requirements in state (JSON-serialized)
    callback_context.state["requirements"] = serialize_state_val(req_list.requirements)
    check_stage_emptiness_warning("requirements", "Requirements Generation/Refinement", callback_context)
    return None

async def ground_and_check_coverage(callback_context: CallbackContext) -> None:
    """Post-agent callback for user_story_agent.
    
    Verifies that all MUST/SHOULD requirements in the session state are covered
    by at least one user story. Prints warnings for any uncovered requirements.
    """
    print("[callback] Running ground_and_check_coverage callback...")
    
    stories_data = callback_context.state.get("user_stories")
    if not stories_data:
        print("[callback] No user stories found in state.")
        return None

    if isinstance(stories_data, dict):
        stories = UserStoryList.model_validate(stories_data)
    elif isinstance(stories_data, UserStoryList):
        stories = stories_data
    else:
        stories = UserStoryList(user_stories=to_pydantic_list(stories_data, UserStory))

    requirements_data = callback_context.state.get("requirements", [])
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

    # Coverage Rule: Every must/should priority requirement must be implemented by >=1 story
    must_should_ids = {
        r.id for r in requirements
        if r.priority in (Priority.must, Priority.should) and r.status != Status.deprecated
    }

    covered_ids = set()
    for us in stories.user_stories:
        covered_ids.update(us.requirement_ids)

    uncovered = must_should_ids - covered_ids
    if uncovered:
        print(f"[callback] WARNING: The following MUST/SHOULD requirements are not covered by user stories: {sorted(uncovered)}")
    else:
        print("[callback] Coverage validation passed: All MUST/SHOULD requirements are covered by user stories.")

    # Store list of UserStories in state (JSON-serialized)
    callback_context.state["user_stories"] = serialize_state_val(stories.user_stories)
    check_stage_emptiness_warning("user_stories", "User Story Writer", callback_context)
    return None

async def process_qa_review_findings(callback_context: CallbackContext) -> None:
    """Post-agent callback for qa_critic.
    
    Converts QAFindings into OpenQuestions and appends them to session state.
    """
    print("[callback] Running process_qa_review_findings callback...")
    state = callback_context.state
    review_data = state.get("srs_review")
    if not review_data:
        print("[callback] No QA review findings found in state.")
        return None

    # Load open questions
    oq_list = []
    existing_oqs = state.get("open_questions") or []
    if existing_oqs:
        oq_list = to_pydantic_list(existing_oqs, OpenQuestion)

    # Convert review findings
    findings = []
    if hasattr(review_data, "findings"):
        findings = review_data.findings
    elif isinstance(review_data, dict) and "findings" in review_data:
        findings = review_data["findings"]

    next_num = len(oq_list) + 1
    findings_list = to_pydantic_list(findings, QAFinding)
    
    for f in findings_list:
        # Avoid duplicates based on the question text
        exists = any(q.question == f.note for q in oq_list)
        if not exists:
            blocking = (f.severity == "block")
            oq_id = f"OQ-{next_num:03d}"
            oq = OpenQuestion(
                id=oq_id,
                question=f.note,
                synthetic_origin=SourceOrigin.reviewer,
                status=OpenQuestionStatus.open,
                blocking=blocking,
                blocking_rationale=f.note if blocking else None,
                affects=[f.target_id] if f.target_id else [],
                default_if_deferred=DefaultIfDeferred.leave_open
            )
            oq_list.append(oq)
            next_num += 1

    state["open_questions"] = serialize_state_val(oq_list)
    print(f"[callback] Processed {len(findings_list)} findings, total open questions in state: {len(oq_list)}")
    return None

async def auto_resolve_open_questions_in_test(callback_context: CallbackContext) -> None:
    """Pre-agent callback for elicitation_agent to auto-resolve open questions in tests."""
    if os.getenv("PLINTH_TEST_AUTO_RESOLVE") == "true":
        state = callback_context.state
        oqs = state.get("open_questions") or []
        if oqs:
            oq_list = to_pydantic_list(oqs, OpenQuestion)
            for q in oq_list:
                if q.status == OpenQuestionStatus.open:
                    q.status = OpenQuestionStatus.answered
                    q.answer = f"Auto-resolved answer for test to {q.question}"
            state["open_questions"] = serialize_state_val(oq_list)
            print("[callback] Test mode: Auto-resolved all open questions to bypass human gate.")
    return None

def log_stage_output_count(state_key: str, display_name: str, callback_context: CallbackContext) -> None:
    val = callback_context.state.get(state_key)
    count = 0
    if isinstance(val, list):
        count = len(val)
    elif isinstance(val, dict):
        if state_key == "mermaid_diagrams":
            count = sum(1 for v in val.values() if v and str(v).strip())
        else:
            count = len(val)
    elif hasattr(val, "__len__"):
        count = len(val)
    elif val:
        # If it's a Pydantic object
        if hasattr(val, "domain_entities"):
            count = len(val.domain_entities)
        elif hasattr(val, "user_stories"):
            count = len(val.user_stories)
        elif hasattr(val, "requirements"):
            count = len(val.requirements)
        elif hasattr(val, "use_case_diagram"):
            diagrams = [
                getattr(val, "use_case_diagram", ""),
                getattr(val, "sequence_diagram", ""),
                getattr(val, "activity_diagram", "")
            ]
            count = sum(1 for d in diagrams if d and str(d).strip())
        else:
            count = 1
            
    print(f"\n[STAGE LOG] Stage '{display_name}' output count for '{state_key}': {count}")
    
    if count == 0:
        transcript = callback_context.state.get("transcript", "")
        if transcript and len(transcript.strip()) > 0:
            print(f"\n⚠️  [WARNING] Stage '{display_name}' produced an EMPTY result under state key '{state_key}', despite having non-empty transcript input! Please verify model generation.\n")

def check_stage_emptiness_warning(state_key: str, display_name: str, callback_context: CallbackContext) -> None:
    log_stage_output_count(state_key, display_name, callback_context)

async def before_domain_modeler_log(callback_context: CallbackContext) -> None:
    transcript = callback_context.state.get("transcript", "")
    requirements = callback_context.state.get("requirements", [])
    print(f"\n[TRACE] Domain Modeler Agent: transcript length={len(transcript)}, requirements count={len(requirements)}")

async def before_diagram_log(callback_context: CallbackContext) -> None:
    transcript = callback_context.state.get("transcript", "")
    requirements = callback_context.state.get("requirements", [])
    domain_entities = callback_context.state.get("domain_entities", [])
    print(f"\n[TRACE] Diagram Agent: transcript length={len(transcript)}, requirements count={len(requirements)}, domain_entities count={len(domain_entities)}")

async def check_domain_model_emptiness(callback_context: CallbackContext) -> None:
    raw_entities = callback_context.state.get("domain_entities")
    print(f"\n[TRACE] Domain Modeler raw output in state: {raw_entities}")
    if raw_entities:
        from .schemas import DomainEntityList
        if isinstance(raw_entities, DomainEntityList):
            callback_context.state["domain_entities"] = serialize_state_val(raw_entities.domain_entities)
        elif isinstance(raw_entities, dict) and "domain_entities" in raw_entities:
            callback_context.state["domain_entities"] = serialize_state_val(raw_entities["domain_entities"])
        elif hasattr(raw_entities, "domain_entities"):
            callback_context.state["domain_entities"] = serialize_state_val(raw_entities.domain_entities)
            
    log_stage_output_count("domain_entities", "Domain Modeling", callback_context)

async def check_diagram_emptiness(callback_context: CallbackContext) -> None:
    raw_diagrams = callback_context.state.get("mermaid_diagrams")
    print(f"\n[TRACE] Diagram Agent raw output in state: {raw_diagrams}")
    if raw_diagrams:
        from .schemas import MermaidDiagramList
        if isinstance(raw_diagrams, MermaidDiagramList):
            callback_context.state["mermaid_diagrams"] = {
                "use_case": getattr(raw_diagrams, "use_case_diagram", ""),
                "sequence": getattr(raw_diagrams, "sequence_diagram", ""),
                "activity": getattr(raw_diagrams, "activity_diagram", "")
            }
        elif hasattr(raw_diagrams, "use_case_diagram"):
            callback_context.state["mermaid_diagrams"] = {
                "use_case": getattr(raw_diagrams, "use_case_diagram", ""),
                "sequence": getattr(raw_diagrams, "sequence_diagram", ""),
                "activity": getattr(raw_diagrams, "activity_diagram", "")
            }
            
    log_stage_output_count("mermaid_diagrams", "UML Diagram Authoring", callback_context)
