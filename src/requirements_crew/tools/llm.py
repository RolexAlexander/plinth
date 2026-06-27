import os
from crewai import LLM
from ..settings import Settings

def get_default_llm() -> LLM:
    settings = Settings.load()
    model = settings.llm.default_model
    # Set default temperature or parameters if desired
    return LLM(model=model)

def get_render_llm() -> LLM:
    settings = Settings.load()
    model = settings.llm.render_model
    return LLM(model=model)
