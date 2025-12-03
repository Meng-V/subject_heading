"""Main FastAPI application for AI Subject Heading Assistant."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from routes import router
from lcsh_index import lcsh_search
from config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup: Connect to Weaviate
    print("🚀 Starting AI Subject Heading Assistant...")
    print(f"📁 Data directory: {settings.data_dir}")
    print(f"🔗 Weaviate URL: {settings.weaviate_url}")
    
    try:
        lcsh_search.connect()
        print("✅ Connected to Weaviate")
    except Exception as e:
        print(f"⚠️  Warning: Could not connect to Weaviate: {str(e)}")
        print("   Make sure Weaviate is running: docker-compose up -d")
    
    yield
    
    # Shutdown: Disconnect from Weaviate
    print("👋 Shutting down...")
    lcsh_search.disconnect()
    print("✅ Disconnected from Weaviate")


# Create FastAPI app
app = FastAPI(
    title="AI Subject Heading Assistant",
    description="""
    AI-powered subject heading assistant for library cataloging.
    
    ## Features
    
    * **OCR**: Extract metadata from book images using OpenAI Vision
    * **Topic Generation**: Generate semantic topics using LLM
    * **LCSH Matching**: Find Library of Congress Subject Headings via vector search
    * **MARC Generation**: Build MARC 650 fields automatically
    * **Data Storage**: Store librarian selections for continual improvement
    
    ## Workflow
    
    1. Upload images (cover, back, TOC) → `/api/ingest-images`
    2. Generate topics → `/api/generate-topics`
    3. Match LCSH headings → `/api/lcsh-match`
    4. Build MARC 650 fields → `/api/marc650`
    5. Submit final selection → `/api/submit-final`
    
    ## Admin Endpoints
    
    * Initialize LCSH schema → `/api/initialize-lcsh`
    * Index sample data → `/api/index-lcsh-sample`
    * Check stats → `/api/lcsh-stats`
    """,
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "AI Subject Heading Assistant API",
        "version": "1.0.0",
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
