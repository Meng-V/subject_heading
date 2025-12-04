"""
Enhanced Subject Search with Multiple Inputs

This script accepts multiple book metadata fields to improve MARC subject accuracy.
Instead of just searching by title, you can provide:
- Title
- Author
- Abstract/Summary
- Table of Contents
- Publisher notes
- Any other descriptive text

Usage:
    # Simple title search (like before)
    python scripts/search_to_marc_enhanced.py --title "Chinese calligraphy"
    
    # Enhanced search with multiple inputs
    python scripts/search_to_marc_enhanced.py \
        --title "History of Chinese Calligraphy" \
        --author "Wang Xizhi" \
        --abstract "This book explores the development of calligraphy during Ming and Qing dynasties" \
        --toc "Chapter 1: Early History" "Chapter 2: Ming Dynasty Masters" \
        --limit 3
    
    # From JSON file (for batch processing)
    python scripts/search_to_marc_enhanced.py --from-json book_metadata.json
"""

import sys
import json
import asyncio
import argparse
from pathlib import Path
from typing import List, Optional

sys.path.append(str(Path(__file__).parent.parent))

from authority_search import authority_search
from models import Subject65X, Subfield


def build_rich_query(
    title: str = "",
    author: str = "",
    abstract: str = "",
    toc: List[str] = None,
    publisher_notes: str = "",
    keywords: List[str] = None,
    **kwargs
) -> str:
    """
    Build a rich semantic query from multiple book metadata fields.
    
    The query is structured to prioritize different types of information:
    1. Title and keywords (highest weight)
    2. Abstract/summary (high weight)
    3. Table of contents (medium weight)
    4. Author and publisher notes (context)
    
    Args:
        title: Book title
        author: Author name(s)
        abstract: Book summary or abstract
        toc: List of table of contents entries
        publisher_notes: Publisher description
        keywords: Additional keywords
        **kwargs: Other metadata fields
        
    Returns:
        Rich query string for embedding
    """
    query_parts = []
    
    # 1. Title (highest priority - appears 2x for emphasis)
    if title:
        query_parts.append(f"TITLE: {title}")
        query_parts.append(title)  # Repeat for emphasis
    
    # 2. Keywords (high priority)
    if keywords:
        query_parts.append(f"TOPICS: {' | '.join(keywords)}")
    
    # 3. Abstract/Summary (high priority)
    if abstract:
        # Limit to first 300 chars to avoid dilution
        abstract_snippet = abstract[:300] + "..." if len(abstract) > 300 else abstract
        query_parts.append(f"ABOUT: {abstract_snippet}")
    
    # 4. Table of Contents (medium priority)
    if toc:
        # Take first 5 entries
        toc_sample = toc[:5]
        toc_text = " | ".join(toc_sample)
        query_parts.append(f"CONTENTS: {toc_text}")
    
    # 5. Author (context)
    if author:
        query_parts.append(f"AUTHOR: {author}")
    
    # 6. Publisher notes (context)
    if publisher_notes:
        notes_snippet = publisher_notes[:200] + "..." if len(publisher_notes) > 200 else publisher_notes
        query_parts.append(f"DESCRIPTION: {notes_snippet}")
    
    # Combine all parts
    rich_query = " | ".join(query_parts)
    
    return rich_query


def authority_to_marc65x(authority_candidate, score: float = None) -> Subject65X:
    """Convert AuthorityCandidate to Subject65X MARC field."""
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
    if '--' in heading:
        parts = heading.split('--')
        
        # First part is always $a
        subfields.append(Subfield(code='a', value=parts[0]))
        
        # Subsequent parts need classification
        for part in parts[1:]:
            # Determine subfield code
            if any(keyword in part.lower() for keyword in ['century', 'b.c.', 'a.d.']) or (
                '-' in part and any(char.isdigit() for char in part)
            ):
                code = 'y'  # Chronological
            elif part[0].isupper() and not any(keyword in part.lower() for keyword in ['history', 'politics', 'social', 'conditions', 'civilization']):
                code = 'z'  # Geographic
            else:
                code = 'x'  # General
            
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


async def search_with_rich_context(
    title: str = "",
    author: str = "",
    abstract: str = "",
    toc: List[str] = None,
    publisher_notes: str = "",
    keywords: List[str] = None,
    limit: int = 5,
    min_score: float = 0.70,
    verbose: bool = False
):
    """
    Search for subjects using rich book metadata.
    
    Returns:
        Tuple of (marc_fields, rich_query)
    """
    # Build rich query
    rich_query = build_rich_query(
        title=title,
        author=author,
        abstract=abstract,
        toc=toc or [],
        publisher_notes=publisher_notes,
        keywords=keywords or []
    )
    
    if verbose:
        print("\n📝 Rich Query Generated:")
        print("=" * 80)
        print(rich_query)
        print("=" * 80)
    
    # Connect and search
    authority_search.connect()
    
    try:
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
            marc_field = authority_to_marc65x(result, result.score)
            marc_fields.append(marc_field)
        
        return marc_fields, rich_query
        
    finally:
        authority_search.client.close()


def format_marc_display(subject_65x: Subject65X) -> str:
    """Format MARC field for human-readable display."""
    return subject_65x.to_marc_string()


