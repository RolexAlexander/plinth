import re
from ..models.enums import SourceOrigin, Status, REAL_ORIGINS

class GroundingError(Exception):
    pass

def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip().lower()

def check_confirmed_grounding(excerpt: str, haystack: str) -> bool:
    """
    P02-6: Grounding check for confirmed requirements.
    Normalizes away trailing/embedded ellipses before the substring check.
    For multi-sentence excerpts, splits the excerpt on sentence boundaries (and ellipses)
    and requires each part to be a verbatim substring of the source, appearing in sequence.
    Reject single concatenated string that isn't contiguous.
    """
    if not excerpt or not haystack:
        return False
    # Clean leading/trailing ellipsis
    clean_excerpt = excerpt.strip()
    clean_excerpt = re.sub(r'^(\.\.\.+|…)\s*', '', clean_excerpt)
    clean_excerpt = re.sub(r'\s*(\.\.\.+|…)$', '', clean_excerpt)
    
    # Split on sentence boundaries (. ! ?) followed by whitespace, or ellipses
    parts = re.split(r'\.\s+|\?\s+|\!\s+|\.\.\.+|…', clean_excerpt)
    parts = [p.strip() for p in parts if p.strip()]
    if not parts:
        return False
        
    current_pos = 0
    for part in parts:
        norm_part = _norm(part)
        pos = haystack.find(norm_part, current_pos)
        if pos != -1:
            current_pos = pos + len(norm_part)
        else:
            return False
    return True

def check_verbatim_grounding(needle: str, haystack: str) -> bool:
    """
    Existing verbatim grounding check for non-confirmed requirements/general use.
    """
    if not needle or not haystack:
        return False
        
    # Check if the entire needle exists in the haystack directly
    if needle in haystack:
        return True
        
    # Split the needle by common ellipsis representations
    parts = re.split(r'\.\.\.+|…', needle)
    parts = [p.strip() for p in parts if p.strip()]
    if not parts:
        return False
        
    current_pos = 0
    for part in parts:
        pos = haystack.find(part, current_pos)
        if pos != -1:
            current_pos = pos + len(part)
        else:
            # Fallback: split by punctuation and search for clauses with 3+ words
            subparts = re.split(r'[.,;:?!\-\u2014]+', part)
            subparts = [sp.strip() for sp in subparts if len(sp.strip().split()) >= 3]
            
            if not subparts:
                return False
                
            sub_pos = current_pos
            for sp in subparts:
                sp_pos = haystack.find(sp, sub_pos)
                if sp_pos == -1:
                    return False
                sub_pos = sp_pos + len(sp)
            current_pos = sub_pos
            
    return True

def validate_source_grounding(pkg, registry, *, mode: str = "strict") -> list[str]:
    """
    Validates that every confirmed/assumed/open requirement with a real human origin
    has a source excerpt that exists as a normalized substring of the registered source text.
    
    P02-6: For confirmed requirements, uses check_confirmed_grounding which is stricter and 
    rejects concatenated non-contiguous strings.
    
    P02-7: For personas, applies the verbatim check, and marks status as 'assumed' if 
    inferred rather than stated (e.g. role title not near name in transcript).
    """
    errors = []
    warnings = []
    
    for r in pkg.requirements:
        for s in r.source:
            if s.origin not in REAL_ORIGINS:
                continue
                
            haystack_text = registry.text_for_kind(s.origin)
            haystack = _norm(haystack_text)
            
            if r.status == Status.confirmed:
                # P02-6: Use the strict check_confirmed_grounding
                if not check_confirmed_grounding(s.excerpt, haystack):
                    msg = (
                        f"Requirement '{r.id}' source excerpt not found in any '{s.origin.value}' "
                        f"document (failed confirmed grounding validator). Excerpt: {s.excerpt!r}"
                    )
                    errors.append(msg)
            else:
                needle = _norm(s.excerpt)
                if not check_verbatim_grounding(needle, haystack):
                    msg = (
                        f"Requirement '{r.id}' source excerpt not found in any '{s.origin.value}' "
                        f"document. Excerpt: {s.excerpt!r}"
                    )
                    warnings.append(msg)
                    
    # P02-7: Validate Persona excerpts and role titles
    transcript_text = registry.text_for_kind(SourceOrigin.transcript)
    haystack = _norm(transcript_text)
    
    for p in pkg.personas:
        role_grounded = False
        if p.role_excerpt:
            if check_confirmed_grounding(p.role_excerpt, haystack):
                role_grounded = True
            else:
                warnings.append(
                    f"Persona '{p.id}' role_excerpt not found in transcript: {p.role_excerpt!r}"
                )
                
        # Check if the role title appears near their name in the transcript (within 150 chars)
        name_norm = _norm(p.name)
        role_norm = _norm(p.role)
        name_role_near = False
        if name_norm in haystack and role_norm in haystack:
            name_positions = [m.start() for m in re.finditer(re.escape(name_norm), haystack)]
            for pos in name_positions:
                window = haystack[max(0, pos - 150):min(len(haystack), pos + 150)]
                if role_norm in window:
                    name_role_near = True
                    break
                    
        if not role_grounded or not name_role_near:
            p.status = "assumed"
            warnings.append(
                f"Persona '{p.id}' ({p.name}) role/title '{p.role}' is inferred rather than stated (marked as assumed). "
                f"Role excerpt grounded: {role_grounded}, Role name near persona name: {name_role_near}."
            )
            
        # Validate goals excerpts
        for g_exc in p.goals_excerpts:
            if g_exc:
                if not check_confirmed_grounding(g_exc, haystack):
                    warnings.append(
                        f"Persona '{p.id}' goal excerpt not found in transcript: {g_exc!r}"
                    )
                    
    if errors:
        raise GroundingError("; ".join(errors))
        
    return warnings
