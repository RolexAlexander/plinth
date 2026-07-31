import pytest
from unittest.mock import MagicMock
from plinth_agent.models.package import RequirementsPackage, DomainEntity, UserStory, Persona
from plinth_agent.models.records import Requirement, AcceptanceCriterion, Source
from plinth_agent.models.enums import RequirementType, Status, Priority, SourceOrigin
from plinth_agent.validation.definition_of_ready import compute_definition_of_ready
from plinth_agent.packaging.manifest import generate_handoff_manifest
from plinth_agent.callbacks import log_stage_output_count

def test_has_domain_model_readiness():
    # 1. Package with confirmed functional requirements but NO domain entities
    req = Requirement(
        id="REQ-001",
        statement="The system must allow members to book classes.",
        type=RequirementType.functional,
        status=Status.confirmed,
        priority=Priority.must,
        source=[
            Source(
                origin=SourceOrigin.transcript,
                ref="sample_transcript.txt",
                excerpt="walk in, scan a QR code on any machine"
            )
        ],
        acceptance_criteria=[
            AcceptanceCriterion(
                id="AC-001-a",
                given="The member is logged in",
                when="They select a class",
                then="They are booked successfully"
            )
        ]
    )
    
    pkg = RequirementsPackage(
        requirements=[req],
        domain_entities=[],
        user_stories=[
            UserStory(
                id="US-001",
                epic="Booking",
                as_a="Member",
                i_want="To book classes",
                so_that="I can attend them",
                requirement_ids=["REQ-001"],
                priority=Priority.must,
                acceptance_criteria=[]
            )
        ],
        personas=[
            Persona(
                id="PERS-001",
                name="Member Alice",
                role="Member",
                goals=["Book classes"]
            )
        ],
        source_provenance=["sample_transcript.txt"]
    )
    
    dor = compute_definition_of_ready(pkg)
    assert dor["has_domain_model"] is False
    
    manifest = generate_handoff_manifest(pkg)
    assert manifest["ready_for"] == []

    # 2. Add a domain entity and check that has_domain_model becomes True
    pkg.domain_entities = [
        DomainEntity(
            id="ENT-Booking",
            name="Booking",
            attributes=[],
            relationships=[]
        )
    ]
    
    dor_updated = compute_definition_of_ready(pkg)
    assert dor_updated["has_domain_model"] is True
    
    # 3. Package with NO confirmed functional requirements and NO domain entities
    # should yield True for has_domain_model because there are no requirements to model.
    pkg_no_req = RequirementsPackage(
        requirements=[],
        domain_entities=[],
        user_stories=[],
        personas=[]
    )
    dor_no_req = compute_definition_of_ready(pkg_no_req)
    assert dor_no_req["has_domain_model"] is True


def test_log_stage_output_count(capsys):
    # Mock CallbackContext
    callback_context = MagicMock()
    callback_context.state = {
        "transcript": "Project brief: we want to build a fitness app.",
        "some_key": []
    }
    
    # 1. Test empty list stage warning
    log_stage_output_count("some_key", "Stage Name Test", callback_context)
    captured = capsys.readouterr()
    assert "[STAGE LOG] Stage 'Stage Name Test' output count for 'some_key': 0" in captured.out
    assert "⚠️  [WARNING] Stage 'Stage Name Test' produced an EMPTY result" in captured.out

    # 2. Test non-empty list stage logging without warning
    callback_context.state["some_key"] = [1, 2, 3]
    log_stage_output_count("some_key", "Stage Name Test", callback_context)
    captured = capsys.readouterr()
    assert "[STAGE LOG] Stage 'Stage Name Test' output count for 'some_key': 3" in captured.out
    assert "⚠️  [WARNING]" not in captured.out
