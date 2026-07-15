import json
from pathlib import Path
from typing import Union, Any
from ..models.package import RequirementsPackage
from ..validation.package_validators import validate_package_integrity
from .render import (
    render_srs,
    render_personas,
    render_user_stories,
    render_open_questions,
    render_decisions,
    render_domain_class_diagram,
)
from .traceability import build_traceability_matrix, render_traceability_markdown
from .manifest import generate_handoff_manifest

def write_package_to_disk(pkg: RequirementsPackage, output_dir: Union[str, Path], orphan_check: str = "warn") -> None:
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    
    uml_path = out_path / "uml"
    uml_path.mkdir(parents=True, exist_ok=True)
    
    # 1. Run package-level validations (X1, X2, X4, X5). Will raise PackageValidationError on hard fail.
    # Note: X3 Readiness is evaluated dynamically inside generate_handoff_manifest and doesn't raise exception, 
    # but populates ready_for = [] if checks don't pass.
    validate_package_integrity(pkg, orphan_check=orphan_check)
    
    # 2. Render human-readable views
    srs_md = render_srs(pkg)
    personas_md = render_personas(pkg)
    stories_md = render_user_stories(pkg)
    questions_md = render_open_questions(pkg)
    decisions_md = render_decisions(pkg)
    domain_mermaid = render_domain_class_diagram(pkg)
    
    # Traceability Matrix
    trace_matrix = build_traceability_matrix(pkg)
    trace_md = render_traceability_markdown(trace_matrix)
    
    # Manifest
    manifest_dict = generate_handoff_manifest(pkg, orphan_check=orphan_check)
    
    # 3. Write human-readable files
    with open(out_path / "srs.md", "w", encoding="utf-8") as f:
        f.write(srs_md)
    with open(out_path / "personas.md", "w", encoding="utf-8") as f:
        f.write(personas_md)
    with open(out_path / "user_stories.md", "w", encoding="utf-8") as f:
        f.write(stories_md)
    with open(out_path / "open_questions.md", "w", encoding="utf-8") as f:
        f.write(questions_md)
    with open(out_path / "decisions.md", "w", encoding="utf-8") as f:
        f.write(decisions_md)
    with open(uml_path / "domain_class.mermaid", "w", encoding="utf-8") as f:
        f.write(domain_mermaid)
    with open(out_path / "traceability.md", "w", encoding="utf-8") as f:
        f.write(trace_md)
        
    # 4. Write machine-readable JSON files
    def write_json(filename: str, obj: Any) -> None:
        with open(out_path / filename, "w", encoding="utf-8") as f:
            json.dump(obj, f, indent=2, default=str)
            
    # Serialize Pydantic objects using model_dump
    write_json("requirements.json", [r.model_dump(mode="json") for r in pkg.requirements])
    write_json("domain_model.json", [e.model_dump(mode="json") for e in pkg.domain_entities])
    write_json("user_stories.json", [s.model_dump(mode="json") for s in pkg.user_stories])
    write_json("personas.json", [p.model_dump(mode="json") for p in pkg.personas])
    write_json("open_questions.json", [q.model_dump(mode="json") for q in pkg.open_questions])
    write_json("decisions.json", [d.model_dump(mode="json") for d in pkg.decisions])
    write_json("traceability.json", trace_matrix)
    write_json("handoff_manifest.json", manifest_dict)
