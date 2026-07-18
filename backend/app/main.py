import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings

app = FastAPI(
    title="Agentic Workspace System of Action API",
    version="1.0.0",
    description="Orchestration gateway mediating between Next.js frontend, SQLite client vaults, and local vector indices."
)

# Enable CORS for the frontend development server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {
        "status": "healthy",
        "service": "Agentic Workspace API Core",
        "environment": settings.env
    }

if __name__ == "__main__":
    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=(settings.env == "development")
    )
