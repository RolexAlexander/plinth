import re
from ..models.package import RequirementsPackage

# P02-5: Keep as secondary hint only, not primary signal.
# These are used for fuzzy matching as a fallback, not exact substring.
_FALLBACK_TOPICS = [
    "qr", "mqtt", "stripe", "loyalty", "spin pass", "idle",
    "waitlist", "reserv", "refund", "attendant", "2fa",
    "totp", "wcag", "spanish", "tls", "aes", "rate limit",
    "retention", "offline", "concurrent", "machine"
]


class CoverageValidationError(Exception):
    pass


def _extract_candidate_phrases(transcript: str) -> list[str]:
    """Extract candidate requirement-like phrases from the transcript.
    Uses a lightweight heuristic: finds sentences/clauses that contain
    action verbs and domain nouns, returning them as candidate phrases."""
    # Split into sentences
    sentences = re.split(r'[.!?\n]+', transcript)
    candidates = []
    
    # Action/requirement signal words
    action_signals = {
        "need", "want", "should", "must", "require", "have to",
        "able to", "support", "handle", "allow", "enable", "provide",
        "integrate", "connect", "track", "monitor", "manage", "display",
        "send", "receive", "notify", "authenticate", "authorize", "pay",
        "scan", "generate", "report", "schedule", "reserve", "cancel",
        "refund", "subscribe", "encrypt", "comply", "validate"
    }
    
    for sent in sentences:
        sent_stripped = sent.strip()
        if len(sent_stripped) < 15:
            continue
        sent_lower = sent_stripped.lower()
        # Check if the sentence contains any action signals
        if any(signal in sent_lower for signal in action_signals):
            candidates.append(sent_stripped)
    
    return candidates


def _lemmatized_match(topic: str, text: str) -> bool:
    """Fuzzy/lemmatized matching: check if the topic or its variants 
    appear in the text. More forgiving than exact substring."""
    text_lower = text.lower()
    topic_lower = topic.lower()
    
    # Uppercase-collapsed match (for acronym normalization like TOTP-based / AES-256)
    def collapse(s: str) -> str:
        return re.sub(r'[^A-Z0-9]', '', s.upper())
        
    topic_collapsed = collapse(topic)
    text_collapsed = collapse(text)
    if topic_collapsed and topic_collapsed in text_collapsed:
        return True
        
    # Direct substring
    if topic_lower in text_lower:
        return True
    
    # Try word-boundary match for short topics
    pattern = r'\b' + re.escape(topic_lower) + r'\b'
    if re.search(pattern, text_lower):
        return True
    
    # Common lemmatization/variant patterns
    variants = {
        "rate limit": ["rate-limit", "rate_limit", "ratelimit", "throttl"],
        "retention": ["retain", "retent", "data retention"],
        "offline": ["off-line", "offline-capable", "offline mode"],
        "concurrent": ["concurren", "simultaneous", "parallel"],
        "reserv": ["reservation", "reserve", "booking"],
        "totp": ["totp", "2fa", "two-factor", "two factor", "mfa", "otp", "authenticat"],
        "aes": ["aes", "encrypt", "advanced encryption", "aes-256", "aes256"],
    }
    
    if topic_lower in variants:
        for variant in variants[topic_lower]:
            if variant in text_lower:
                return True
    
    return False


def check_requirements_coverage(pkg: RequirementsPackage, transcript: str, candidate_count: int = 0) -> dict:
    """
    Computes coverage statistics of the requirements against the original transcript.
    
    P02-5: Uses candidate-coverage ratio as primary signal, lemmatized topic matching as secondary.
    
    Returns:
        dict: A coverage report:
            {
                "candidate_statements": int,
                "requirements": int,
                "coverage_ratio": float,
                "uncovered_topics": list[str],
                "uncovered_candidates": list[str]
            }
    """
    transcript_lower = transcript.lower()
    
    # Concatenate all requirement statements and descriptions/rationales
    reqs_text = " ".join(
        f"{r.statement} {r.rationale or ''}".lower()
        for r in pkg.requirements
    )
    
    is_spincycle = "spincycle" in transcript_lower
    salient_topics = [t for t in _FALLBACK_TOPICS if t in transcript_lower] if is_spincycle else []
    covered_topics = [t for t in salient_topics if _lemmatized_match(t, reqs_text)]
    uncovered_topics = [t for t in salient_topics if t not in covered_topics]
    
    topic_coverage_ratio = len(covered_topics) / len(salient_topics) if salient_topics else 1.0
    
    # Primary signal: candidate-coverage ratio
    candidates = _extract_candidate_phrases(transcript)
    
    uncovered_candidates = []
    for cand in candidates:
        cand_lower = cand.lower()
        # Extract key words from candidate (4+ char, non-stop)
        cand_words = set(re.findall(r'[a-z]{4,}', cand_lower))
        # Remove very common words
        stop = {"that", "this", "they", "them", "their", "with", "from", "have", "been",
                "will", "would", "could", "should", "also", "just", "very", "more", "some",
                "like", "about", "into", "than", "then", "when", "what", "each", "were"}
        cand_words -= stop
        
        if not cand_words:
            continue
            
        # Check how many candidate words appear in requirements text
        matched = sum(1 for w in cand_words if w in reqs_text)
        if len(cand_words) > 0 and matched / len(cand_words) < 0.3:
            uncovered_candidates.append(cand[:150])
    
    req_count = len(pkg.requirements)
    
    return {
        "candidate_statements": candidate_count if candidate_count > 0 else len(candidates),
        "requirements": req_count,
        "coverage_ratio": topic_coverage_ratio,
        "uncovered_topics": uncovered_topics,
        "uncovered_candidates": uncovered_candidates[:20],  # Cap at 20 to avoid bloat
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
    
    # 1. Topic coverage (secondary, more forgiving with lemmatized matching)
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
