from pydantic import BaseModel, Field
from .enums import SourceOrigin

class SourceDocument(BaseModel):
    doc_id: str               # "transcript", "intake_form", "gate_answers"
    kind: SourceOrigin        # transcript | intake | human_answer (REAL origins only)
    text: str

class SourceRegistry(BaseModel):
    documents: dict[str, SourceDocument] = Field(default_factory=dict)
    
    def text_for_kind(self, kind: SourceOrigin) -> str:
        return "\n".join(d.text for d in self.documents.values() if d.kind == kind)
        
    def all_real_text(self) -> str:
        return "\n".join(d.text for d in self.documents.values())
