import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.api.chat_router import router as chat_router

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Jira Agentic Copilot API",
    version="1.0.0",
    description="Enterprise Multi-Agent SDLC & QA Copilot powered by LangGraph, MCP, and Gemini."
)

# Enable CORS for React Frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins in development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(chat_router)


@app.get("/health")
async def health_check():
    """Health check endpoint for Docker & Cloud deployments."""
    return {
        "status": "healthy",
        "service": "Jira-Agentic-Copilot",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)