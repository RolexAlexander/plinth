import json
import os
import tempfile
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from requirements_crew.flow.requirements_flow import RequirementsFlow, FlowState
from requirements_crew.flow.human_gate import GateResponse, GatePayload
from requirements_crew.settings import Settings
from requirements_crew.models import (
    RequirementsPackage,
    ProjectBrief,
    Requirement,
    RequirementType,
    Status,
    Priority,
    Source,
    SourceOrigin,
    Persona,
    DomainEntity,
    OpenQuestion,
    OpenQuestionStatus,
    AcceptanceCriterion,
    DefaultIfDeferred,
    UserStory,
    UserStoryList,
)
from requirements_crew.models.outputs import (
    SourceList,
    BriefAndRequirements,
    PersonaList,
    OpenQuestionList,
    RequirementList,
    DomainEntityList,
    MermaidDiagramList,
    QaReviewFindings,
    ProxyReviewFindings,
)

# Mocked outputs for the Crews
class MockTaskOutput:
    def __init__(self, pydantic_obj):
        self.pydantic = pydantic_obj
        self.raw = "mock raw output"

class MockCrewResult:
    def __init__(self, task_outputs, final_pydantic=None):
        self.tasks_output = [MockTaskOutput(obj) for obj in task_outputs]
        self.pydantic = final_pydantic
        self.raw = "mock raw result"

@pytest.fixture
def mock_crews():
    with patch("requirements_crew.flow.requirements_flow.DiscoveryCrew") as mock_class:
        # We return a mock instance
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        
        # Mock Discovery Crew: 3 sequential tasks
        mock_sources = SourceList(statements=[
            Source(origin=SourceOrigin.transcript, ref="tests/sample_transcript.txt", excerpt="Statement 1")
        ])
        mock_brief_req = BriefAndRequirements(
            brief=ProjectBrief(
                project_name="Mock ECommerce",
                vision="A mock order platform",
                goals=["Process payments"],
                scope=["Guest registration"],
                out_of_scope=["Social login"],
                success_criteria=["Fast page load"]
            ),
            requirements=[
                Requirement(
                    id="REQ-001",
                    type=RequirementType.functional,
                    statement="Allow guest registration with username and email",
                    status=Status.confirmed,
                    priority=Priority.must,
                    source=[Source(origin=SourceOrigin.transcript, ref="tests/sample_transcript.txt", excerpt="Statement 1")],
                    acceptance_criteria=[
                        AcceptanceCriterion(
                            id="AC-001-a",
                            given="A guest user",
                            when="They submit username and email",
                            then="An account is created and logged in automatically"
                        )
                    ]
                )
            ]
        )
        mock_personas = PersonaList(personas=[
            Persona(id="PERS-01", name="Guest User", role="Shopper", goals=["Buy items"], pains=["Complex registration"], permissions=["checkout"])
        ])
        
        discovery_result = MockCrewResult([mock_sources, mock_brief_req, mock_personas])
        
        # When DiscoveryCrew().crew().kickoff() is called
        mock_crew_obj = MagicMock()
        mock_crew_obj.kickoff.return_value = discovery_result
        mock_instance.crew.return_value = mock_crew_obj
        
        # Mock other methods for direct tasks creation
        mock_instance.requirements_analyst.return_value = MagicMock()
        mock_instance.client_proxy.return_value = MagicMock()
        mock_instance.srs_writer.return_value = MagicMock()
        mock_instance.domain_modeler.return_value = MagicMock()
        mock_instance.uml_architect.return_value = MagicMock()
        mock_instance.requirements_reviewer.return_value = MagicMock()
        mock_instance.researcher.return_value = MagicMock()
        mock_instance.user_story_writer.return_value = MagicMock()
        
        mock_instance.extract_statements.return_value = MagicMock()
        mock_instance.draft_brief_and_requirements.return_value = MagicMock()
        mock_instance.build_personas.return_value = MagicMock()
        mock_instance.generate_clarifying_questions.return_value = MagicMock()
        mock_instance.author_srs.return_value = MagicMock()
        mock_instance.model_domain.return_value = MagicMock()
        mock_instance.author_diagrams.return_value = MagicMock()
        mock_instance.qa_review.return_value = MagicMock()
        mock_instance.proxy_review.return_value = MagicMock()
        mock_instance.research_context.return_value = MagicMock()
        mock_instance.author_user_stories.return_value = MagicMock()
        
        yield mock_instance

