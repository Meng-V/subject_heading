"""LLM-based topic generation module using OpenAI Responses API.

Uses o4-mini with reasoning_effort='high' for better topic generation.
"""
import json
from typing import List
from openai import OpenAI

from config import settings
from models import BookMetadata, TopicCandidate


class TopicGenerator:
    """Generates semantic topic candidates using o4-mini with Responses API."""
    
    def __init__(self):
        """Initialize topic generator with OpenAI client."""
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.topic_model
        self.reasoning_effort = settings.reasoning_effort
        self.max_topics = settings.max_topics
    
    def _format_metadata_for_prompt(self, metadata: BookMetadata) -> str:
        """Format book metadata into a text prompt."""
        parts = []
        
        if metadata.title:
            parts.append(f"Title: {metadata.title}")
        if metadata.author:
            parts.append(f"Author: {metadata.author}")
        if metadata.publisher:
            parts.append(f"Publisher: {metadata.publisher}")
        if metadata.pub_year:
            parts.append(f"Publication Year: {metadata.pub_year}")
        if metadata.summary:
            parts.append(f"\nSummary:\n{metadata.summary}")
        if metadata.table_of_contents:
            toc_text = "\n".join([f"- {item}" for item in metadata.table_of_contents])
            parts.append(f"\nTable of Contents:\n{toc_text}")
        
        return "\n".join(parts)
    
    async def generate_topics(self, metadata: BookMetadata) -> List[TopicCandidate]:
        """
        Generate semantic topic candidates from book metadata.
        
        Args:
            metadata: Extracted book metadata
            
        Returns:
            List of TopicCandidate objects
        """
        # Format metadata for the prompt
        metadata_text = self._format_metadata_for_prompt(metadata)
        
        # Create the prompt with East Asian collection focus
        prompt = f"""You are an expert library cataloger specializing in EAST ASIAN COLLECTIONS.
Based on the following book metadata, identify 3-{self.max_topics} distinct concepts covering topical subjects, geographic locations, and genre/form terms.

COLLECTION FOCUS: EAST ASIAN STUDIES
This catalog serves collections from China, Korea, Japan, Taiwan, Mongolia, and neighboring regions.
Prioritize topics relevant to:
- Chinese, Korean, Japanese, and CJK (Chinese-Japanese-Korean) studies
- East Asian history, culture, arts, language, literature, philosophy, and religion
- Asian Studies and area studies related to East Asia
- Geographic locations within or related to East Asia
- Topics involving cross-cultural exchange with East Asia

IMPORTANT GUIDELINES:
- Output semantic topic statements in natural language
- Do NOT output LCSH (Library of Congress Subject Headings) formatted headings
- For each topic, classify its type:
  * "topical" - subject matter, themes, concepts (e.g., "Chinese calligraphy", "Korean Buddhism", "Japanese literature")
  * "geographic" - places, regions, countries (e.g., "China", "Seoul, Korea", "Kyoto, Japan")
  * "genre" - form/genre terms (e.g., "Conference papers", "Handbooks", "Essays", "Poetry collections")
- Be specific but not overly granular
- Consider East Asian context and cultural significance
- Consider the title, summary, table of contents, and preface

BOOK METADATA:
{metadata_text}

Return your response as a JSON array in this exact format:
[
  {{"topic": "first topic concept", "type": "topical"}},
  {{"topic": "geographic location", "type": "geographic"}},
  {{"topic": "genre or form term", "type": "genre"}}
]

Return ONLY the JSON array, no additional text."""

        try:
            # Use Responses API with o4-mini
            response = self.client.responses.create(
                model=self.model,
                input=[
                    {
                        "role": "user",
                        "content": [{"type": "input_text", "text": prompt}]
                    }
                ],
                reasoning={"effort": self.reasoning_effort},
                max_output_tokens=16000
            )
            
            # Check for incomplete response
            if response.status == "incomplete":
                raise ValueError(f"API response incomplete - reasoning used all tokens")
            
            # Parse response from Responses API - try structured output first
            if hasattr(response, 'output') and response.output and len(response.output) > 0:
                if hasattr(response.output[0], 'content') and response.output[0].content:
                    content_block = response.output[0].content[0]
                    
                    if hasattr(content_block, 'type'):
                        if content_block.type == "output_text":
                            text = content_block.text.strip()
                        elif content_block.type == "output_json":
                            topics_data = content_block.json
                            # Skip JSON parsing, already parsed
                            if not isinstance(topics_data, list):
                                raise ValueError("Expected JSON array of topics")
                            topics = [TopicCandidate(**item) for item in topics_data]
                            topics = topics[:self.max_topics]
                            return topics
                        else:
                            text = str(content_block)
                    else:
                        text = str(content_block)
                else:
                    text = response.output_text if hasattr(response, 'output_text') else ""
            else:
                text = response.output_text if hasattr(response, 'output_text') else ""
            
            # Fallback: Parse as text with JSON extraction
            text = text.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            
            topics_data = json.loads(text)
            
            # Validate and create TopicCandidate objects
            if not isinstance(topics_data, list):
                raise ValueError("Expected JSON array of topics")
            
            topics = [TopicCandidate(**item) for item in topics_data]
            
            # Limit to max_topics
            topics = topics[:self.max_topics]
            
            return topics
            
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Failed to parse LLM response as JSON: {str(e)}; "
                f"raw_response={response.model_dump_json()[:1000]}"
            )
        except Exception as e:
            raise Exception(f"Topic generation failed: {str(e)}")
    
    async def refine_topic(self, topic: str, context: str = "") -> str:
        """
        Refine a single topic if needed.
        
        Args:
            topic: Topic to refine
            context: Additional context
            
        Returns:
            Refined topic string
        """
        prompt = f"""Refine this topic concept for library subject cataloging.
Make it more precise and cataloging-appropriate while maintaining its meaning.

Topic: {topic}
{f"Context: {context}" if context else ""}

Return only the refined topic, no explanation."""

        try:
            # Use Responses API with o4-mini
            response = self.client.responses.create(
                model=self.model,
                input=[
                    {
                        "role": "user",
                        "content": [{"type": "input_text", "text": prompt}]
                    }
                ],
                reasoning={"effort": self.reasoning_effort},
                max_output_tokens=500
            )
            
            # Parse response
            if response.output and response.output[0].content:
                content_block = response.output[0].content[0]
                if content_block.type == "output_text":
                    return content_block.text.strip()
                elif hasattr(content_block, 'text'):
                    return content_block.text.strip()
            
            return response.output_text.strip() if hasattr(response, 'output_text') else ""
            
        except Exception as e:
            # If refinement fails, return original
            return topic


# Global topic generator instance
topic_generator = TopicGenerator()
