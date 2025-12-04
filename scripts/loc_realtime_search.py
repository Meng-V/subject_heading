"""
Real-time LOC Subject Heading Search
Uses LOC's Suggest API - NO download/embedding required!

LOC API Documentation:
- https://id.loc.gov/techcenter/searching.html
- https://id.loc.gov/authorities/subjects/suggest2/

Advantages:
- ✅ No download needed
- ✅ No embedding costs
- ✅ Always up-to-date
- ✅ Free API

Disadvantages:
- ❌ Slower (network latency)
- ❌ Requires internet connection
- ❌ Limited to exact/prefix matching (no semantic search)
- ❌ Rate limits may apply

Usage:
    python scripts/loc_realtime_search.py "Chinese calligraphy"
"""

import sys
import json
import requests
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class LOCSubject:
    """LOC subject heading result."""
    label: str
    uri: str
    alt_labels: List[str] = None
    
    def __post_init__(self):
        if self.alt_labels is None:
            self.alt_labels = []


class LOCRealtimeSearch:
    """Real-time search against LOC APIs."""
    
    # LOC Suggest API endpoints
    SUGGEST_API = "https://id.loc.gov/authorities/subjects/suggest2/"
    LOOKUP_API = "https://id.loc.gov/authorities/subjects/"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'SubjectHeadingApp/1.0',
            'Accept': 'application/json'
        })
    
    def suggest_subjects(self, query: str, limit: int = 10) -> List[LOCSubject]:
        """
        Search LOC subjects using Suggest API.
        
        This is a lightweight autocomplete/typeahead API.
        Good for: prefix matching, exact matches
        Not good for: semantic similarity
        
        Args:
            query: Search term (e.g., "Chinese calligraphy")
            limit: Max results to return
            
        Returns:
            List of LOCSubject matches
        """
        try:
            # LOC Suggest API format
            params = {
                'q': query,
                'count': limit
            }
            
            response = self.session.get(
                self.SUGGEST_API,
                params=params,
                timeout=5
            )
            response.raise_for_status()
            
            results = []
            data = response.json()
            
            # Parse suggest response format
            # Returns: [query, [labels], [uris]]
            if isinstance(data, list) and len(data) >= 3:
                labels = data[1] if len(data) > 1 else []
                uris = data[2] if len(data) > 2 else []
                
                for label, uri in zip(labels, uris):
                    results.append(LOCSubject(
                        label=label,
                        uri=uri,
                        alt_labels=[]
                    ))
            
            return results
            
        except Exception as e:
            print(f"❌ Error searching LOC: {e}")
            return []
    
    def get_subject_details(self, uri: str) -> Optional[Dict]:
        """
        Get full details for a subject by URI.
        
        This fetches complete SKOS data including:
        - prefLabel
        - altLabel
        - broader/narrower terms
        - scope notes
        
        Args:
            uri: Full LOC URI (e.g., "http://id.loc.gov/authorities/subjects/sh85018909")
            
        Returns:
            Full subject data as dict
        """
        try:
            # Request JSON-LD format
            response = self.session.get(
                uri + ".json",
                timeout=5
            )
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            print(f"❌ Error fetching details: {e}")
            return None
    
    def search_with_details(self, query: str, limit: int = 5) -> List[Dict]:
        """
        Search and fetch full details for each result.
        
        This is slower but gives you complete information.
        
        Args:
            query: Search term
            limit: Max results
            
        Returns:
            List of full subject records
        """
        # First, get suggestions
        suggestions = self.suggest_subjects(query, limit)
        
        # Then, fetch details for each
        results = []
        for subject in suggestions:
            details = self.get_subject_details(subject.uri)
            if details:
                results.append(details)
        
        return results


def format_subject(subject: LOCSubject) -> str:
    """Format subject for display."""
    output = f"\n📌 {subject.label}"
    output += f"\n   URI: {subject.uri}"
    if subject.alt_labels:
        output += f"\n   Alt: {', '.join(subject.alt_labels)}"
    return output


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Real-time LOC subject search (no download needed)'
    )
    parser.add_argument('query', help='Search query')
    parser.add_argument('--limit', type=int, default=10, help='Max results')
    parser.add_argument('--details', action='store_true', help='Fetch full details')
    
    args = parser.parse_args()
    
    searcher = LOCRealtimeSearch()
    
    print(f"\n🔍 Searching LOC for: '{args.query}'")
    print("=" * 70)
    
    if args.details:
        print("Fetching full details (slower)...")
        results = searcher.search_with_details(args.query, args.limit)
        
        for i, data in enumerate(results, 1):
            # Parse JSON-LD data
            print(f"\n{i}. Subject Details:")
            print(f"   URI: {data.get('@id', 'N/A')}")
            
            # Extract labels
            labels = data.get('http://www.w3.org/2004/02/skos/core#prefLabel', [])
            if labels:
                print(f"   Label: {labels[0].get('@value', 'N/A')}")
            
            # Extract alt labels
            alt_labels = data.get('http://www.w3.org/2004/02/skos/core#altLabel', [])
            if alt_labels:
                alts = [a.get('@value', '') for a in alt_labels[:3]]
                print(f"   Alt: {', '.join(alts)}")
            
            # Extract scope note
            scope = data.get('http://www.w3.org/2004/02/skos/core#scopeNote', [])
            if scope:
                note = scope[0].get('@value', '')
                print(f"   Scope: {note[:100]}...")
    
    else:
        results = searcher.suggest_subjects(args.query, args.limit)
        
        if not results:
            print("No results found.")
        else:
            for i, subject in enumerate(results, 1):
                print(f"\n{i}. {subject.label}")
                print(f"   {subject.uri}")
    
    print("\n" + "=" * 70)
    print(f"✅ Found {len(results)} results")
    print(f"💰 Cost: $0.00 (LOC API is free!)")
    print(f"⚡ Latency: ~500ms per query")
    print("\n⚠️  Note: This is keyword matching, not semantic similarity")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
