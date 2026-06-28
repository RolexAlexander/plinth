from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from .records import Source, Requirement, OpenQuestion, AcceptanceCriterion
from .package import ProjectBrief, Persona, DomainEntity

class SourceList(BaseModel):
    statements: List[Source]

class BriefAndRequirements(BaseModel):
    brief: ProjectBrief
    requirements: List[Requirement]

class PersonaList(BaseModel):
    personas: List[Persona]
    open_questions: List[OpenQuestion] = []

class OpenQuestionList(BaseModel):
    open_questions: List[OpenQuestion]

class RequirementList(BaseModel):
    requirements: List[Requirement]

class DomainEntityList(BaseModel):
    domain_entities: List[DomainEntity]

class MermaidDiagramList(BaseModel):
    use_case_diagram: str = ""
    sequence_diagram: str = ""
    activity_diagram: str = ""

class QAFinding(BaseModel):
    severity: str  # block | info
    kind: str      # ambiguity | contradiction | edge_case | validation
    target_id: str
    note: str

class QaReviewFindings(BaseModel):
    findings: List[QAFinding]

class ProxyObjection(BaseModel):
    target_id: str
    objection: str
    transcript_reference: Optional[str] = None

class ProxyReviewFindings(BaseModel):
    objections: List[ProxyObjection] = Field(default_factory=list)
    open_questions: List[OpenQuestion] = Field(default_factory=list)
    abstained: bool = False
    reason: Optional[str] = None
