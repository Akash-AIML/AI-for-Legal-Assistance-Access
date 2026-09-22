import os
import sys
import tempfile
import traceback
from pathlib import Path

# Mark serverless environment
os.environ.setdefault("VERCEL", "1")

# Locate backend/src across various deployment root structures
current_file = Path(__file__).resolve()
candidate_paths = [
    current_file.parent.parent / "compliance-ai" / "backend" / "src",
    current_file.parent / "compliance-ai" / "backend" / "src",
    current_file.parent.parent / "backend" / "src",
    current_file.parent / "backend" / "src",
    Path("/var/task/compliance-ai/backend/src"),
    Path("/var/task/backend/src"),
]

for p in candidate_paths:
    if p.is_dir() and (p / "main.py").is_file():
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))
        break

try:
    from main import app
except Exception as exc:
    # Diagnostic fallback app to prevent FUNCTION_INVOCATION_FAILED and surface the exact issue
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse

    app = FastAPI(title="LegalLens Deployment Diagnostic")
    err_trace = traceback.format_exc()

    @app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
    async def diagnostic_handler(full_path: str):
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "LegalLens backend failed to initialize on Vercel.",
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "traceback": err_trace.splitlines(),
                "python_path": sys.path,
                "cwd": os.getcwd(),
            },
        )
