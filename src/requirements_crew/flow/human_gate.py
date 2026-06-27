import json
import os
from pathlib import Path
from typing import List, Protocol, Dict, Any
from pydantic import BaseModel
from ..models.records import OpenQuestion, Source
from ..models.package import ProjectBrief, RequirementsPackage
from ..models.enums import Status, SourceOrigin, OpenQuestionStatus, DefaultIfDeferred

class GatePayload(BaseModel):
    brief: ProjectBrief
    blocking_questions: List[OpenQuestion]

class GateResponse(BaseModel):
    approved: bool
    answers: Dict[str, str]  # maps OQ-id -> answer string
    deferred_ids: List[str]  # list of OQ-ids that the user wants to defer

class HumanGate(Protocol):
    def request(self, payload: GatePayload) -> GateResponse:
        ...

class ConsoleHumanGate:
    def __init__(self, answers_file: str = "answers.json"):
        self.answers_file = answers_file
        
    def request(self, payload: GatePayload) -> GateResponse:
        print("\n" + "="*50)
        print(f"HUMAN APPROVAL GATE: {payload.brief.project_name}")
        print(f"Vision: {payload.brief.vision}")
        print("="*50)
        
        if not payload.blocking_questions:
            print("No blocking questions! Automatically approved.")
            return GateResponse(approved=True, answers={}, deferred_ids=[])
            
        print(f"\nThere are {len(payload.blocking_questions)} blocking open questions that need resolution:\n")
        
        # Check if editable answers file exists
        answers_path = Path(self.answers_file)
        if answers_path.exists():
            print(f"Found answers file: {self.answers_file}. Reading answers from file...")
            try:
                with open(answers_path, "r", encoding="utf-8") as f:
                    file_answers = json.load(f)
                
                # Check if all blocking questions are answered/deferred in the file
                answers = {}
                deferred_ids = []
                all_resolved = True
                
                for oq in payload.blocking_questions:
                    if oq.id in file_answers:
                        val = file_answers[oq.id].strip()
                        if val.lower() == "defer":
                            deferred_ids.append(oq.id)
                        elif val:
                            answers[oq.id] = val
                        else:
                            all_resolved = False
                            print(f"  [MISSING] Question {oq.id}: {oq.question} is present in file but has empty answer.")
                    else:
                        all_resolved = False
                        print(f"  [MISSING] Question {oq.id}: {oq.question} is not in the answers file.")
                        
                if all_resolved:
                    print("All blocking questions resolved from file.")
                    return GateResponse(approved=True, answers=answers, deferred_ids=deferred_ids)
                else:
                    print(f"\nPlease fill in the answers in {self.answers_file} or use the console input.")
            except Exception as e:
                print(f"Error reading answers file: {e}")
                
        # Fallback to stdin console input
        print("Please answer the following questions (or type 'defer' to adopt the proposed assumption, or 'exit' to stop):")
        answers = {}
        deferred_ids = []
        
        for oq in payload.blocking_questions:
            print(f"\n[{oq.id}] Question: {oq.question}")
            if oq.proposed_assumption:
                print(f"      Proposed Assumption: {oq.proposed_assumption}")
                print(f"      Default if Deferred: {oq.default_if_deferred.value}")
            
            # Read from stdin
            try:
                response = input("Your answer: ").strip()
            except OSError:
                # If stdin is not available (e.g. during pytest capture), we default to defer
                print("Stdin not available. Automatically deferring question.")
                response = "defer"
                
            if response.lower() == "exit":
                print("Exiting gate. Please edit the answers file and re-run.")
                return GateResponse(approved=False, answers={}, deferred_ids=[])
            elif response.lower() == "defer":
                deferred_ids.append(oq.id)
                print("Deferred (using default assumption).")
            else:
                answers[oq.id] = response
                print("Answered.")
                
        # Write template answers file for convenience if it doesn't exist
        if not answers_path.exists():
            template = {oq.id: "" for oq in payload.blocking_questions}
            try:
                with open(answers_path, "w", encoding="utf-8") as f:
                    json.dump(template, f, indent=2)
                print(f"\nCreated template answers file at: {self.answers_file}")
            except Exception as e:
                print(f"Error creating template: {e}")
                
        return GateResponse(approved=True, answers=answers, deferred_ids=deferred_ids)

def apply_gate_responses(pkg: RequirementsPackage, response: GateResponse) -> None:
    # 1. Update questions
    for oq in pkg.open_questions:
        if oq.id in response.answers:
            oq.answer = response.answers[oq.id]
            oq.status = OpenQuestionStatus.answered
            
            # For each affected requirement, append human_answer source and promote to confirmed
            for r_id in oq.affects:
                req = next((r for r in pkg.requirements if r.id == r_id), None)
                if req:
                    # Create source
                    src = Source(
                        origin=SourceOrigin.human_answer,
                        ref=f"gate_resolution",
                        excerpt=f"Resolved by human: {oq.answer}"
                    )
                    req.source.append(src)
                    # Promote status to confirmed
                    req.status = Status.confirmed
                    
        elif oq.id in response.deferred_ids:
            oq.status = OpenQuestionStatus.deferred
            
            # For deferred questions: status deferred, apply default_if_deferred
            if oq.default_if_deferred == DefaultIfDeferred.adopt_assumption:
                # write proposed_assumption onto the affected requirements as an assumed-tier source
                for r_id in oq.affects:
                    req = next((r for r in pkg.requirements if r.id == r_id), None)
                    if req:
                        src = Source(
                            origin=SourceOrigin.analyst_inference,
                            ref=f"deferred_oq_{oq.id}",
                            excerpt=f"Deferred question assumption: {oq.proposed_assumption}"
                        )
                        req.source.append(src)
                        req.status = Status.assumed
            elif oq.default_if_deferred == DefaultIfDeferred.drop_scope:
                # drop the requirement (change status to deprecated)
                for r_id in oq.affects:
                    req = next((r for r in pkg.requirements if r.id == r_id), None)
                    if req:
                        req.status = Status.deprecated