@patch("requirements_crew.flow.requirements_flow.Crew")
@patch("requirements_crew.flow.requirements_flow.ConsoleHumanGate")
def test_requirements_flow_full_execution(mock_gate_class, mock_crew_constructor, mock_crews):
    # Mock Crew constructor and returns for elicitation and actor-critic tasks
    mock_elicitation_crew = MagicMock()
    mock_elicitation_crew.kickoff.return_value = MockCrewResult([], final_pydantic=OpenQuestionList(open_questions=[
        OpenQuestion(
            id="OQ-001",
            question="Should email registration require validation?",
            synthetic_origin=SourceOrigin.client_proxy,
            blocking=True,
            blocking_rationale="Gates guest registration flow",
            proposed_assumption="Yes",
            default_if_deferred=DefaultIfDeferred.adopt_assumption,
            affects=["REQ-001"]
        )
    ]))
    
    mock_actor_crew = MagicMock()
    mock_actor_crew.kickoff.return_value = MockCrewResult([
        RequirementList(requirements=[
            Requirement(
                id="REQ-001",
                type=RequirementType.functional,
                statement="Allow guest registration with username and email",
                status=Status.confirmed,
                priority=Priority.must,
                source=[Source(origin=SourceOrigin.transcript, ref="tests/sample_transcript.txt", excerpt="Statement 1")],
                acceptance_criteria=[
                    AcceptanceCriterion(
                        id="AC-001-a",
                        given="A guest user",
                        when="They submit username and email",
                        then="An account is created and logged in automatically"
                    )
                ]
            )
        ]),
        DomainEntityList(domain_entities=[
            DomainEntity(id="ENT-User", name="User", description="Represents platform user", attributes=[], relationships=[])
        ]),
        MermaidDiagramList(use_case_diagram="usecase-code", sequence_diagram="seq-code", activity_diagram="act-code")
    ])
    
    mock_qa_crew = MagicMock()
    mock_qa_crew.kickoff.return_value = MockCrewResult([], final_pydantic=QaReviewFindings(findings=[]))
    
    mock_stories_crew = MagicMock()
    mock_stories_crew.kickoff.return_value = MockCrewResult([], final_pydantic=UserStoryList(user_stories=[
        UserStory(
            id="US-001",
            epic="Auth",
            as_a="User",
            i_want="Action",
            so_that="Benefit",
            requirement_ids=["REQ-001"],
            priority=Priority.must,
            acceptance_criteria=[AcceptanceCriterion(id="AC-001-b", given="g", when="w", then="t")]
        )
    ]))
    
    # We return these mock crews in sequence of constructor calls
    mock_crew_constructor.side_effect = [
        mock_elicitation_crew,  # for elicitation step
        mock_actor_crew,        # for actor loop round 1
        mock_qa_crew,           # for QA reviewer
        mock_stories_crew,      # for user stories generation
    ]
    
    # Mock Human Gate 1 (gate_scope) to answer OQ-001
    mock_gate_instance1 = MagicMock()
    mock_gate_instance1.request.return_value = GateResponse(
        approved=True,
        answers={"OQ-001": "Yes, require verification code"},
        deferred_ids=[]
    )
    
    # Mock Human Gate 2 (gate_signoff) to approve
    mock_gate_instance2 = MagicMock()
    mock_gate_instance2.request.return_value = GateResponse(
        approved=True,
        answers={},
        deferred_ids=[]
    )
    
    mock_gate_class.side_effect = [
        mock_gate_instance1,  # Gate 1
        mock_gate_instance2   # Gate 2
    ]
    
    # Configure temporary directories for test settings
    with tempfile.TemporaryDirectory() as tmpdir:
        settings = Settings.load()
        settings.io.output_dir = str(Path(tmpdir) / "output")
        settings.client_proxy.mode = "off"
        settings.research.enabled = False  # disable research context tool for simplicity
        
        # Override loaded settings
        with patch("requirements_crew.flow.requirements_flow.Settings.load", return_value=settings):
            
            flow = RequirementsFlow()
            flow.state.brief = ProjectBrief(project_name="Test ECommerce", vision="Vision")
            flow.state.source_provenance = ["tests/sample_transcript.txt"]
            flow.state.transcript_text = "Alice: Hi Bob. Bob: Hi. We need Guest registration. Statement 1"
            
            result = flow.kickoff()
            
            assert result == "complete"
            
            # Verify status changes
            assert flow.state.current_phase == "package"
            assert flow.state.open_questions[0].status == OpenQuestionStatus.answered
            assert flow.state.open_questions[0].answer == "Yes, require verification code"
            assert flow.state.requirements[0].status == Status.confirmed
            
            # Verify packaging output files exist
            out_path = Path(settings.io.output_dir)
            assert (out_path / "handoff_manifest.json").exists()
            assert (out_path / "srs.md").exists()
            assert (out_path / "uml" / "use_case.mermaid").exists()
            assert (out_path / "uml" / "sequence.mermaid").exists()
