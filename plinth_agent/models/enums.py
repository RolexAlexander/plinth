from enum import Enum

class RequirementType(str, Enum):
    functional = "functional"
    non_functional = "non_functional"
    business_rule = "business_rule"
    constraint = "constraint"

class Status(str, Enum):            # provenance tier
    confirmed = "confirmed"
    assumed = "assumed"
    open = "open"
    deprecated = "deprecated"

class Priority(str, Enum):           # MoSCoW
    must = "must"
    should = "should"
    could = "could"
    wont = "wont"

class SourceOrigin(str, Enum):
    # REAL (can support `confirmed`)
    transcript = "transcript"
    intake = "intake"
    human_answer = "human_answer"
    # SYNTHETIC (can only support `assumed`/`open`)
    analyst_inference = "analyst_inference"
    research = "research"
    client_proxy = "client_proxy"
    reviewer = "reviewer"

REAL_ORIGINS = {SourceOrigin.transcript, SourceOrigin.intake, SourceOrigin.human_answer}

class OpenQuestionStatus(str, Enum):
    open = "open"
    answered = "answered"
    deferred = "deferred"
    wont_resolve = "wont_resolve"

class DefaultIfDeferred(str, Enum):
    adopt_assumption = "adopt_assumption"
    leave_open = "leave_open"
    drop_scope = "drop_scope"
