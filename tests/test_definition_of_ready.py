import pytest
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
    Metric,
    OpenQuestion,
    OpenQuestionStatus,
    UserStory,
)
from requirements_crew.validation.definition_of_ready import compute_definition_of_ready

@pytest.fixture
def base_package():
    return RequirementsPackage(
        brief=ProjectBrief(
            project_name="Test DoR",
            vision="A test vision"
        ),
        requirements=[],
        user_stories=[],
        domain_entities=[],
        open_questions=[]
    )

def test_dor_fully_ready(base_package):
    req = Requirement(
        id="REQ-001",
        type=RequirementType.functional,
        statement="Auth",
        status=Status.confirmed,
        priority=Priority.must,
        source=[Source(origin=SourceOrigin.transcript)],
        acceptance_criteria=[AcceptanceCriterion(id="AC-001-a", given="g", when="w", then="t")]
    )
    story = UserStory(
        id="US-001",
        epic="Auth Epic",
        as_a="user",
        i_want="login",
        so_that="access",
        requirement_ids=["REQ-001"],
        priority=Priority.must
    )
    base_package.requirements.append(req)
    base_package.user_stories.append(story)
    
    dor = compute_definition_of_ready(base_package)
    assert dor["every_requirement_has_source"] is True
    assert dor["every_nfr_has_metric"] is True
    assert dor["every_confirmed_functional_has_ac"] is True
    assert dor["no_blocking_open_questions"] is True
    assert dor["no_dangling_references"] is True
    assert dor["no_orphan_requirements"] is True

def test_dor_missing_source(base_package):
    # Requirement with no source (note: confirmed req requires source at model construction,
    # so we must create it as open or assumed with empty source list)
    req = Requirement(
        id="REQ-001",
        type=RequirementType.functional,
        statement="Auth",
        status=Status.open,
        priority=Priority.must,
        source=[]
    )
    base_package.requirements.append(req)
    dor = compute_definition_of_ready(base_package)
    assert dor["every_requirement_has_source"] is False

def test_dor_blocking_question_present(base_package):
    req = Requirement(
        id="REQ-001",
        type=RequirementType.functional,
        statement="Auth",
        status=Status.confirmed,
        priority=Priority.must,
        source=[Source(origin=SourceOrigin.transcript)],
        acceptance_criteria=[AcceptanceCriterion(id="AC-001-a", given="g", when="w", then="t")]
    )
    story = UserStory(
        id="US-001",
        epic="Auth Epic",
        as_a="user",
        i_want="login",
        so_that="access",
        requirement_ids=["REQ-001"],
        priority=Priority.must
    )
    oq = OpenQuestion(
        id="OQ-001",
        question="Which LDAP server?",
        synthetic_origin=SourceOrigin.client_proxy,
        blocking=True,
        blocking_rationale="Blocks integration configuration",
        status=OpenQuestionStatus.open
    )
    base_package.requirements.append(req)
    base_package.user_stories.append(story)
    base_package.open_questions.append(oq)
    
    dor = compute_definition_of_ready(base_package)
    assert dor["no_blocking_open_questions"] is False
