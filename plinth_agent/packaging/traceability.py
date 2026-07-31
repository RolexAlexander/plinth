import json
from typing import Dict, List, Any
from ..models.package import RequirementsPackage

def build_traceability_matrix(pkg: RequirementsPackage) -> Dict[str, Any]:
    matrix = {}
    
    # Pre-collect relations
    us_by_req = {}
    for us in pkg.user_stories:
        for r_id in us.requirement_ids:
            us_by_req.setdefault(r_id, []).append(us.id)
            
    oq_by_req = {}
    for oq in pkg.open_questions:
        # Check both oq.affects and requirement's affected_by
        for r_id in oq.affects:
            oq_by_req.setdefault(r_id, set()).add(oq.id)
            
    for req in pkg.requirements:
        for oq_id in req.affected_by:
            oq_by_req.setdefault(req.id, set()).add(oq_id)

    # Heuristic for domain entities: check if entity name is mentioned in requirement or user stories
    for req in pkg.requirements:
        req_text = (req.statement + " " + (req.rationale or "")).lower()
        associated_stories = us_by_req.get(req.id, [])
        story_text = ""
        for us_id in associated_stories:
            us = next((s for s in pkg.user_stories if s.id == us_id), None)
            if us:
                story_text += f" {us.epic} {us.as_a} {us.i_want} {us.so_that}"
        combined_text = (req_text + " " + story_text).lower()

        matched_entities = []
        for ent in pkg.domain_entities:
            # Match by entity name (e.g. "User") or entity ID (e.g. "ENT-User")
            ent_name_lower = ent.name.lower()
            ent_id_lower = ent.id.lower()
            if ent_name_lower in combined_text or ent_id_lower in combined_text:
                matched_entities.append(ent.id)

        matrix[req.id] = {
            "statement": req.statement,
            "user_stories": associated_stories,
            "entities": matched_entities,
            "open_questions": sorted(list(oq_by_req.get(req.id, [])))
        }
        
    return matrix

def render_traceability_markdown(matrix: Dict[str, Any]) -> str:
    lines = [
        "# Traceability Matrix",
        "",
        "| Requirement ID | Statement | User Stories | Entities | Open Questions |",
        "| --- | --- | --- | --- | --- |"
    ]
    
    for req_id, data in sorted(matrix.items()):
        us_str = ", ".join(data["user_stories"]) if data["user_stories"] else "-"
        ent_str = ", ".join(data["entities"]) if data["entities"] else "-"
        oq_str = ", ".join(data["open_questions"]) if data["open_questions"] else "-"
        
        # Escape pipe symbols in statement if any
        stmt = data["statement"].replace("|", "\\|")
        lines.append(f"| {req_id} | {stmt} | {us_str} | {ent_str} | {oq_str} |")
        
    return "\n".join(lines)
