# 🧪 Testing & Verification Instructions

## 1. Prerequisites & Installation

Ensure Python `3.11+` and [`uv`](https://docs.astral.sh/uv/) (or standard `pip`) are installed.

```bash
# Clone the repository
git clone https://github.com/RolexAlexander/plinth.git
cd plinth

# Install dependencies with uv
uv sync
```

---

## 2. Environment Configuration

Create a `.env` file in the project root (or copy `.env.example`):

```bash
# Qwen / DashScope Configuration
QWEN_API_KEY=your_qwen_api_key_here
QWEN_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1

# OpenAI-compatible mapping for LiteLLM
OPENAI_API_KEY=your_qwen_api_key_here
OPENAI_API_BASE=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
DASHSCOPE_API_KEY=your_qwen_api_key_here

# Model Choice
MODEL_NAME=openai/qwen3.7-plus
```

*(Note: The system automatically reads `config.yaml` configured for `openai/qwen3.7-plus`)*

---

## 3. Running the Agent

### Option A: Interactive ADK Playground UI
Launch the interactive web UI (visual event flow, state inspector, and artifact viewer):
```bash
agents-cli playground
# Or: adk web
```

### Option B: CLI Run (One-Shot Execution)
Run the pipeline against the default discovery transcript (`sample_transcript.txt`):
```bash
agents-cli run "Generate requirements for SpinCycle"
```

### Option C: Running via CrewAI Kickoff (CrewAI Flow Mode)
```bash
uv run kickoff
```

---

## 4. Automated Unit & Validation Tests

Run the deterministic test suite (validates anti-hallucination rules, grounding logic, and schema constraints):

```bash
uv run pytest tests/unit
```

---

## 5. Verification & Expected Deliverables

Upon completion, all generated artifacts are available in the `./output/` directory:

| Deliverable | Description |
|---|---|
| 📄 `srs.md` | Full Software Requirements Specification |
| 📊 `requirements.json` | 100% verbatim-grounded requirements list (`REQ-xxx`) with acceptance criteria & metrics |
| 👤 `personas.md` | Extracted user personas (`PERS-xxx`) |
| 🏷️ `domain_model.json` | Field-level domain entities, relationships, and attributes |
| 🔗 `traceability.md` | Full cross-reference matrix linking requirements ↔ user stories ↔ domain entities |
| ❓ `open_questions.json` | Tracked open questions (`OQ-xxx`) with resolution strategies |
| 📋 `handoff_manifest.json` | Machine-readable handoff manifest for downstream build agents |
