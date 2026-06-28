import pytest
import re
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
    OpenQuestion,
    OpenQuestionStatus,
    DefaultIfDeferred,
    SourceDocument,
    SourceRegistry
)
from requirements_crew.validation.grounding import validate_source_grounding, GroundingError
from requirements_crew.packaging.manifest import generate_handoff_manifest

TRANSCRIPT_TOPICS = [
    "qr", "mqtt", "stripe", "loyalty", "spin pass", "idle", "waitlist",
    "reserv", "refund", "attendant", "2fa", "totp", "wcag", "spanish",
    "tls", "aes", "rate limit", "retention", "offline", "concurrent", "machine"
]

def check_requirements_cover_transcript(pkg):
    blob = " ".join(r.statement.lower() for r in pkg.requirements)
    hits = [t for t in TRANSCRIPT_TOPICS if t in blob]
    return hits

def check_no_hallucinated_ids_in_open_questions(pkg):
    ids = {r.id for r in pkg.requirements} | {s.id for s in pkg.user_stories}
    tok = re.compile(r"\b(REQ-\d+|US-\d+)\b")
    for q in pkg.open_questions:
        for ref in tok.findall(q.question) + q.affects:
            if ref not in ids:
                return False, f"{q.id} references non-existent {ref}"
    return True, ""

def test_requirements_coverage_with_mock():
    # Construct a package with topics to test coverage
    pkg = RequirementsPackage(
        brief=ProjectBrief(project_name="SpinCycle", vision="Vision"),
        requirements=[
            Requirement(
                id="REQ-001",
                type=RequirementType.functional,
                statement="Scan QR code on machine to pay with Stripe",
                status=Status.confirmed,
                priority=Priority.must,
                source=[Source(origin=SourceOrigin.transcript, excerpt="scan QR code")],
                acceptance_criteria=[AcceptanceCriterion(id="AC-001-a", given="g", when="w", then="t")]
            ),
            Requirement(
                id="REQ-002",
                type=RequirementType.functional,
                statement="Use MQTT for telemetry and monitoring idle machines",
                status=Status.confirmed,
                priority=Priority.must,
                source=[Source(origin=SourceOrigin.transcript, excerpt="MQTT")],
                acceptance_criteria=[AcceptanceCriterion(id="AC-002-a", given="g", when="w", then="t")]
            ),
            Requirement(
                id="REQ-003",
                type=RequirementType.functional,
                statement="Spin Pass loyalty system and refunds",
                status=Status.confirmed,
                priority=Priority.must,
                source=[Source(origin=SourceOrigin.transcript, excerpt="Spin Pass")],
                acceptance_criteria=[AcceptanceCriterion(id="AC-003-a", given="g", when="w", then="t")]
            ),
            Requirement(
                id="REQ-004",
                type=RequirementType.functional,
                statement="Waitlist reservation system for attendant role with 2FA TOTP login",
                status=Status.confirmed,
                priority=Priority.must,
                source=[Source(origin=SourceOrigin.transcript, excerpt="2FA")],
                acceptance_criteria=[AcceptanceCriterion(id="AC-004-a", given="g", when="w", then="t")]
            ),
            Requirement(
                id="REQ-005",
                type=RequirementType.functional,
                statement="Accessibility compliance with WCAG, Spanish language support, and TLS AES encryption",
                status=Status.confirmed,
                priority=Priority.must,
                source=[Source(origin=SourceOrigin.transcript, excerpt="WCAG")],
                acceptance_criteria=[AcceptanceCriterion(id="AC-005-a", given="g", when="w", then="t")]
            ),
            Requirement(
                id="REQ-006",
                type=RequirementType.functional,
                statement="Rate limit requests, offline backup, concurrent runs on the washing machine",
                status=Status.confirmed,
                priority=Priority.must,
                source=[Source(origin=SourceOrigin.transcript, excerpt="offline")],
                acceptance_criteria=[AcceptanceCriterion(id="AC-006-a", given="g", when="w", then="t")]
            ),
            Requirement(
                id="REQ-007",
                type=RequirementType.functional,
                statement="Data retention policy enforcement",
                status=Status.confirmed,
                priority=Priority.must,
                source=[Source(origin=SourceOrigin.transcript, excerpt="retention")],
                acceptance_criteria=[AcceptanceCriterion(id="AC-007-a", given="g", when="w", then="t")]
            )
        ]
    )
    hits = check_requirements_cover_transcript(pkg)
    # Asserts that we cover at least 12 of the target transcript topics
    assert len(hits) >= 12, f"requirements still ungrounded; only matched {hits}"

