"""API routes for AI Subject Heading Assistant.

Uses OpenAI o4-mini with Responses API.
MVP Scope: LCSH and FAST vocabularies only.
"""
import uuid
import json
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse

from config import settings
from models import (
    IngestImagesResponse,
    GenerateTopicsRequest,
    GenerateTopicsResponse,
    LCSHMatchRequest,
    LCSHMatchResponse,
    Build65XRequest,
    Build65XResponse,
    SubmitFinalRequest,
    SubmitFinalResponse,
    FinalRecord,
    Subject65X,
    TopicCandidate
)
from ocr_multi import multi_ocr_processor
from llm_topics import topic_generator
from authority_search import authority_search
from marc_65x_builder import marc_65x_builder


# Create router
router = APIRouter(prefix="/api", tags=["subject-heading"])


@router.post("/ingest-images", response_model=IngestImagesResponse)
async def ingest_images(
    images: List[UploadFile] = File(..., description="Multiple book page images"),
    page_hints: Optional[str] = Form(None, description="JSON array of page hints")
):
    """
    Extract structured metadata from multiple uploaded book images with page classification.
    
    - **images**: Multiple image files (cover, back, TOC, preface, flap, etc.)
    - **page_hints**: Optional JSON array of hints like ["front_cover", "back_cover", "toc", ...]
    """
    try:
        # Parse page hints if provided
        hints = []
        if page_hints:
            try:
                hints = json.loads(page_hints)
            except:
                hints = []
        
        # Ensure hints list matches images length
        while len(hints) < len(images):
            hints.append(None)
        
        # Read all images
        image_data = []
        for img, hint in zip(images, hints):
            img_bytes = await img.read()
            image_data.append((img_bytes, hint))
        
        # Process with multi-image OCR
        metadata = await multi_ocr_processor.process_multiple_images(image_data)
        
        return IngestImagesResponse(
            success=True,
            metadata=metadata,
            message=f"Processed {len(images)} images, identified {len(metadata.raw_pages)} pages"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Multi-image OCR failed: {str(e)}")


@router.post("/generate-topics", response_model=GenerateTopicsResponse)
async def generate_topics(request: GenerateTopicsRequest):
    """
    Generate semantic topic candidates with type classification (topical/geographic/genre).
    
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


@router.post("/authority-match", response_model=LCSHMatchResponse)
async def authority_match(request: LCSHMatchRequest):
    """
    Find authority heading matches for LCSH and FAST vocabularies (MVP).
    
    - **topics**: List of semantic topic strings
    
    Note: MVP supports LCSH and FAST only. Other vocabularies (GTT, RERO, SWD, etc.)
    are future extensions.
    """
    try:
        # Ensure connection
        if not authority_search.client:
            authority_search.connect()
        
        # Convert topics to TopicCandidate objects (default to topical)
        topic_candidates = [TopicCandidate(topic=t, type="topical") for t in request.topics]
        
        # Search for matches - MVP: LCSH and FAST only
        matches = await authority_search.search_multiple_topics(
            topics=topic_candidates,
            vocabularies=["lcsh", "fast"],  # MVP vocabularies
            limit_per_vocab=5,
            min_score=0.7
        )
        
        return LCSHMatchResponse(
            success=True,
            matches=matches,
            message=f"Found LCSH/FAST matches for {len(matches)} topics"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authority matching failed: {str(e)}")


@router.post("/authority-match-typed")
async def authority_match_typed(
    topics: List[dict],
    vocabularies: Optional[List[str]] = None
):
    """
    Find authority matches for typed topics (topical/geographic/genre).
    
    MVP: Supports LCSH and FAST vocabularies only.
    
    - **topics**: List of dicts with "topic" and "type" keys
    - **vocabularies**: Optional list (default: ["lcsh", "fast"])
    
    Example:
    ```json
    {
      "topics": [
        {"topic": "Chinese calligraphy", "type": "topical"},
        {"topic": "China", "type": "geographic"},
        {"topic": "Conference papers", "type": "genre"}
      ],
      "vocabularies": ["lcsh", "fast"]
    }
    ```
    """
    try:
        if not authority_search.client:
            authority_search.connect()
        
        topic_candidates = [TopicCandidate(**t) for t in topics]
        
        # MVP: Only allow LCSH and FAST
        if vocabularies is None:
            vocabularies = ["lcsh", "fast"]
        else:
            # Filter to MVP vocabularies only
            vocabularies = [v for v in vocabularies if v in ["lcsh", "fast"]]
            if not vocabularies:
                vocabularies = ["lcsh", "fast"]
        
        matches = await authority_search.search_multiple_topics(
            topics=topic_candidates,
            vocabularies=vocabularies,
            limit_per_vocab=5,
            min_score=0.7
        )
        
        return {
            "success": True,
            "matches": [m.model_dump() for m in matches],
            "message": f"Found LCSH/FAST matches for {len(matches)} topics"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authority matching failed: {str(e)}")


@router.post("/build-65x", response_model=Build65XResponse)
async def build_65x_fields(request: Build65XRequest):
    """
    Build Subject65X objects (650/651/655) from authority candidates.
    
    MVP: Generates LCSH and FAST subject headings only.
    
    Returns:
    ```json
    {
      "success": true,
      "subjects_65x": [
        {
          "tag": "650",
          "ind1": "_",
          "ind2": "0",
          "vocabulary": "lcsh",
          "heading_string": "Calligraphy, Chinese",
          "subfields": [{"code": "a", "value": "Calligraphy, Chinese"}, ...],
          "uri": "http://id.loc.gov/authorities/subjects/sh85018909",
          "authority_id": "sh85018909",
          "source_system": "ai_generated",
          "score": 0.92,
          "explanation": "...",
          "status": "suggested"
        }
      ]
    }
    ```
    """
    try:
        subjects_65x = await marc_65x_builder.build_from_topic_matches(
            topic_matches=request.topics_with_candidates,
            max_per_topic=3,
            generate_explanations=True,
            vocabularies=["lcsh", "fast"]  # MVP vocabularies
        )
        
        return Build65XResponse(
            success=True,
            subjects_65x=subjects_65x,
            message=f"Generated {len(subjects_65x)} Subject65X entries (LCSH/FAST)"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Subject65X generation failed: {str(e)}")


@router.post("/submit-final", response_model=SubmitFinalResponse)
async def submit_final(request: SubmitFinalRequest):
    """
    Store final librarian selections for continual improvement.
    
    Saves complete record to JSON file for future training/analysis.
    The record includes Subject65X entries with LCSH and FAST headings.
    """
    try:
        # Generate UUID
        record_uuid = str(uuid.uuid4())
        
        # Create final record with Subject65X
        record = FinalRecord(
            uuid=record_uuid,
            metadata=request.metadata,
            ai_topics=request.ai_topics,
            lcsh_matches=request.lcsh_matches,
            subjects_65x=request.subjects_65x or [],
            # Legacy fields
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
        "authority_search_connected": authority_search.client is not None
    }


@router.get("/authority-stats")
async def authority_stats():
    """Get statistics about all authority indexes."""
    try:
        stats = authority_search.get_stats()
        return {"success": True, "stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.post("/initialize-authorities")
async def initialize_authorities():
    """Initialize authority schemas in Weaviate (admin endpoint)."""
    try:
        authority_search.connect()
        authority_search.initialize_schemas()
        return {"success": True, "message": "Authority schemas initialized"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Initialization failed: {str(e)}")


@router.post("/index-sample-authorities")
async def index_sample_authorities():
    """
    Index sample authority entries for testing (admin endpoint).
    """
    try:
        # Sample LCSH entries
        lcsh_samples = [
            {"label": "Calligraphy, Chinese", "uri": "http://id.loc.gov/authorities/subjects/sh85018909"},
            {"label": "Calligraphy, Chinese -- Ming-Qing dynasties, 1368-1912", "uri": "http://id.loc.gov/authorities/subjects/sh85018910"},
            {"label": "Art, Chinese", "uri": "http://id.loc.gov/authorities/subjects/sh85007461"},
            {"label": "China -- Civilization", "uri": "http://id.loc.gov/authorities/subjects/sh85024024"},
            {"label": "China -- History", "uri": "http://id.loc.gov/authorities/subjects/sh85024089"},
        ]
        
        # Sample FAST entries
        fast_samples = [
            {"label": "Calligraphy, Chinese", "uri": "(OCoLC)fst00844437"},
            {"label": "Art, Chinese", "uri": "(OCoLC)fst00815630"},
            {"label": "China", "uri": "(OCoLC)fst01206073"},
        ]
        
        authority_search.connect()
        authority_search.batch_index_authorities(lcsh_samples, "lcsh")
        authority_search.batch_index_authorities(fast_samples, "fast")
        
        return {
            "success": True,
            "message": f"Indexed {len(lcsh_samples)} LCSH + {len(fast_samples)} FAST sample entries"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}")
