<div align="center">

# 🏛️ Plinth

**Turns discovery into a foundation downstream agents can build on.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB.svg)](https://python.org)
[![CrewAI](https://img.shields.io/badge/Built%20with-CrewAI-FF6B35.svg)](https://crewai.com)

</div>

---

Plinth is an AI-powered **requirements discovery engine** that transforms raw stakeholder conversations into structured, validated Software Requirements Specifications (SRS). Feed it a transcript — get back a complete requirements package with traceability, domain models, and UML diagrams.

## ✨ Features

- **Structured extraction** — Parses stakeholder transcripts into typed requirements, personas, user stories, and domain entities
- **Actor–Critic refinement** — Multi-round deep authoring loop with QA review and client-proxy validation
- **Human-in-the-loop gates** — Blocking open questions surface for human approval before proceeding
- **Deterministic validation** — Pydantic-enforced rules (R1–R5) ensure no requirement is `confirmed` without a real human source
- **Full traceability** — Cross-reference matrix linking requirements ↔ user stories ↔ domain entities
- **UML generation** — Auto-generated use case, sequence, and activity diagrams in Mermaid syntax
- **Handoff manifest** — Machine-readable readiness report for downstream consumers

## 🏗️ Architecture

```
Transcript → Ingest → Extract Skeleton → Elicitation → Gate 1 (Scope)
                                                            ↓
                                          Deep Authoring (Actor → Critic loop)
                                                            ↓
                                                      Gate 2 (Signoff)
                                                            ↓
                                                    Package & Export
```

Plinth runs as a **CrewAI Flow** orchestrating specialized agent crews:

| Phase | Agents | Purpose |
|---|---|---|
| **Discovery** | Senior Requirements Analyst | Extract initial requirements skeleton from transcript |
| **Elicitation** | Elicitation Specialist | Generate clarifying open questions |
| **Deep Authoring** | SRS Writer, Domain Modeler, UML Architect | Produce full SRS, domain model, and diagrams |
| **QA Review** | Requirements Reviewer | Critic pass — find gaps, contradictions, untestable items |
| **Proxy Review** | Client Proxy | Simulate client objections against extracted personas |
| **Research** | Web Researcher | Ground requirements with compliance/domain context |

## 🚀 Quick Start

### Prerequisites

- Python 3.10–3.13
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- An LLM API key (Gemini, OpenAI, Anthropic, etc.)

### Install

```bash
git clone https://github.com/RolexAlexander/plinth.git
cd plinth
uv sync
```

### Configure

```bash
# Copy the example env and add your API key
cp .env.example .env
```

```env
GEMINI_API_KEY=your-key-here
```

Customize behavior in [`config.yaml`](config.yaml):

```yaml
llm:
  default_model: "gemini/gemini-3.5-flash"

actor_critic:
  max_rounds: 3

validation:
  orphan_check: warn   # warn | fail
```

### Run

```bash
# Run with the sample transcript
uv run kickoff

# Run with your own transcript
uv run kickoff path/to/your/transcript.txt
```

### Docker

```bash
# Build
docker build -t plinth .

# Run (mount your transcript and collect output)
docker run --rm \
  --env-file .env \
  -v ./my_transcript.txt:/app/tests/sample_transcript.txt \
  -v ./output:/app/output \
  plinth
```

Or use Docker Compose:

```bash
docker compose run --rm plinth
```

## 📦 Output

After a successful run, the `output/` directory contains:

| File | Description |
|---|---|
| `srs.md` | Full Software Requirements Specification |
| `requirements.json` | Structured requirements with status, priority, acceptance criteria |
| `open_questions.md` | Unresolved questions with proposed assumptions |
| `personas.md` | Extracted stakeholder personas |
| `domain_model.json` | Domain entities and relationships |
| `traceability.md` | Cross-reference matrix |
| `uml/*.mmd` | Mermaid diagrams (use case, sequence, activity) |
| `handoff_manifest.json` | Machine-readable readiness summary |

## 🧪 Testing

```bash
# Run all tests (no LLM required for M0–M2 tests)
uv run pytest tests/ -v

# Run with coverage
uv run pytest tests/ --cov=requirements_crew --cov-report=term-missing
```

## 🗂️ Project Structure

```
plinth/
├── config.yaml              # Runtime configuration
├── pyproject.toml            # Project metadata & dependencies
├── Dockerfile                # Container image
├── docker-compose.yml        # Compose orchestration
├── tests/
│   ├── sample_transcript.txt # Example stakeholder interview
│   └── test_*.py             # Deterministic test suite
└── src/requirements_crew/
    ├── main.py               # CLI entrypoint
    ├── settings.py           # Config loader
    ├── models/               # Pydantic models (R1–R5 validators)
    │   ├── package.py        # Core domain types
    │   └── outputs.py        # Crew output wrappers
    ├── agents/               # Agent definitions (YAML)
    ├── tasks/                # Task definitions (YAML)
    ├── crews/                # Crew wiring
    ├── flow/                 # Flow orchestration
    │   └── requirements_flow.py
    ├── validation/           # Package integrity checks
    ├── packaging/            # Output rendering & export
    └── tools/                # Custom CrewAI tools
```

## 🔧 Configuration Reference

| Key | Default | Description |
|---|---|---|
| `llm.default_model` | `gemini/gemini-3.5-flash` | LLM for all agents |
| `llm.render_model` | `gemini/gemini-3.5-flash` | LLM for rendering tasks |
| `client_proxy.mode` | `auto` | `on` / `off` / `auto` — controls proxy critic |
| `actor_critic.max_rounds` | `3` | Max deep-authoring revision loops |
| `research.enabled` | `true` | Enable web research grounding |
| `validation.orphan_check` | `warn` | `warn` or `fail` on orphan requirements |

## 📜 License

[MIT](LICENSE) — use it, fork it, build on it.

---

<div align="center">

**Plinth** — because every great system starts with a solid foundation.

</div>
