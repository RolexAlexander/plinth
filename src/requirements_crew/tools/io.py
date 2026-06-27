from pathlib import Path

def read_transcript(file_path: str) -> str:
    path = Path(file_path)
    if not path.exists():
        # Try to resolve relative to requirements_crew project root
        sibling_path = Path(__file__).resolve().parents[3] / file_path
        if sibling_path.exists():
            path = sibling_path
        else:
            raise FileNotFoundError(f"Transcript file not found at: {file_path}")
            
    with open(path, "r", encoding="utf-8") as f:
        return f.read()
