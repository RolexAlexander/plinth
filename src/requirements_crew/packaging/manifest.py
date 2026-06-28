from datetime import datetime
from typing import Dict, Any
from ..models.package import RequirementsPackage
from ..models.enums import Status, OpenQuestionStatus
from ..validation.definition_of_ready import compute_definition_of_ready
from ..validation.coverage import check_requirements_coverage

def generate_handoff_manifest(pkg: RequirementsPackage, orphan_check: str = "warn") -> Dict[str, Any]:
    # Counts
    counts = {
        "requirements": len(pkg.requirements),
        "confirmed": sum(1 for r in pkg.requirements if r.status == Status.confirmed),
        "assumed": sum(1 for r in pkg.requirements if r.status == Status.assumed),
        "open": sum(1 for r in pkg.requirements if r.status == Status.open),
    }

    # Open blocking questions
    from ..models.enums import DefaultIfDeferred
    blocking_questions = [
        q.id for q in pkg.open_questions 
        if q.blocking and (
            q.status == OpenQuestionStatus.open or
            (q.status == OpenQuestionStatus.deferred and q.default_if_deferred in (DefaultIfDeferred.leave_open, DefaultIfDeferred.drop_scope))
        )
    ]

    # Check: no confirmed requirement has an affected_by pointing at an open+blocking question
    confirmed_req_affected_by_blocking = False
    for r in pkg.requirements:
        if r.status == Status.confirmed:
            for oq_id in r.affected_by:
                if oq_id in blocking_questions:
                    confirmed_req_affected_by_blocking = True
                    break

    # Compute Definition of Ready
    dor = compute_definition_of_ready(pkg, orphan_check=orphan_check)
    
    # Exclude "no_orphan_requirements" from blocking ready_for if orphan_check is "warn"
    blocking_dor_keys = [
        "every_requirement_has_source",
        "every_nfr_has_metric",
        "every_confirmed_functional_has_ac",
        "no_blocking_open_questions",
        "no_dangling_references",
        "has_user_stories"
    ]
    if orphan_check == "fail":
        blocking_dor_keys.append("no_orphan_requirements")
        
    dor_all_pass = all(dor[key] for key in blocking_dor_keys)

    # ready_for populated ONLY when blocking_questions == [] and blocking DoR passes and not affected by blocking OQ
    if len(blocking_questions) == 0 and dor_all_pass and not confirmed_req_affected_by_blocking:
        ready_for = [
            "architecture_agent",
            "backend_agent",
            "frontend_agent",
            "qa_agent",
            "project_planner_agent"
        ]
    else:
        ready_for = []

    generated_at_str = pkg.generated_at.isoformat() if pkg.generated_at else datetime.now().isoformat()

    # Calculate coverage
    from ..models.enums import SourceOrigin
    transcript_text = ""
    if pkg.source_registry:
        transcript_text = pkg.source_registry.text_for_kind(SourceOrigin.transcript)
    coverage_block = check_requirements_coverage(pkg, transcript_text, pkg.candidate_statement_count)

    manifest = {
        "schema_version": "1.0",
        "project_name": pkg.brief.project_name if pkg.brief else "Unknown",
        "package_version": pkg.package_version,
        "generated_at": generated_at_str,
        "source_provenance": pkg.source_provenance,
        "artifacts": {
            "requirements": { "human": "srs.md", "machine": "requirements.json" },
            "domain_model": { "human": "uml/domain_class.mermaid", "machine": "domain_model.json" },
            "user_stories": { "human": "user_stories.md", "machine": "user_stories.json" },
            "personas":     { "human": "personas.md", "machine": "personas.json" },
            "open_questions": "open_questions.json",
            "decisions": "decisions.md",
            "traceability": "traceability.json"
        },
        "counts": counts,
        "coverage": coverage_block,
        "blocking_questions": blocking_questions,
        "definition_of_ready": dor,
        "ready_for": ready_for,
        "_invariant": "ready_for is empty until blocking_questions==[] and all definition_of_ready checks pass"
    }

    return manifest
