from ..models.package import RequirementsPackage
from ..models.enums import RequirementType, Status, OpenQuestionStatus, DefaultIfDeferred, SourceOrigin
from .package_validators import run_package_validation_checks
from .coverage import check_requirements_coverage

def compute_definition_of_ready(pkg: RequirementsPackage, orphan_check: str = "warn") -> dict:
    nfrs = [r for r in pkg.requirements if r.type == RequirementType.non_functional]
    confirmed_functionals = [
        r for r in pkg.requirements 
        if r.type == RequirementType.functional and r.status == Status.confirmed
    ]
    blocking_questions = [
        q for q in pkg.open_questions 
        if q.blocking and (
            q.status == OpenQuestionStatus.open or
            (q.status == OpenQuestionStatus.deferred and q.default_if_deferred in (DefaultIfDeferred.leave_open, DefaultIfDeferred.drop_scope))
        )
    ]
    
    # Check referential integrity and primary uniqueness using the structured checks
    checks = run_package_validation_checks(pkg)
    
    no_dangling_references = (
        checks["X1_pass"] and 
        checks["X4_pass"] and 
        checks["X5_pass"] and 
        checks["primary_ids_unique"]
    )
    no_orphan_requirements_check = checks["X2_pass"]

    # Calculate coverage ratio
    transcript = ""
    if pkg.source_registry:
        transcript = pkg.source_registry.text_for_kind(SourceOrigin.transcript)
    coverage_report = check_requirements_coverage(pkg, transcript, pkg.candidate_statement_count)
    has_satisfactory_coverage = coverage_report["coverage_ratio"] >= 0.50

    return {
        "every_requirement_has_source": all(len(r.source) > 0 for r in pkg.requirements) if pkg.requirements else True,
        "every_nfr_has_metric": all(r.metric is not None for r in nfrs) if nfrs else True,
        "every_confirmed_functional_has_ac": all(len(r.acceptance_criteria) > 0 for r in confirmed_functionals) if confirmed_functionals else True,
        "no_blocking_open_questions": len(blocking_questions) == 0,
        "no_dangling_references": no_dangling_references,
        "no_orphan_requirements": no_orphan_requirements_check,
        "has_user_stories": (len(pkg.requirements) == 0) or (len(pkg.user_stories) > 0),
        "has_confirmed_requirements": any(r.status == Status.confirmed for r in pkg.requirements),
        "has_satisfactory_coverage": has_satisfactory_coverage,
        "has_domain_model": (
            len(pkg.domain_entities) > 0
            if any(r.type == RequirementType.functional and r.status == Status.confirmed
                   for r in pkg.requirements)
            else True
        ),
    }
