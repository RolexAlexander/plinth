import json
import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from requirements_crew.flow.requirements_flow import RequirementsFlow
from requirements_crew.settings import Settings
from requirements_crew.models.package import ProjectBrief
from requirements_crew.models.enums import Priority
from crewai import LLM

# Load the cassette
CASSETTE_PATH = Path(__file__).parent / "cassettes" / "sample_run.json"
with open(CASSETTE_PATH, "r", encoding="utf-8") as f:
    CASSETTE_DATA = json.load(f)


def find_cassette_response(messages) -> str:
    """Helper to find the mock cassette response based on prompt keywords."""
    if isinstance(messages, str):
        prompt_text = messages
    elif isinstance(messages, list):
        prompt_text = "\n".join(
            msg.get("content", "") if isinstance(msg, dict) else str(msg)
            for msg in messages
        )
    else:
        prompt_text = str(messages)

    prompt_lower = prompt_text.lower()
    matched_key = None

    if "intake analyst" in prompt_lower or "extract_statements" in prompt_lower:
        matched_key = "extract_statements"
    elif "draft a project brief" in prompt_lower or "draft_brief_and_requirements" in prompt_lower:
        matched_key = "draft_brief_and_requirements"
    elif "persona and workflow" in prompt_lower or "build_personas" in prompt_lower:
        matched_key = "build_personas"
    elif "clarifying question" in prompt_lower or "generate_clarifying_questions" in prompt_lower:
        matched_key = "generate_clarifying_questions"
    elif "documentation specialist" in prompt_lower or "author_srs" in prompt_lower:
        matched_key = "author_srs"
    elif "system modeler" in prompt_lower or "model_domain" in prompt_lower:
        matched_key = "model_domain"
    elif "diagram author" in prompt_lower or "author_diagrams" in prompt_lower:
        matched_key = "author_diagrams"
    elif "qa reviewer" in prompt_lower or "qa_review" in prompt_lower:
        matched_key = "qa_review"
    elif "embodied client" in prompt_lower or "proxy_review" in prompt_lower:
        matched_key = "proxy_review"
    elif "compliance researcher" in prompt_lower or "research_context" in prompt_lower:
        matched_key = "research_context"
    elif "user story author" in prompt_lower or "author_user_stories" in prompt_lower:
        matched_key = "author_user_stories"

    print(f"\n[CASSETTE DEBUG] Prompt excerpt: {prompt_lower[:120].strip().replace('\n', ' ')}")
    print(f"[CASSETTE DEBUG] Matched key: {matched_key}")
    
    if matched_key:
        return json.dumps(CASSETTE_DATA[matched_key])
    raise ValueError(f"Unmatched prompt in cassette mock: {prompt_lower[:200]}")


def mock_llm_call(self, messages, *args, **kwargs):
    """Replacement for LLM.call that reads from cassette."""
    return find_cassette_response(messages)


@pytest.fixture
def cassette_env(monkeypatch):
    """Setup mock cassette replayer environment."""
    monkeypatch.setenv("PLINTH_UNATTENDED", "true")
    with patch.object(LLM, "call", mock_llm_call), \
         patch.object(LLM, "supports_function_calling", return_value=False):
        yield


