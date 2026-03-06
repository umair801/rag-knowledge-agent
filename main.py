"""
RAG Knowledge Base Agent -- Entry Point
Railway dynamically assigns PORT via environment variable.
"""
import os
from app.api.app import app

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)