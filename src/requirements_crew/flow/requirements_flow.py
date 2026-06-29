import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from crewai.flow.flow import Flow, listen, start, router
from crewai import Crew, Process

from ..models.package import RequirementsPackage, ProjectBrief
from ..models.enums import Status, OpenQuestionStatus, SourceOrigin, DefaultIfDeferred
from ..models.records import OpenQuestion, Requirement
from ..models.sources import SourceDocument, SourceRegistry
from ..validation.package_validators import validate_package_integrity, PackageValidationError
from ..packaging.writer import write_package_to_disk
from ..crews.discovery_crew import DiscoveryCrew
from ..settings import Settings
from .human_gate import ConsoleHumanGate, GatePayload, GateResponse, apply_gate_responses
from ..tools.io import read_transcript

import os

def log_task_context(task_name: str, inputs: dict) -> None:
    if os.getenv("DEBUG_CONTEXT") == "true":
        transcript = inputs.get("transcript", "")
        pkg_json = inputs.get("current_package_json", "")
        print(f"\n[DEBUG CONTEXT] Task: {task_name}")
        print(f"  Transcript: length={len(transcript)} characters")
        if transcript:
            start_chars = transcript[:200].replace('\n', ' ')
            end_chars = transcript[-200:].replace('\n', ' ')
            print(f"  Transcript Start: {start_chars!r}")
            print(f"  Transcript End:   {end_chars!r}")
        if pkg_json:
            print(f"  Package JSON: length={len(pkg_json)} characters")
            try:
                pkg_dict = json.loads(pkg_json)
                req_count = len(pkg_dict.get("requirements", []))
                print(f"  Requirements in Package: count={req_count}")
            except Exception:
                pass
        print("=" * 60 + "\n")

