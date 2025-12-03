"""MARC 65X field builder for topical, geographic, and genre/form headings.

MVP Scope:
- Generate Subject65X for LCSH and FAST vocabularies
- LCSH: 650/651/655 with ind2=0
- FAST: 650/651/655 with ind2=7 and $2 fast

Uses OpenAI Chat Completions API with gpt-4o-mini.
"""
import re
import json
from typing import List, Optional, Dict, Literal
from openai import OpenAI

from config import settings
from models import (
    AuthorityCandidate, 
    Subject65X, 
    Subfield, 
    TopicMatchResult,
    SubjectStatus
)


class MARC65XBuilder:
    """Builds Subject65X objects (650/651/655) using gpt-4o-mini."""
    
    # MVP: LCSH and FAST vocabulary mapping
    VOCAB_TO_MARC = {
        "lcsh": {"ind2": "0", "subfield2": None},
        "fast": {"ind2": "7", "subfield2": "fast"},
    }
    
    # Future extensions (not auto-generated in MVP)
    FUTURE_VOCAB_TO_MARC = {
        "gtt": {"ind2": "7", "subfield2": "gtt"},
        "rero": {"ind2": "7", "subfield2": "rero"},
        "swd": {"ind2": "7", "subfield2": "swd"},
        "idszbz": {"ind2": "7", "subfield2": "idszbz"},
        "ram": {"ind2": "7", "subfield2": "ram"}
    }
    
    def __init__(self):
        """Initialize MARC builder with gpt-4o-mini."""
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.explanation_model
    
    def _determine_tag(
        self,
        authority: AuthorityCandidate,
        topic_type: str
    ) -> str:
        """
        Determine MARC tag (650/651/655) based on topic type and authority data.
        
        Args:
            authority: Authority candidate
            topic_type: Topic type (topical, geographic, genre)
            
        Returns:
            MARC tag (650, 651, or 655)
        """
        # Priority 1: Use topic type hint
        if topic_type == "geographic":
            return "651"
        elif topic_type == "genre":
            return "655"
        elif topic_type == "topical":
            return "650"
        
        # Priority 2: Heuristic based on label
        label_lower = authority.label.lower()
        
        # Geographic patterns
        geographic_patterns = [
            r'\bcountry\b', r'\bcity\b', r'\bregion\b',
            r'\bchina\b', r'\bjapan\b', r'\bunited states\b',
            r'\beurope\b', r'\basia\b', r'\bafrica\b'
        ]
        for pattern in geographic_patterns:
            if re.search(pattern, label_lower):
                return "651"
        
        # Genre/form patterns
        genre_patterns = [
            r'\bconference', r'\bhandbook', r'\bmanual',
            r'\bessay', r'\bpaper', r'\bproceeding',
            r'\btextbook', r'\bguide'
        ]
        for pattern in genre_patterns:
            if re.search(pattern, label_lower):
                return "655"
        
        # Default to topical
        return "650"
    
    def _parse_subdivisions(self, label: str) -> List[Subfield]:
        """
        Parse authority label into MARC subfields.
        
        Splits by -- and assigns:
        - First part: $a (main heading)
        - Subdivisions: $x (general), $y (chronological), $z (geographic), $v (form)
        
        Args:
            label: Authority label string
            
        Returns:
            List of Subfield objects
        """
        parts = [p.strip() for p in label.split("--")]
        
        if not parts:
            return [Subfield(code="a", value=label)]
        
        subfields = [Subfield(code="a", value=parts[0])]
        
        # Process subdivisions
        for part in parts[1:]:
            subfield_code = self._classify_subdivision(part)
            subfields.append(Subfield(code=subfield_code, value=part))
        
        return subfields
    
    def _classify_subdivision(self, text: str) -> str:
        """
        Classify a subdivision into appropriate subfield code.
        
        Args:
            text: Subdivision text
            
        Returns:
            Subfield code (x, y, z, or v)
        """
        text_lower = text.lower()
        
        # Chronological patterns ($y)
        chronological_patterns = [
            r'\d{3,4}', r'century', r'period', r'era',
            r'dynasty', r'age', r'to \d+', r'\d+-\d+'
        ]
        for pattern in chronological_patterns:
            if re.search(pattern, text_lower):
                return "y"
        
        # Geographic patterns ($z)
        geographic_keywords = [
            'united states', 'america', 'china', 'japan', 'europe',
            'asia', 'africa', 'city', 'state', 'province', 'region',
            'county', 'kingdom', 'republic'
        ]
        for keyword in geographic_keywords:
            if keyword in text_lower:
                return "z"
        
        # Form subdivision patterns ($v)
        form_keywords = [
            'congresses', 'conferences', 'periodicals',
            'handbooks', 'manuals', 'guidebooks',
            'dictionaries', 'encyclopedias', 'directories',
            'bibliography', 'catalogs', 'indexes',
            'abstracts', 'reviews', 'case studies',
            'textbooks', 'problems', 'exercises',
            'examinations', 'outlines', 'study guides'
        ]
        for keyword in form_keywords:
            if keyword in text_lower:
                return "v"
        
        # Default to general/topical subdivision ($x)
        return "x"
    
    def _extract_authority_id(self, uri: str) -> Optional[str]:
        """Extract authority ID from URI."""
        if not uri:
            return None
        
        # LCSH: http://id.loc.gov/authorities/subjects/sh85024024 -> sh85024024
        if "id.loc.gov" in uri:
            parts = uri.rstrip("/").split("/")
            return parts[-1] if parts else None
        
        # FAST: (OCoLC)fst00844437 -> fst00844437
        if "fst" in uri.lower():
            import re
            match = re.search(r'fst\d+', uri, re.IGNORECASE)
            return match.group(0) if match else None
        
        return None
    
    async def _generate_explanation(
        self,
        authority: AuthorityCandidate,
        topic: str,
        subject: Subject65X
    ) -> str:
        """
        Generate natural language explanation for cataloger.
        
        Args:
            authority: Authority candidate
            topic: Original topic
            marc_field: Built MARC field
            
        Returns:
            Explanation string
        """
        prompt = f"""You are a library cataloging assistant. 
Explain in one concise sentence why this MARC subject heading is appropriate for the given topic.

Original Topic: {topic}
Selected Heading: {authority.label}
MARC Field: {subject.to_marc_string()}

Provide a brief, cataloger-friendly explanation (1-2 sentences max)."""

        try:
            # Use Chat Completions API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=150
            )
            return response.choices[0].message.content.strip()
        except:
            # Fallback explanation
            return f"Selected based on semantic match to '{topic}' with confidence {authority.score:.2f}"
    
    async def build_subject_65x(
        self,
        authority: AuthorityCandidate,
        topic: str,
        topic_type: str,
        generate_explanation: bool = True
    ) -> Subject65X:
        """
        Build a Subject65X from an authority candidate.
        
        Args:
            authority: Authority candidate (LCSH or FAST)
            topic: Original semantic topic
            topic_type: Topic type (topical/geographic/genre)
            generate_explanation: Whether to generate explanation with LLM
            
        Returns:
            Subject65X object with all required fields
        """
        # Determine tag based on topic type
        tag = self._determine_tag(authority, topic_type)
        
        # Get vocabulary mapping (MVP: LCSH or FAST)
        vocab = authority.vocabulary.lower()
        vocab_config = self.VOCAB_TO_MARC.get(
            vocab,
            {"ind2": "7", "subfield2": vocab}  # Fallback for future vocabs
        )
        
        # Parse heading into subfields
        subfields = self._parse_subdivisions(authority.label)
        
        # Add $0 (URI) if available
        if authority.uri:
            subfields.append(Subfield(code="0", value=authority.uri))
        
        # Add $2 (source) for non-LCSH vocabularies
        if vocab_config["subfield2"]:
            subfields.append(Subfield(code="2", value=vocab_config["subfield2"]))
        
        # Extract authority ID from URI
        authority_id = self._extract_authority_id(authority.uri)
        
        # Create Subject65X with all fields
        subject = Subject65X(
            # MARC structure
            tag=tag,
            ind1="_",
            ind2=vocab_config["ind2"],
            
            # Vocabulary
            vocabulary=vocab,
            
            # Heading content
            heading_string=authority.label,
            subfields=subfields,
            
            # Authority linking
            uri=authority.uri,
            authority_id=authority_id,
            
            # Source and scoring
            source_system="ai_generated",
            score=authority.score,
            
            # Workflow
            status=SubjectStatus.SUGGESTED,
            
            # Explanation (will be filled below)
            explanation=""
        )
        
        # Generate explanation if requested
        if generate_explanation:
            explanation = await self._generate_explanation(authority, topic, subject)
            subject.explanation = explanation
        else:
            subject.explanation = f"Match score: {authority.score:.2f}"
        
        return subject
    
    # Alias for backward compatibility
    async def build_65x_field(self, *args, **kwargs) -> Subject65X:
        return await self.build_subject_65x(*args, **kwargs)
    
    async def build_from_topic_matches(
        self,
        topic_matches: List[TopicMatchResult],
        max_per_topic: int = 3,
        generate_explanations: bool = True,
        vocabularies: List[str] = None
    ) -> List[Subject65X]:
        """
        Build Subject65X list from topic match results.
        
        Args:
            topic_matches: List of TopicMatchResult objects
            max_per_topic: Maximum subjects per topic
            generate_explanations: Whether to generate LLM explanations
            vocabularies: Filter by vocabularies (default: ["lcsh", "fast"])
            
        Returns:
            List of Subject65X objects
        """
        if vocabularies is None:
            vocabularies = ["lcsh", "fast"]  # MVP default
        
        all_subjects = []
        
        for topic_result in topic_matches:
            # Filter candidates by vocabulary and take top N
            filtered_candidates = [
                c for c in topic_result.authority_candidates 
                if c.vocabulary.lower() in vocabularies
            ][:max_per_topic]
            
            for candidate in filtered_candidates:
                try:
                    subject = await self.build_subject_65x(
                        authority=candidate,
                        topic=topic_result.topic,
                        topic_type=topic_result.topic_type,
                        generate_explanation=generate_explanations
                    )
                    all_subjects.append(subject)
                except Exception as e:
                    print(f"Failed to build subject for '{candidate.label}': {str(e)}")
                    continue
        
        return all_subjects
    
    def format_for_display(self, subjects: List[Subject65X]) -> str:
        """
        Format Subject65X list for human-readable display.
        
        Args:
            subjects: List of Subject65X objects
            
        Returns:
            Formatted string
        """
        lines = []
        for subject in subjects:
            lines.append(subject.to_marc_string())
            lines.append(f"   Vocabulary: {subject.vocabulary.upper()}")
            if subject.score:
                lines.append(f"   Score: {subject.score:.2f}")
            if subject.explanation:
                lines.append(f"   → {subject.explanation}")
            lines.append("")
        return "\n".join(lines)
    
    def to_json_response(self, subjects: List[Subject65X]) -> dict:
        """
        Format subjects for JSON API response.
        
        Args:
            subjects: List of Subject65X objects
            
        Returns:
            Dict with subjects_65x array
        """
        return {
            "subjects_65x": [s.model_dump() for s in subjects]
        }


# Global MARC 65X builder instance
marc_65x_builder = MARC65XBuilder()
