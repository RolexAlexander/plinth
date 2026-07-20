import os
from dotenv import load_dotenv

load_dotenv()

from crewai import LLM
from ..settings import Settings

def _setup_qwen_env():
    qwen_key = os.getenv("QWEN_API_KEY") or os.getenv("DASHSCOPE_API_KEY")
    qwen_base = os.getenv("QWEN_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1")
    if qwen_key:
        os.environ.setdefault("OPENAI_API_KEY", qwen_key)
        os.environ.setdefault("OPENAI_API_BASE", qwen_base)
        os.environ.setdefault("DASHSCOPE_API_KEY", qwen_key)

def get_default_llm() -> LLM:
    _setup_qwen_env()
    settings = Settings.load()
    model = os.getenv("MODEL_NAME") or settings.llm.default_model
    qwen_key = os.getenv("QWEN_API_KEY") or os.getenv("OPENAI_API_KEY")
    qwen_base = os.getenv("QWEN_BASE_URL") or os.getenv("OPENAI_API_BASE")
    if qwen_key and qwen_base and ("qwen" in model.lower() or "openai/" in model.lower()):
        return LLM(model=model, api_key=qwen_key, base_url=qwen_base)
    return LLM(model=model)

def get_render_llm() -> LLM:
    _setup_qwen_env()
    settings = Settings.load()
    model = os.getenv("MODEL_NAME") or settings.llm.render_model
    qwen_key = os.getenv("QWEN_API_KEY") or os.getenv("OPENAI_API_KEY")
    qwen_base = os.getenv("QWEN_BASE_URL") or os.getenv("OPENAI_API_BASE")
    if qwen_key and qwen_base and ("qwen" in model.lower() or "openai/" in model.lower()):
        return LLM(model=model, api_key=qwen_key, base_url=qwen_base)
    return LLM(model=model)
