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
from .schemas import RequirementList, UserStoryList, QaReviewFindings, QAFinding
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
    """Initializes all required session state keys and seeds the transcript."""
    print("[callback] Initializing state keys...")
    state = callback_context.state
    
    # Initialize basic state keys
    keys = [
        "brief", "personas", "statements", "requirements", "user_stories", 
        "open_questions", "decisions", "domain_entities", "srs_review", 
        "intake_result", "candidate_statement_count"
    ]
    for key in keys:
        if key not in state:
            state[key] = [] if key in ["personas", "statements", "requirements", "user_stories", "open_questions", "decisions", "domain_entities"] else ""
            
    # Seed transcript if not already set
    if not state.get("transcript"):
        transcript_path = Path("sample_transcript.txt")
        if not transcript_path.exists():
            # Try to resolve relative to this file
            transcript_path = Path(__file__).resolve().parent.parent / "sample_transcript.txt"
        if transcript_path.exists():
            try:
                with open(transcript_path, "r", encoding="utf-8") as f:
                    state["transcript"] = f.read()
                print(f"[callback] Successfully seeded transcript from: {transcript_path}")
            except Exception as e:
                print(f"[callback] Error loading transcript: {e}")
        else:
            print("[callback] Warning: sample_transcript.txt not found.")

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
