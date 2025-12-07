"""OCR module with multi-image support and page classification.

Uses OpenAI o4-mini with Responses API and vision support.
"""
import base64
import json
from typing import List, Tuple
from openai import OpenAI

from config import settings
from models import BookMetadata, PageImage


class MultiImageOCRProcessor:
    """Handles OCR processing for multiple book images using o4-mini with Responses API."""
    
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
            # Use Responses API with vision support
            response = self.client.responses.create(
                model=self.model,
                input=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": prompt},
                            {
                                "type": "input_image",
                                "detail": "auto",
                                "image_url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        ]
                    }
                ],
                reasoning={"effort": self.reasoning_effort},
                max_output_tokens=16000
            )
            
            content = response.output_text
            
            # Check for incomplete response
            if response.status == "incomplete" or not content:
                print(f"[OCR] Warning: Incomplete response, status={response.status}")
                return PageImage(
                    page_hint=page_hint,
                    page_type="other",
                    text="[OCR incomplete - please retry or enter manually]"
                )
            
            print(f"[OCR] Raw response: {content[:200]}...")
            
            # Extract JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            page_data = json.loads(content)
            
            print(f"[OCR] Extracted page_type={page_data.get('page_type')}, text_len={len(page_data.get('text', ''))}")
            
            return PageImage(
                page_hint=page_hint,
                page_type=page_data.get("page_type", "other"),
                text=page_data.get("text", "")
            )
            
        except json.JSONDecodeError as e:
            print(f"[OCR] JSON parse error: {e}, content was: {content[:500] if content else 'empty'}")
            return PageImage(
                page_hint=page_hint,
                page_type="other",
                text=content if content else f"Error: JSON parse failed"
            )
        except Exception as e:
            print(f"[OCR] Exception: {type(e).__name__}: {str(e)}")
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
        
        # Also include text from other page types
        other_pages = [p for p in pages if p.page_type == "other"]
        other_text = "\n\n".join([p.text for p in other_pages])
        
        # Aggregate with LLM - comprehensive extraction
        aggregation_prompt = f"""You are an expert library cataloger and metadata extractor specializing in EAST ASIAN materials.
Carefully analyze ALL the following book page texts and extract COMPREHENSIVE metadata.

IMPORTANT: Extract as much information as possible. These are images of book covers, title pages, copyright pages, tables of contents, and other informational pages. Look for ALL of the following:

FRONT COVER TEXT:
{front_text}

BACK COVER TEXT:
{back_text}

FLAP TEXT:
{flap_text}

TABLE OF CONTENTS:
{toc_text}

PREFACE/INTRODUCTION:
{preface_text}

OTHER PAGES (may include title page, copyright page, etc.):
{other_text}

Extract and return ONLY valid JSON with ALL available information:
{{
  "title": "main book title (include subtitle after colon if present)",
  "author": "author name(s), separated by semicolons if multiple",
  "publisher": "publisher name",
  "pub_place": "publication place (city, country)",
  "pub_year": "publication year (4-digit year)",
  "edition": "edition statement if any (e.g., '2nd edition', 'revised edition')",
  "language": "primary language of the book (e.g., Chinese, Japanese, Korean, English)",
  "isbn": "ISBN-10 or ISBN-13 if visible",
  "series": "series title if the book is part of a series",
  "summary": "comprehensive summary combining back cover, flap text, and any description. Include key themes, topics, and scope of the book.",
  "subjects_hint": "list of potential subject terms you can identify from the content (these will help with cataloging)",
  "table_of_contents": ["chapter/section 1 title", "chapter/section 2 title", ...],
  "preface_snippets": ["key excerpts from preface that describe the book's purpose or scope"],
  "notes": "any other relevant information (translator, illustrator, awards, etc.)"
}}

EXTRACTION GUIDELINES:
- For CJK (Chinese/Japanese/Korean) texts, include both original script and romanization if visible
- Look for copyright page information: publisher, year, ISBN, edition
- Extract chapter titles from table of contents
- Identify the book's subject matter from all available text
- If information appears in multiple places, use the most complete version
- If a field is not found, use empty string "" for text or empty array [] for lists."""

        # Log what we're sending
        all_text = front_text + back_text + flap_text + toc_text + preface_text + other_text
        print(f"[OCR Aggregate] Total extracted text length: {len(all_text)} chars")
        print(f"[OCR Aggregate] Page types: {[p.page_type for p in pages]}")
        
        try:
            # Use Responses API
            response = self.client.responses.create(
                model=self.model,
                input=[
                    {
                        "role": "user",
                        "content": [{"type": "input_text", "text": aggregation_prompt}]
                    }
                ],
                reasoning={"effort": self.reasoning_effort},
                max_output_tokens=16000
            )
            
            content = response.output_text
            print(f"[OCR Aggregate] Response status: {response.status}, content length: {len(content) if content else 0}")
            
            # Check for incomplete response
            if not content or response.status == "incomplete":
                raise ValueError(f"API response incomplete - status={response.status}")
            
            # Extract JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            metadata_dict = json.loads(content)
            print(f"[OCR Aggregate] Extracted metadata: title='{metadata_dict.get('title', '')[:50]}', author='{metadata_dict.get('author', '')}'")
            
            # Create BookMetadata with raw_pages
            metadata = BookMetadata(
                **metadata_dict,
                raw_pages=pages
            )
            
            return metadata
            
        except Exception as e:
            print(f"[OCR Aggregate] ERROR: {type(e).__name__}: {str(e)}")
            # Fallback: try to extract from raw text
            all_texts = [p.text for p in pages if p.text and not p.text.startswith("Error")]
            combined = "\n".join(all_texts)
            
            # Try to parse partial JSON if available
            title_fallback = ""
            author_fallback = ""
            if 'content' in dir() and content:
                try:
                    import re
                    title_match = re.search(r'"title"\s*:\s*"([^"]+)"', content)
                    author_match = re.search(r'"author"\s*:\s*"([^"]+)"', content)
                    if title_match:
                        title_fallback = title_match.group(1)
                    if author_match:
                        author_fallback = author_match.group(1)
                except:
                    pass
            
            return BookMetadata(
                title=title_fallback or "Please enter title",
                author=author_fallback,
                publisher="",
                pub_place="",
                pub_year="",
                summary=combined[:1000] if combined else "",
                table_of_contents=[],
                preface_snippets=[],
                notes="Image was processed but some fields could not be extracted. Please review and complete the information above.",
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
