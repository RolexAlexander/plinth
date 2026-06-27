import yaml
from pathlib import Path
from typing import List, Literal
from pydantic import BaseModel, Field

class LLMSettings(BaseModel):
    default_model: str = "gemini/gemini-1.5-pro"
    render_model: str = "gemini/gemini-1.5-flash"

class ClientProxySettings(BaseModel):
    mode: Literal["on", "off", "auto"] = "auto"
    grounding_threshold: int = 1500

class ActorCriticSettings(BaseModel):
    max_rounds: int = 3
    stop_on: str = "no_new_material_objections"

class ResearchSettings(BaseModel):
    enabled: bool = True
    allowed_query_types: List[str] = ["compliance", "domain_terminology", "comparable_features"]

class ValidationSettings(BaseModel):
    orphan_check: Literal["warn", "fail"] = "warn"

class IOSettings(BaseModel):
    output_dir: str = "./output"

class Settings(BaseModel):
    llm: LLMSettings = Field(default_factory=LLMSettings)
    client_proxy: ClientProxySettings = Field(default_factory=ClientProxySettings)
    actor_critic: ActorCriticSettings = Field(default_factory=ActorCriticSettings)
    research: ResearchSettings = Field(default_factory=ResearchSettings)
    validation: ValidationSettings = Field(default_factory=ValidationSettings)
    io: IOSettings = Field(default_factory=IOSettings)

    @classmethod
    def load(cls, path: str | Path = "config.yaml") -> "Settings":
        # Resolve config.yaml relative to workspace or project root
        config_path = Path(path)
        if not config_path.exists():
            # Try to resolve relative to requirements_crew dir
            sibling_path = Path(__file__).resolve().parents[2] / path
            if sibling_path.exists():
                config_path = sibling_path
        
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                return cls.model_validate(data)
            except Exception:
                pass
        return cls()
