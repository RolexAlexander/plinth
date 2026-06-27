import re
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from .enums import Priority
from .records import Requirement, OpenQuestion, AcceptanceCriterion

class UserStory(BaseModel):
    id: str                          # US-\d+
    epic: str
    as_a: str
    i_want: str
    so_that: str
    requirement_ids: List[str] = Field(default_factory=list)  # the join: story -> requirements it implements
    acceptance_criteria: List[AcceptanceCriterion] = Field(default_factory=list)
    edge_cases: List[str] = Field(default_factory=list)
    priority: Priority

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        if not re.match(r"^US-\d+$", v):
            raise ValueError(f"User Story ID must match pattern US-\\d+: {v}")
        return v

class Persona(BaseModel):
    id: str                          # PERS-\d+
    name: str
    role: str
    goals: List[str] = Field(default_factory=list)
    pains: List[str] = Field(default_factory=list)
    permissions: List[str] = Field(default_factory=list)

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        if not re.match(r"^PERS-\d+$", v):
            raise ValueError(f"Persona ID must match pattern PERS-\\d+: {v}")
        return v

class EntityAttribute(BaseModel):
    name: str
    type: str
    nullable: bool = True

class Relationship(BaseModel):
    to: str                          # ENT id
    kind: str                        # one_to_one | one_to_many | many_to_one | many_to_many
    via: Optional[str] = None           # attribute name

class DomainEntity(BaseModel):
    id: str                          # ENT-<Name>
    name: str
    attributes: List[EntityAttribute] = Field(default_factory=list)
    relationships: List[Relationship] = Field(default_factory=list)

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        # Relaxing ENT- prefix validator to allow arbitrary PascalCase or alphanumeric names
        if not re.match(r"^ENT-[a-zA-Z0-9_]+$", v):
            raise ValueError(f"Domain Entity ID must match pattern ENT-<Name>: {v}")
        return v

class Decision(BaseModel):
    id: str                          # DEC-\d+
    statement: str
    rationale: str
    related_ids: List[str] = Field(default_factory=list)

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        if not re.match(r"^DEC-\d+$", v):
            raise ValueError(f"Decision ID must match pattern DEC-\\d+: {v}")
        return v

class ProjectBrief(BaseModel):
    project_name: str
    vision: str
    goals: List[str] = Field(default_factory=list)
    scope: List[str] = Field(default_factory=list)
    out_of_scope: List[str] = Field(default_factory=list)
    success_criteria: List[str] = Field(default_factory=list)

class RequirementsPackage(BaseModel):
    schema_version: str = "1.0"
    brief: Optional[ProjectBrief] = None
    personas: List[Persona] = Field(default_factory=list)
    requirements: List[Requirement] = Field(default_factory=list)
    user_stories: List[UserStory] = Field(default_factory=list)
    domain_entities: List[DomainEntity] = Field(default_factory=list)
    open_questions: List[OpenQuestion] = Field(default_factory=list)
    decisions: List[Decision] = Field(default_factory=list)
    package_version: str = "0.1.0"
    generated_at: Optional[datetime] = None
    source_provenance: List[str] = Field(default_factory=list)     # input filenames
