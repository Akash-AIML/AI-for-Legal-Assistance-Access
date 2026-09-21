import sys
from pathlib import Path

# Add src to python path for Vercel Serverless runtime
backend_dir = Path(__file__).resolve().parent.parent
src_dir = backend_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from main import app
