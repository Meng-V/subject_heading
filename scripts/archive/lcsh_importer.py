"""
LCSH Data Importer

This script helps import LCSH (Library of Congress Subject Headings) data
into Weaviate for vector search.

Download LCSH data from: https://id.loc.gov/download/

Example usage:
    python scripts/lcsh_importer.py --file path/to/subjects.nt --format ntriples
    python scripts/lcsh_importer.py --file path/to/subjects.rdf --format rdfxml
"""

import sys
import asyncio
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from lcsh_index import lcsh_search


def parse_ntriples(filepath: str, limit: int = None):
    """
    Parse LCSH data from N-Triples format.
    
    Args:
        filepath: Path to .nt file
        limit: Optional limit on number of entries to parse
        
    Returns:
        List of LCSH entries
    """
    entries = []
    current_uri = None
    current_label = None
    
    print(f"📖 Parsing N-Triples file: {filepath}")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if limit and len(entries) >= limit:
                    break
                
                # Parse N-Triples format
                # Example: <http://id.loc.gov/authorities/subjects/sh85001> <http://www.w3.org/2004/02/skos/core#prefLabel> "Label" .
                
                if 'skos/core#prefLabel' in line:
                    parts = line.strip().split('"')
                    if len(parts) >= 2:
                        uri = line.split('<')[1].split('>')[0]
                        label = parts[1]
                        
                        if label and uri:
                            entries.append({
                                'label': label,
                                'uri': uri,
                                'broader': '',
                                'narrower': ''
                            })
                
                if (i + 1) % 10000 == 0:
                    print(f"   Processed {i + 1} lines, found {len(entries)} entries...")
    
    except Exception as e:
        print(f"❌ Error parsing file: {str(e)}")
        return []
    
    print(f"✅ Parsed {len(entries)} LCSH entries")
    return entries


def parse_rdfxml(filepath: str, limit: int = None):
    """
    Parse LCSH data from RDF/XML format.
    
    Requires rdflib: pip install rdflib
    """
    try:
        from rdflib import Graph, Namespace
    except ImportError:
        print("❌ rdflib not installed. Install with: pip install rdflib")
        return []
    
    entries = []
    
    print(f"📖 Parsing RDF/XML file: {filepath}")
    
    try:
        g = Graph()
        g.parse(filepath, format='xml')
        
        SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
        
        # Query for all concepts with prefLabels
        for subject in g.subjects(predicate=SKOS.prefLabel):
            if limit and len(entries) >= limit:
                break
            
            label = str(g.value(subject, SKOS.prefLabel))
            uri = str(subject)
            
            if label and uri:
                entries.append({
                    'label': label,
                    'uri': uri,
                    'broader': '',
                    'narrower': ''
                })
            
            if len(entries) % 1000 == 0:
                print(f"   Found {len(entries)} entries...")
    
    except Exception as e:
        print(f"❌ Error parsing file: {str(e)}")
        return []
    
    print(f"✅ Parsed {len(entries)} LCSH entries")
    return entries


async def import_lcsh(filepath: str, format: str = 'ntriples', limit: int = None, batch_size: int = 100):
    """
    Import LCSH data into Weaviate.
    
    Args:
        filepath: Path to LCSH data file
        format: File format ('ntriples' or 'rdfxml')
        limit: Optional limit on entries to import
        batch_size: Number of entries per batch
    """
    print("\n🚀 Starting LCSH Import\n")
    
    # Connect to Weaviate
    print("🔗 Connecting to Weaviate...")
    lcsh_search.connect()
    
    # Initialize schema
    print("🗂️  Initializing schema...")
    lcsh_search.initialize_schema()
    
    # Parse data
    if format == 'ntriples':
        entries = parse_ntriples(filepath, limit)
    elif format == 'rdfxml':
        entries = parse_rdfxml(filepath, limit)
    else:
        print(f"❌ Unsupported format: {format}")
        return
    
    if not entries:
        print("❌ No entries to import")
        return
    
    # Import in batches
    print(f"\n📥 Importing {len(entries)} entries in batches of {batch_size}...")
    
    for i in range(0, len(entries), batch_size):
        batch = entries[i:i + batch_size]
        try:
            lcsh_search.batch_index_lcsh(batch)
            print(f"   ✅ Imported batch {i // batch_size + 1} ({i + len(batch)}/{len(entries)})")
        except Exception as e:
            print(f"   ❌ Error importing batch: {str(e)}")
    
    # Get stats
    print("\n📊 Final Statistics:")
    stats = lcsh_search.get_stats()
    print(f"   {stats}")
    
    print("\n✅ Import completed!")


def main():
    parser = argparse.ArgumentParser(
        description='Import LCSH data into Weaviate vector database'
    )
    parser.add_argument(
        '--file',
        type=str,
        required=True,
        help='Path to LCSH data file'
    )
    parser.add_argument(
        '--format',
        type=str,
        choices=['ntriples', 'rdfxml'],
        default='ntriples',
        help='File format (default: ntriples)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Limit number of entries to import (for testing)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Batch size for import (default: 100)'
    )
    
    args = parser.parse_args()
    
    # Validate file exists
    if not Path(args.file).exists():
        print(f"❌ File not found: {args.file}")
        return
    
    # Run import
    asyncio.run(import_lcsh(
        filepath=args.file,
        format=args.format,
        limit=args.limit,
        batch_size=args.batch_size
    ))


if __name__ == '__main__':
    main()
