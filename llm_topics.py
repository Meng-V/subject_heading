"""LLM-based topic generation module using OpenAI Chat Completions API.

Uses gpt-4o-mini with low temperature for consistent topic generation.
"""
import json
from typing import List
from openai import OpenAI

from config import settings
from models import BookMetadata, TopicCandidate


class TopicGenerator:
    """Generates semantic topic candidates using gpt-4o-mini."""
    
    def __init__(self):
        """Initialize topic generator with OpenAI client."""
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.topic_model
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
        
        # Create the prompt
        prompt = f"""You are an expert library cataloger with deep knowledge of subject analysis.
Based on the following book metadata, identify 3-{self.max_topics} distinct concepts covering topical subjects, geographic locations, and genre/form terms.

IMPORTANT GUIDELINES:
- Output semantic topic statements in natural language
- Do NOT output LCSH (Library of Congress Subject Headings) formatted headings
- For each topic, classify its type:
  * "topical" - subject matter, themes, concepts (e.g., "Chinese calligraphy techniques")
  * "geographic" - places, regions, countries (e.g., "China", "Beijing")
  * "genre" - form/genre terms (e.g., "Conference papers", "Handbooks", "Essays")
- Be specific but not overly granular
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
            # Use Chat Completions API (gpt-4o-mini doesn't support reasoning parameter)
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,  # Low temperature for consistent output
                max_tokens=2000
            )
            
            # Parse response from Chat Completions API
            content = response.choices[0].message.content.strip()
            
            # Extract JSON from response (handle markdown code blocks)
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            # Parse JSON
            topics_data = json.loads(content)
            
            # Validate and create TopicCandidate objects
            if not isinstance(topics_data, list):
                raise ValueError("Expected JSON array of topics")
            
            topics = [TopicCandidate(**item) for item in topics_data]
            
            # Limit to max_topics
            topics = topics[:self.max_topics]
            
            return topics
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse LLM response as JSON: {str(e)}\nContent: {content}")
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
            # Use Chat Completions API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=500
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            # If refinement fails, return original
            return topic


# Global topic generator instance
topic_generator = TopicGenerator()
