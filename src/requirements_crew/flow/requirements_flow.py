import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from crewai.flow.flow import Flow, listen, start, router
from crewai import Crew, Process

from ..models.package import RequirementsPackage, ProjectBrief
from ..models.enums import Status, OpenQuestionStatus, SourceOrigin, DefaultIfDeferred
from ..models.records import OpenQuestion, Requirement
from ..validation.package_validators import validate_package_integrity, PackageValidationError
from ..packaging.writer import write_package_to_disk
from ..crews.discovery_crew import DiscoveryCrew
from ..settings import Settings
from .human_gate import ConsoleHumanGate, GatePayload, GateResponse, apply_gate_responses
from ..tools.io import read_transcript

def prune_invalid_affects(pkg: RequirementsPackage) -> None:
    req_ids = {r.id for r in pkg.requirements}
    for oq in pkg.open_questions:
        oq.affects = [aff for aff in oq.affects if aff in req_ids]
        
    seen_questions = {}
    unique_questions = []
    id_mapping = {}
    next_num = 1
    
    for oq in pkg.open_questions:
        if oq.question in seen_questions:
            id_mapping[oq.id] = seen_questions[oq.question]
            continue
            
        new_id = f"OQ-{next_num:03d}"
        id_mapping[oq.id] = new_id
        seen_questions[oq.question] = new_id
        
        oq.id = new_id
        unique_questions.append(oq)
        next_num += 1
        
    pkg.open_questions = unique_questions
    
    # Build set of valid OQ IDs after dedup
    valid_oq_ids = {oq.id for oq in pkg.open_questions}
    
    for r in pkg.requirements:
        new_affected_by = []
        for aff in r.affected_by:
            # Remap old OQ IDs to new ones
            mapped = id_mapping.get(aff, aff)
            # Only keep if it's a valid, existing open question ID
            if mapped in valid_oq_ids:
                new_affected_by.append(mapped)
        r.affected_by = list(set(new_affected_by))

class FlowState(RequirementsPackage):
    current_phase: str = "ingest"
    round_count: int = 0
    transcript_text: str = ""
    qa_findings: List[Dict[str, Any]] = Field(default_factory=list)
    proxy_objections: List[Dict[str, Any]] = Field(default_factory=list)
    mermaid_diagrams: Dict[str, str] = Field(default_factory=dict)

