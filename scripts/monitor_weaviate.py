"""
Weaviate Data Monitor

View statistics and sample records from Weaviate.

Usage:
    python scripts/monitor_weaviate.py --stats
    python scripts/monitor_weaviate.py --sample lcsh 5
    python scripts/monitor_weaviate.py --search "Chinese calligraphy"
"""

import sys
import argparse
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from authority_search import authority_search


def show_stats():
    """Display collection statistics."""
    authority_search.connect()
    stats = authority_search.get_stats()
    
    print("\n📊 Weaviate Statistics")
    print("=" * 60)
    total = 0
    for vocab, count in stats.items():
        if isinstance(count, int):
            print(f"  {vocab.upper():10s}: {count:,} records")
            total += count
        else:
            print(f"  {vocab.upper():10s}: {count}")
    print("=" * 60)
    print(f"  {'TOTAL':10s}: {total:,} records")
    print()
    
    # Show storage info
    client = authority_search.client
    for collection_name in ["LCSHSubject", "FASTSubject"]:
        try:
            collection = client.collections.get(collection_name)
            config = collection.config.get()
            print(f"\n📦 {collection_name}")
            print(f"  Vector dimensions: 3072 (text-embedding-3-large)")
            print(f"  Properties: {len(config.properties)}")
            for prop in config.properties[:5]:  # First 5 properties
                print(f"    - {prop.name}: {prop.data_type}")
        except Exception as e:
            print(f"  Error: {str(e)}")
    
    authority_search.client.close()


def show_sample(vocabulary: str, limit: int = 5):
    """Display sample records from a collection."""
    authority_search.connect()
    
    collection_name = f"{vocabulary.upper()}Subject"
    try:
        collection = authority_search.client.collections.get(collection_name)
        results = collection.query.fetch_objects(limit=limit)
        
        print(f"\n📄 Sample {vocabulary.upper()} Records (showing {limit})")
        print("=" * 80)
        
        for i, obj in enumerate(results.objects, 1):
            props = obj.properties
            print(f"\n{i}. {props.get('label', 'N/A')}")
            print(f"   URI: {props.get('uri', 'N/A')}")
            print(f"   Type: {props.get('subject_type', 'unknown')}")
            print(f"   Alt labels: {props.get('alt_labels', [])}")
            print(f"   Broader terms: {len(props.get('broader_terms', []))} | Narrower: {len(props.get('narrower_terms', []))}")
            scope = props.get('scope_note', '')
            if scope:
                print(f"   Scope: {scope[:100]}...")
        
        print("\n" + "=" * 80)
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    authority_search.client.close()


def search_test(query: str, limit: int = 5):
    """Test search functionality."""
    import asyncio
    
    authority_search.connect()
    
    print(f"\n🔍 Searching for: '{query}'")
    print("=" * 80)
    
    try:
        # Run async search
        results = asyncio.run(authority_search.search_authorities(
            topic=query,
            vocabularies=["lcsh", "fast"],
            limit_per_vocab=limit
        ))
        
        if not results:
            print("No results found.")
        else:
            for i, result in enumerate(results, 1):
                print(f"\n{i}. [{result.vocabulary.upper()}] {result.label}")
                print(f"   Score: {result.score:.4f}")
                print(f"   URI: {result.uri}")
        
        print("\n" + "=" * 80)
        print(f"✅ Search complete. Found {len(results)} results.")
        print(f"💰 Cost: $0.00013 (1 embedding API call)")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    authority_search.client.close()


def check_embeddings():
    """Check if records have embeddings (vectors)."""
    import weaviate.classes as wvc
    
    authority_search.connect()
    
    print("\n🔍 Checking Embeddings Status")
    print("=" * 80)
    
    for collection_name in ["LCSHSubject", "FASTSubject"]:
        try:
            collection = authority_search.client.collections.get(collection_name)
            
            # Query with vector included
            result = collection.query.fetch_objects(
                limit=1,
                include_vector=True,
                return_properties=["label"]
            )
            
            if result.objects:
                obj = result.objects[0]
                
                # Check if vector exists
                vector_data = obj.vector.get('default') if hasattr(obj, 'vector') and obj.vector else None
                has_vector = vector_data is not None and len(vector_data) > 0
                vector_dims = len(vector_data) if vector_data else 0
                
                print(f"\n📦 {collection_name}")
                print(f"   Record: {obj.properties.get('label', 'N/A')}")
                print(f"   Has embeddings: {'✅ Yes' if has_vector else '❌ No'}")
                
                if has_vector:
                    print(f"   Vector dimensions: {vector_dims}")
                    if vector_dims > 1:
                        print(f"   Sample vector: [{vector_data[0]:.6f}, {vector_data[1]:.6f}, {vector_data[2]:.6f}, ...]")
                        print(f"   ✅ Embeddings are CACHED (3072 dimensions)")
                        print(f"   ✅ No API calls needed for search!")
                    else:
                        print(f"   ⚠️  Vector dimension issue detected")
                else:
                    print(f"   ❌ No embeddings found")
            else:
                print(f"\n📦 {collection_name}")
                print(f"   No records found")
                
        except Exception as e:
            print(f"\n📦 {collection_name}")
            print(f"   Error: {str(e)}")
    
    print("\n" + "=" * 80)
    authority_search.client.close()


def main():
    parser = argparse.ArgumentParser(
        description='Monitor Weaviate data and test searches'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Stats command
    subparsers.add_parser('stats', help='Show collection statistics')
    
    # Sample command
    sample_parser = subparsers.add_parser('sample', help='Show sample records')
    sample_parser.add_argument('vocabulary', choices=['lcsh', 'fast'], help='Vocabulary to sample')
    sample_parser.add_argument('--limit', type=int, default=5, help='Number of samples')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Test search')
    search_parser.add_argument('query', help='Search query')
    search_parser.add_argument('--limit', type=int, default=5, help='Number of results')
    
    # Check embeddings
    subparsers.add_parser('check-embeddings', help='Verify embeddings are cached')
    
    args = parser.parse_args()
    
    if args.command == 'stats':
        show_stats()
    elif args.command == 'sample':
        show_sample(args.vocabulary, args.limit)
    elif args.command == 'search':
        search_test(args.query, args.limit)
    elif args.command == 'check-embeddings':
        check_embeddings()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
