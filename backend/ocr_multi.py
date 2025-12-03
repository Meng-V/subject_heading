"""OCR module with multi-image support and page classification.

Uses OpenAI Responses API with o4-mini model and reasoning_effort="high".
"""
import base64
import json
from typing import List, Tuple
from openai import OpenAI

from config import settings
from models import BookMetadata, PageImage


class MultiImageOCRProcessor:
    """Handles OCR processing for multiple book images using Responses API with o4-mini."""
    
    def __init__(self):
        """Initialize OCR processor with OpenAI client."""
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.ocr_model
        self.reasoning_effort = settings.reasoning_effort
        
    def _encode_image(self, image_bytes: bytes) -> str:
        """Encode image bytes to base64 string."""
        return base64.b64encode(image_bytes).decode('utf-8')
    
    async def classify_and_extract_single_page(
        self,
        image_bytes: bytes,
        page_hint: str = None
    ) -> PageImage:
        """
        Classify a single page and extract its text.
        
        Args:
            image_bytes: Image bytes
            page_hint: Optional client-side hint
            
        Returns:
            PageImage with classification and text
        """
        image_base64 = self._encode_image(image_bytes)
        
        prompt = """You are a library metadata extractor. 
Analyze this page image and:
1. Classify the page type (choose one): front_cover, back_cover, flap, toc, preface, other
2. Extract all readable text from the page

Return ONLY valid JSON in this format:
{
  "page_type": "front_cover",
  "text": "extracted text here..."
}"""
        
        if page_hint:
            prompt += f"\n\nClient hint: This page might be '{page_hint}'"
        
        try:
            # Use Responses API with o4-mini
            response = self.client.responses.create(
                model=self.model,
                input=[
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}",
                            "detail": "high"
                        }
                    }
                ],
                reasoning={"effort": self.reasoning_effort},
                max_output_tokens=2000
            )
            
            content = response.output_text
            
            # Extract JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            page_data = json.loads(content)
            
            return PageImage(
                page_hint=page_hint,
                page_type=page_data.get("page_type", "other"),
                text=page_data.get("text", "")
            )
            
        except Exception as e:
            return PageImage(
                page_hint=page_hint,
                page_type="other",
                text=f"Error extracting: {str(e)}"
            )
    
    async def aggregate_metadata(self, pages: List[PageImage]) -> BookMetadata:
        """
        Aggregate classified pages into unified metadata.
        
        Args:
            pages: List of classified PageImage objects
            
        Returns:
            BookMetadata with aggregated information
        """
        # Group pages by type
        front_cover_pages = [p for p in pages if p.page_type == "front_cover"]
        back_cover_pages = [p for p in pages if p.page_type == "back_cover"]
        flap_pages = [p for p in pages if p.page_type == "flap"]
        toc_pages = [p for p in pages if p.page_type == "toc"]
        preface_pages = [p for p in pages if p.page_type == "preface"]
        
        # Concatenate texts
        front_text = "\n\n".join([p.text for p in front_cover_pages])
        back_text = "\n\n".join([p.text for p in back_cover_pages])
        flap_text = "\n\n".join([p.text for p in flap_pages])
        toc_text = "\n\n".join([p.text for p in toc_pages])
        preface_text = "\n\n".join([p.text for p in preface_pages])
        
        # Aggregate with LLM
        aggregation_prompt = f"""You are a library metadata extractor. 
Aggregate the following book page texts into a single structured metadata object.

FRONT COVER TEXT:
{front_text}

BACK COVER TEXT:
{back_text}

FLAP TEXT:
{flap_text}

TABLE OF CONTENTS:
{toc_text}

PREFACE:
{preface_text}

Extract and return ONLY valid JSON in this format:
{{
  "title": "main book title",
  "author": "author name(s)",
  "publisher": "publisher name",
  "pub_place": "publication place",
  "pub_year": "publication year",
  "summary": "summary from back cover/flap",
  "table_of_contents": ["chapter 1", "chapter 2", ...],
  "preface_snippets": ["preface paragraph 1", "preface paragraph 2", ...]
}}

If any field is not found, use empty string "" for text fields or empty array [] for lists."""

        try:
            # Use Responses API with o4-mini
            response = self.client.responses.create(
                model=self.model,
                input=aggregation_prompt,
                reasoning={"effort": self.reasoning_effort},
                max_output_tokens=3000
            )
            
            content = response.output_text
            
            # Extract JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            metadata_dict = json.loads(content)
            
            # Create BookMetadata with raw_pages
            metadata = BookMetadata(
                **metadata_dict,
                raw_pages=pages
            )
            
            return metadata
            
        except Exception as e:
            # Fallback: basic extraction
            return BookMetadata(
                title="",
                author="",
                publisher="",
                pub_place="",
                pub_year="",
                summary=back_text[:500] if back_text else "",
                table_of_contents=[],
                preface_snippets=[],
                raw_pages=pages
            )
    
    async def process_multiple_images(
        self,
        images: List[Tuple[bytes, str]]
    ) -> BookMetadata:
        """
        Process multiple images with page classification.
        
        Args:
            images: List of (image_bytes, page_hint) tuples
            
        Returns:
            BookMetadata with aggregated information
        """
        # Step 1: Classify and extract each page
        pages = []
        for image_bytes, page_hint in images:
            page = await self.classify_and_extract_single_page(image_bytes, page_hint)
            pages.append(page)
        
        # Step 2: Aggregate into metadata
        metadata = await self.aggregate_metadata(pages)
        
        return metadata


# Global multi-image OCR processor
multi_ocr_processor = MultiImageOCRProcessor()
