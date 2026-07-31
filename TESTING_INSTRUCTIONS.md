# 🧪 Testing & Verification Instructions (Google ADK / Gemini Build)

## 1. Prerequisites & Installation

Ensure Python `3.11+` and [`uv`](https://docs.astral.sh/uv/) (or standard `pip`) are installed.

```bash
# Clone the repository and checkout the adk-build branch
git clone https://github.com/RolexAlexander/plinth.git
cd plinth
git checkout adk-build

# Install dependencies with uv
uv sync
```

---

## 2. Environment Configuration

Create a `.env` file in the project root (or copy `.env.example`):

```bash
# Gemini API Key Configuration
GEMINI_API_KEY=your_gemini_api_key_here
GOOGLE_GENAI_USE_VERTEXAI=FALSE
```

*(Note: The system automatically reads `config.yaml` configured for `gemini/gemini-2.5-pro` and `gemini/gemini-2.5-flash`)*

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

---

## 4. Automated Unit & Validation Tests

Run the deterministic test suite:

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
