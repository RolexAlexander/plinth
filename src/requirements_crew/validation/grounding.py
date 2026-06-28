import re
from ..models.enums import SourceOrigin, Status, REAL_ORIGINS

class GroundingError(Exception):
    pass

def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip().lower()

def validate_source_grounding(pkg, registry, *, mode: str = "strict") -> list[str]:
    """
    Validates that every confirmed/assumed/open requirement with a real human origin
    (transcript, intake, human_answer) has a source excerpt that exists as a normalized
    substring of the registered source text of that origin kind.
    
    Returns:
        list[str]: A list of warning messages (for assumed/open requirements with invalid grounding).
        
    Raises:
        GroundingError: If a confirmed requirement has an excerpt that is not found in the source.
    """
    errors = []
    warnings = []
    
    for r in pkg.requirements:
        for s in r.source:
            if s.origin not in REAL_ORIGINS:
                continue
                
            haystack_text = registry.text_for_kind(s.origin)
            haystack = _norm(haystack_text)
            needle = _norm(s.excerpt)
            
            if not needle or needle not in haystack:
                msg = (
                    f"Requirement '{r.id}' source excerpt not found in any '{s.origin.value}' "
                    f"document. Excerpt: {s.excerpt!r}"
                )
                if r.status == Status.confirmed:
                    errors.append(msg)
                else:
                    warnings.append(msg)
                    
    # Validate Persona excerpts (warn-tier)
    for p in pkg.personas:
        transcript_text = registry.text_for_kind(SourceOrigin.transcript)
        haystack = _norm(transcript_text)
        
        if p.role_excerpt:
            needle = _norm(p.role_excerpt)
            if not needle or needle not in haystack:
                warnings.append(
                    f"Persona '{p.id}' role_excerpt not found in transcript: {p.role_excerpt!r}"
                )
                
        for g_exc in p.goals_excerpts:
            if g_exc:
                needle = _norm(g_exc)
                if not needle or needle not in haystack:
                    warnings.append(
                        f"Persona '{p.id}' goal excerpt not found in transcript: {g_exc!r}"
                    )
                    
    if errors:
        raise GroundingError("; ".join(errors))
        
    return warnings
