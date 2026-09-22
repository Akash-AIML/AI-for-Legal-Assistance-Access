import os
import sys
import traceback
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# Mark serverless environment
os.environ.setdefault("VERCEL", "1")

# Robust backend discovery
current_file = Path(__file__).resolve()
cwd = Path(os.getcwd())

def find_backend_src() -> Path | None:
    candidate_paths = [
        current_file.parent.parent / "backend" / "src",
        current_file.parent.parent / "compliance-ai" / "backend" / "src",
        current_file.parent / "backend" / "src",
        current_file.parent / "compliance-ai" / "backend" / "src",
        cwd / "backend" / "src",
        cwd / "compliance-ai" / "backend" / "src",
        Path("/var/task/backend/src"),
        Path("/var/task/compliance-ai/backend/src"),
    ]
    for p in candidate_paths:
        if p.is_dir() and (p / "main.py").is_file():
            return p
    # Recursive upward search
    for start in [current_file.parent, cwd]:
        cur = start
        for _ in range(5):
            for sub in [cur / "backend" / "src", cur / "compliance-ai" / "backend" / "src", cur / "src"]:
                if sub.is_dir() and (sub / "main.py").is_file():
                    return sub
            cur = cur.parent
    return None

backend_path = find_backend_src()
if backend_path:
    if str(backend_path) not in sys.path:
        sys.path.insert(0, str(backend_path))

# Vercel requires top-level `app` declaration for static analysis
app = FastAPI(title="LegalLens AI")

_init_error = None
_init_trace = None

try:
    if not backend_path:
        raise FileNotFoundError(
            f"Could not find backend/src/main.py. Current file: {current_file}, cwd: {cwd}, "
            f"cwd contents: {os.listdir(cwd) if cwd.exists() else 'N/A'}"
        )
    # Import the real FastAPI app from backend
    from main import app as _real_app  # noqa: E402
    app = _real_app
except Exception as _exc:
    _init_error = _exc
    _init_trace = traceback.format_exc()

    @app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
    async def diagnostic_handler(request: Request, full_path: str = ""):
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "LegalLens backend failed to initialize on Vercel.",
                "error_type": type(_init_error).__name__,
                "error_message": str(_init_error),
                "traceback": _init_trace.splitlines() if _init_trace else [],
                "python_path": [str(x) for x in sys.path],
                "cwd": str(os.getcwd()),
                "backend_path": str(backend_path),
            },
        )
