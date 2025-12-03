"""
Generate synthetic LCSH test data for infrastructure testing.

This creates a small RDF file with realistic LCSH-like data for testing
the importer, schema, and embedding generation without downloading
the full dataset.

Usage:
    python scripts/generate_test_sample.py --output data/test_lcsh.rdf --count 100
"""

import argparse
from pathlib import Path
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import SKOS, RDF

def generate_test_lcsh(count: int = 100) -> Graph:
    """
    Generate a test LCSH RDF graph with realistic data.
    
    Args:
        count: Number of test subjects to generate
        
    Returns:
        RDF Graph with test data
    """
    g = Graph()
    g.bind('skos', SKOS)
    
    # Test subjects with various characteristics
    test_subjects = [
        {
            "id": "sh85018909",
            "label": "Calligraphy, Chinese",
            "alt_labels": ["Chinese calligraphy", "Shufa"],
            "broader": ["sh85023424"],
            "narrower": ["sh85018910", "sh85018911"],
            "scope": "Here are entered works on the art of writing Chinese characters.",
            "type": "topical"
        },
        {
            "id": "sh85018910",
            "label": "Calligraphy, Chinese -- Ming-Qing dynasties, 1368-1912",
            "alt_labels": ["Ming-Qing calligraphy"],
            "broader": ["sh85018909"],
            "narrower": [],
            "scope": "Calligraphy from the Ming and Qing dynasties.",
            "type": "topical"
        },
        {
            "id": "sh85023424",
            "label": "Calligraphy",
            "alt_labels": ["Penmanship", "Handwriting art"],
            "broader": [],
            "narrower": ["sh85018909", "sh85023425"],
            "scope": "General works on the art of beautiful writing.",
            "type": "topical"
        },
        {
            "id": "sh85026722",
            "label": "China",
            "alt_labels": ["People's Republic of China", "PRC", "Zhongguo"],
            "broader": ["sh85044923"],  # Asia
            "narrower": ["sh85026723", "sh85026724"],
            "scope": "Works on China as a geographic entity.",
            "type": "geographic"
        },
        {
            "id": "sh85026723",
            "label": "China -- History -- Ming dynasty, 1368-1644",
            "alt_labels": ["Ming dynasty China"],
            "broader": ["sh85026722"],
            "narrower": [],
            "scope": "Historical period of Ming dynasty rule.",
            "type": "topical"
        },
        {
            "id": "gf2014026068",
            "label": "Handbooks and manuals",
            "alt_labels": ["Manuals", "Guidebooks", "How-to books"],
            "broader": [],
            "narrower": [],
            "scope": "Instructional works providing practical information.",
            "type": "genre_form"
        },
        {
            "id": "sh85011303",
            "label": "Art, Chinese",
            "alt_labels": ["Chinese art", "Art of China"],
            "broader": ["sh85007488"],  # Art, Asian
            "narrower": ["sh85018909"],
            "scope": "Works on art originating in China.",
            "type": "topical"
        },
        {
            "id": "sh85013838",
            "label": "Books",
            "alt_labels": ["Publications", "Printed books"],
            "broader": [],
            "narrower": ["gf2014026068"],
            "scope": "General works about books as physical objects.",
            "type": "topical"
        },
    ]
    
    # Add more synthetic subjects to reach desired count
    for i in range(len(test_subjects), count):
        test_subjects.append({
            "id": f"sh{85000000 + i:08d}",
            "label": f"Test Subject {i}",
            "alt_labels": [f"Alternative {i}", f"Variant {i}"],
            "broader": [],
            "narrower": [],
            "scope": f"Synthetic test subject number {i}.",
            "type": "topical"
        })
    
    # Build RDF graph
    for subj in test_subjects[:count]:
        uri = URIRef(f"http://id.loc.gov/authorities/subjects/{subj['id']}")
        
        # Add type
        g.add((uri, RDF.type, SKOS.Concept))
        
        # Add prefLabel
        g.add((uri, SKOS.prefLabel, Literal(subj['label'], lang='en')))
        
        # Add altLabels
        for alt in subj['alt_labels']:
            g.add((uri, SKOS.altLabel, Literal(alt, lang='en')))
        
        # Add broader terms
        for broader_id in subj['broader']:
            broader_uri = URIRef(f"http://id.loc.gov/authorities/subjects/{broader_id}")
            g.add((uri, SKOS.broader, broader_uri))
        
        # Add narrower terms
        for narrower_id in subj['narrower']:
            narrower_uri = URIRef(f"http://id.loc.gov/authorities/subjects/{narrower_id}")
            g.add((uri, SKOS.narrower, narrower_uri))
        
        # Add scope note
        if subj['scope']:
            g.add((uri, SKOS.scopeNote, Literal(subj['scope'], lang='en')))
    
    return g


def main():
    parser = argparse.ArgumentParser(
        description='Generate synthetic LCSH test data'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/test_lcsh.rdf',
        help='Output RDF file path (default: data/test_lcsh.rdf)'
    )
    parser.add_argument(
        '--count',
        type=int,
        default=100,
        help='Number of test subjects to generate (default: 100)'
    )
    parser.add_argument(
        '--format',
        type=str,
        default='xml',
        choices=['xml', 'n3', 'turtle', 'nt'],
        help='RDF output format (default: xml)'
    )
    
    args = parser.parse_args()
    
    print("🧪 Generating synthetic LCSH test data...")
    print(f"   Count: {args.count}")
    print(f"   Format: {args.format}")
    print(f"   Output: {args.output}")
    
    # Generate graph
    g = generate_test_lcsh(args.count)
    
    # Create output directory
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Serialize to file
    g.serialize(destination=str(output_path), format=args.format)
    
    print(f"✅ Generated {len(g)} triples")
    print(f"✅ Saved to: {output_path}")
    print()
    print("📋 Next steps:")
    print(f"   1. Test the importer:")
    print(f"      python scripts/lcsh_importer_v2.py --input {args.output} --limit 50")
    print()
    print(f"   2. Verify in Weaviate:")
    print(f"      python -c 'from authority_search import authority_search; authority_search.connect(); print(authority_search.get_stats())'")


if __name__ == '__main__':
    main()
