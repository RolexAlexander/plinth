import json
import os
import sys
import logging
from pathlib import Path
from typing import List, Protocol, Dict, Any, Optional
from pydantic import BaseModel
from ..models.records import OpenQuestion, Source
from ..models.package import ProjectBrief, RequirementsPackage, Decision
from ..models.enums import Status, SourceOrigin, OpenQuestionStatus, DefaultIfDeferred
from ..models.sources import SourceDocument


def _is_unattended() -> bool:
    """Check if running in unattended mode."""
    return os.environ.get("PLINTH_UNATTENDED", "").lower() == "true"


class GatePayload(BaseModel):
    brief: ProjectBrief
    blocking_questions: List[OpenQuestion]


class GateResponse(BaseModel):
    approved: bool
    answers: Dict[str, str]           # maps OQ-id -> answer string
    deferred_ids: List[str]           # list of OQ-ids that the user wants to defer
    auto_deferred_ids: List[str] = [] # list of OQ-ids auto-adopted in unattended mode


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

        # Determine run mode
        unattended = _is_unattended()

        if unattended:
            return self._handle_unattended(payload)
        else:
            return self._handle_interactive(payload)

    def _handle_unattended(self, payload: GatePayload) -> GateResponse:
        """Unattended mode: auto-adopt where default_if_deferred == adopt_assumption.
        Questions with leave_open or drop_scope cannot auto-clear."""
        print("[UNATTENDED] Auto-resolving blocking questions...")
        answers = {}
        deferred_ids = []
        auto_deferred_ids = []
        cannot_auto_resolve = []
        
        for oq in payload.blocking_questions:
            if oq.default_if_deferred == DefaultIfDeferred.adopt_assumption:
                deferred_ids.append(oq.id)
                auto_deferred_ids.append(oq.id)
                print(f"  [AUTO-ADOPT] {oq.id}: {oq.question}")
                print(f"    -> Adopting assumption: {oq.proposed_assumption}")
            else:
                cannot_auto_resolve.append(oq)
                print(f"  [CANNOT AUTO-RESOLVE] {oq.id}: {oq.question}")
                print(f"    -> default_if_deferred={oq.default_if_deferred.value} — requires human input")

        if cannot_auto_resolve:
            print(f"\n[UNATTENDED] WARNING: {len(cannot_auto_resolve)} blocking questions could not be auto-resolved.")
            print("  These questions have default_if_deferred of 'leave_open' or 'drop_scope' and require human input.")
            print("  Run interactively (without --unattended) to resolve them.")

        print(f"\n[UNATTENDED] Summary: {len(auto_deferred_ids)} auto-adopted, {len(cannot_auto_resolve)} require human input.")
        
        # Approve only if all questions were handled
        approved = len(cannot_auto_resolve) == 0
        return GateResponse(
            approved=approved,
            answers=answers,
            deferred_ids=deferred_ids,
            auto_deferred_ids=auto_deferred_ids
        )

    def _handle_interactive(self, payload: GatePayload) -> GateResponse:
        """Interactive mode: blocking questions MUST receive explicit human input."""
        print("Please answer the following questions (or type 'defer' to adopt the proposed assumption, or 'exit' to stop):")
        answers = {}
        deferred_ids = []
        
        for oq in payload.blocking_questions:
            # Print the question info on its own lines (P02-3 fix: label above input)
            print(f"\n{'-'*40}")
            print(f"[{oq.id}] Question: {oq.question}")
            if oq.proposed_assumption:
                print(f"      Proposed Assumption: {oq.proposed_assumption}")
                print(f"      Default if Deferred: {oq.default_if_deferred.value}")
            print()  # Blank line before the input prompt
            
            # P02-3: Flush stdout and suppress rich handlers before reading
            sys.stdout.flush()
            
            # Temporarily suppress rich/logging handlers to prevent line overwrite
            root_logger = logging.getLogger()
            original_handlers = root_logger.handlers[:]
            original_level = root_logger.level
            
            # Detach all stdout-targeting handlers during prompt
            stdout_handlers = []
            for h in root_logger.handlers[:]:
                if hasattr(h, 'stream') and getattr(h, 'stream', None) is sys.stdout:
                    stdout_handlers.append(h)
                    root_logger.removeHandler(h)
            
            try:
                # Read on a clean line (P02-3: never styled label + input() on same line)
                response = input("Your answer: ").strip()
            except (OSError, EOFError):
                # P02-2: In interactive mode, a blocked stdin is an error, not a silent defer
                print("\n[ERROR] Stdin/terminal input not available.")
                print("  Blocking questions require human input in interactive mode.")
                print("  Run with --unattended to auto-adopt defaults, or provide an answers file.")
                # Restore handlers
                for h in stdout_handlers:
                    root_logger.addHandler(h)
                return GateResponse(approved=False, answers={}, deferred_ids=[])
            finally:
                # Restore logging handlers
                for h in stdout_handlers:
                    if h not in root_logger.handlers:
                        root_logger.addHandler(h)
                
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
        answers_path = Path(self.answers_file)
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
    """Apply gate responses to the package, tagging decisions with resolved_by."""
    # Append human answers to the registry as a "gate_answers" document
    if hasattr(pkg, "source_registry") and pkg.source_registry is not None:
        new_text = "\n".join(f"[{oq_id}] {ans}" for oq_id, ans in response.answers.items() if ans)
        if new_text:
            existing_gate_doc = pkg.source_registry.documents.get("gate_answers")
            if existing_gate_doc:
                existing_gate_doc.text += "\n" + new_text
            else:
                pkg.source_registry.documents["gate_answers"] = SourceDocument(
                    doc_id="gate_answers",
                    kind=SourceOrigin.human_answer,
                    text=new_text
                )

    # Determine next Decision ID
    import re
    existing_decisions = []
    for d in pkg.decisions:
        match = re.match(r"^DEC-(\d+)$", d.id)
        if match:
            existing_decisions.append(int(match.group(1)))
    next_dec_num = max(existing_decisions, default=0) + 1

    # Build the set of auto-deferred IDs for tagging
    auto_deferred_set = set(getattr(response, 'auto_deferred_ids', []))

    # 1. Update questions
    for oq in pkg.open_questions:
        if oq.id in response.answers:
            oq.answer = response.answers[oq.id]
            oq.status = OpenQuestionStatus.answered
            
            # Create a Decision record for this resolved question
            dec_id = f"DEC-{next_dec_num:03d}"
            dec = Decision(
                id=dec_id,
                statement=f"Adopted resolution: {oq.answer}",
                rationale=f"Resolved open question: {oq.question}",
                related_ids=oq.affects,
                resolved_by="human"
            )
            pkg.decisions.append(dec)
            next_dec_num += 1
            
            # For each affected requirement, append human_answer source and promote to confirmed
            for r_id in oq.affects:
                req = next((r for r in pkg.requirements if r.id == r_id), None)
                if req:
                    # Create source
                    src = Source(
                        origin=SourceOrigin.human_answer,
                        ref=f"gate_resolution",
                        excerpt=oq.answer  # Verbatim answer as excerpt
                    )
                    req.source.append(src)
                    # Promote status to confirmed
                    req.status = Status.confirmed
                    
        elif oq.id in response.deferred_ids:
            oq.status = OpenQuestionStatus.deferred
            
            # Determine resolved_by tag
            is_auto = oq.id in auto_deferred_set
            resolved_by_tag = "auto_default" if is_auto else "human"
            
            # For deferred questions: status deferred, apply default_if_deferred
            if oq.default_if_deferred == DefaultIfDeferred.adopt_assumption:
                # Create a Decision record for this adopted assumption
                dec_id = f"DEC-{next_dec_num:03d}"
                dec = Decision(
                    id=dec_id,
                    statement=f"Adopted default assumption: {oq.proposed_assumption}",
                    rationale=f"Deferred open question: {oq.question}",
                    related_ids=oq.affects,
                    resolved_by=resolved_by_tag
                )
                pkg.decisions.append(dec)
                next_dec_num += 1
                
                # write proposed_assumption onto the affected requirements as an assumed-tier source
                for r_id in oq.affects:
                    req = next((r for r in pkg.requirements if r.id == r_id), None)
                    if req:
                        src = Source(
                            origin=SourceOrigin.analyst_inference,
                            ref=f"deferred_oq_{oq.id}",
                            excerpt=oq.proposed_assumption
                        )
                        req.source.append(src)
                        req.status = Status.assumed
            elif oq.default_if_deferred == DefaultIfDeferred.drop_scope:
                # drop the requirement (change status to deprecated)
                for r_id in oq.affects:
                    req = next((r for r in pkg.requirements if r.id == r_id), None)
                    if req:
                        req.status = Status.deprecated
