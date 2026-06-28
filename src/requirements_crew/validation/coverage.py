import re
from ..models.package import RequirementsPackage

TRANSCRIPT_TOPICS = [
    "qr", "mqtt", "stripe", "loyalty", "spin pass", "idle", 
    "waitlist", "reserv", "refund", "attendant", "2fa", 
    "totp", "wcag", "spanish", "tls", "aes", "rate limit", 
    "retention", "offline", "concurrent", "machine"
]

class CoverageValidationError(Exception):
    pass

def check_requirements_coverage(pkg: RequirementsPackage, transcript: str, candidate_count: int = 0) -> dict:
    """
    Computes coverage statistics of the requirements against the original transcript.
    
    Returns:
        dict: A coverage report:
            {
                "candidate_statements": int,
                "requirements": int,
                "coverage_ratio": float,
                "uncovered_topics": list[str]
            }
    """
    transcript_lower = transcript.lower()
    salient_topics = [t for t in TRANSCRIPT_TOPICS if t in transcript_lower]
    
    # Concatenate all requirement statements and descriptions/rationales
    reqs_text = " ".join(
        f"{r.statement} {r.rationale or ''}".lower() 
        for r in pkg.requirements
    )
    
    covered_topics = [t for t in salient_topics if t in reqs_text]
    uncovered_topics = [t for t in salient_topics if t not in covered_topics]
    
    coverage_ratio = len(covered_topics) / len(salient_topics) if salient_topics else 1.0
    req_count = len(pkg.requirements)
    
    return {
        "candidate_statements": candidate_count,
        "requirements": req_count,
        "coverage_ratio": coverage_ratio,
        "uncovered_topics": uncovered_topics
    }

def validate_coverage(pkg: RequirementsPackage, transcript: str, candidate_count: int = 0) -> None:
    """
    Validates that the requirements package has sufficient coverage of the transcript.
    Fails if coverage_ratio < 0.50 (50% of salient topics found in transcript) OR
    if requirements count is less than 25% of candidate statement count (if candidate_count > 0).
    """
    if not pkg.requirements:
        raise CoverageValidationError("Requirements package is empty.")
        
    report = check_requirements_coverage(pkg, transcript, candidate_count)
    
    # 1. Topic coverage
    if report["coverage_ratio"] < 0.50:
        raise CoverageValidationError(
            f"Coverage Validation Failed: Only {report['coverage_ratio']:.1%} of salient topics are covered. "
            f"Uncovered topics: {report['uncovered_topics']}"
        )
        
    # 2. Volume coverage (candidate statements vs requirements count)
    if candidate_count > 0 and report["requirements"] < (candidate_count * 0.25):
        raise CoverageValidationError(
            f"Coverage Validation Failed: Requirements count ({report['requirements']}) is disproportionately low "
            f"compared to candidate statements extracted ({candidate_count}). Potential information loss."
        )
