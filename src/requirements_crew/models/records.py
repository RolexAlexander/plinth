import re
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator
from .enums import (
    RequirementType,
    Status,
    Priority,
    SourceOrigin,
    REAL_ORIGINS,
    OpenQuestionStatus,
    DefaultIfDeferred,
)

class Source(BaseModel):
    origin: SourceOrigin
    ref: Optional[str] = None          # e.g. "discovery_2026-06-20.txt#L142-148"
    excerpt: Optional[str] = None

class AcceptanceCriterion(BaseModel):
    id: str                          # e.g. "AC-014-a"
    given: str
    when: str
    then: str

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        if not re.match(r"^AC-\d+-[a-z]$", v):
            raise ValueError(f"Acceptance Criterion ID must match pattern ^AC-\\d+-[a-z]$: {v}")
        return v

from typing import List, Optional, Any

class Metric(BaseModel):
    dimension: str                   # latency | throughput | availability | ...
    target: str                      # "p95 < 2s"
    condition: Optional[str] = None     # "<= 500 concurrent agents"

    @model_validator(mode="before")
    @classmethod
    def validate_before(cls, v: Any) -> Any:
        if isinstance(v, str):
            return {
                "dimension": "performance",
                "target": v
            }
        return v

class Requirement(BaseModel):
    id: str                          # pattern: REQ-\d+
    type: RequirementType
    statement: str
    rationale: Optional[str] = None
    status: Status
    priority: Priority
    source: List[Source] = Field(default_factory=list)
    metric: Optional[Metric] = None     # required iff type == non_functional (R2)
    acceptance_criteria: List[AcceptanceCriterion] = Field(default_factory=list)
    depends_on: List[str] = Field(default_factory=list)       # REQ ids
    affected_by: List[str] = Field(default_factory=list)      # OQ ids
    revision: int = 1

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        if not re.match(r"^REQ-\d+$", v):
            raise ValueError(f"Requirement ID must match pattern REQ-\\d+: {v}")
        return v

    @model_validator(mode="after")
    def validate_requirement_rules(self) -> "Requirement":
        # R1 / R4: status == confirmed => at least one source with origin in REAL_ORIGINS
        if self.status == Status.confirmed:
            if not self.source:
                raise ValueError(f"Requirement {self.id} is marked confirmed but has no sources.")
            has_real = any(s.origin in REAL_ORIGINS for s in self.source)
            if not has_real:
                raise ValueError(
                    f"Requirement {self.id} is marked confirmed but has no real human sources "
                    f"(only synthetic: {[s.origin.value for s in self.source]})."
                )

        # R2: type == non_functional => metric is not None and metric.target is non-empty
        if self.type == RequirementType.non_functional:
            if self.metric is None:
                raise ValueError(f"Requirement {self.id} is non-functional but has no metric defined.")
            if not self.metric.target or not self.metric.target.strip():
                raise ValueError(f"Requirement {self.id} is non-functional but has an empty metric target.")

        # R3: type == functional and status == confirmed => len(acceptance_criteria) >= 1
        if self.type == RequirementType.functional and self.status == Status.confirmed:
            if not self.acceptance_criteria:
                raise ValueError(f"Requirement {self.id} is a confirmed functional requirement but has no acceptance criteria.")

        return self

class OpenQuestion(BaseModel):
    id: str                          # pattern: OQ-\d+
    question: str
    synthetic_origin: SourceOrigin   # client_proxy | research | analyst_inference | reviewer | intake (gap)
    status: OpenQuestionStatus = OpenQuestionStatus.open
    blocking: bool
    blocking_rationale: Optional[str] = None   # required iff blocking is True
    affects: List[str] = Field(default_factory=list)          # REQ ids this question gates
    proposed_assumption: Optional[str] = None
    default_if_deferred: DefaultIfDeferred = DefaultIfDeferred.leave_open
    answer: Optional[str] = None        # set at the human gate

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        if not re.match(r"^OQ-\d+$", v):
            raise ValueError(f"Open Question ID must match pattern OQ-\\d+: {v}")
        return v

    @model_validator(mode="after")
    def validate_open_question_rules(self) -> "OpenQuestion":
        if self.blocking and (not self.blocking_rationale or not self.blocking_rationale.strip()):
            raise ValueError(f"Open Question {self.id} is marked blocking but has no blocking rationale.")
        if self.status == OpenQuestionStatus.answered:
            if not self.answer or not self.answer.strip():
                raise ValueError(f"Open Question {self.id} is marked answered but has an empty answer.")
            self.answer = self.answer.strip()
        return self