def test_flow_integration_end_to_end(cassette_env):
    """Integration test: Runs full Flow on sample_transcript.txt and asserts on the written artifact pack."""
    transcript_path = Path(__file__).parent / "sample_transcript.txt"
    assert transcript_path.exists(), f"Transcript not found at {transcript_path}"

    with tempfile.TemporaryDirectory() as tmpdir:
        # Load and configure settings to output to tmpdir
        settings = Settings.load()
        original_output_dir = settings.io.output_dir
        settings.io.output_dir = str(Path(tmpdir) / "output")
        settings.client_proxy.mode = "on"
        settings.research.enabled = True
        
        # Override settings class loader
        with patch("requirements_crew.flow.requirements_flow.Settings.load", return_value=settings):
            flow = RequirementsFlow()
            flow.state.brief = ProjectBrief(
                project_name="SpinCycle",
                vision="Cashless Laundromat Platform"
            )
            flow.state.source_provenance = [str(transcript_path)]
            
            # Run the Flow
            flow.kickoff()
            
            # Assertions on the written files in tmpdir
            out_path = Path(settings.io.output_dir)
            assert out_path.exists()
            
            # 1. Handoff manifest exists and is correct
            manifest_file = out_path / "handoff_manifest.json"
            assert manifest_file.exists()
            with open(manifest_file, "r", encoding="utf-8") as f:
                manifest = json.load(f)
                
            assert manifest["project_name"] == "SpinCycle"
            assert manifest["counts"]["requirements"] == 20
            assert manifest["counts"]["confirmed"] == 20
            assert manifest["counts"]["assumed"] == 0
            
            # generated_at is fresh (not the hardcoded stale timestamp)
            assert manifest["generated_at"] != "2026-06-28T09:59:24.683023"
            
            # Stories coverage must show must/should covered
            assert manifest["stories_coverage"]["must_should_total"] == 20
            assert manifest["stories_coverage"]["must_should_covered"] == 20
            assert manifest["stories_coverage"]["coverage_ratio"] == 1.0
            
            # Since all questions are deferred/answered and stories present, DoR passes
            assert manifest["definition_of_ready"]["has_user_stories"] is True
            assert manifest["definition_of_ready"]["no_blocking_open_questions"] is True
            assert "architecture_agent" in manifest["ready_for"]
            
            # 2. User Stories file contains generated stories
            user_stories_file = out_path / "user_stories.json"
            assert user_stories_file.exists()
            with open(user_stories_file, "r", encoding="utf-8") as f:
                stories = json.load(f)
            assert len(stories) == 2
            assert stories[0]["id"] == "US-001"
            assert stories[1]["id"] == "US-002"
            
            # Assert every "must" requirement is covered by at least one user story
            requirements_file = out_path / "requirements.json"
            assert requirements_file.exists()
            with open(requirements_file, "r", encoding="utf-8") as f:
                reqs = json.load(f)
                
            must_req_ids = {r["id"] for r in reqs if r.get("priority") == "must" and r.get("status") != "deprecated"}
            story_covered_req_ids = set()
            for us in stories:
                story_covered_req_ids.update(us.get("requirement_ids", []))
            
            uncovered_must_reqs = must_req_ids - story_covered_req_ids
            assert not uncovered_must_reqs, f"The following MUST requirements are not covered by any user story: {uncovered_must_reqs}"
            
            # User Stories markdown should render and match JSON
            user_stories_md = out_path / "user_stories.md"
            assert user_stories_md.exists()
            content_md = user_stories_md.read_text(encoding="utf-8")
            assert "US-001" in content_md
            assert "US-002" in content_md
            for us in stories:
                assert us["id"] in content_md
                assert us["as_a"] in content_md
            
            # 3. Decisions file carries resolved_by
            decisions_file = out_path / "decisions.json"
            assert decisions_file.exists()
            with open(decisions_file, "r", encoding="utf-8") as f:
                decisions = json.load(f)
            assert len(decisions) == 1
            assert "DEC-001" in decisions[0]["id"]
            
            # Ensure EVERY decision carries resolved_by and it's valid
            for dec in decisions:
                assert "resolved_by" in dec
                assert dec["resolved_by"] in ("human", "auto_default")
            
            # Decisions markdown matches JSON
            decisions_md = out_path / "decisions.md"
            assert decisions_md.exists()
            dec_md_content = decisions_md.read_text(encoding="utf-8")
            for dec in decisions:
                assert dec["id"] in dec_md_content
                assert dec["statement"] in dec_md_content
            
            # 4. Open Questions file is updated
            oq_file = out_path / "open_questions.json"
            assert oq_file.exists()
            with open(oq_file, "r", encoding="utf-8") as f:
                oq_list = json.load(f)
            assert len(oq_list) == 1
            assert oq_list[0]["status"] == "deferred"
            
            # Open Questions markdown matches JSON
            oq_md = out_path / "open_questions.md"
            assert oq_md.exists()
            oq_md_content = oq_md.read_text(encoding="utf-8")
            for oq in oq_list:
                assert oq["id"] in oq_md_content
                assert oq["question"] in oq_md_content
            
            # 5. Off-domain questions are dropped
            off_domain_keywords = ["employee performance", "learning development", "learning resource", "development plan", "goal completion"]
            for q in oq_list:
                for kw in off_domain_keywords:
                    assert kw not in q["question"].lower()
                    
            for dec in decisions:
                for kw in off_domain_keywords:
                    assert kw not in dec["rationale"].lower()
                    assert kw not in dec["statement"].lower()
                
            # 6. Traceability mapping is present
            trace_file = out_path / "traceability.json"
            assert trace_file.exists()
            with open(trace_file, "r", encoding="utf-8") as f:
                trace = json.load(f)
            # Find the user stories mapping in traceability for REQ-001
            req_trace = trace.get("REQ-001") or trace.get("req-001")
            assert req_trace is not None
            assert "US-001" in req_trace["user_stories"]
            
            # Traceability markdown matches JSON
            trace_md = out_path / "traceability.md"
            assert trace_md.exists()
            trace_md_content = trace_md.read_text(encoding="utf-8")
            for req_id, mapping in trace.items():
                assert req_id in trace_md_content
                for story_id in mapping.get("user_stories", []):
                    assert story_id in trace_md_content
                    
            # Persona markdown matches JSON
            personas_file = out_path / "personas.json"
            assert personas_file.exists()
            with open(personas_file, "r", encoding="utf-8") as f:
                personas = json.load(f)
            personas_md = out_path / "personas.md"
            assert personas_md.exists()
            personas_md_content = personas_md.read_text(encoding="utf-8")
            for pers in personas:
                assert pers["id"] in personas_md_content
                assert pers["name"] in personas_md_content
                assert pers["role"] in personas_md_content
