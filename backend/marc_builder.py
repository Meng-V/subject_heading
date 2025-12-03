"""MARC 650 field builder module (legacy).

Note: Uses OpenAI Responses API with o4-mini model.
For new code, use marc_65x_builder.py instead.
"""
import re
import json
from typing import List, Optional
from openai import OpenAI

from config import settings
from models import LCSHMatch, MARCField650


class MARCBuilder:
    """Builds MARC 650 fields from LCSH headings using o4-mini."""
    
    def __init__(self):
        """Initialize MARC builder with o4-mini."""
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.default_model
        self.reasoning_effort = settings.reasoning_effort
    
    def _parse_lcsh_label(self, label: str) -> dict:
        """
        Parse LCSH label into MARC subfields using rule-based approach.
        
        LCSH format uses -- as delimiter:
        - Main heading comes first
        - $x = General subdivision (topical)
        - $y = Chronological subdivision
        - $z = Geographic subdivision
        
        Args:
            label: LCSH authority label
            
        Returns:
            Dict with subfield assignments
        """
        # Split by double dash
        parts = [p.strip() for p in label.split("--")]
        
        if not parts:
            return {"subfield_a": label}
        
        result = {
            "subfield_a": parts[0],
            "subfield_x": None,
            "subfield_y": None,
            "subfield_z": None
        }
        
        # Process subdivisions
        for i, part in enumerate(parts[1:], 1):
            # Check if it looks like a chronological subdivision
            # Pattern: contains dates, centuries, or time periods
            if self._is_chronological(part):
                result["subfield_y"] = part
            # Check if it looks like a geographic subdivision
            elif self._is_geographic(part):
                result["subfield_z"] = part
            # Default to topical subdivision
            else:
                # Concatenate multiple topical subdivisions
                if result["subfield_x"]:
                    result["subfield_x"] += f" -- {part}"
                else:
                    result["subfield_x"] = part
        
        return result
    
    def _is_chronological(self, text: str) -> bool:
        """Check if a subdivision appears to be chronological."""
        chronological_patterns = [
            r'\d{3,4}',  # Years (3-4 digits)
            r'\d{1,2}th century',
            r'century',
            r'period',
            r'era',
            r'dynasty',
            r'age',
            r'To \d+',
            r'\d+-\d+',  # Date ranges
        ]
        
        for pattern in chronological_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def _is_geographic(self, text: str) -> bool:
        """Check if a subdivision appears to be geographic."""
        # Common geographic indicators
        geographic_keywords = [
            'United States', 'America', 'China', 'Japan', 'Europe',
            'Asia', 'Africa', 'City', 'State', 'Province', 'Region',
            'County', 'Kingdom', 'Republic', 'East', 'West', 'North', 'South'
        ]
        
        for keyword in geographic_keywords:
            if keyword.lower() in text.lower():
                return True
        return False
    
    async def _validate_with_llm(self, label: str, parsed: dict) -> dict:
        """
        Use LLM to validate and refine MARC field parsing for ambiguous cases.
        
        Args:
            label: Original LCSH label
            parsed: Rule-based parsed result
            
        Returns:
            Validated/refined subfield dict
        """
        prompt = f"""You are a MARC-21 cataloging expert. Convert the following LCSH label into proper MARC 650 field subfields.

LCSH Label: {label}

Rules:
- $a = Main heading (first part)
- $x = General/topical subdivision
- $y = Chronological subdivision (dates, time periods)
- $z = Geographic subdivision (places)

Return ONLY valid JSON in this format:
{{
  "subfield_a": "...",
  "subfield_x": "..." or null,
  "subfield_y": "..." or null,
  "subfield_z": "..." or null
}}"""

        try:
            # Use Responses API with o4-mini
            response = self.client.responses.create(
                model=self.model,
                input=prompt,
                reasoning={"effort": self.reasoning_effort},
                max_output_tokens=500
            )
            
            content = response.output_text.strip()
            
            # Extract JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            validated = json.loads(content)
            return validated
            
        except Exception as e:
            # If LLM validation fails, return rule-based result
            print(f"LLM validation failed: {str(e)}, using rule-based result")
            return parsed
    
    async def build_marc_field(
        self,
        lcsh_match: LCSHMatch,
        validate_with_llm: bool = False
    ) -> MARCField650:
        """
        Build a MARC 650 field from an LCSH match.
        
        Args:
            lcsh_match: LCSH authority match
            validate_with_llm: Whether to validate with LLM
            
        Returns:
            MARCField650 object
        """
        # Parse the label
        parsed = self._parse_lcsh_label(lcsh_match.label)
        
        # Optionally validate with LLM for ambiguous cases
        if validate_with_llm and (parsed["subfield_x"] or parsed["subfield_y"] or parsed["subfield_z"]):
            parsed = await self._validate_with_llm(lcsh_match.label, parsed)
        
        # Build MARC field
        marc_field = MARCField650(
            tag="650",
            ind1="_",
            ind2="0",  # Library of Congress Subject Headings
            subfield_a=parsed["subfield_a"],
            subfield_x=parsed.get("subfield_x"),
            subfield_y=parsed.get("subfield_y"),
            subfield_z=parsed.get("subfield_z"),
            subfield_0=lcsh_match.uri  # Authority record URI
        )
        
        return marc_field
    
    async def build_multiple_marc_fields(
        self,
        lcsh_matches: List[LCSHMatch],
        validate_with_llm: bool = False
    ) -> List[MARCField650]:
        """
        Build MARC 650 fields for multiple LCSH matches.
        
        Args:
            lcsh_matches: List of LCSH matches
            validate_with_llm: Whether to validate with LLM
            
        Returns:
            List of MARCField650 objects
        """
        marc_fields = []
        
        for match in lcsh_matches:
            try:
                field = await self.build_marc_field(match, validate_with_llm)
                marc_fields.append(field)
            except Exception as e:
                print(f"Failed to build MARC field for '{match.label}': {str(e)}")
                continue
        
        return marc_fields
    
    def marc_to_string(self, marc_field: MARCField650) -> str:
        """
        Convert MARC field to human-readable string.
        
        Args:
            marc_field: MARCField650 object
            
        Returns:
            MARC format string
        """
        return marc_field.to_marc_string()
    
    def export_marc_fields(self, marc_fields: List[MARCField650]) -> str:
        """
        Export multiple MARC fields as formatted text.
        
        Args:
            marc_fields: List of MARC fields
            
        Returns:
            Formatted MARC output
        """
        lines = []
        for field in marc_fields:
            lines.append(field.to_marc_string())
        return "\n".join(lines)


# Global MARC builder instance
marc_builder = MARCBuilder()
