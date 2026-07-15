# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import time
import json
import shutil
import pytest
from pathlib import Path
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.artifacts import InMemoryArtifactService
from google.adk.apps import ResumabilityConfig
from google.genai import types

from plinth_agent.agent import root_agent, app
from plinth_agent.settings import Settings

TRANSCRIPT_SPINCYCLE = """Project: SpinCycle — Smart Laundromat Management Platform
Participants:
  - Marcus Chen (Product Owner, SpinCycle Inc.)
  - Dana Reeves (Operations Manager, CleanWave Laundromats — pilot partner)
  - Priya Kapoor (Lead Developer, SpinCycle Inc.)

MARCUS: Sure. SpinCycle is a mobile-first platform for self-service laundromats. We want to let customers walk in, scan a QR code on any machine, pay from their phone, and get notified when their cycle is done. On the owner side, Dana and folks like her need a dashboard showing real-time machine status, revenue reports, and maintenance alerts.
DANA: Three things kill us. First, coin jams — we lose about twelve percent of revenue to jammed coin slots and people walking away. Going cashless would be huge. Second, we have no idea which machines are running and which are sitting idle unless someone physically walks the floor. Third, maintenance is reactive. A dryer runs with a bad belt for two weeks before anyone notices.
"""

TRANSCRIPT_PETWELL = """Project: PetWell — Veterinary Clinic Management System
Participants:
  - Dr. Sarah Jenkins (Lead Veterinarian, PetWell Services)
  - John Miller (Operations Manager, PetWell Services)
  - Alice Smith (Lead Developer, PetWell Services)

SARAH: Sure. PetWell is a web-first system for veterinary clinics. We want to let pet owners walk in, scan a QR code at the check-in desk, register their pet, and get notified when their exam room is ready. On the vet side, John and folks like him need a dashboard showing real-time exam room status, pet medical reports, and veterinarian alerts.
JOHN: Three things kill us. First, check-in delays — we lose about twelve percent of slot capacity to manual check-ins and clients sitting waiting. Going automated would be huge. Second, we have no idea which exam rooms are currently busy and which are sitting empty unless someone physically walks the clinic. Third, room assignment is reactive.
"""

