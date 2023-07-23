"""
Entrypoint to the application
"""
import uvicorn

from .tools import setup_logging

if __name__ == "__main__":
    setup_logging()
    uvicorn.run(
        "llama.api.app:create_app",
        workers=1,
        reload=True,
        host="0.0.0.0",
        factory=True,
        port=8000,
    )
