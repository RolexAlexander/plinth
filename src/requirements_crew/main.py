#!/usr/bin/env python
import os
import sys
from pathlib import Path
from requirements_crew.flow.requirements_flow import RequirementsFlow, FlowState
from requirements_crew.models.package import ProjectBrief

def kickoff():
    """Kick off the requirements gathering flow."""
    print("Initializing Requirements Discovery Flow...")
    
    # Parse --debug-context flag
    if "--debug-context" in sys.argv:
        os.environ["DEBUG_CONTEXT"] = "true"
        sys.argv.remove("--debug-context")

    # Check if a transcript argument was passed
    transcript_path = "tests/sample_transcript.txt"
    if len(sys.argv) > 1:
        arg_path = sys.argv[1]
        if os.path.exists(arg_path):
            transcript_path = arg_path
            
    print(f"Using transcript file: {transcript_path}")
    
    # Initialize state
    brief = ProjectBrief(
        project_name="Discovery Project",
        vision="Initial Discovery Vision"
    )
    
    flow = RequirementsFlow()
    flow.state.brief = brief
    flow.state.source_provenance = [transcript_path]
    
    # Run
    flow.kickoff()
    print("Flow completed successfully!")

def plot():
    """Plot the flow diagram."""
    print("Plotting flow diagram...")
    flow = RequirementsFlow()
    flow.plot("requirements_flow_chart")
    print("Flow chart saved as requirements_flow_chart.png")

if __name__ == "__main__":
    kickoff()
