import pytest
from pydantic import ValidationError
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
    UserStory,
    DomainEntity,
    Relationship,
    OpenQuestion,
    OpenQuestionStatus,
)
from requirements_crew.validation.package_validators import (
    validate_package_integrity,
    PackageValidationError,
)

@pytest.fixture
def base_package():
    return RequirementsPackage(
        brief=ProjectBrief(
            project_name="Test Project",
            vision="A test vision"
        ),
        requirements=[],
        user_stories=[],
        domain_entities=[],
        open_questions=[]
    )

def test_valid_package(base_package):
    # A perfectly valid package
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
        i_want="to login",
        so_that="I can access details",
        requirement_ids=["REQ-001"],
        priority=Priority.must
    )
    base_package.requirements.append(req)
    base_package.user_stories.append(story)
    
    # Should not raise any error
    warnings = validate_package_integrity(base_package)
    assert len(warnings) == 0

def test_x1_dangling_requirement_dependency(base_package):
    req = Requirement(
        id="REQ-001",
        type=RequirementType.functional,
        statement="Auth",
        status=Status.confirmed,
        priority=Priority.must,
        source=[Source(origin=SourceOrigin.transcript)],
        acceptance_criteria=[AcceptanceCriterion(id="AC-001-a", given="g", when="w", then="t")],
        depends_on=["REQ-999"] # Dangling
    )
    base_package.requirements.append(req)
    with pytest.raises(PackageValidationError) as exc:
        validate_package_integrity(base_package)
    assert "depends on non-existent requirement" in str(exc.value)

def test_x1_dangling_user_story_reference(base_package):
    story = UserStory(
        id="US-001",
        epic="Auth Epic",
        as_a="user",
        i_want="to login",
        so_that="I can access details",
        requirement_ids=["REQ-999"], # Dangling
        priority=Priority.must
    )
    base_package.user_stories.append(story)
    with pytest.raises(PackageValidationError) as exc:
        validate_package_integrity(base_package)
    assert "references non-existent requirement" in str(exc.value)

def test_x1_dangling_domain_relationship(base_package):
    entity = DomainEntity(
        id="ENT-User",
        name="User",
        relationships=[Relationship(to="ENT-Group", kind="one_to_many")] # Dangling
    )
    base_package.domain_entities.append(entity)
    with pytest.raises(PackageValidationError) as exc:
        validate_package_integrity(base_package)
    assert "has relationship to non-existent entity" in str(exc.value)

def test_x4_dangling_open_question_affects(base_package):
    oq = OpenQuestion(
        id="OQ-001",
        question="What database?",
        synthetic_origin=SourceOrigin.client_proxy,
        blocking=False,
        affects=["REQ-999"] # Dangling
    )
    base_package.open_questions.append(oq)
    with pytest.raises(PackageValidationError) as exc:
        validate_package_integrity(base_package)
    assert "affects non-existent requirement" in str(exc.value)

def test_x5_duplicate_acceptance_criteria_id(base_package):
    req = Requirement(
        id="REQ-001",
        type=RequirementType.functional,
        statement="Auth",
        status=Status.confirmed,
        priority=Priority.must,
        source=[Source(origin=SourceOrigin.transcript)],
        acceptance_criteria=[
            AcceptanceCriterion(id="AC-001-a", given="g", when="w", then="t"),
            AcceptanceCriterion(id="AC-001-a", given="x", when="y", then="z") # Duplicate ID
        ]
    )
    base_package.requirements.append(req)
    with pytest.raises(PackageValidationError) as exc:
        validate_package_integrity(base_package)
    assert "Duplicate Acceptance Criterion ID" in str(exc.value)

def test_x2_orphan_check_warn(base_package):
    req = Requirement(
        id="REQ-001",
        type=RequirementType.functional,
        statement="Auth",
        status=Status.confirmed,
        priority=Priority.must,
        source=[Source(origin=SourceOrigin.transcript)],
        acceptance_criteria=[AcceptanceCriterion(id="AC-001-a", given="g", when="w", then="t")]
    )
    base_package.requirements.append(req)
    # Should only return a warning in default "warn" mode
    warnings = validate_package_integrity(base_package, orphan_check="warn")
    assert len(warnings) == 1
    assert "is not referenced by any User Story" in warnings[0]

def test_x2_orphan_check_fail(base_package):
    req = Requirement(
        id="REQ-001",
        type=RequirementType.functional,
        statement="Auth",
        status=Status.confirmed,
        priority=Priority.must,
        source=[Source(origin=SourceOrigin.transcript)],
        acceptance_criteria=[AcceptanceCriterion(id="AC-001-a", given="g", when="w", then="t")]
    )
    base_package.requirements.append(req)
    # Should fail in "fail" mode
    with pytest.raises(PackageValidationError) as exc:
        validate_package_integrity(base_package, orphan_check="fail")
    assert "is not referenced by any User Story" in str(exc.value)

def test_duplicate_primary_ids(base_package):
    req1 = Requirement(
        id="REQ-001",
        type=RequirementType.functional,
        statement="Auth",
        status=Status.open,
        priority=Priority.must,
        source=[]
    )
    req2 = Requirement(
        id="REQ-001", # Duplicate primary ID
        type=RequirementType.functional,
        statement="Auth duplicate",
        status=Status.open,
        priority=Priority.must,
        source=[]
    )
    base_package.requirements.extend([req1, req2])
    with pytest.raises(PackageValidationError) as exc:
        validate_package_integrity(base_package)
    assert "Duplicate Requirement ID" in str(exc.value)


