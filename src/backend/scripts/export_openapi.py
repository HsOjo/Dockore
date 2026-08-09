#!/usr/bin/env python3
"""Export the FastAPI OpenAPI schema to openapi.json for frontend type generation."""

import json
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.main import app

out_path = backend_dir / "openapi.json"
out_path.write_text(json.dumps(app.openapi(), indent=2) + "\n", encoding="utf-8")
print(f"Exported OpenAPI schema to {out_path}")
