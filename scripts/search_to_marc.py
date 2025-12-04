"""
Search for subjects and get MARC 65X output

This script searches for authority subjects and returns them
in MARC 65X format, ready to use in cataloging.

Usage:
    python scripts/search_to_marc.py "Chinese calligraphy"
    python scripts/search_to_marc.py "Ming dynasty art" --limit 3
    python scripts/search_to_marc.py "handbooks" --format json
"""

import sys
import json
import asyncio
import argparse
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from authority_search import authority_search
from models import Subject65X, Subfield


def authority_to_marc65x(authority_candidate, score: float = None) -> Subject65X:
    """
    Convert AuthorityCandidate to Subject65X MARC field.
    
    Args:
        authority_candidate: Authority search result
        score: Search confidence score
        
    Returns:
        Subject65X object
    """
    # Determine MARC tag based on subject type
    subject_type = getattr(authority_candidate, 'subject_type', 'topical')
    
    if subject_type == 'geographic':
        tag = '651'
    elif subject_type == 'genre_form':
        tag = '655'
    else:  # topical or unknown
        tag = '650'
    
    # Determine second indicator based on vocabulary
    vocab = authority_candidate.vocabulary.lower()
    if vocab == 'lcsh':
        ind2 = '0'
    elif vocab == 'fast':
        ind2 = '7'
    else:
        ind2 = '7'
    
    # Parse heading into subfields
    heading = authority_candidate.label
    subfields = []
    
    # Check if heading has subdivisions (marked by --)
    if ' -- ' in heading:
        parts = heading.split(' -- ')
        
        # First part is always $a
        subfields.append(Subfield(code='a', value=parts[0]))
        
        # Subsequent parts need classification
        for part in parts[1:]:
            # Determine subfield code
            if any(keyword in part.lower() for keyword in ['century', 'b.c.', 'a.d.', '-']):
                # Chronological subdivision: $y
                code = 'y'
            elif part[0].isupper() and not any(keyword in part.lower() for keyword in ['history', 'politics', 'social']):
                # Geographic subdivision: $z (starts with capital, looks like place name)
                code = 'z'
            else:
                # General subdivision: $x
                code = 'x'
            
            subfields.append(Subfield(code=code, value=part))
    else:
        # No subdivisions, just main heading
        subfields.append(Subfield(code='a', value=heading))
    
    # Add authority record control number (URI)
    if authority_candidate.uri:
        subfields.append(Subfield(code='0', value=authority_candidate.uri))
    
    # Add source code if not LCSH
    if vocab != 'lcsh':
        subfields.append(Subfield(code='2', value=vocab))
    
    # Create Subject65X object
    subject_65x = Subject65X(
        tag=tag,
        ind1='_',
        ind2=ind2,
        vocabulary=vocab,
        heading_string=heading,
        subfields=subfields,
        uri=authority_candidate.uri,
        source_system='ai_generated',
        score=score or authority_candidate.score,
        explanation=f"Matched with confidence {score or authority_candidate.score:.2%}"
    )
    
    return subject_65x


async def search_and_convert_to_marc(query: str, limit: int = 5, min_score: float = 0.70):
    """
    Search for subjects and convert to MARC 65X format.
    
    Args:
        query: Search query
        limit: Maximum number of results
        min_score: Minimum confidence score
        
    Returns:
        List of Subject65X objects
    """
    authority_search.connect()
    
    try:
        # Search authorities
        results = await authority_search.search_authorities(
            topic=query,
            vocabularies=["lcsh", "fast"],
            limit_per_vocab=limit,
            min_score=min_score
        )
        
        # Convert to MARC 65X
        marc_fields = []
        for result in results:
            marc_field = authority_to_marc65x(result, result.score)
            marc_fields.append(marc_field)
        
        return marc_fields
        
    finally:
        authority_search.client.close()


def format_marc_display(subject_65x: Subject65X) -> str:
    """Format MARC field for human-readable display."""
    return subject_65x.to_marc_string()


def format_marc_json(subject_65x: Subject65X) -> dict:
    """Format MARC field as JSON."""
    return {
        'tag': subject_65x.tag,
        'ind1': subject_65x.ind1,
        'ind2': subject_65x.ind2,
        'subfields': [
            {'code': sf.code, 'value': sf.value}
            for sf in subject_65x.subfields
        ],
        'vocabulary': subject_65x.vocabulary,
        'uri': subject_65x.uri,
        'score': subject_65x.score,
        'explanation': subject_65x.explanation
    }


async def main():
    parser = argparse.ArgumentParser(
        description='Search for subjects and get MARC 65X output'
    )
    parser.add_argument('query', help='Search query')
    parser.add_argument('--limit', type=int, default=5, help='Max results per vocabulary')
    parser.add_argument('--min-score', type=float, default=0.70, help='Minimum confidence score')
    parser.add_argument('--format', choices=['display', 'json', 'both'], default='display',
                       help='Output format')
    
    args = parser.parse_args()
    
    print(f"\n🔍 Searching for: '{args.query}'")
    print(f"Min score: {args.min_score:.0%}")
    print("=" * 80)
    
    # Search and convert
    marc_fields = await search_and_convert_to_marc(
        query=args.query,
        limit=args.limit,
        min_score=args.min_score
    )
    
    if not marc_fields:
        print("\n❌ No results found above confidence threshold")
        print(f"Try lowering --min-score (current: {args.min_score:.0%})")
        return 1
    
    print(f"\n✅ Found {len(marc_fields)} result(s)\n")
    
    # Display results
    for i, marc_field in enumerate(marc_fields, 1):
        print(f"\n{'='*80}")
        print(f"Result {i}/{len(marc_fields)}")
        print(f"{'='*80}")
        
        if args.format in ['display', 'both']:
            print("\n📋 MARC Format:")
            print(f"   {format_marc_display(marc_field)}")
            
            print("\n📊 Details:")
            print(f"   Tag: {marc_field.tag} (Subject - {marc_field.tag})")
            print(f"   Indicators: {marc_field.ind1}{marc_field.ind2}")
            print(f"   Vocabulary: {marc_field.vocabulary.upper()}")
            print(f"   Confidence: {marc_field.score:.1%}")
            print(f"   URI: {marc_field.uri}")
            
            print("\n📝 Subfields:")
            for sf in marc_field.subfields:
                sf_meaning = {
                    'a': 'Main heading',
                    'x': 'General subdivision',
                    'y': 'Chronological subdivision',
                    'z': 'Geographic subdivision',
                    'v': 'Form subdivision',
                    '0': 'Authority record control number',
                    '2': 'Source'
                }.get(sf.code, 'Other')
                print(f"      ${sf.code} {sf.value:30s}  ({sf_meaning})")
        
        if args.format in ['json', 'both']:
            print("\n🔧 JSON Format:")
            print(json.dumps(format_marc_json(marc_field), indent=2))
    
    # Summary
    print("\n" + "=" * 80)
    print(f"💰 Cost: $0.00013 (1 embedding API call)")
    print(f"📋 Ready to use: {len(marc_fields)} MARC 65X field(s)")
    print("=" * 80)
    
    return 0


if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
