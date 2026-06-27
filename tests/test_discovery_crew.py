import os
import pytest
from requirements_crew.crews.discovery_crew import DiscoveryCrew
from requirements_crew.tools.io import read_transcript
from requirements_crew.models.outputs import SourceList, BriefAndRequirements, PersonaList

# Helper to check if any API key is configured
def has_api_key():
    # Check env vars (making sure they aren't dummy values)
    for key in ["GEMINI_API_KEY", "OPENAI_API_KEY"]:
        val = os.environ.get(key)
        if val and val.strip() and val != "YOUR_API_KEY":
            return True
    # Check .env file
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                if "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip("'").strip('"')
                    if k in ["GEMINI_API_KEY", "OPENAI_API_KEY"] and v and v != "YOUR_API_KEY":
                        return True
    return False

@pytest.mark.skipif(
    not has_api_key(),
    reason="LLM API key not configured in environment or .env file"
)
def test_discovery_crew_execution():
    # Load transcript
    transcript = read_transcript("tests/sample_transcript.txt")
    
    # Run the crew
    result = DiscoveryCrew().crew().kickoff(inputs={"transcript": transcript})
    
    assert result is not None
    assert len(result.tasks_output) == 3
    
    # Task 0: extract_statements -> SourceList
    statements_out = result.tasks_output[0].pydantic
    assert isinstance(statements_out, SourceList)
    assert len(statements_out.statements) > 0
    
    # Task 1: draft_brief_and_requirements -> BriefAndRequirements
    brief_reqs_out = result.tasks_output[1].pydantic
    assert isinstance(brief_reqs_out, BriefAndRequirements)
    assert brief_reqs_out.brief.project_name != ""
    assert len(brief_reqs_out.requirements) > 0
    
    # Task 2: build_personas -> PersonaList
    personas_out = result.tasks_output[2].pydantic
    assert isinstance(personas_out, PersonaList)
    assert len(personas_out.personas) > 0
