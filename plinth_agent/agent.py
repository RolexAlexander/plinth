from google.adk.agents import Agent, SequentialAgent, LoopAgent
from google.adk.apps import App, ResumabilityConfig
from google.adk.models import Gemini
from google.adk.tools import request_input
from google.genai import types

from .schemas import IntakeResult, RequirementList, QaReviewFindings, UserStoryList
from .callbacks import (
    init_state, unpack_intake, ground_requirements, ground_and_check_coverage, 
    process_qa_review_findings, before_intake_log, before_requirements_log, before_writer_log,
    auto_resolve_open_questions_in_test
)
from .tools import mark_review_passed, finalize_package, resolve_open_questions

def create_intake_agent() -> Agent:
    """Creates the Discovery Intake Analyst agent.
    
    Extracts project brief details, user personas, and verbatim stakeholder
    statements from the raw transcript.
    """
    instruction = """Analyze the raw discovery input transcript:
---
{transcript}
---

Identify and extract:
1. The Project Brief details:
   - project_name (e.g. SpinCycle)
   - vision
   - goals (list of goals)
   - scope (list of scope items)
   - out_of_scope (list of out of scope items)
   - success_criteria (list of success criteria)

2. Every distinct stakeholder statement.
   For each statement:
   - Origin must be set to 'transcript'.
   - Set 'ref' to the filename (e.g. 'sample_transcript.txt') optionally with lines if known.
   - Extract the exact 'excerpt' (verbatim quote). You must be highly faithful to the text; do not summarize, generalise, infer, or embellish. If it is not explicitly stated in the transcript, do not extract it.

3. User types, their goals, pain points, and permissions. Build structured personas representing these users.
   CRITICAL REQUIREMENT FOR PERSONA IDs:
   - Every Persona ID MUST match the pattern PERS-\\d+ (strictly PERS-\\d+, e.g. PERS-001, PERS-002, PERS-003, PERS-004).
   - You MUST NOT use names or descriptive strings like 'customer', 'laundromat_owner', 'manager', or 'attendant' as IDs.
   - For example: name a persona with ID 'PERS-001', not 'customer' or 'laundromat_owner'.
   - For each persona, specify a verbatim 'role_excerpt' from the transcript, and a list of verbatim 'goals_excerpts' from the transcript.
   
   If you identify any gaps or unanswered details about a persona, list them as OpenQuestions.
   CRITICAL REQUIREMENT FOR OPEN QUESTION IDs:
   - Every OpenQuestion ID MUST match the pattern OQ-\\d+ (strictly OQ-\\d+, e.g. OQ-001, OQ-002).
   - synthetic_origin must be set to 'intake'.
   - default_if_deferred must be exactly one of: 'adopt_assumption', 'leave_open', 'drop_scope' (strictly lowercase).
   - If you mark an OpenQuestion as blocking (blocking is True), you MUST provide a detailed `blocking_rationale` explaining why it blocks the affected requirements.
   - affects must be empty or contain valid Requirement IDs (matching pattern REQ-\\d+), NEVER Persona IDs.
"""
    return Agent(
        name="intake_agent",
        model=Gemini(
            model="gemini-2.5-flash",
            retry_options=types.HttpRetryOptions(attempts=3),
        ),
        instruction=instruction,
        output_schema=IntakeResult,
        output_key="intake_result",
        before_agent_callback=before_intake_log,
        after_agent_callback=unpack_intake,
    )