def is_api_quota_available() -> bool:
    if not (os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_GENAI_USE_VERTEXAI") == "True"):
        return False
    try:
        import asyncio
        from google.adk.models import Gemini
        m = Gemini(model="gemini-2.5-flash")
        async def ping():
            async for chunk in m.generate_content_async("ping"):
                break
        
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(asyncio.wait_for(ping(), timeout=5.0))
        finally:
            loop.close()
        return True
    except Exception as e:
        print(f"\n[SKIP CHECK] Live API call failed (likely 429 rate limit or missing auth): {e}")
        return False

@pytest.mark.live
@pytest.mark.skipif(
    not is_api_quota_available(),
    reason="Vertex AI API is rate-limited, quota-exhausted, or credentials are not configured."
)
def test_pipeline_regression_back_to_back(monkeypatch) -> None:
    """
    Regression test that runs two different transcripts back-to-back
    in one process and asserts neither package contains the other's domain terms.
    """
    monkeypatch.setenv("PLINTH_TEST_AUTO_RESOLVE", "true")
    
    print("Waiting 45 seconds to clear any active API rate limit quotas...")
    time.sleep(45)
    
    # Locate output directory
    settings = Settings.load()
    out_dir = Path(settings.io.output_dir)
    
    transcript_path = Path("sample_transcript.txt")
    if not transcript_path.exists():
        transcript_path = Path(__file__).resolve().parents[2] / "sample_transcript.txt"
        
    backup_path = Path("sample_transcript.txt.bak")
    
    # Backup original transcript if it exists
    if transcript_path.exists():
        shutil.copy(transcript_path, backup_path)
        
    try:
        # 1. First Run: SpinCycle
        print("\n=== RUNNING SPINCYCLE PIPELINE ===")
        with open(transcript_path, "w", encoding="utf-8") as f:
            f.write(TRANSCRIPT_SPINCYCLE)
            
        session_service = InMemorySessionService()
        session_1 = session_service.create_session_sync(user_id="test_user", app_name=app.name)
        runner_1 = Runner(
            app=app,
            session_service=session_service,
            artifact_service=InMemoryArtifactService(),
        )
        
        # helper to drive the sequential agent steps to completion
        def run_pipeline_to_completion(runner, session, start_message) -> None:
            # 1. Start the first step
            print("--- Pipeline Step 1 (Start) ---")
            list(runner.run(
                new_message=types.Content(role="user", parts=[types.Part.from_text(text=start_message)]),
                user_id="test_user",
                session_id=session.id,
            ))
            
            # 2. Loop to resume remaining steps
            for step in range(2, 12):
                # Cool down API between sequential agent steps to mitigate 429
                time.sleep(15)
                
                req_file = out_dir / "requirements.json"
                if req_file.exists():
                    print(f"requirements.json found. Pipeline completed in {step-1} steps!")
                    return
                    
                print(f"--- Pipeline Step {step} (Resume) ---")
                list(runner.run(
                    new_message=types.Content(role="user", parts=[types.Part.from_text(text="ok")]),
                    user_id="test_user",
                    session_id=session.id,
                ))
                
            raise RuntimeError("Pipeline failed to complete and generate requirements.json within 10 steps.")

        run_pipeline_to_completion(runner_1, session_1, "Start requirements discovery")
        
        # Verify SpinCycle outputs
        req_file = out_dir / "requirements.json"
        srs_file = out_dir / "srs.md"
        assert req_file.exists(), "requirements.json was not created for SpinCycle run"
        assert srs_file.exists(), "srs.md was not created for SpinCycle run"
        
        with open(req_file, "r", encoding="utf-8") as f:
            req_data = json.load(f)
            
        with open(srs_file, "r", encoding="utf-8") as f:
            srs_text = f.read()
            
        # Assertions for SpinCycle
        req_text = json.dumps(req_data).lower()
        srs_text_lower = srs_text.lower()
        
        assert "laundromat" in srs_text_lower or "machine" in srs_text_lower or "dryer" in srs_text_lower
        assert "veterinary" not in srs_text_lower and "petwell" not in srs_text_lower and "exam room" not in srs_text_lower
        assert "veterinary" not in req_text and "petwell" not in req_text and "exam room" not in req_text
        
        # 2. Second Run: PetWell
        print("\n=== RUNNING PETWELL PIPELINE ===")
        print("Waiting 20 seconds to cool down API rate limits...")
        time.sleep(20)
        with open(transcript_path, "w", encoding="utf-8") as f:
            f.write(TRANSCRIPT_PETWELL)
            
        session_2 = session_service.create_session_sync(user_id="test_user", app_name=app.name)
        runner_2 = Runner(
            app=app,
            session_service=session_service,
            artifact_service=InMemoryArtifactService(),
        )
        
        run_pipeline_to_completion(runner_2, session_2, "Start requirements discovery")
        
        # Verify PetWell outputs
        assert req_file.exists(), "requirements.json was not created for PetWell run"
        assert srs_file.exists(), "srs.md was not created for PetWell run"
        
        with open(req_file, "r", encoding="utf-8") as f:
            req_data_2 = json.load(f)
            
        with open(srs_file, "r", encoding="utf-8") as f:
            srs_text_2 = f.read()
            
        # Assertions for PetWell
        req_text_2 = json.dumps(req_data_2).lower()
        srs_text_2_lower = srs_text_2.lower()
        
        assert "veterinary" in srs_text_2_lower or "pet" in srs_text_2_lower or "exam room" in srs_text_2_lower
        assert "laundromat" not in srs_text_2_lower and "spincycle" not in srs_text_2_lower and "coin slot" not in srs_text_2_lower
        assert "laundromat" not in req_text_2 and "spincycle" not in req_text_2 and "coin slot" not in req_text_2
        
    finally:
        # Restore backup
        if backup_path.exists():
            shutil.copy(backup_path, transcript_path)
            backup_path.unlink()
        elif transcript_path.exists():
            transcript_path.unlink()
