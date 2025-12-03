"""OCR module using OpenAI Responses API with o4-mini for extracting book metadata from images.

Uses the Responses API with reasoning_effort="high" for better quality output.
"""
import base64
import json
from typing import List
from io import BytesIO
from openai import OpenAI

from config import settings
from models import BookMetadata


class OCRProcessor:
    """Handles OCR processing using OpenAI Responses API with o4-mini."""
    
    def __init__(self):
        """Initialize OCR processor with OpenAI client."""
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.ocr_model
        self.reasoning_effort = settings.reasoning_effort
        
    def _encode_image(self, image_bytes: bytes) -> str:
        """Encode image bytes to base64 string."""
        return base64.b64encode(image_bytes).decode('utf-8')
    
    def _create_vision_message(self, image_base64: str, image_type: str = "cover") -> dict:
        """Create a vision API message with image."""
        return {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{image_base64}",
                "detail": "high"
            }
        }
    
    async def extract_metadata(
        self,
        cover_image: bytes,
        back_image: bytes = None,
        toc_image: bytes = None
    ) -> BookMetadata:
        """
        Extract structured metadata from book images using OpenAI Vision.
        
        Args:
            cover_image: Front cover image bytes
            back_image: Back cover image bytes (optional)
            toc_image: Table of contents image bytes (optional)
            
        Returns:
            BookMetadata object with extracted information
        """
        # Encode images
        messages_content = [
            {
                "type": "text",
                "text": """You are a structured data extractor for library cataloging. 
Analyze the provided book images and extract the following information:
- title: The main title of the book
- author: Author name(s)
- publisher: Publisher name
- pub_place: Place of publication
- pub_year: Year of publication
- summary: Summary or description text (usually on back cover)
- toc: Table of contents as an array of chapter/section titles

Return ONLY valid JSON in this exact format:
{
  "title": "...",
  "author": "...",
  "publisher": "...",
  "pub_place": "...",
  "pub_year": "...",
  "summary": "...",
  "toc": ["...", "..."]
}

If any field is not visible or available, use an empty string "" for text fields or empty array [] for toc.
"""
            }
        ]
        
        # Add cover image
        cover_base64 = self._encode_image(cover_image)
        messages_content.append(self._create_vision_message(cover_base64, "cover"))
        
        # Add back cover if provided
        if back_image:
            back_base64 = self._encode_image(back_image)
            messages_content.append(self._create_vision_message(back_base64, "back"))
        
        # Add TOC if provided
        if toc_image:
            toc_base64 = self._encode_image(toc_image)
            messages_content.append(self._create_vision_message(toc_base64, "toc"))
        
        try:
            # Call OpenAI Responses API with o4-mini
            response = self.client.responses.create(
                model=self.model,
                input=messages_content,
                reasoning={"effort": self.reasoning_effort},
                max_output_tokens=2000
            )
            
            # Parse response from Responses API
            content = response.output_text
            
            # Extract JSON from response (handle markdown code blocks)
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            # Parse JSON and create BookMetadata
            metadata_dict = json.loads(content)
            metadata = BookMetadata(**metadata_dict)
            
            return metadata
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse OCR response as JSON: {str(e)}\nContent: {content}")
        except Exception as e:
            raise Exception(f"OCR processing failed: {str(e)}")
    
    async def process_image_files(
        self,
        cover_path: str = None,
        back_path: str = None,
        toc_path: str = None
    ) -> BookMetadata:
        """
        Process image files from disk.
        
        Args:
            cover_path: Path to cover image
            back_path: Path to back cover image
            toc_path: Path to TOC image
            
        Returns:
            BookMetadata object
        """
        cover_bytes = None
        back_bytes = None
        toc_bytes = None
        
        if cover_path:
            with open(cover_path, 'rb') as f:
                cover_bytes = f.read()
        
        if back_path:
            with open(back_path, 'rb') as f:
                back_bytes = f.read()
        
        if toc_path:
            with open(toc_path, 'rb') as f:
                toc_bytes = f.read()
        
        if not cover_bytes:
            raise ValueError("At least cover image is required")
        
        return await self.extract_metadata(cover_bytes, back_bytes, toc_bytes)


# Global OCR processor instance
ocr_processor = OCRProcessor()
