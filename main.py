"""AI Subject Heading Assistant - FastAPI Application.

Uses OpenAI o4-mini with Responses API for all LLM tasks.
Supports multi-image OCR, LCSH/FAST authority search, and MARC 65X generation.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from routes import router
from authority_search import authority_search
from config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    print("🚀 Starting AI Subject Heading Assistant...")
    print(f"📁 Data directory: {settings.data_dir}")
    print(f"🔗 Weaviate URL: {settings.weaviate_url}")
    print(f"🤖 Model: {settings.default_model} (reasoning_effort={settings.reasoning_effort})")
    
    try:
        authority_search.connect()
        print("✅ Connected to Weaviate (LCSH + FAST)")
    except Exception as e:
        print(f"⚠️  Warning: Could not connect to Weaviate: {str(e)}")
        print("   Make sure Weaviate is running: docker-compose up -d")
    
    yield
    
    # Shutdown
    print("👋 Shutting down...")
    authority_search.disconnect()
    print("✅ Disconnected from Weaviate")


# Create FastAPI app
app = FastAPI(
    title="AI Subject Heading Assistant",
    description="""
AI-powered subject heading assistant for library cataloging.

## 🤖 Technology
- **Model**: OpenAI o4-mini with Responses API
- **Quality**: reasoning_effort="high" for best results
- **Vocabularies**: LCSH and FAST (MVP scope)

## 📚 Workflow

1. **Upload images** → `/api/ingest-images`
2. **Generate topics** → `/api/generate-topics`
3. **Match authorities** → `/api/authority-match`
4. **Build 65X fields** → `/api/build-65x`
5. **Submit final** → `/api/submit-final`

## 🔧 Admin Endpoints

- Initialize schemas → `/api/initialize-authorities`
- Index sample data → `/api/index-sample-authorities`
- Check stats → `/api/authority-stats`
    """,
    version="2.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "AI Subject Heading Assistant",
        "version": "2.0.0",
        "model": settings.default_model,
        "reasoning_effort": settings.reasoning_effort,
        "vocabularies": ["lcsh", "fast"],
        "docs": "/docs",
        "health": "/api/health"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
