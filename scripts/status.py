import json
from pathlib import Path
p = Path(__file__).resolve().parents[1] / 'PUBLIC_RELEASE_MANIFEST.json'
print(json.dumps(json.loads(p.read_text()), indent=2))