def prune_invalid_affects(pkg: RequirementsPackage) -> None:
    # 1. Clear and rebuild affected_by on all requirements from oq.affects
    for r in pkg.requirements:
        r.affected_by = []
    for oq in pkg.open_questions:
        for req_id in oq.affects:
            req = next((r for r in pkg.requirements if r.id == req_id), None)
            if req and oq.id not in req.affected_by:
                req.affected_by.append(oq.id)

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

    # Common English stop words to ignore when extracting key nouns
    _STOP_WORDS = frozenset({
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "shall", "can", "need", "must", "to", "of",
        "in", "for", "on", "with", "at", "by", "from", "as", "into", "about",
        "between", "through", "during", "before", "after", "above", "below",
        "and", "or", "but", "not", "no", "nor", "so", "if", "then", "than",
        "that", "this", "these", "those", "it", "its", "they", "them", "their",
        "we", "our", "you", "your", "he", "she", "his", "her", "what", "which",
        "who", "whom", "how", "when", "where", "why", "all", "each", "every",
        "any", "some", "more", "most", "other", "such", "only", "same", "also",
        "there", "here", "just", "very", "much", "well", "still", "already",
        "system", "user", "users", "platform", "application", "data", "shall",
        "specific", "defined", "provide", "support", "allow", "enable", "ensure",
        "feature", "requirement", "requirements", "question", "questions"
    })

    def _log_phase_counts(self, phase_name: str) -> None:
        """P03-2: Print record counts for the current flow state for debugging."""
        if os.getenv("DEBUG_CONTEXT") == "true":
            print(f"\n[DEBUG CONTEXT] End of phase: {phase_name}")
            print(f"  Requirements:    {len(self.state.requirements)}")
            print(f"  Personas:        {len(self.state.personas)}")
            print(f"  User Stories:    {len(self.state.user_stories)}")
            print(f"  Open Questions:  {len(self.state.open_questions)}")
            print(f"  Decisions:       {len(self.state.decisions)}")
            print("=" * 60 + "\n")

    def _filter_off_domain_questions(self) -> None:
        """P02-4: Drop off-domain open questions whose key nouns are absent from
        the transcript and existing requirements. Only drops questions that also
        have no valid `affects` targets."""
        import re as _re

        # Build a reference corpus of domain nouns from transcript + requirements
        transcript_lower = self.state.transcript_text.lower()
        req_text = " ".join(
            f"{r.statement} {r.rationale or ''}"
            for r in self.state.requirements
        ).lower()
        domain_corpus = transcript_lower + " " + req_text

        filtered = []
        for oq in self.state.open_questions:
            # If the question has valid affects targets, keep it regardless
            if oq.affects:
                filtered.append(oq)
                continue

            # Extract key nouns (words with 4+ chars, not stop words)
            words = _re.findall(r"[a-zA-Z]{4,}", oq.question.lower())
            key_nouns = [w for w in words if w not in self._STOP_WORDS]

            if not key_nouns:
                filtered.append(oq)
                continue

            # Check if at least 40% of key nouns appear in the domain corpus
            grounded_count = sum(1 for n in key_nouns if n in domain_corpus)
            grounding_ratio = grounded_count / len(key_nouns)

            if grounding_ratio >= 0.4:
                filtered.append(oq)
            else:
                print(
                    f"[{self.state.current_phase}] Dropped off-domain question {oq.id}: "
                    f"{oq.question[:80]}... (grounding ratio: {grounding_ratio:.0%})"
                )

        dropped_count = len(self.state.open_questions) - len(filtered)
        if dropped_count > 0:
            print(f"[{self.state.current_phase}] Filtered out {dropped_count} off-domain question(s).")
        self.state.open_questions = filtered
    
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
        
        # Register the transcript
        if self.state.transcript_text:
            self.state.source_registry.documents["transcript"] = SourceDocument(
                doc_id="transcript",
                kind=SourceOrigin.transcript,
                text=self.state.transcript_text
            )
        print(f"[{self.state.current_phase}] Transcript length: {len(self.state.transcript_text)} characters.")
        self._log_phase_counts("ingest")

    @listen(ingest)
    def extract_skeleton(self):
        self.state.current_phase = "extract_skeleton"
        print(f"[{self.state.current_phase}] Running Discovery Crew (extract_statements -> draft_brief_and_requirements -> build_personas)...")
        
        dc = DiscoveryCrew()
        inputs = {
            "transcript": self.state.transcript_text,
            "current_package_json": self.state.model_dump_json()
        }
        log_task_context("extract_skeleton", inputs)
        result = dc.crew().kickoff(inputs=inputs)
        
        # 1. Parse SourceList
        statements_out = result.tasks_output[0].pydantic
        if statements_out and statements_out.statements:
            self.state.candidate_statement_count = len(statements_out.statements)
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
        
        # Verify source grounding
        from ..validation.grounding import validate_source_grounding
        validate_source_grounding(self.state, self.state.source_registry)
        
        # Verify coverage
        from ..validation.coverage import validate_coverage
        validate_coverage(self.state, self.state.transcript_text, self.state.candidate_statement_count)
        print(f"[{self.state.current_phase}] Skeleton package, grounding, and coverage validated successfully.")
        self._log_phase_counts("extract_skeleton")

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
        
        inputs = {
            "transcript": self.state.transcript_text,
            "current_package_json": self.state.model_dump_json(),
            "brief": self.state.brief.model_dump_json() if self.state.brief else "None",
            "requirements": json.dumps([r.model_dump(mode="json") for r in self.state.requirements]),
            "personas": json.dumps([p.model_dump(mode="json") for p in self.state.personas])
        }
        log_task_context("elicitation", inputs)
        res = elicitation_crew.kickoff(inputs=inputs)
        
        questions_out = res.pydantic
        if questions_out and questions_out.open_questions:
            # Merge questions ensuring no ID collisions
            existing_ids = {q.id for q in self.state.open_questions}
            for oq in questions_out.open_questions:
                if oq.id not in existing_ids:
                    self.state.open_questions.append(oq)
            
            # Prune invalid affects references from newly generated open questions
            prune_invalid_affects(self.state)
            
            # P02-4: Ground clarifying questions — drop off-domain questions
            self._filter_off_domain_questions()
            
            print(f"[{self.state.current_phase}] Generated {len(questions_out.open_questions)} clarifying questions.")
        self._log_phase_counts("elicitation")

    @router(elicitation)
    def gate_scope(self):
        self.state.current_phase = "gate_scope"
        blocking_questions = [
            q for q in self.state.open_questions 
            if q.blocking and (
                q.status == OpenQuestionStatus.open or
                (q.status == OpenQuestionStatus.deferred and q.default_if_deferred in (DefaultIfDeferred.leave_open, DefaultIfDeferred.drop_scope))
            )
        ]
        
        if not blocking_questions:
            print(f"[{self.state.current_phase}] No blocking questions. Proceeding to deep authoring.")
            self._log_phase_counts("gate_scope")
            return "approved"
            
        print(f"[{self.state.current_phase}] Presenting {len(blocking_questions)} questions at Human Gate 1...")
        gate = ConsoleHumanGate(answers_file="gate1_answers.json")
        response = gate.request(GatePayload(brief=self.state.brief, blocking_questions=blocking_questions))
        
        if response.approved:
            apply_gate_responses(self.state, response)
            # Recheck
            remaining = [
                q for q in self.state.open_questions 
                if q.blocking and (
                    q.status == OpenQuestionStatus.open or
                    (q.status == OpenQuestionStatus.deferred and q.default_if_deferred in (DefaultIfDeferred.leave_open, DefaultIfDeferred.drop_scope))
                )
            ]
            if not remaining:
                print(f"[{self.state.current_phase}] All blocking questions resolved. Proceeding.")
                self._log_phase_counts("gate_scope")
                return "approved"
                
        print(f"[{self.state.current_phase}] Stdin resolution paused or blocking questions remain. Eliciting more.")
        self._log_phase_counts("gate_scope")
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
            
            inputs = {
                "confirmed_requirements": json.dumps([r.model_dump(mode="json") for r in confirmed_reqs]),
                "findings": json.dumps(self.state.qa_findings) if self.state.qa_findings else "None",
                "objections": json.dumps(self.state.proxy_objections) if self.state.proxy_objections else "None",
                "transcript": self.state.transcript_text,
                "current_package_json": self.state.model_dump_json()
            }
            log_task_context("deep_authoring_actor", inputs)
            actor_res = actor_crew.kickoff(inputs=inputs)
            
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
                
            # Verbatim Grounding check
            try:
                from ..validation.grounding import validate_source_grounding
                validate_source_grounding(self.state, self.state.source_registry)
            except Exception as e:
                print(f"[{self.state.current_phase}] Grounding validation failed in Round {self.state.round_count + 1}: {e}")
                self.state.qa_findings.append({
                    "severity": "block",
                    "kind": "grounding",
                    "target_id": "package",
                    "note": f"Grounding validation failed: {str(e)}"
                })
                self.state.round_count += 1
                continue
                
            # 2. Critic A (qa_review)
            critic_crew_a = Crew(
                agents=[dc.requirements_reviewer()],
                tasks=[dc.qa_review()],
                verbose=True
            )
            inputs = {
                "requirements": json.dumps([r.model_dump(mode="json") for r in self.state.requirements]),
                "domain_entities": json.dumps([e.model_dump(mode="json") for e in self.state.domain_entities]),
                "transcript": self.state.transcript_text,
                "current_package_json": self.state.model_dump_json()
            }
            log_task_context("qa_review", inputs)
            qa_res = critic_crew_a.kickoff(inputs=inputs)
            qa_findings_out = qa_res.pydantic
            self.state.qa_findings = [f.model_dump() for f in qa_findings_out.findings] if qa_findings_out else []
            
            # 3. Critic B (proxy_review)
            if proxy_enabled:
                critic_crew_b = Crew(
                    agents=[dc.client_proxy()],
                    tasks=[dc.proxy_review()],
                    verbose=True
                )
                inputs = {
                    "requirements": json.dumps([r.model_dump(mode="json") for r in self.state.requirements]),
                    "transcript": self.state.transcript_text,
                    "personas": json.dumps([p.model_dump(mode="json") for p in self.state.personas]),
                    "current_package_json": self.state.model_dump_json()
                }
                log_task_context("proxy_review", inputs)
                proxy_res = critic_crew_b.kickoff(inputs=inputs)
                proxy_out = proxy_res.pydantic
                if proxy_out and not getattr(proxy_out, "abstained", False):
                    self.state.proxy_objections = [obj.model_dump() for obj in proxy_out.objections]
                    # Append inferred objections as open questions
                    existing_oq_questions = {q.question for q in self.state.open_questions}
                    for oq in proxy_out.open_questions:
                        if oq.question not in existing_oq_questions:
                            self.state.open_questions.append(oq)
                else:
                    if proxy_out and getattr(proxy_out, "abstained", False):
                        print(f"[{self.state.current_phase}] Proxy critic abstained: {proxy_out.reason}")
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
                inputs = {
                    "transcript": self.state.transcript_text,
                    "current_package_json": self.state.model_dump_json(),
                    "brief": self.state.brief.model_dump_json() if self.state.brief else "None",
                    "requirements": json.dumps([r.model_dump(mode="json") for r in self.state.requirements])
                }
                log_task_context("research_context", inputs)
                research_res = research_crew.kickoff(inputs=inputs)
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
        valid_ids = (
            {r.id for r in self.state.requirements} |
            {us.id for us in self.state.user_stories} |
            {pers.id for pers in self.state.personas} |
            {ent.id for ent in self.state.domain_entities} |
            {dec.id for dec in self.state.decisions}
        )

        # Residual unresolved objections become open questions
        blocking_qa = [f for f in self.state.qa_findings if f["severity"] == "block"]
        for f in blocking_qa:
            target_id = f["target_id"]
            if target_id not in valid_ids:
                print(f"[{self.state.current_phase}] Dropping QA objection targeting non-existent record: {target_id}")
                continue
                
            question_text = f"QA Critic Objection: {f['note']} (target: {target_id})"
            if not any(q.question == question_text for q in self.state.open_questions):
                oq_id = f"OQ-{next_num:03d}"
                aff_list = [target_id] if target_id in req_ids else []
                oq = OpenQuestion(
                    id=oq_id,
                    question=question_text,
                    synthetic_origin=SourceOrigin.reviewer,
                    blocking=True,
                    blocking_rationale=f"QA reviewer flagged blocking defect on {target_id}",
                    affects=aff_list,
                    proposed_assumption=f"Resolve the critic issue by adopting the current implementation draft for {target_id}.",
                    default_if_deferred=DefaultIfDeferred.adopt_assumption
                )
                self.state.open_questions.append(oq)
                next_num += 1
                
        for obj in self.state.proxy_objections:
            target_id = obj["target_id"]
            if target_id not in valid_ids:
                print(f"[{self.state.current_phase}] Dropping proxy objection targeting non-existent record: {target_id}")
                continue
                
            question_text = f"Proxy Critic Objection: {obj['objection']} (target: {target_id})"
            if not any(q.question == question_text for q in self.state.open_questions):
                oq_id = f"OQ-{next_num:03d}"
                aff_list = [target_id] if target_id in req_ids else []
                oq = OpenQuestion(
                    id=oq_id,
                    question=question_text,
                    synthetic_origin=SourceOrigin.client_proxy,
                    blocking=True,
                    blocking_rationale=f"Client proxy raised concern about {target_id}",
                    affects=aff_list,
                    proposed_assumption=f"Proceed with the current draft requirements for {target_id} as specified.",
                    default_if_deferred=DefaultIfDeferred.adopt_assumption
                )
                self.state.open_questions.append(oq)
                next_num += 1
                
        print(f"[{self.state.current_phase}] Deep authoring finished after {self.state.round_count} rounds.")
        self._log_phase_counts("deep_authoring")

    @listen(deep_authoring)
    def generate_user_stories(self):
        self.state.current_phase = "generate_user_stories"
        print(f"[{self.state.current_phase}] Generating user stories from finalized requirements...")
        
        dc = DiscoveryCrew()
        stories_crew = Crew(
            agents=[dc.user_story_writer()],
            tasks=[dc.author_user_stories()],
            process=Process.sequential,
            verbose=True
        )
        
        inputs = {
            "transcript": self.state.transcript_text,
            "current_package_json": self.state.model_dump_json()
        }
        log_task_context("generate_user_stories", inputs)
        stories_res = stories_crew.kickoff(inputs=inputs)
        
        stories_out = stories_res.pydantic
        if stories_out and stories_out.user_stories:
            self.state.user_stories = stories_out.user_stories
            print(f"[{self.state.current_phase}] Generated {len(self.state.user_stories)} user stories.")
            
            # Check coverage: every must/should requirement should be referenced
            must_should_ids = {
                r.id for r in self.state.requirements
                if r.priority.value in ("must", "should")
                and r.status != Status.deprecated
            }
            covered_ids = set()
            for us in self.state.user_stories:
                covered_ids.update(us.requirement_ids)
            uncovered = must_should_ids - covered_ids
            if uncovered:
                print(f"[{self.state.current_phase}] WARNING: {len(uncovered)} must/should requirements not covered by user stories: {sorted(uncovered)}")
        else:
            print(f"[{self.state.current_phase}] WARNING: No user stories generated.")
        self._log_phase_counts("generate_user_stories")

    @router(generate_user_stories)
    def gate_signoff(self):
        self.state.current_phase = "gate_signoff"
        
        # Track signoff attempts to prevent infinite loops
        if not hasattr(self, '_signoff_attempts'):
            self._signoff_attempts = 0
        self._signoff_attempts += 1
        
        blocking_questions = [
            q for q in self.state.open_questions 
            if q.blocking and (
                q.status == OpenQuestionStatus.open or
                (q.status == OpenQuestionStatus.deferred and q.default_if_deferred in (DefaultIfDeferred.leave_open, DefaultIfDeferred.drop_scope))
            )
        ]
        
        if not blocking_questions:
            print(f"[{self.state.current_phase}] No blocking questions remaining. Proceeding to package.")
            self._log_phase_counts("gate_signoff")
            return "signoff_approved"
        
        # In unattended mode, bail after 1 attempt to avoid infinite loop
        unattended = os.environ.get("PLINTH_UNATTENDED", "").lower() == "true"
        max_attempts = 1 if unattended else 3
        
        if self._signoff_attempts > max_attempts:
            print(f"[{self.state.current_phase}] Max signoff attempts ({max_attempts}) reached.")
            print(f"[{self.state.current_phase}] {len(blocking_questions)} blocking questions remain unresolved — proceeding to package anyway.")
            print(f"[{self.state.current_phase}] NOTE: ready_for will be empty in the handoff manifest.")
            self._log_phase_counts("gate_signoff")
            return "signoff_approved"
            
        print(f"[{self.state.current_phase}] Presenting {len(blocking_questions)} questions at Human Gate 2...")
        gate = ConsoleHumanGate(answers_file="gate2_answers.json")
        response = gate.request(GatePayload(brief=self.state.brief, blocking_questions=blocking_questions))
        
        if response.approved:
            apply_gate_responses(self.state, response)
            remaining = [
                q for q in self.state.open_questions 
                if q.blocking and (
                    q.status == OpenQuestionStatus.open or
                    (q.status == OpenQuestionStatus.deferred and q.default_if_deferred in (DefaultIfDeferred.leave_open, DefaultIfDeferred.drop_scope))
                )
            ]
            if not remaining:
                print(f"[{self.state.current_phase}] All blocking questions resolved. Proceeding to package.")
                self._log_phase_counts("gate_signoff")
                return "signoff_approved"
                
        print(f"[{self.state.current_phase}] Stdin resolution paused or blocking questions remain.")
        self._log_phase_counts("gate_signoff")
        return "signoff_needs_more"

    @listen("signoff_needs_more")
    def loop_signoff(self):
        # Route back to re-check signoff (with attempt counter to prevent infinite loop)
        return self.gate_signoff()

    @listen("signoff_approved")
    def package(self):
        self.state.current_phase = "package"
        print(f"[{self.state.current_phase}] Executing deterministic packaging...")
        
        settings = Settings.load()
        out_dir = settings.io.output_dir
        
        # Verify source grounding before packaging (strict mode, will raise GroundingError if ungrounded)
        from ..validation.grounding import validate_source_grounding
        validate_source_grounding(self.state, self.state.source_registry)
        
        # Verify coverage before packaging
        from ..validation.coverage import validate_coverage
        validate_coverage(self.state, self.state.transcript_text, self.state.candidate_statement_count)
        
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
        self._log_phase_counts("package")
        return "complete"
