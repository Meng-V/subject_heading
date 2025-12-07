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
    TopicCandidate,
    Subfield
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
        # Use existing connection from global instance
        if not authority_search.client:
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
        
        # Use existing connection from global instance
        if not authority_search.client:
            authority_search.connect()
        authority_search.batch_index_authorities(lcsh_samples, "lcsh")
        authority_search.batch_index_authorities(fast_samples, "fast")
        
        return {
            "success": True,
            "message": f"Indexed {len(lcsh_samples)} LCSH + {len(fast_samples)} FAST sample entries"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}")


@router.post("/enhanced-search")
async def enhanced_search(
    title: str = Form(""),
    author: str = Form(""),
    abstract: str = Form(""),
    toc: str = Form(""),
    keywords: str = Form(""),
    publisher_notes: str = Form(""),
    limit: int = Form(5),
    min_score: float = Form(0.70)
):
    """
    Enhanced subject search with rich book metadata.
    
    Accepts multiple metadata fields to build a rich semantic query.
    Returns MARC 65X fields ready to use.
    
    Args:
        title: Book title
        author: Author name(s)
        abstract: Book summary/abstract
        toc: Table of contents (newline or comma separated)
        keywords: Keywords (comma separated)
        publisher_notes: Publisher description
        limit: Max results per vocabulary
        min_score: Minimum confidence score
    
    Returns:
        JSON with marc_fields and metadata
    """
    try:
        # Parse TOC and keywords
        toc_list = []
        if toc:
            # Split by newlines or commas
            toc_list = [line.strip() for line in toc.replace(',', '\n').split('\n') if line.strip()]
        
        keywords_list = []
        if keywords:
            keywords_list = [kw.strip() for kw in keywords.split(',') if kw.strip()]
        
        # Build rich query
        query_parts = []
        
        if title:
            query_parts.append(f"TITLE: {title}")
            query_parts.append(title)  # Repeat for emphasis
        
        if keywords_list:
            query_parts.append(f"TOPICS: {' | '.join(keywords_list)}")
        
        if abstract:
            abstract_snippet = abstract[:300] + "..." if len(abstract) > 300 else abstract
            query_parts.append(f"ABOUT: {abstract_snippet}")
        
        if toc_list:
            toc_sample = toc_list[:5]
            toc_text = " | ".join(toc_sample)
            query_parts.append(f"CONTENTS: {toc_text}")
        
        if author:
            query_parts.append(f"AUTHOR: {author}")
        
        if publisher_notes:
            notes_snippet = publisher_notes[:200] + "..." if len(publisher_notes) > 200 else publisher_notes
            query_parts.append(f"DESCRIPTION: {notes_snippet}")
        
        rich_query = " | ".join(query_parts)
        
        if not rich_query:
            raise HTTPException(status_code=400, detail="Please provide at least one input field")
        
        # Connect to authority search
        if not authority_search.client:
            authority_search.connect()
        
        # Search authorities
        results = await authority_search.search_authorities(
            topic=rich_query,
            vocabularies=["lcsh", "fast"],
            limit_per_vocab=limit,
            min_score=min_score
        )
        
        # Convert to MARC 65X
        marc_fields = []
        for result in results:
            # Determine MARC tag
            subject_type = getattr(result, 'subject_type', 'topical')
            if subject_type == 'geographic':
                tag = '651'
            elif subject_type == 'genre_form':
                tag = '655'
            else:
                tag = '650'
            
            # Determine second indicator
            vocab = result.vocabulary.lower()
            ind2 = '0' if vocab == 'lcsh' else '7'
            
            # Parse heading into subfields
            heading = result.label
            subfields = []
            
            if '--' in heading:
                parts = heading.split('--')
                subfields.append({"code": "a", "value": parts[0]})
                
                for part in parts[1:]:
                    if any(keyword in part.lower() for keyword in ['century', 'b.c.', 'a.d.']) or ('-' in part and any(char.isdigit() for char in part)):
                        code = 'y'
                    elif part[0].isupper() and not any(keyword in part.lower() for keyword in ['history', 'politics', 'social', 'conditions', 'civilization']):
                        code = 'z'
                    else:
                        code = 'x'
                    subfields.append({"code": code, "value": part})
            else:
                subfields.append({"code": "a", "value": heading})
            
            if result.uri:
                subfields.append({"code": "0", "value": result.uri})
            
            if vocab != 'lcsh':
                subfields.append({"code": "2", "value": vocab})
            
            # Build MARC string
            marc_string = f"{tag} _{ind2}"
            for sf in subfields:
                marc_string += f" ${sf['code']} {sf['value']}"
            marc_string += "."
            
            marc_fields.append({
                "tag": tag,
                "ind1": "_",
                "ind2": ind2,
                "subfields": subfields,
                "vocabulary": vocab,
                "uri": result.uri,
                "score": result.score,
                "label": result.label,
                "marc_string": marc_string
            })
        
        return {
            "success": True,
            "count": len(marc_fields),
            "marc_fields": marc_fields,
            "rich_query": rich_query,
            "input_fields_used": sum([bool(title), bool(author), bool(abstract), bool(toc), bool(keywords), bool(publisher_notes)]),
            "message": f"Found {len(marc_fields)} MARC subject heading(s)"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Enhanced search failed: {str(e)}")
