from typing import Dict
from ..models.package import RequirementsPackage

def render_srs(pkg: RequirementsPackage) -> str:
    lines = [
        f"# Software Requirements Specification (SRS) for {pkg.brief.project_name}",
        "",
        "## 1. Project Brief",
        f"**Vision:** {pkg.brief.vision}",
        "",
        "### Project Goals",
        "\n".join(f"- {goal}" for goal in pkg.brief.goals) if pkg.brief.goals else "*None defined*",
        "",
        "### Project Scope",
        "\n".join(f"- {item}" for item in pkg.brief.scope) if pkg.brief.scope else "*None defined*",
        "",
        "### Out of Scope",
        "\n".join(f"- {item}" for item in pkg.brief.out_of_scope) if pkg.brief.out_of_scope else "*None defined*",
        "",
        "### Success Criteria",
        "\n".join(f"- {item}" for item in pkg.brief.success_criteria) if pkg.brief.success_criteria else "*None defined*",
        "",
        "## 2. Requirements Specifications",
        ""
    ]

    # Group requirements by type
    reqs_by_type = {}
    for r in pkg.requirements:
        reqs_by_type.setdefault(r.type.value, []).append(r)

    for req_type, reqs in reqs_by_type.items():
        lines.append(f"### {req_type.replace('_', ' ').title()} Requirements")
        lines.append("")
        for r in reqs:
            lines.append(f"#### {r.id}: {r.statement}")
            if r.rationale:
                lines.append(f"- **Rationale:** {r.rationale}")
            lines.append(f"- **Status:** `{r.status.value}`")
            lines.append(f"- **Priority:** `{r.priority.value}`")
            
            if r.metric:
                lines.append(f"- **Metric:** {r.metric.dimension} - Target: {r.metric.target}" + (f" (Condition: {r.metric.condition})" if r.metric.condition else ""))
                
            if r.source:
                src_lines = []
                for s in r.source:
                    ref_str = f" ({s.ref})" if s.ref else ""
                    excerpt_str = f' - "{s.excerpt}"' if s.excerpt else ""
                    src_lines.append(f"`{s.origin.value}`{ref_str}{excerpt_str}")
                lines.append(f"- **Sources:** " + ", ".join(src_lines))
                
            if r.acceptance_criteria:
                lines.append("- **Acceptance Criteria:**")
                for ac in r.acceptance_criteria:
                    lines.append(f"  - **{ac.id}**:")
                    lines.append(f"    - **Given:** {ac.given}")
                    lines.append(f"    - **When:** {ac.when}")
                    lines.append(f"    - **Then:** {ac.then}")
            
            if r.depends_on:
                lines.append(f"- **Depends On:** " + ", ".join(r.depends_on))
            if r.affected_by:
                lines.append(f"- **Affected By:** " + ", ".join(r.affected_by))
            lines.append("")
            
    return "\n".join(lines)


def render_personas(pkg: RequirementsPackage) -> str:
    lines = [
        "# User Personas",
        "",
    ]
    if not pkg.personas:
        lines.append("*No personas defined.*")
    for p in pkg.personas:
        lines.append(f"## {p.id}: {p.name}")
        lines.append(f"- **Role:** {p.role}")
        lines.append("")
        lines.append("### Goals")
        lines.append("\n".join(f"- {goal}" for goal in p.goals) if p.goals else "*None*")
        lines.append("")
        lines.append("### Pain Points")
        lines.append("\n".join(f"- {pain}" for pain in p.pains) if p.pains else "*None*")
        lines.append("")
        lines.append("### Permissions")
        lines.append("\n".join(f"- {perm}" for perm in p.permissions) if p.permissions else "*None*")
        lines.append("")
    return "\n".join(lines)