async def main():
    parser = argparse.ArgumentParser(
        description='Enhanced subject search with multiple inputs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    # Input options
    parser.add_argument('--title', help='Book title')
    parser.add_argument('--author', help='Author name(s)')
    parser.add_argument('--abstract', help='Book summary/abstract')
    parser.add_argument('--toc', nargs='+', help='Table of contents entries')
    parser.add_argument('--publisher-notes', help='Publisher description')
    parser.add_argument('--keywords', nargs='+', help='Additional keywords')
    
    # JSON input
    parser.add_argument('--from-json', help='Load metadata from JSON file')
    
    # Search options
    parser.add_argument('--limit', type=int, default=5, help='Max results per vocabulary')
    parser.add_argument('--min-score', type=float, default=0.70, help='Minimum confidence score')
    parser.add_argument('--verbose', action='store_true', help='Show rich query text')
    parser.add_argument('--format', choices=['compact', 'display', 'json'], default='compact')
    
    args = parser.parse_args()
    
    # Load from JSON if specified
    if args.from_json:
        json_path = Path(args.from_json)
        if not json_path.exists():
            print(f"❌ JSON file not found: {args.from_json}")
            return 1
        
        with open(json_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        title = metadata.get('title', '')
        author = metadata.get('author', '')
        abstract = metadata.get('abstract', metadata.get('summary', ''))
        toc = metadata.get('toc', metadata.get('table_of_contents', []))
        publisher_notes = metadata.get('publisher_notes', metadata.get('description', ''))
        keywords = metadata.get('keywords', [])
    else:
        # Use command line arguments
        title = args.title or ""
        author = args.author or ""
        abstract = args.abstract or ""
        toc = args.toc or []
        publisher_notes = args.publisher_notes or ""
        keywords = args.keywords or []
    
    # Validate we have at least some input
    if not any([title, author, abstract, toc, publisher_notes, keywords]):
        print("❌ Error: Please provide at least one input field")
        parser.print_help()
        return 1
    
    print("\n🔍 Enhanced Subject Search")
    print("=" * 80)
    print(f"Input fields provided:")
    if title: print(f"  • Title: {title}")
    if author: print(f"  • Author: {author}")
    if abstract: print(f"  • Abstract: {abstract[:60]}..." if len(abstract) > 60 else f"  • Abstract: {abstract}")
    if toc: print(f"  • TOC entries: {len(toc)}")
    if publisher_notes: print(f"  • Publisher notes: Yes")
    if keywords: print(f"  • Keywords: {', '.join(keywords)}")
    print(f"Min score: {args.min_score:.0%}")
    print("=" * 80)
    
    # Search with rich context
    marc_fields, rich_query = await search_with_rich_context(
        title=title,
        author=author,
        abstract=abstract,
        toc=toc,
        publisher_notes=publisher_notes,
        keywords=keywords,
        limit=args.limit,
        min_score=args.min_score,
        verbose=args.verbose
    )
    
    if not marc_fields:
        print("\n❌ No results found above confidence threshold")
        print(f"Try lowering --min-score (current: {args.min_score:.0%})")
        return 1
    
    print(f"\n✅ Found {len(marc_fields)} result(s)\n")
    
    # Display results
    if args.format == 'compact':
        print("📋 MARC 65X Fields (ready to copy/paste):\n")
        print("=" * 80)
        for i, marc_field in enumerate(marc_fields, 1):
            vocab_tag = f" ({marc_field.vocabulary.upper()})" if marc_field.vocabulary != 'lcsh' else ""
            print(f"{i:2}. {format_marc_display(marc_field):70s} [{marc_field.score:.0%}]{vocab_tag}")
        print("=" * 80)
    
    elif args.format == 'display':
        print("📋 MARC 65X Fields:\n")
        print("=" * 80)
        for i, marc_field in enumerate(marc_fields, 1):
            print(f"{i:2}. {format_marc_display(marc_field)}")
            vocab_indicator = f"({marc_field.vocabulary.upper()})" if marc_field.vocabulary != 'lcsh' else ""
            print(f"    Confidence: {marc_field.score:.1%} {vocab_indicator}")
            print("    Subfields:")
            for sf in marc_field.subfields:
                sf_meaning = {
                    'a': 'Main heading',
                    'x': 'General subdivision',
                    'y': 'Chronological subdivision',
                    'z': 'Geographic subdivision',
                    'v': 'Form subdivision',
                    '0': 'Authority URI',
                    '2': 'Source vocabulary'
                }.get(sf.code, 'Other')
                print(f"       ${sf.code} {sf.value} ({sf_meaning})")
            print()
    
    elif args.format == 'json':
        output = []
        for marc_field in marc_fields:
            output.append({
                'tag': marc_field.tag,
                'ind1': marc_field.ind1,
                'ind2': marc_field.ind2,
                'subfields': [{'code': sf.code, 'value': sf.value} for sf in marc_field.subfields],
                'vocabulary': marc_field.vocabulary,
                'uri': marc_field.uri,
                'score': marc_field.score,
                'explanation': marc_field.explanation
            })
        print(json.dumps(output, indent=2, ensure_ascii=False))
    
    # Summary
    print("\n" + "=" * 80)
    print(f"💰 Cost: $0.00013 (1 embedding API call)")
    print(f"📋 Ready to use: {len(marc_fields)} MARC 65X field(s)")
    print(f"✨ Enhanced search used {len([x for x in [title, author, abstract, toc, publisher_notes, keywords] if x])} input fields")
    print("=" * 80)
    
    return 0


if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
