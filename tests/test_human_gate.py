import json
import tempfile
from pathlib import Path
from requirements_crew.models import (
    RequirementsPackage,
    ProjectBrief,
    Requirement,
    RequirementType,
    Status,
    Priority,
    Source,
    SourceOrigin,
    AcceptanceCriterion,
    OpenQuestion,
    OpenQuestionStatus,
    DefaultIfDeferred,
)
from requirements_crew.flow.human_gate import (
    ConsoleHumanGate,
    GatePayload,
    GateResponse,
    apply_gate_responses,
)

def test_apply_gate_responses_answered():
    req = Requirement(
        id="REQ-001",
        type=RequirementType.functional,
        statement="Auth",
        status=Status.open,
        priority=Priority.must,
        source=[]
    )
    oq = OpenQuestion(
        id="OQ-001",
        question="What auth?",
        synthetic_origin=SourceOrigin.client_proxy,
        blocking=True,
        blocking_rationale="Gates authentication integration details",
        affects=["REQ-001"]
    )
    pkg = RequirementsPackage(
        brief=ProjectBrief(project_name="Test", vision="Vision"),
        requirements=[req],
        open_questions=[oq]
    )
    
    # User resolves the question with an answer
    resp = GateResponse(
        approved=True,
        answers={"OQ-001": "Use OAuth2"},
        deferred_ids=[]
    )
    
    apply_gate_responses(pkg, resp)
    
    # Verify open question is answered
    assert pkg.open_questions[0].status == OpenQuestionStatus.answered
    assert pkg.open_questions[0].answer == "Use OAuth2"
    
    # Verify requirement is promoted to confirmed
    assert pkg.requirements[0].status == Status.confirmed
    assert any(s.origin == SourceOrigin.human_answer for s in pkg.requirements[0].source)
    assert any("Use OAuth2" in s.excerpt for s in pkg.requirements[0].source)

def test_apply_gate_responses_deferred_adopt():
    req = Requirement(
        id="REQ-001",
        type=RequirementType.functional,
        statement="Auth",
        status=Status.open,
        priority=Priority.must,
        source=[]
    )
    oq = OpenQuestion(
        id="OQ-001",
        question="What auth?",
        synthetic_origin=SourceOrigin.client_proxy,
        blocking=True,
        blocking_rationale="Gates authentication integration details",
        proposed_assumption="Use dummy auth",
        default_if_deferred=DefaultIfDeferred.adopt_assumption,
        affects=["REQ-001"]
    )
    pkg = RequirementsPackage(
        brief=ProjectBrief(project_name="Test", vision="Vision"),
        requirements=[req],
        open_questions=[oq]
    )
    
    # User defers the question
    resp = GateResponse(
        approved=True,
        answers={},
        deferred_ids=["OQ-001"]
    )
    
    apply_gate_responses(pkg, resp)
    
    # Verify open question is deferred
    assert pkg.open_questions[0].status == OpenQuestionStatus.deferred
    
    # Verify requirement is set to assumed and gets the assumption source
    assert pkg.requirements[0].status == Status.assumed
    assert any(s.origin == SourceOrigin.analyst_inference for s in pkg.requirements[0].source)
    assert any("dummy auth" in s.excerpt for s in pkg.requirements[0].source)

def test_apply_gate_responses_deferred_drop():
    req = Requirement(
        id="REQ-001",
        type=RequirementType.functional,
        statement="Auth",
        status=Status.open,
        priority=Priority.must,
        source=[]
    )
    oq = OpenQuestion(
        id="OQ-001",
        question="What auth?",
        synthetic_origin=SourceOrigin.client_proxy,
        blocking=True,
        blocking_rationale="Gates authentication integration details",
        default_if_deferred=DefaultIfDeferred.drop_scope,
        affects=["REQ-001"]
    )
    pkg = RequirementsPackage(
        brief=ProjectBrief(project_name="Test", vision="Vision"),
        requirements=[req],
        open_questions=[oq]
    )
    
    # User defers the question which has drop_scope action
    resp = GateResponse(
        approved=True,
        answers={},
        deferred_ids=["OQ-001"]
    )
    
    apply_gate_responses(pkg, resp)
    
    # Verify open question is deferred
    assert pkg.open_questions[0].status == OpenQuestionStatus.deferred
    
    # Verify requirement status is set to deprecated
    assert pkg.requirements[0].status == Status.deprecated

def test_console_human_gate_reads_answers_file():
    brief = ProjectBrief(project_name="ECommerce", vision="Store")
    oq = OpenQuestion(
        id="OQ-001",
        question="Which db?",
        synthetic_origin=SourceOrigin.client_proxy,
        blocking=True,
        blocking_rationale="Gates persistence choice"
    )
    payload = GatePayload(brief=brief, blocking_questions=[oq])
    
    with tempfile.TemporaryDirectory() as tmpdir:
        ans_file = Path(tmpdir) / "test_answers.json"
        
        # Write template
        with open(ans_file, "w", encoding="utf-8") as f:
            json.dump({"OQ-001": "Use PostgreSQL"}, f)
            
        gate = ConsoleHumanGate(answers_file=str(ans_file))
        res = gate.request(payload)
        
        assert res.approved is True
        assert res.answers["OQ-001"] == "Use PostgreSQL"
        assert len(res.deferred_ids) == 0