class RequirementsFlow(Flow[FlowState]):
    
    @start()
    def ingest(self):
        self.state.current_phase = "ingest"
        print(f"[{self.state.current_phase}] Reading transcript...")
        # Fallback to default if source_provenance and transcript_text are empty
        if not self.state.source_provenance and not self.state.transcript_text:
            self.state.source_provenance = ["tests/sample_transcript.txt"]
            
        # Read transcript if path is provided, otherwise use transcript_text directly
        if not self.state.transcript_text and self.state.source_provenance:
            self.state.transcript_text = read_transcript(self.state.source_provenance[0])
        print(f"[{self.state.current_phase}] Transcript length: {len(self.state.transcript_text)} characters.")

    @listen(ingest)
    def extract_skeleton(self):
        self.state.current_phase = "extract_skeleton"
        print(f"[{self.state.current_phase}] Running Discovery Crew (extract_statements -> draft_brief_and_requirements -> build_personas)...")
        
        dc = DiscoveryCrew()
        result = dc.crew().kickoff(inputs={"transcript": self.state.transcript_text})
        
        # 1. Parse SourceList
        statements_out = result.tasks_output[0].pydantic
        if statements_out and statements_out.statements:
            print(f"[{self.state.current_phase}] Extracted {len(statements_out.statements)} raw stakeholder statements.")
            
        # 2. Parse BriefAndRequirements
        brief_reqs_out = result.tasks_output[1].pydantic
        if brief_reqs_out:
            self.state.brief = brief_reqs_out.brief
            self.state.requirements = brief_reqs_out.requirements
            print(f"[{self.state.current_phase}] Project Name: '{self.state.brief.project_name}'. Drafted {len(self.state.requirements)} requirements.")
            
        # 3. Parse PersonaList
        personas_out = result.tasks_output[2].pydantic
        if personas_out:
            self.state.personas = personas_out.personas
            if personas_out.open_questions:
                self.state.open_questions.extend(personas_out.open_questions)
            print(f"[{self.state.current_phase}] Documented {len(self.state.personas)} user personas.")
            
        # Prune invalid affects references from open questions to ensure referential integrity
        prune_invalid_affects(self.state)
        
        # Run M1/M2 validation to verify skeleton structure
        settings = Settings.load()
        validate_package_integrity(self.state, orphan_check=settings.validation.orphan_check)
        print(f"[{self.state.current_phase}] Skeleton package validated successfully.")

    @listen(extract_skeleton)
    def elicitation(self):
        self.state.current_phase = "elicitation"
        print(f"[{self.state.current_phase}] Running elicitation turn...")
        
        settings = Settings.load()
        
        # Determine if Client Proxy is enabled
        proxy_mode = settings.client_proxy.mode
        proxy_enabled = False
        if proxy_mode == "on":
            proxy_enabled = True
        elif proxy_mode == "auto":
            proxy_enabled = len(self.state.transcript_text) >= settings.client_proxy.grounding_threshold
            
        print(f"[{self.state.current_phase}] Client proxy enabled: {proxy_enabled} (mode: {proxy_mode})")
        
        dc = DiscoveryCrew()
        agents = [dc.requirements_analyst()]
        if proxy_enabled:
            agents.append(dc.client_proxy())
            
        elicitation_crew = Crew(
            agents=agents,
            tasks=[dc.generate_clarifying_questions()],
            process=Process.sequential,
            verbose=True
        )
        
        res = elicitation_crew.kickoff(inputs={
            "transcript": self.state.transcript_text,
            "brief": self.state.brief.model_dump_json() if self.state.brief else "None",
            "requirements": json.dumps([r.model_dump(mode="json") for r in self.state.requirements]),
            "personas": json.dumps([p.model_dump(mode="json") for p in self.state.personas])
        })
        
        questions_out = res.pydantic
        if questions_out and questions_out.open_questions:
            # Merge questions ensuring no ID collisions
            existing_ids = {q.id for q in self.state.open_questions}
            for oq in questions_out.open_questions:
                if oq.id not in existing_ids:
                    self.state.open_questions.append(oq)
            
            # Prune invalid affects references from newly generated open questions
            prune_invalid_affects(self.state)
            print(f"[{self.state.current_phase}] Generated {len(questions_out.open_questions)} clarifying questions.")

    @router(elicitation)
    def gate_scope(self):
        self.state.current_phase = "gate_scope"
        blocking_questions = [
            q for q in self.state.open_questions 
            if q.blocking and q.status == OpenQuestionStatus.open
        ]
        
        if not blocking_questions:
            print(f"[{self.state.current_phase}] No blocking questions. Proceeding to deep authoring.")
            return "approved"
            
        print(f"[{self.state.current_phase}] Presenting {len(blocking_questions)} questions at Human Gate 1...")
        gate = ConsoleHumanGate(answers_file="gate1_answers.json")
        response = gate.request(GatePayload(brief=self.state.brief, blocking_questions=blocking_questions))
        
        if response.approved:
            apply_gate_responses(self.state, response)
            # Recheck
            remaining = [
                q for q in self.state.open_questions 
                if q.blocking and q.status == OpenQuestionStatus.open
            ]
            if not remaining:
                print(f"[{self.state.current_phase}] All blocking questions resolved. Proceeding.")
                return "approved"
                
        print(f"[{self.state.current_phase}] Stdin resolution paused or blocking questions remain. Eliciting more.")
        return "needs_more"

    @listen("needs_more")
    def loop_elicitation(self):
        # Simply route back to elicitation step
        return self.elicitation()

    @listen("approved")
    def deep_authoring(self):
        self.state.current_phase = "deep_authoring"
        print(f"[{self.state.current_phase}] Beginning actor-critic deep authoring...")
        
        settings = Settings.load()
        max_rounds = settings.actor_critic.max_rounds
        
        # Decide if proxy is enabled
        proxy_mode = settings.client_proxy.mode
        proxy_enabled = False
        if proxy_mode == "on":
            proxy_enabled = True
        elif proxy_mode == "auto":
            proxy_enabled = len(self.state.transcript_text) >= settings.client_proxy.grounding_threshold
            
        previous_objections = set()
        
        dc = DiscoveryCrew()
        
        while self.state.round_count < max_rounds:
            print(f"\n[{self.state.current_phase}] --- Round {self.state.round_count + 1}/{max_rounds} ---")
            
            confirmed_reqs = [r for r in self.state.requirements if r.status == Status.confirmed]
            
            # 1. Run Actor Crew
            actor_crew = Crew(
                agents=[dc.srs_writer(), dc.domain_modeler(), dc.uml_architect()],
                tasks=[
                    dc.author_srs(),
                    dc.model_domain(),
                    dc.author_diagrams()
                ],
                process=Process.sequential,
                verbose=True
            )
            
            actor_res = actor_crew.kickoff(inputs={
                "confirmed_requirements": json.dumps([r.model_dump(mode="json") for r in confirmed_reqs]),
                "findings": json.dumps(self.state.qa_findings) if self.state.qa_findings else "None",
                "objections": json.dumps(self.state.proxy_objections) if self.state.proxy_objections else "None",
                "transcript": self.state.transcript_text
            })
            
            # Merge Actor outputs
            srs_out = actor_res.tasks_output[0].pydantic
            if srs_out and srs_out.requirements:
                self.state.requirements = srs_out.requirements
                
            domain_out = actor_res.tasks_output[1].pydantic
            if domain_out and domain_out.domain_entities:
                self.state.domain_entities = domain_out.domain_entities
                
            diagrams_out = actor_res.tasks_output[2].pydantic
            if diagrams_out:
                self.state.mermaid_diagrams = {
                    "use_case": diagrams_out.use_case_diagram,
                    "sequence": diagrams_out.sequence_diagram,
                    "activity": diagrams_out.activity_diagram
                }
                
            # Prune invalid affects references from open questions to ensure referential integrity
            prune_invalid_affects(self.state)
            
            # Structural validation check
            try:
                validate_package_integrity(self.state, orphan_check=settings.validation.orphan_check)
            except PackageValidationError as e:
                print(f"[{self.state.current_phase}] Package validation failed in Round {self.state.round_count + 1}: {e}")
                self.state.qa_findings.append({
                    "severity": "block",
                    "kind": "validation",
                    "target_id": "package",
                    "note": f"Package validation failed: {str(e)}"
                })
                self.state.round_count += 1
                continue
                
            # 2. Critic A (qa_review)
            critic_crew_a = Crew(
                agents=[dc.requirements_reviewer()],
                tasks=[dc.qa_review()],
                verbose=True
            )
            qa_res = critic_crew_a.kickoff(inputs={
                "requirements": json.dumps([r.model_dump(mode="json") for r in self.state.requirements]),
                "domain_entities": json.dumps([e.model_dump(mode="json") for e in self.state.domain_entities]),
                "transcript": self.state.transcript_text
            })
            qa_findings_out = qa_res.pydantic
            self.state.qa_findings = [f.model_dump() for f in qa_findings_out.findings] if qa_findings_out else []
            
            # 3. Critic B (proxy_review)
            if proxy_enabled:
                critic_crew_b = Crew(
                    agents=[dc.client_proxy()],
                    tasks=[dc.proxy_review()],
                    verbose=True
                )
                proxy_res = critic_crew_b.kickoff(inputs={
                    "requirements": json.dumps([r.model_dump(mode="json") for r in self.state.requirements]),
                    "transcript": self.state.transcript_text,
                    "personas": json.dumps([p.model_dump(mode="json") for p in self.state.personas])
                })
                proxy_out = proxy_res.pydantic
                if proxy_out:
                    self.state.proxy_objections = [obj.model_dump() for obj in proxy_out.objections]
                    # Append inferred objections as open questions
                    existing_oq_questions = {q.question for q in self.state.open_questions}
                    for oq in proxy_out.open_questions:
                        if oq.question not in existing_oq_questions:
                            self.state.open_questions.append(oq)
                else:
                    self.state.proxy_objections = []
            else:
                self.state.proxy_objections = []
                
            # 4. Research Context (first round only)
            if self.state.round_count == 0 and settings.research.enabled:
                research_crew = Crew(
                    agents=[dc.researcher()],
                    tasks=[dc.research_context()],
                    verbose=True
                )
                research_res = research_crew.kickoff(inputs={
                    "brief": self.state.brief.model_dump_json() if self.state.brief else "None",
                    "requirements": json.dumps([r.model_dump(mode="json") for r in self.state.requirements])
                })
                research_out = research_res.pydantic
                if research_out and research_out.open_questions:
                    existing_oq_questions = {q.question for q in self.state.open_questions}
                    for oq in research_out.open_questions:
                        if oq.question not in existing_oq_questions:
                            oq.synthetic_origin = SourceOrigin.research
                            self.state.open_questions.append(oq)
                            
            # Check stopping criteria
            blocking_qa = [f for f in self.state.qa_findings if f["severity"] == "block"]
            current_objections = {f["note"] for f in blocking_qa} | {obj["objection"] for obj in self.state.proxy_objections}
            
            if not current_objections or current_objections.issubset(previous_objections):
                print(f"[{self.state.current_phase}] No new material objections. Exiting loop.")
                break
                
            previous_objections = current_objections
            self.state.round_count += 1
            
        # Determine the next available integer suffix for OQ-xxx
        import re
        existing_numbers = []
        for q in self.state.open_questions:
            match = re.match(r"^OQ-(\d+)$", q.id)
            if match:
                existing_numbers.append(int(match.group(1)))
        next_num = max(existing_numbers, default=0) + 1
        
        req_ids = {r.id for r in self.state.requirements}

        # Residual unresolved objections become open questions
        blocking_qa = [f for f in self.state.qa_findings if f["severity"] == "block"]
        for f in blocking_qa:
            question_text = f"QA Critic Objection: {f['note']} (target: {f['target_id']})"
            if not any(q.question == question_text for q in self.state.open_questions):
                oq_id = f"OQ-{next_num:03d}"
                target_valid = f["target_id"].startswith("REQ-") and f["target_id"] in req_ids
                oq = OpenQuestion(
                    id=oq_id,
                    question=question_text,
                    synthetic_origin=SourceOrigin.reviewer,
                    blocking=True,
                    blocking_rationale=f"QA reviewer flagged blocking defect on {f['target_id']}",
                    affects=[f["target_id"]] if target_valid else []
                )
                self.state.open_questions.append(oq)
                next_num += 1
                
        for obj in self.state.proxy_objections:
            question_text = f"Proxy Critic Objection: {obj['objection']} (target: {obj['target_id']})"
            if not any(q.question == question_text for q in self.state.open_questions):
                oq_id = f"OQ-{next_num:03d}"
                target_valid = obj["target_id"].startswith("REQ-") and obj["target_id"] in req_ids
                oq = OpenQuestion(
                    id=oq_id,
                    question=question_text,
                    synthetic_origin=SourceOrigin.client_proxy,
                    blocking=True,
                    blocking_rationale=f"Client proxy raised concern about {obj['target_id']}",
                    affects=[obj["target_id"]] if target_valid else []
                )
                self.state.open_questions.append(oq)
                next_num += 1
                
        print(f"[{self.state.current_phase}] Deep authoring finished after {self.state.round_count} rounds.")

    @router(deep_authoring)
    def gate_signoff(self):
        self.state.current_phase = "gate_signoff"
        blocking_questions = [
            q for q in self.state.open_questions 
            if q.blocking and q.status == OpenQuestionStatus.open
        ]
        
        if not blocking_questions:
            print(f"[{self.state.current_phase}] No blocking questions remaining. Proceeding to package.")
            return "signoff_approved"
            
        print(f"[{self.state.current_phase}] Presenting {len(blocking_questions)} questions at Human Gate 2...")
        gate = ConsoleHumanGate(answers_file="gate2_answers.json")
        response = gate.request(GatePayload(brief=self.state.brief, blocking_questions=blocking_questions))
        
        if response.approved:
            apply_gate_responses(self.state, response)
            remaining = [
                q for q in self.state.open_questions 
                if q.blocking and q.status == OpenQuestionStatus.open
            ]
            if not remaining:
                print(f"[{self.state.current_phase}] All blocking questions resolved. Proceeding to package.")
                return "signoff_approved"
                
        print(f"[{self.state.current_phase}] Stdin resolution paused or blocking questions remain.")
        return "signoff_needs_more"

    @listen("signoff_needs_more")
    def loop_signoff(self):
        # Route back to deep_authoring or re-check signoff
        return self.gate_signoff()

    @listen("signoff_approved")
    def package(self):
        self.state.current_phase = "package"
        print(f"[{self.state.current_phase}] Executing deterministic packaging...")
        
        settings = Settings.load()
        out_dir = settings.io.output_dir
        
        # Prune invalid affects references from open questions to ensure referential integrity
        prune_invalid_affects(self.state)
        
        # Write packaging to disk
        write_package_to_disk(self.state, out_dir, orphan_check=settings.validation.orphan_check)
        
        # Write Mermaid diagram files specifically
        out_path = Path(out_dir)
        uml_path = out_path / "uml"
        
        for name, code in self.state.mermaid_diagrams.items():
            if code:
                with open(uml_path / f"{name}.mermaid", "w", encoding="utf-8") as f:
                    f.write(code)
                    
        print(f"[{self.state.current_phase}] Handoff package compiled and written to: {out_dir}")
        return "complete"
