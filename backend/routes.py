"""API routes for the Subject Heading Assistant."""
import uuid
import json
from pathlib import Path
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse

from config import settings
from models import (
    IngestImagesResponse,
    GenerateTopicsRequest,
    GenerateTopicsResponse,
    LCSHMatchRequest,
    LCSHMatchResponse,
    MARC650Request,
    MARC650Response,
    SubmitFinalRequest,
    SubmitFinalResponse,
    FinalRecord
)
from ocr import ocr_processor
from llm_topics import topic_generator
from lcsh_index import lcsh_search
from marc_builder import marc_builder


# Create router
router = APIRouter(prefix="/api", tags=["subject-heading"])


@router.post("/ingest-images", response_model=IngestImagesResponse)
async def ingest_images(
    cover: UploadFile = File(..., description="Front cover image"),
    back: UploadFile = File(None, description="Back cover image (optional)"),
    toc: UploadFile = File(None, description="Table of contents image (optional)")
):
    """
    Extract structured metadata from uploaded book images using OCR.
    
    - **cover**: Front cover image (required)
    - **back**: Back cover image (optional)
    - **toc**: Table of contents image (optional)
    """
    try:
        # Read image bytes
        cover_bytes = await cover.read()
        back_bytes = await back.read() if back else None
        toc_bytes = await toc.read() if toc else None
        
        # Process with OCR
        metadata = await ocr_processor.extract_metadata(
            cover_image=cover_bytes,
            back_image=back_bytes,
            toc_image=toc_bytes
        )
        
        return IngestImagesResponse(
            success=True,
            metadata=metadata,
            message="Metadata extracted successfully"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")


@router.post("/generate-topics", response_model=GenerateTopicsResponse)
async def generate_topics(request: GenerateTopicsRequest):
    """
    Generate semantic topic candidates from book metadata using LLM.
    
    - **metadata**: BookMetadata object from OCR
    """
    try:
        topics = await topic_generator.generate_topics(request.metadata)
        
        return GenerateTopicsResponse(
            success=True,
            topics=topics,
            message=f"Generated {len(topics)} topic candidates"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Topic generation failed: {str(e)}")


@router.post("/lcsh-match", response_model=LCSHMatchResponse)
async def lcsh_match(request: LCSHMatchRequest):
    """
    Find LCSH authority heading matches for given topics using vector search.
    
    - **topics**: List of semantic topic strings
    """
    try:
        # Ensure connection to Weaviate
        if not lcsh_search.client:
            lcsh_search.connect()
        
        # Search for matches
        matches = await lcsh_search.search_multiple_topics(
            topics=request.topics,
            limit_per_topic=10,
            certainty=0.7
        )
        
        return LCSHMatchResponse(
            success=True,
            matches=matches,
            message=f"Found matches for {len(matches)} topics"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LCSH matching failed: {str(e)}")


@router.post("/marc650", response_model=MARC650Response)
async def build_marc650(request: MARC650Request):
    """
    Build MARC 650 fields from selected LCSH headings.
    
    - **lcsh_selections**: List of LCSHMatch objects selected by librarian
    """
    try:
        marc_fields = await marc_builder.build_multiple_marc_fields(
            lcsh_matches=request.lcsh_selections,
            validate_with_llm=False  # Can be made configurable
        )
        
        return MARC650Response(
            success=True,
            marc_fields=marc_fields,
            message=f"Generated {len(marc_fields)} MARC 650 fields"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MARC generation failed: {str(e)}")


@router.post("/submit-final", response_model=SubmitFinalResponse)
async def submit_final(request: SubmitFinalRequest):
    """
    Store final librarian selections for continual improvement.
    
    Saves complete record to JSON file for future training/analysis.
    """
    try:
        # Generate UUID
        record_uuid = str(uuid.uuid4())
        
        # Create final record
        record = FinalRecord(
            uuid=record_uuid,
            metadata=request.metadata,
            ai_topics=request.ai_topics,
            lcsh_matches=request.lcsh_matches,
            librarian_selected=request.librarian_selected,
            marc_fields=request.marc_fields
        )
        
        # Save to JSON
        file_path = settings.data_dir / f"{record_uuid}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(record.model_dump(), f, indent=2, ensure_ascii=False)
        
        return SubmitFinalResponse(
            success=True,
            uuid=record_uuid,
            file_path=str(file_path),
            message="Record saved successfully"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save record: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "weaviate_connected": lcsh_search.client is not None
    }


@router.get("/lcsh-stats")
async def lcsh_stats():
    """Get statistics about the LCSH index."""
    try:
        stats = lcsh_search.get_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.post("/initialize-lcsh")
async def initialize_lcsh():
    """Initialize LCSH schema in Weaviate (admin endpoint)."""
    try:
        lcsh_search.connect()
        lcsh_search.initialize_schema()
        return {"success": True, "message": "LCSH schema initialized"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Initialization failed: {str(e)}")


@router.post("/index-lcsh-sample")
async def index_lcsh_sample():
    """
    Index sample LCSH entries for testing (admin endpoint).
    
    This is a sample endpoint. In production, you would parse LCSH data
    from id.loc.gov dumps.
    """
    try:
        # Sample LCSH entries
        sample_entries = [
            {
                "label": "Calligraphy, Chinese",
                "uri": "http://id.loc.gov/authorities/subjects/sh85018909"
            },
            {
                "label": "Calligraphy, Chinese -- Ming-Qing dynasties, 1368-1912",
                "uri": "http://id.loc.gov/authorities/subjects/sh85018910"
            },
            {
                "label": "Art, Chinese",
                "uri": "http://id.loc.gov/authorities/subjects/sh85007461"
            },
            {
                "label": "Painting, Chinese",
                "uri": "http://id.loc.gov/authorities/subjects/sh85096898"
            },
            {
                "label": "Buddhism -- China",
                "uri": "http://id.loc.gov/authorities/subjects/sh85017454"
            },
            {
                "label": "Philosophy, Chinese",
                "uri": "http://id.loc.gov/authorities/subjects/sh85100967"
            },
            {
                "label": "Literature, Chinese",
                "uri": "http://id.loc.gov/authorities/subjects/sh85077519"
            },
            {
                "label": "Landscape painting, Chinese",
                "uri": "http://id.loc.gov/authorities/subjects/sh85074473"
            },
            {
                "label": "Ink painting, Chinese",
                "uri": "http://id.loc.gov/authorities/subjects/sh85066206"
            },
            {
                "label": "Confucianism",
                "uri": "http://id.loc.gov/authorities/subjects/sh85031028"
            }
        ]
        
        lcsh_search.connect()
        lcsh_search.batch_index_lcsh(sample_entries)
        
        return {
            "success": True,
            "message": f"Indexed {len(sample_entries)} sample LCSH entries"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}")