def create_requirements_agent() -> Agent:
    """Creates the Senior Requirements Analyst agent.
    
    Converts sourced statements into clear, testable, individually-traceable requirements.
    """
    instruction = """Based on the raw discovery transcript:
---
{transcript}
---

And the project brief, personas, and stakeholder statements from the intake analysis:
---
Project Brief:
{brief}

User Personas:
{personas}

Stakeholder Statements:
{statements}
---

Convert stakeholder statements into clear, testable, individually traceable requirements.
For each requirement, you must strictly adhere to the following schema constraints:
- Assign an ID in the format REQ-001, REQ-002, etc. (strictly REQ-\\d+, e.g. REQ-001, REQ-002). DO NOT use REQ-000 under any circumstances.
- Select its type: functional, non_functional, business_rule, or constraint (strictly lowercase).
- If it is a non-functional requirement, you MUST define a quantified 'metric' containing dimension (e.g. latency, availability) and target (e.g. 'p95 < 2s'). The target must NOT be empty.
- Trace each requirement to its sources:
  - You MUST set the initial status of all requirements to 'open' (if it traces to a stakeholder statement) or 'assumed' (if inferred/synthetic). Do NOT set the status to 'confirmed' directly in your output. The grounding callback will automatically promote them to 'confirmed' if they are verified.
  - If the requirement is inferred by you (not explicitly stated by the stakeholder), you MUST set its status to 'assumed' or 'open' and set its source origin to 'analyst_inference'.
  - REMEMBER the safety rule: The grounding callback only promotes to 'confirmed' if it has at least one source with a real human origin ('transcript', 'intake', or 'human_answer').
- CRITICAL VALIDATION RULE: For every functional requirement (type is 'functional'), you MUST define at least one acceptance criterion in the `acceptance_criteria` list, even if its status is initially 'open' or 'assumed'. This ensures that if the requirement is promoted to 'confirmed' by the grounding callback, it will already have the required acceptance criteria.
- Acceptance criterion IDs must match the pattern AC-\\d+-[a-z] (strictly AC-\\d+-[a-z], e.g. AC-001-a).
- Define dependencies using 'depends_on' (list of REQ IDs).
- Select its priority: must, should, could, wont (strictly lowercase MoSCoW values).
"""
    return Agent(
        name="requirements_agent",
        model=Gemini(
            model="gemini-2.5-pro",
            retry_options=types.HttpRetryOptions(attempts=3),
        ),
        instruction=instruction,
        output_schema=RequirementList,
        output_key="requirements",
        before_agent_callback=before_requirements_log,
        after_agent_callback=ground_requirements,
    )

def create_srs_writer() -> Agent:
    """Creates the SRS Writer agent (Actor in the refinement loop).
    
    Assembles confirmed requirements into a complete, consistent SRS structure,
    refining them based on the QA reviewer's findings.
    """
    instruction = """Refine and assemble the requirements into a complete, consistent SRS structure.
Refer to the raw stakeholder transcript for grounding:
---
{transcript}
---
And the current requirements:
---
{requirements}
---
And the QA critic review comments:
---
{srs_review}
---
Address all findings from the critic review.

You must strictly adhere to the following requirement rules to ensure Pydantic schema validation passes:
1. Grounding Rule (R1/R4): You MUST set the status of all requirements to 'open' (for real sources) or 'assumed' (for synthetic/inferred sources). Do NOT set the status to 'confirmed' directly in your output. The grounding callback will automatically promote them to 'confirmed' if they pass the verbatim grounding check.
2. IDs Rule: Requirement IDs MUST start from REQ-001 and increment sequentially (strictly REQ-\\d+, e.g. REQ-001, REQ-002). DO NOT use REQ-000 under any circumstances. Acceptance criterion IDs MUST match pattern AC-\\d+-[a-z] (strictly, e.g. AC-001-a).
3. Non-Functional Metrics (R2): For every non-functional requirement (type is 'non_functional'), you MUST define a quantified 'metric' containing dimension (e.g. latency, availability) and target (e.g. 'p95 < 2s'). The target must NOT be empty.
4. Acceptance Criteria (R3): For every functional requirement (type is 'functional'), you MUST define at least one acceptance criterion in the `acceptance_criteria` list, even if its status is initially 'open' or 'assumed'.
5. Only confirmed and assumed requirements can be finalized; do not include unconfirmed inferences or open questions in the requirements list.
"""
    return Agent(
        name="srs_writer",
        model=Gemini(
            model="gemini-2.5-flash",
            retry_options=types.HttpRetryOptions(attempts=3),
        ),
        instruction=instruction,
        output_schema=RequirementList,
        output_key="requirements",
        before_agent_callback=before_writer_log,
        after_agent_callback=ground_requirements,
    )

def create_qa_critic() -> Agent:
    """Creates the QA Critic agent (Reviewer in the refinement loop).
    
    Audits the specifications for ambiguity, contradictions, or missing edge cases,
    and signals loop exit when no material objections remain.
    """
    instruction = """Perform a quality assurance review of the drafted SRS (requirements and domain model) against the original stakeholder transcript:
---
{transcript}
---
Here are the current requirements:
---
{requirements}
---
Identify ambiguities, contradictions, missing edge cases, or acceptance criteria that do not properly test their requirement statements.
If there are NO remaining material objections or blockages, you MUST call the mark_review_passed tool to conclude the review and exit the loop.
Otherwise, output the QA findings list.
"""
    return Agent(
        name="qa_critic",
        model=Gemini(
            model="gemini-2.5-pro",
            retry_options=types.HttpRetryOptions(attempts=3),
        ),
        instruction=instruction,
        output_schema=QaReviewFindings,
        output_key="srs_review",
        tools=[mark_review_passed],
        after_agent_callback=process_qa_review_findings,
    )

