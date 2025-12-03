"""Main FastAPI application with v2 multi-image and 65X support."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from routes import router as routes_v1
from routes_v2 import router as routes_v2
from authority_search import authority_search
from lcsh_index import lcsh_search
from config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup
    print("🚀 Starting AI Subject Heading Assistant (V2 with 65X support)...")
    print(f"📁 Data directory: {settings.data_dir}")
    print(f"🔗 Weaviate URL: {settings.weaviate_url}")
    
    try:
        authority_search.connect()
        print("✅ Connected to Weaviate (multi-vocabulary support)")
    except Exception as e:
        print(f"⚠️  Warning: Could not connect to Weaviate: {str(e)}")
        print("   Make sure Weaviate is running: docker-compose up -d")
    
    # Also try legacy connection for backward compatibility
    try:
        lcsh_search.connect()
        print("✅ Legacy LCSH connection available")
    except:
        pass
    
    yield
    
    # Shutdown
    print("👋 Shutting down...")
    authority_search.disconnect()
    lcsh_search.disconnect()
    print("✅ Disconnected from Weaviate")


# Create FastAPI app
app = FastAPI(
    title="AI Subject Heading Assistant V2",
    description="""
    AI-powered subject heading assistant for library cataloging with multi-image support and 65X family.
    
    ## ✨ New Features in V2
    
    * **Multi-Image Input**: Upload multiple page images (cover, back, TOC, preface, flaps)
    * **Page Classification**: Automatic detection of page types
    * **Topic Types**: Classify topics as topical, geographic, or genre
    * **Multi-Vocabulary**: Support LCSH, FAST, GTT, RERO, SWD, and more
    * **Full 65X Family**: Generate 650 (topical), 651 (geographic), 655 (genre/form) fields
    * **Vocabulary-Aware**: Proper indicators and $2 subfields for each vocabulary
    
    ## 📚 API Endpoints
    
    ### V2 Workflow (Recommended)
    
    1. Upload multiple images → `/api/ingest-images` (multi-image with hints)
    2. Generate typed topics → `/api/generate-topics` (with topical/geographic/genre)
    3. Match authorities → `/api/authority-match-typed` (multi-vocabulary)
    4. Build 65X fields → `/api/build-65x` (full 65X family)
    5. Submit final → `/api/submit-final`
    
    ### V1 Endpoints (Legacy)
    
    Still available for backward compatibility.
    
    ### Admin Endpoints
    
    * Initialize schemas → `/api/initialize-authorities`
    * Index sample data → `/api/index-sample-authorities`
    * Check stats → `/api/authority-stats`
    """,
    version="2.0.0",
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

# Include both V1 and V2 routes
app.include_router(routes_v1, prefix="", tags=["v1-legacy"])
app.include_router(routes_v2, prefix="/v2", tags=["v2-enhanced"])


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "AI Subject Heading Assistant API V2",
        "version": "2.0.0",
        "features": [
            "Multi-image OCR with page classification",
            "Topic type classification (topical/geographic/genre)",
            "Multi-vocabulary authority search (LCSH/FAST/GTT/RERO/SWD)",
            "Full 65X MARC family (650/651/655)",
            "Automatic indicator and $2 subfield assignment"
        ],
        "docs": "/docs",
        "v1_endpoints": "/api",
        "v2_endpoints": "/v2/api",
        "health": "/api/health"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main_v2:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
