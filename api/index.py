import os
import sys
import traceback
from pathlib import Path

# Mark serverless environment
os.environ.setdefault("VERCEL", "1")

# Locate backend/src across various deployment root structures
current_file = Path(__file__).resolve()
cwd = Path(os.getcwd())

candidate_paths = [
    current_file.parent.parent / "compliance-ai" / "backend" / "src",
    current_file.parent / "compliance-ai" / "backend" / "src",
    current_file.parent.parent / "backend" / "src",
    current_file.parent / "backend" / "src",
    cwd / "compliance-ai" / "backend" / "src",
    cwd / "backend" / "src",
    Path("/var/task/compliance-ai/backend/src"),
    Path("/var/task/backend/src"),
]

for p in candidate_paths:
    if p.is_dir() and (p / "main.py").is_file():
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))
        break

# Vercel requires `app` to be declared at the top level of the module.
# We create a placeholder first, then replace it with the real FastAPI app.
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="LegalLens AI")

try:
    # Import the real FastAPI app from the backend
    from main import app as _real_app  # noqa: E402
    app = _real_app
except Exception as _exc:
    # Diagnostic fallback: surfaces the exact error instead of a generic 500
    _err_trace = traceback.format_exc()

    @app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
    async def diagnostic_handler(full_path: str):
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "LegalLens backend failed to initialize on Vercel.",
                "error_type": type(_exc).__name__,
                "error_message": str(_exc),
                "traceback": _err_trace.splitlines(),
                "python_path": sys.path,
                "cwd": os.getcwd(),
            },
        )
