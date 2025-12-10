import json
from pathlib import Path
from typing import List, Dict, Any

def flatten_resume_pack(p: Path) -> List[Dict[str, Any]]:
    data = json.loads(p.read_text(encoding="utf-8"))
    blocks = []

    def add(section: str, payload: Any):
        blocks.append({
            "section": section,
            "text": json.dumps(payload, ensure_ascii=False) if not isinstance(payload, str) else payload
        })

    for k, v in data.items():
        if isinstance(v, list):
            for i, item in enumerate(v):
                add(f"{k}[{i}]", item)
        elif isinstance(v, dict):
            add(k, v)
        else:
            add(k, str(v))
    return blocks
