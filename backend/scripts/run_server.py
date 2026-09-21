import uvicorn
import os
import sys

# Ensure backend root is on PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting AgriGo Python FastAPI Server on port {port}...")
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
