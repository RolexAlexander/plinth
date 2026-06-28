import json
import tempfile
from pathlib import Path
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
    UserStory,
    DomainEntity,
    EntityAttribute,
    Relationship,
    OpenQuestion,
    OpenQuestionStatus,
    Decision,
)
from requirements_crew.packaging.render import (
    render_srs,
    render_personas,
    render_user_stories,
    render_open_questions,
    render_decisions,
    render_domain_class_diagram,
)
from requirements_crew.packaging.traceability import (
    build_traceability_matrix,
    render_traceability_markdown,
)
from requirements_crew.packaging.manifest import generate_handoff_manifest
from requirements_crew.packaging.writer import write_package_to_disk

@pytest.fixture
def sample_package():
    req = Requirement(
        id="REQ-001",
        type=RequirementType.functional,
        statement="The system shall allow user registration.",
        status=Status.confirmed,
        priority=Priority.must,
        source=[Source(origin=SourceOrigin.transcript, ref="trans.txt", excerpt="register")],
        acceptance_criteria=[
            AcceptanceCriterion(
                id="AC-001-a",
                given="User is guest",
                when="User registers",
                then="User account is created"
            )
        ]
    )
    story = UserStory(
        id="US-001",
        epic="Registration Epic",
        as_a="Guest",
        i_want="to register",
        so_that="I can login",
        requirement_ids=["REQ-001"],
        priority=Priority.must
    )
    entity = DomainEntity(
        id="ENT-User",
        name="User",
        attributes=[
            EntityAttribute(name="username", type="str", nullable=False),
            EntityAttribute(name="email", type="str", nullable=False)
        ]
    )
    oq = OpenQuestion(
        id="OQ-001",
        question="Is email confirmation required?",
        synthetic_origin=SourceOrigin.client_proxy,
        blocking=False,
        status=OpenQuestionStatus.open
    )
    dec = Decision(
        id="DEC-001",
        statement="Use SQL database.",
        rationale="Proven reliability."
    )
    
    return RequirementsPackage(
        brief=ProjectBrief(
            project_name="ECommerce",
            vision="A simple ecommerce store",
            goals=["Goal 1"],
            scope=["Scope 1"],
            success_criteria=["Success 1"]
        ),
        requirements=[req],
        user_stories=[story],
        domain_entities=[entity],
        open_questions=[oq],
        decisions=[dec],
        source_provenance=["trans.txt"]
    )

def test_rendering_outputs(sample_package):
    srs_md = render_srs(sample_package)
    assert "Software Requirements Specification" in srs_md
    assert "REQ-001" in srs_md
    assert "The system shall allow user registration" in srs_md
    
    personas_md = render_personas(sample_package)
    assert "User Personas" in personas_md
    
    stories_md = render_user_stories(sample_package)
    assert "Guest" in stories_md
    
    questions_md = render_open_questions(sample_package)
    assert "Is email confirmation required?" in questions_md
    
    decisions_md = render_decisions(sample_package)
    assert "Use SQL database." in decisions_md
    
    mermaid_diag = render_domain_class_diagram(sample_package)
    assert "classDiagram" in mermaid_diag
    assert "class ENT_User" in mermaid_diag or "class User" in mermaid_diag

def test_traceability_matrix(sample_package):
    matrix = build_traceability_matrix(sample_package)
    assert "REQ-001" in matrix
    assert "US-001" in matrix["REQ-001"]["user_stories"]
    assert "ENT-User" in matrix["REQ-001"]["entities"]
    
    trace_md = render_traceability_markdown(matrix)
    assert "Traceability Matrix" in trace_md
    assert "REQ-001" in trace_md

def test_handoff_manifest(sample_package):
    manifest = generate_handoff_manifest(sample_package)
    assert manifest["project_name"] == "ECommerce"
    assert manifest["counts"]["requirements"] == 1
    assert manifest["counts"]["confirmed"] == 1
    assert len(manifest["blocking_questions"]) == 0
    # No blocking questions and DoR passes => ready_for is populated
    assert "architecture_agent" in manifest["ready_for"]

def test_write_package_to_disk(sample_package):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        write_package_to_disk(sample_package, tmp_path)
        
        # Verify human-readable files exist
        assert (tmp_path / "srs.md").exists()
        assert (tmp_path / "personas.md").exists()
        assert (tmp_path / "user_stories.md").exists()
        assert (tmp_path / "open_questions.md").exists()
        assert (tmp_path / "decisions.md").exists()
        assert (tmp_path / "uml" / "domain_class.mermaid").exists()
        assert (tmp_path / "traceability.md").exists()
        
        # Verify machine-readable files exist
        assert (tmp_path / "requirements.json").exists()
        assert (tmp_path / "domain_model.json").exists()
        assert (tmp_path / "user_stories.json").exists()
        assert (tmp_path / "personas.json").exists()
        assert (tmp_path / "open_questions.json").exists()
        assert (tmp_path / "decisions.json").exists()
        assert (tmp_path / "traceability.json").exists()
        assert (tmp_path / "handoff_manifest.json").exists()
        
        # Spot check JSON content
        with open(tmp_path / "handoff_manifest.json", "r", encoding="utf-8") as f:
            manifest = json.load(f)
            assert manifest["project_name"] == "ECommerce"
            assert "architecture_agent" in manifest["ready_for"]

def test_manifest_ready_for_with_orphans():
    # Package with a confirmed requirement but NO user stories (so it has an orphan)
    req = Requirement(
        id="REQ-001",
        type=RequirementType.functional,
        statement="Auth",
        status=Status.confirmed,
        priority=Priority.must,
        source=[Source(origin=SourceOrigin.transcript)],
        acceptance_criteria=[AcceptanceCriterion(id="AC-001-a", given="g", when="w", then="t")]
    )
    pkg = RequirementsPackage(
        brief=ProjectBrief(
            project_name="Orphan Test",
            vision="A test vision"
        ),
        requirements=[req],
        user_stories=[
            UserStory(
                id="US-001",
                epic="Auth Epic",
                as_a="user",
                i_want="login",
                so_that="access",
                requirement_ids=[], # Empty, so REQ-001 is still an orphan
                priority=Priority.must
            )
        ],
        domain_entities=[],
        open_questions=[]
    )
    
    # Under orphan_check="warn" (default), it should NOT block ready_for
    manifest_warn = generate_handoff_manifest(pkg, orphan_check="warn")
    assert manifest_warn["definition_of_ready"]["no_orphan_requirements"] is False
    assert "architecture_agent" in manifest_warn["ready_for"]
    
    # Under orphan_check="fail", it SHOULD block ready_for
    manifest_fail = generate_handoff_manifest(pkg, orphan_check="fail")
    assert manifest_fail["definition_of_ready"]["no_orphan_requirements"] is False
    assert manifest_fail["ready_for"] == []