def create_user_story_agent() -> Agent:
    """Creates the User Story Writer agent.
    
    Transforms the finalized requirements into user stories covered by acceptance criteria.
    """
    instruction = """Transform the finalized requirements into user stories grouped under epics.

Stakeholder Transcript (for context):
---
{transcript}
---
Current Requirements:
---
{requirements}
---
User Personas:
---
{personas}
---

Rules:
1. Group stories under epics that map to the project brief's scope areas (e.g. authentication/payments, machine control, loyalty/subscription, dashboard/roles, maintenance, reservations, etc.).
2. Write each story in canonical form: As a (persona role), I want (action), So that (benefit).
3. Each story MUST carry `requirement_ids` linking to the requirements it implements. Every requirement ID in `requirement_ids` MUST be selected from the provided Current Requirements list (e.g. REQ-001, REQ-002). DO NOT use or invent other requirement IDs (like REQ-CUST-002, REQ-PAY-001, REQ-MACH-001, etc.).
4. Coverage rule: Every requirement with priority `must` or `should` MUST be referenced by at least one user story's `requirement_ids`. If a must/should requirement is not covered, create a story for it.
5. Include `acceptance_criteria` (id pattern AC-\\d+-[a-z], e.g., AC-001-a, AC-002-b. DO NOT use the story ID in the AC ID, e.g., do not output AC-US-003-a. The middle part MUST be numeric only) and `edge_cases` for each story.
6. Story IDs must match pattern US-\\d+.
7. Story priority should inherit from the highest-priority requirement it covers.
8. Use the personas to inform the `as_a` field — use the persona's role, not their name.
9. Do NOT invent new requirements. Only organize existing requirements into user stories. You must strictly use the requirement IDs exactly as defined in the Current Requirements list.
"""
    return Agent(
        name="user_story_agent",
        model=Gemini(
            model="gemini-2.5-flash",
            retry_options=types.HttpRetryOptions(attempts=3),
        ),
        instruction=instruction,
        output_schema=UserStoryList,
        output_key="user_stories",
        after_agent_callback=ground_and_check_coverage,
        include_contents="none",
    )

def create_package_agent() -> Agent:
    """Creates the final Packaging agent.
    
    Executes the deterministic finalize_package tool.
    """
    instruction = """You are the packaging agent. Your only task is to call the finalize_package tool to compile the requirements package, run validators, and write the output files to disk. You MUST execute this tool call immediately."""
    return Agent(
        name="package_agent",
        model=Gemini(
            model="gemini-2.5-flash",
            retry_options=types.HttpRetryOptions(attempts=3),
        ),
        instruction=instruction,
        tools=[finalize_package],
        include_contents="none",
    )

def create_authoring_loop() -> LoopAgent:
    """Creates the actor-critic refinement LoopAgent."""
    return LoopAgent(
        name="authoring_loop",
        sub_agents=[
            create_srs_writer(),
            create_qa_critic(),
        ],
        max_iterations=3,
    )

def create_elicitation_agent() -> Agent:
    """Creates the Elicitation Specialist agent.
    
    Presents open clarifying questions to the user and resolves them using their answers.
    """
    instruction = """You are the Elicitation Specialist.
Your task is to resolve open/blocking questions before final packaging.

First, look at the open questions in the state:
{open_questions}

1. If there are NO open questions, or if all open questions already have an answer (i.e., status is not 'open'), do not call any tools and stop.
2. If there are open questions:
   a. Check if the user has already provided answers to them in the conversation history.
   b. If the user has NOT provided answers yet: call the request_input tool with a formatted list of all open questions to ask the user to resolve them. Do not call resolve_open_questions until you have answers.
   c. If you have the user's answers: parse them to map each question ID (e.g. OQ-001) to its answer, and call the resolve_open_questions tool. Once the tool returns, stop.
"""
    return Agent(
        name="elicitation_agent",
        model=Gemini(
            model="gemini-2.5-pro",
            retry_options=types.HttpRetryOptions(attempts=3),
        ),
        instruction=instruction,
        tools=[request_input, resolve_open_questions],
        before_agent_callback=auto_resolve_open_questions_in_test,
    )

# The root agent that orchestrates the entire requirements discovery pipeline
root_agent = SequentialAgent(
    name="plinth_pipeline",
    sub_agents=[
        create_intake_agent(),
        create_requirements_agent(),
        create_authoring_loop(),
        create_elicitation_agent(),
        create_user_story_agent(),
        create_package_agent(),
    ],
    before_agent_callback=init_state,
)

# App instance required by the ADK Runner / playground
app = App(
    root_agent=root_agent,
    name="plinth_agent",
    resumability_config=ResumabilityConfig(is_resumable=True),
)