def render_user_stories(pkg: RequirementsPackage) -> str:
    lines = [
        "# User Stories",
        "",
    ]
    if not pkg.user_stories:
        lines.append("*No user stories defined.*")
    for s in pkg.user_stories:
        lines.append(f"## {s.id}: {s.epic}")
        lines.append(f"**As a** {s.as_a}")
        lines.append(f"**I want to** {s.i_want}")
        lines.append(f"**So that** {s.so_that}")
        lines.append("")
        lines.append(f"- **Priority:** `{s.priority.value}`")
        if s.requirement_ids:
            lines.append(f"- **Implements Requirements:** " + ", ".join(s.requirement_ids))
        if s.acceptance_criteria:
            lines.append("- **Acceptance Criteria:**")
            for ac in s.acceptance_criteria:
                lines.append(f"  - **{ac.id}**:")
                lines.append(f"    - **Given:** {ac.given}")
                lines.append(f"    - **When:** {ac.when}")
                lines.append(f"    - **Then:** {ac.then}")
        if s.edge_cases:
            lines.append("- **Edge Cases:**")
            lines.append("\n".join(f"  - {ec}" for ec in s.edge_cases))
        lines.append("")
    return "\n".join(lines)


def render_open_questions(pkg: RequirementsPackage) -> str:
    lines = [
        "# Open Questions",
        "",
    ]
    if not pkg.open_questions:
        lines.append("*No open questions.*")
    for q in pkg.open_questions:
        lines.append(f"## {q.id}: {q.question}")
        lines.append(f"- **Status:** `{q.status.value}`")
        lines.append(f"- **Synthetic Origin:** `{q.synthetic_origin.value}`")
        lines.append(f"- **Blocking:** `{q.blocking}`")
        if q.blocking_rationale:
            lines.append(f"- **Blocking Rationale:** {q.blocking_rationale}")
        if q.affects:
            lines.append(f"- **Affects Requirements:** " + ", ".join(q.affects))
        if q.proposed_assumption:
            lines.append(f"- **Proposed Assumption:** {q.proposed_assumption}")
        lines.append(f"- **Default If Deferred:** `{q.default_if_deferred.value}`")
        if q.answer:
            lines.append(f"- **Answer:** {q.answer}")
        lines.append("")
    return "\n".join(lines)


def render_decisions(pkg: RequirementsPackage) -> str:
    lines = [
        "# Design and Scope Decisions",
        "",
    ]
    if not pkg.decisions:
        lines.append("*No decisions recorded.*")
    for d in pkg.decisions:
        lines.append(f"## {d.id}: {d.statement}")
        lines.append(f"- **Rationale:** {d.rationale}")
        if d.related_ids:
            lines.append(f"- **Related Items:** " + ", ".join(d.related_ids))
        lines.append("")
    return "\n".join(lines)


def render_domain_class_diagram(pkg: RequirementsPackage) -> str:
    lines = ["classDiagram"]
    if not pkg.domain_entities:
        return "classDiagram\n  %% No domain entities defined."
        
    for ent in pkg.domain_entities:
        # Keep class names compliant with Mermaid (use underscores instead of hyphens)
        clean_name = ent.id.replace("-", "_")
        lines.append(f"  class {clean_name} {{")
        for attr in ent.attributes:
            type_str = attr.type
            if attr.nullable:
                type_str += " (nullable)"
            lines.append(f"    +{type_str} {attr.name}")
        lines.append("  }")
        
        for rel in ent.relationships:
            from_symbol = "1"
            to_symbol = "1"
            if rel.kind == "one_to_many":
                from_symbol = "1"
                to_symbol = "*"
            elif rel.kind == "many_to_one":
                from_symbol = "*"
                to_symbol = "1"
            elif rel.kind == "many_to_many":
                from_symbol = "*"
                to_symbol = "*"
            
            clean_to = rel.to.replace("-", "_")
            via_label = f" : {rel.via}" if rel.via else ""
            lines.append(f'  {clean_name} "{from_symbol}" --> "{to_symbol}" {clean_to}{via_label}')
            
    return "\n".join(lines)
