from typing import List, Optional
from pydantic import BaseModel, Field
from .models import Source, Requirement, OpenQuestion, Decision, ProjectBrief, Persona, DomainEntity, UserStory, SourceOrigin

class IntakeResult(BaseModel):
    brief: ProjectBrief = Field(description="The drafted project brief containing name, vision, goals, and scope.")
    personas: List[Persona] = Field(default_factory=list, description="List of user personas.")
    statements: List[Source] = Field(default_factory=list, description="List of extracted verbatim stakeholder statements.")
    open_questions: List[OpenQuestion] = Field(default_factory=list, description="List of open questions representing gaps or unanswered details.")

class RequirementList(BaseModel):
    requirements: List[Requirement] = Field(default_factory=list, description="List of structured requirements.")

class DomainEntityList(BaseModel):
    domain_entities: List[DomainEntity] = Field(default_factory=list, description="List of domain entities.")

class MermaidDiagramList(BaseModel):
    use_case_diagram: str = Field(default="", description="Mermaid use case diagram string.")
    sequence_diagram: str = Field(default="", description="Mermaid sequence diagram string.")
    activity_diagram: str = Field(default="", description="Mermaid activity diagram string.")

class QAFinding(BaseModel):
    severity: str = Field(description="Severity of the finding: 'block' or 'info'.")
    kind: str = Field(description="Kind of finding: 'ambiguity', 'contradiction', 'edge_case', or 'validation'.")
    target_id: str = Field(description="The ID of the requirement or entity this finding targets.")
    note: str = Field(description="Explanatory note about the finding.")

class QaReviewFindings(BaseModel):
    findings: List[QAFinding] = Field(default_factory=list, description="List of QA findings.")

class UserStoryList(BaseModel):
    user_stories: List[UserStory] = Field(default_factory=list, description="List of user stories.")
