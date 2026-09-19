"""Script to launch the RECOMAI FastAPI development server."""
import sys
import uvicorn
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "backend"))

if __name__ == "__main__":
    print("==================================================")
    print("Starting RECOMAI - AI Recommendation System")
    print("Host: http://127.0.0.1:8000")
    print("Interactive API Docs: http://127.0.0.1:8000/docs")
    print("==================================================")
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
