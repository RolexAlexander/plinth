import pytest
from pydantic import ValidationError
from requirements_crew.models import (
    Requirement,
    RequirementType,
    Status,
    Priority,
    Source,
    SourceOrigin,
    AcceptanceCriterion,
    Metric,
    OpenQuestion,
    OpenQuestionStatus,
)

def test_valid_requirement():
    # A valid confirmed functional requirement with a real human source and acceptance criteria
    req = Requirement(
        id="REQ-001",
        type=RequirementType.functional,
        statement="The system must allow users to log in.",
        status=Status.confirmed,
        priority=Priority.must,
        source=[Source(origin=SourceOrigin.transcript, ref="doc.txt", excerpt="log in")],
        acceptance_criteria=[
            AcceptanceCriterion(
                id="AC-001-a",
                given="User is on login page",
                when="User enters correct credentials",
                then="User is logged in"
            )
        ]
    )
    assert req.id == "REQ-001"
    assert req.status == Status.confirmed

def test_invalid_id_format():
    # ID does not match REQ-\d+
    with pytest.raises(ValidationError) as exc_info:
        Requirement(
            id="REQ-abc",
            type=RequirementType.functional,
            statement="Invalid ID",
            status=Status.open,
            priority=Priority.must
        )
    assert "REQ-\\d+" in str(exc_info.value)

def test_r1_confirmed_without_real_source():
    # R1: status == confirmed but only synthetic sources
    with pytest.raises(ValidationError) as exc_info:
        Requirement(
            id="REQ-002",
            type=RequirementType.functional,
            statement="Only synthetic sources",
            status=Status.confirmed,
            priority=Priority.must,
            source=[Source(origin=SourceOrigin.analyst_inference, ref="spec", excerpt="infer")],
            acceptance_criteria=[
                AcceptanceCriterion(
                    id="AC-002-a",
                    given="x",
                    when="y",
                    then="z"
                )
            ]
        )
    assert "no real human sources" in str(exc_info.value)

def test_r2_non_functional_without_metric():
    # R2: type == non_functional but metric is None
    with pytest.raises(ValidationError) as exc_info:
        Requirement(
            id="REQ-003",
            type=RequirementType.non_functional,
            statement="Must be fast",
            status=Status.open,
            priority=Priority.should,
            metric=None
        )
    assert "has no metric defined" in str(exc_info.value)

def test_r2_non_functional_with_empty_metric_target():
    # R2: type == non_functional but metric target is empty
    with pytest.raises(ValidationError) as exc_info:
        Requirement(
            id="REQ-004",
            type=RequirementType.non_functional,
            statement="Must be fast",
            status=Status.open,
            priority=Priority.should,
            metric=Metric(dimension="latency", target="")
        )
    assert "empty metric target" in str(exc_info.value)

def test_r3_confirmed_functional_without_ac():
    # R3: functional + confirmed but no acceptance criteria
    with pytest.raises(ValidationError) as exc_info:
        Requirement(
            id="REQ-005",
            type=RequirementType.functional,
            statement="No AC",
            status=Status.confirmed,
            priority=Priority.must,
            source=[Source(origin=SourceOrigin.transcript, ref="doc.txt", excerpt="yes")]
        )
    assert "has no acceptance criteria" in str(exc_info.value)

def test_r5_invalid_ac_id_format():
    # R5: AcceptanceCriterion ID pattern AC-\d+-[a-z]
    with pytest.raises(ValidationError) as exc_info:
        AcceptanceCriterion(
            id="AC-1",
            given="a",
            when="b",
            then="c"
        )
    assert "AC-\\d+-[a-z]" in str(exc_info.value)

def test_valid_open_question():
    oq = OpenQuestion(
        id="OQ-001",
        question="How many users?",
        synthetic_origin=SourceOrigin.client_proxy,
        blocking=True,
        blocking_rationale="Gates the performance spec"
    )
    assert oq.id == "OQ-001"

def test_invalid_open_question_blocking_no_rationale():
    # OpenQuestion blocking=True requires blocking_rationale
    with pytest.raises(ValidationError) as exc_info:
        OpenQuestion(
            id="OQ-002",
            question="How many users?",
            synthetic_origin=SourceOrigin.client_proxy,
            blocking=True,
            blocking_rationale=None
        )
    assert "has no blocking rationale" in str(exc_info.value)
