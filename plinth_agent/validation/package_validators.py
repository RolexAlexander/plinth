from typing import List, Dict, Any
from ..models.package import RequirementsPackage
from ..models.enums import Status, OpenQuestionStatus

class PackageValidationError(Exception):
    pass

def run_package_validation_checks(pkg: RequirementsPackage) -> Dict[str, Any]:
    results = {
        "primary_ids_unique": True,
        "X1_pass": True,
        "X2_pass": True,
        "X4_pass": True,
        "X5_pass": True,
        "errors": [],
        "warnings": []
    }
    
    # 1. Primary ID uniqueness within their own types
    # Requirements
    seen_req = set()
    for r in pkg.requirements:
        if r.id in seen_req:
            results["primary_ids_unique"] = False
            results["errors"].append(f"X5 Failure: Duplicate Requirement ID '{r.id}' found.")
        seen_req.add(r.id)
        
    # User Stories
    seen_us = set()
    for us in pkg.user_stories:
        if us.id in seen_us:
            results["primary_ids_unique"] = False
            results["errors"].append(f"X5 Failure: Duplicate User Story ID '{us.id}' found.")
        seen_us.add(us.id)
        
    # Open Questions
    seen_oq = set()
    for oq in pkg.open_questions:
        if oq.id in seen_oq:
            results["primary_ids_unique"] = False
            results["errors"].append(f"X5 Failure: Duplicate Open Question ID '{oq.id}' found.")
        seen_oq.add(oq.id)
        
    # Domain Entities
    seen_ent = set()
    for ent in pkg.domain_entities:
        if ent.id in seen_ent:
            results["primary_ids_unique"] = False
            results["errors"].append(f"X5 Failure: Duplicate Domain Entity ID '{ent.id}' found.")
        seen_ent.add(ent.id)
        
    # Personas
    seen_pers = set()
    for pers in pkg.personas:
        if pers.id in seen_pers:
            results["primary_ids_unique"] = False
            results["errors"].append(f"X5 Failure: Duplicate Persona ID '{pers.id}' found.")
        seen_pers.add(pers.id)
        
    # Decisions
    seen_dec = set()
    for dec in pkg.decisions:
        if dec.id in seen_dec:
            results["primary_ids_unique"] = False
            results["errors"].append(f"X5 Failure: Duplicate Decision ID '{dec.id}' found.")
        seen_dec.add(dec.id)
        
    # 2. Check global ID collisions (IDs shared across different record types)
    all_ids = []
    for r in pkg.requirements: all_ids.append((r.id, "Requirement"))
    for us in pkg.user_stories: all_ids.append((us.id, "UserStory"))
    for oq in pkg.open_questions: all_ids.append((oq.id, "OpenQuestion"))
    for ent in pkg.domain_entities: all_ids.append((ent.id, "DomainEntity"))
    for pers in pkg.personas: all_ids.append((pers.id, "Persona"))
    for dec in pkg.decisions: all_ids.append((dec.id, "Decision"))
    
    seen_global = {}
    for item_id, item_type in all_ids:
        if item_id in seen_global:
            results["primary_ids_unique"] = False
            results["errors"].append(
                f"X5 Failure: Global ID collision. ID '{item_id}' is shared by {item_type} and {seen_global[item_id]}."
            )
        seen_global[item_id] = item_type

    # X5: all AcceptanceCriterion.id values are globally unique.
    ac_ids = set()
    for r in pkg.requirements:
        for ac in r.acceptance_criteria:
            if ac.id in ac_ids:
                results["X5_pass"] = False
                results["errors"].append(f"X5 Failure: Duplicate Acceptance Criterion ID '{ac.id}' found in requirement {r.id}.")
            ac_ids.add(ac.id)
    for us in pkg.user_stories:
        for ac in us.acceptance_criteria:
            if ac.id in ac_ids:
                results["X5_pass"] = False
                results["errors"].append(f"X5 Failure: Duplicate Acceptance Criterion ID '{ac.id}' found in user story {us.id}.")
            ac_ids.add(ac.id)

    # X1 & X4: Referential integrity
    req_ids = {r.id for r in pkg.requirements}
    oq_ids = {q.id for q in pkg.open_questions}
    ent_ids = {e.id for e in pkg.domain_entities}
    
    for r in pkg.requirements:
        for dep in r.depends_on:
            if dep not in req_ids:
                results["X1_pass"] = False
                results["errors"].append(f"X1 Failure: Requirement '{r.id}' depends on non-existent requirement '{dep}'.")
        for aff in r.affected_by:
            if aff not in oq_ids:
                results["X1_pass"] = False
                results["errors"].append(f"X1 Failure: Requirement '{r.id}' is affected by non-existent open question '{aff}'.")
                
    for oq in pkg.open_questions:
        for aff in oq.affects:
            if aff not in req_ids:
                results["X4_pass"] = False
                results["errors"].append(f"X4 Failure: Open Question '{oq.id}' affects non-existent requirement '{aff}'.")

    for us in pkg.user_stories:
        for req_ref in us.requirement_ids:
            if req_ref not in req_ids:
                results["X1_pass"] = False
                results["errors"].append(f"X1 Failure: User Story '{us.id}' references non-existent requirement '{req_ref}'.")

    for ent in pkg.domain_entities:
        for rel in ent.relationships:
            if rel.to not in ent_ids:
                results["X1_pass"] = False
                results["errors"].append(f"X1 Failure: Domain Entity '{ent.id}' has relationship to non-existent entity '{rel.to}'.")

    # X2: Orphan check: every confirmed/assumed requirement is referenced by >= 1 user story
    reqs_referenced_by_stories = set()
    for us in pkg.user_stories:
        reqs_referenced_by_stories.update(us.requirement_ids)
        
    for r in pkg.requirements:
        if r.status in (Status.confirmed, Status.assumed):
            if r.id not in reqs_referenced_by_stories:
                results["X2_pass"] = False
                results["warnings"].append(f"X2 Warning: Requirement '{r.id}' ({r.status.value}) is not referenced by any User Story.")

    return results

def validate_package_integrity(pkg: RequirementsPackage, orphan_check: str = "warn") -> List[str]:
    checks = run_package_validation_checks(pkg)
    
    # If there are any primary or referential integrity errors, raise immediately
    if checks["errors"]:
        raise PackageValidationError("\n".join(checks["errors"]))
        
    # If orphan check is set to fail and X2 check failed, raise X2 errors
    if orphan_check == "fail" and not checks["X2_pass"]:
        raise PackageValidationError("\n".join(checks["warnings"]))
        
    return checks["warnings"]