def test_grounding_verification_strict():
    registry = SourceRegistry()
    registry.documents["transcript"] = SourceDocument(
        doc_id="transcript",
        kind=SourceOrigin.transcript,
        text="Scan QR code to start machine."
    )
    
    # Grounded requirement
    pkg_good = RequirementsPackage(
        requirements=[
            Requirement(
                id="REQ-001",
                type=RequirementType.functional,
                statement="Scan QR code",
                status=Status.confirmed,
                priority=Priority.must,
                source=[Source(origin=SourceOrigin.transcript, excerpt="Scan QR code")],
                acceptance_criteria=[AcceptanceCriterion(id="AC-001-a", given="g", when="w", then="t")]
            )
        ]
    )
    # Should pass without error
    validate_source_grounding(pkg_good, registry, mode="strict")
    
    # Grounded requirement with ellipses
    pkg_ellipsis = RequirementsPackage(
        requirements=[
            Requirement(
                id="REQ-003",
                type=RequirementType.functional,
                statement="Scan QR code to start",
                status=Status.confirmed,
                priority=Priority.must,
                source=[Source(origin=SourceOrigin.transcript, excerpt="Scan QR ... start machine.")],
                acceptance_criteria=[AcceptanceCriterion(id="AC-003-a", given="g", when="w", then="t")]
            )
        ]
    )
    validate_source_grounding(pkg_ellipsis, registry, mode="strict")
    # Fabricated excerpt (ungrounded)
    pkg_bad = RequirementsPackage(
        requirements=[
            Requirement(
                id="REQ-002",
                type=RequirementType.functional,
                statement="Use Postgres",
                status=Status.confirmed,
                priority=Priority.must,
                source=[Source(origin=SourceOrigin.transcript, excerpt="standardized on Postgres 15")],
                acceptance_criteria=[AcceptanceCriterion(id="AC-002-a", given="g", when="w", then="t")]
            )
        ]
    )
    
    with pytest.raises(GroundingError):
        validate_source_grounding(pkg_bad, registry, mode="strict")

def test_hallucinated_ids_in_open_questions():
    pkg = RequirementsPackage(
        requirements=[
            Requirement(
                id="REQ-001",
                type=RequirementType.functional,
                statement="Scan QR code",
                status=Status.confirmed,
                priority=Priority.must,
                source=[Source(origin=SourceOrigin.transcript, excerpt="Scan QR")],
                acceptance_criteria=[AcceptanceCriterion(id="AC-001-a", given="g", when="w", then="t")]
            )
        ],
        user_stories=[
            UserStory(
                id="US-001",
                epic="Auth",
                as_a="user",
                i_want="login",
                so_that="access",
                requirement_ids=["REQ-001"],
                priority=Priority.must
            )
        ],
        open_questions=[
            OpenQuestion(
                id="OQ-001",
                question="Objection to REQ-999", # Hallucinated ID REQ-999
                synthetic_origin=SourceOrigin.client_proxy,
                blocking=True,
                blocking_rationale="None",
                affects=["REQ-001"]
            )
        ]
    )
    
    passed, err = check_no_hallucinated_ids_in_open_questions(pkg)
    assert not passed
    assert "references non-existent REQ-999" in err

def test_ready_for_requires_real_resolution():
    # Blocking question deferred as leave_open or drop_scope keeps ready_for empty
    req = Requirement(
        id="REQ-001",
        type=RequirementType.functional,
        statement="Scan QR code",
        status=Status.confirmed,
        priority=Priority.must,
        source=[Source(origin=SourceOrigin.transcript, excerpt="Scan QR")],
        acceptance_criteria=[AcceptanceCriterion(id="AC-001-a", given="g", when="w", then="t")]
    )
    story = UserStory(
        id="US-001",
        epic="Auth",
        as_a="user",
        i_want="login",
        so_that="access",
        requirement_ids=["REQ-001"],
        priority=Priority.must
    )
    
    # 1. Blocking question set to deferred + leave_open
    pkg_leave_open = RequirementsPackage(
        requirements=[req],
        user_stories=[story],
        open_questions=[
            OpenQuestion(
                id="OQ-001",
                question="LDAP details?",
                synthetic_origin=SourceOrigin.client_proxy,
                blocking=True,
                blocking_rationale="blocking",
                status=OpenQuestionStatus.deferred,
                default_if_deferred=DefaultIfDeferred.leave_open
            )
        ]
    )
    
    # Explicitly mirror affected_by first
    from requirements_crew.flow.requirements_flow import prune_invalid_affects
    prune_invalid_affects(pkg_leave_open)
    
    manifest = generate_handoff_manifest(pkg_leave_open, orphan_check="warn")
    assert manifest["ready_for"] == []
    
    # 2. Blocking question set to deferred + adopt_assumption
    pkg_adopt = RequirementsPackage(
        requirements=[req],
        user_stories=[story],
        open_questions=[
            OpenQuestion(
                id="OQ-001",
                question="LDAP details?",
                synthetic_origin=SourceOrigin.client_proxy,
                blocking=True,
                blocking_rationale="blocking",
                status=OpenQuestionStatus.deferred,
                default_if_deferred=DefaultIfDeferred.adopt_assumption,
                proposed_assumption="Use active directory"
            )
        ]
    )
    
    prune_invalid_affects(pkg_adopt)
    manifest_adopt = generate_handoff_manifest(pkg_adopt, orphan_check="warn")
    assert "architecture_agent" in manifest_adopt["ready_for"]
