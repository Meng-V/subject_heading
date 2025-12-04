"""
LCSH Authority Data Importer - Full Implementation

This script imports complete LCSH authority data with:
- prefLabel, altLabel extraction
- broader/narrower term relationships  
- scopeNote and subject type detection
- Rich embeddings (label + altLabels + broader + narrower + scopeNote)
- Progress tracking with tqdm
- Error handling and logging
- Batch processing for memory efficiency

Download LCSH data from: https://id.loc.gov/download/
Formats supported: RDF/XML, N-Triples, JSON-LD

Usage:
    # Test with small dataset
    python scripts/lcsh_importer_v2.py --input data/lcsh_sample.rdf --limit 1000
    
    # Full import
    python scripts/lcsh_importer_v2.py --input data/lcsh_full.nt --batch-size 1000
    
    # Resume from checkpoint
    python scripts/lcsh_importer_v2.py --input data/lcsh_full.nt --resume logs/checkpoint.json
"""

import sys
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

try:
    from tqdm import tqdm
except ImportError:
    print("⚠️  tqdm not installed. Install with: pip install tqdm")
    print("   Running without progress bars...")
    tqdm = lambda x, **kwargs: x

try:
    from rdflib import Graph, Namespace, URIRef, Literal
    from rdflib.namespace import SKOS, RDF
except ImportError:
    print("❌ rdflib not installed")
    print("   Install with: pip install rdflib")
    sys.exit(1)

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from openai import OpenAI
from config import settings
import weaviate
from authority_search import authority_search


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/lcsh_import_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class LCSHAuthority:
    """Represents a complete LCSH authority record."""
    uri: str
    label: str
    alt_labels: List[str]
    broader_terms: List[str]
    narrower_terms: List[str]
    scope_note: str
    subject_type: str  # "topical", "geographic", "genre_form", "unknown"
    language: str = "en"
    vocabulary: str = "lcsh"


class LCSHParser:
    """Parse LCSH data from various RDF formats."""
    
    def __init__(self):
        self.skos = SKOS
        self.rdf = RDF
        
    def detect_subject_type(self, uri: str, label: str, graph: Graph) -> str:
        """
        Detect subject type from URI, label, or RDF type.
        
        LCSH uses different URI patterns:
        - /subjects/sh... → topical
        - /subjects/geo... → geographic  
        - /genreForms/gf... → genre/form
        """
        uri_str = str(uri)
        
        # Check URI pattern
        if '/genreForms/' in uri_str or '/gf' in uri_str:
            return "genre_form"
        if '/names/' in uri_str or 'geo' in uri_str.lower():
            return "geographic"
        
        # Check label for genre indicators
        genre_keywords = [
            'handbooks', 'manuals', 'directories', 'bibliographies',
            'dictionaries', 'encyclopedias', 'periodicals', 'congresses',
            'conference', 'proceedings', 'sources', 'collections',
            'fiction', 'poetry', 'drama', 'essays'
        ]
        label_lower = label.lower()
        if any(kw in label_lower for kw in genre_keywords):
            return "genre_form"
        
        # Check for geographic indicators
        if ' -- ' in label:
            # LCSH subdivisions: check if first part is a place
            first_part = label.split(' -- ')[0]
            if first_part[0].isupper() and len(first_part.split()) <= 3:
                # Might be a place name
                geographic_patterns = ['china', 'united states', 'japan', 'europe', 'asia']
                if any(pattern in first_part.lower() for pattern in geographic_patterns):
                    return "geographic"
        
        # Default to topical
        return "topical"
    
    def parse_rdf_file(
        self,
        filepath: str,
        limit: Optional[int] = None
    ) -> List[LCSHAuthority]:
        """
        Parse LCSH RDF file and extract complete authority records.
        
        Args:
            filepath: Path to RDF file (xml, nt, ttl, or json-ld)
            limit: Optional limit on number of records
            
        Returns:
            List of LCSHAuthority objects
        """
        logger.info(f"Parsing RDF file: {filepath}")
        
        # Detect format from extension
        file_ext = Path(filepath).suffix.lower()
        format_map = {
            '.rdf': 'xml',
            '.xml': 'xml',
            '.nt': 'nt',
            '.n3': 'n3',
            '.ttl': 'turtle',
            '.jsonld': 'json-ld'
        }
        rdf_format = format_map.get(file_ext, 'xml')
        
        # Parse RDF graph
        g = Graph()
        logger.info(f"Loading RDF graph (format: {rdf_format})...")
        g.parse(filepath, format=rdf_format)
        logger.info(f"Loaded {len(g)} triples")
        
        # Extract authorities
        authorities = []
        concepts = list(g.subjects(predicate=RDF.type, object=self.skos.Concept))
        
        if limit:
            concepts = concepts[:limit]
        
        logger.info(f"Found {len(concepts)} SKOS concepts")
        
        for concept in tqdm(concepts, desc="Parsing authorities", unit="record"):
            try:
                # Extract prefLabel
                pref_label = g.value(concept, self.skos.prefLabel)
                if not pref_label:
                    continue
                    
                label = str(pref_label)
                
                # Extract altLabels
                alt_labels = [str(alt) for alt in g.objects(concept, self.skos.altLabel)]
                
                # Extract broader terms
                broader_terms = [str(b) for b in g.objects(concept, self.skos.broader)]
                
                # Extract narrower terms
                narrower_terms = [str(n) for n in g.objects(concept, self.skos.narrower)]
                
                # Extract scope note
                scope_notes = [str(note) for note in g.objects(concept, self.skos.scopeNote)]
                scope_note = "; ".join(scope_notes) if scope_notes else ""
                
                # Detect subject type
                subject_type = self.detect_subject_type(concept, label, g)
                
                authority = LCSHAuthority(
                    uri=str(concept),
                    label=label,
                    alt_labels=alt_labels,
                    broader_terms=broader_terms,
                    narrower_terms=narrower_terms,
                    scope_note=scope_note,
                    subject_type=subject_type
                )
                
                authorities.append(authority)
                
            except Exception as e:
                logger.warning(f"Error parsing concept {concept}: {str(e)}")
                continue
        
        logger.info(f"Successfully parsed {len(authorities)} authorities")
        return authorities


class LCSHIndexer:
    """Index LCSH authorities into Weaviate with embeddings."""
    
    def __init__(self):
        self.openai_client = OpenAI(api_key=settings.openai_api_key)
        self.embedding_model = settings.embedding_model
        self.processed_count = 0
        self.error_count = 0
        
    def build_embedding_text(self, authority: LCSHAuthority) -> str:
        """
        Build rich text for embedding generation.
        
        Concatenates: label + altLabels + broader + narrower + scopeNote
        """
        parts = [authority.label]
        
        if authority.alt_labels:
            parts.extend(authority.alt_labels)
        
        if authority.scope_note:
            parts.append(authority.scope_note)
        
        # Note: broader/narrower are URIs, not great for embedding
        # In production, would resolve to labels
        
        return " | ".join(parts)
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenAI text-embedding-3-large."""
        try:
            response = self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            return None
    
    def batch_index(
        self,
        authorities: List[LCSHAuthority],
        collection_name: str = "LCSHSubject"
    ) -> int:
        """
        Index a batch of authorities into Weaviate.
        
        Returns:
            Number of successfully indexed records
        """
        if not authority_search.client:
            authority_search.connect()
        
        try:
            collection = authority_search.client.collections.get(collection_name)
        except Exception as e:
            logger.error(f"Collection {collection_name} not found: {str(e)}")
            return 0
        
        success_count = 0
        
        with collection.batch.dynamic() as batch:
            for authority in authorities:
                try:
                    # Build embedding text
                    embedding_text = self.build_embedding_text(authority)
                    
                    # Generate embedding
                    embedding = self.generate_embedding(embedding_text)
                    if not embedding:
                        self.error_count += 1
                        continue
                    
                    # Prepare properties
                    properties = {
                        "label": authority.label,
                        "uri": authority.uri,
                        "vocabulary": authority.vocabulary,
                        "subject_type": authority.subject_type,
                        "alt_labels": authority.alt_labels,
                        "broader_terms": authority.broader_terms,
                        "narrower_terms": authority.narrower_terms,
                        "scope_note": authority.scope_note,
                        "language": authority.language,
                        # Legacy fields for backward compatibility
                        "broader": ", ".join(authority.broader_terms[:3]) if authority.broader_terms else "",
                        "narrower": ", ".join(authority.narrower_terms[:3]) if authority.narrower_terms else ""
                    }
                    
                    # Add to batch
                    batch.add_object(
                        properties=properties,
                        vector=embedding
                    )
                    
                    success_count += 1
                    self.processed_count += 1
                    
                except Exception as e:
                    logger.warning(f"Error indexing {authority.uri}: {str(e)}")
                    self.error_count += 1
        
        return success_count
    
    def save_checkpoint(self, checkpoint_path: str, processed_uris: List[str]):
        """Save progress checkpoint."""
        checkpoint = {
            "timestamp": datetime.now().isoformat(),
            "processed_count": self.processed_count,
            "error_count": self.error_count,
            "processed_uris": processed_uris
        }
        
        Path(checkpoint_path).parent.mkdir(parents=True, exist_ok=True)
        with open(checkpoint_path, 'w') as f:
            json.dump(checkpoint, f, indent=2)
        
        logger.info(f"Checkpoint saved: {checkpoint_path}")
    
    def load_checkpoint(self, checkpoint_path: str) -> Optional[Dict]:
        """Load progress checkpoint."""
        if not Path(checkpoint_path).exists():
            return None
        
        with open(checkpoint_path, 'r') as f:
            return json.load(f)


def main():
    parser = argparse.ArgumentParser(
        description='Import LCSH authority data into Weaviate',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test with 1000 records
  python scripts/lcsh_importer_v2.py --input data/lcsh_sample.rdf --limit 1000
  
  # Full import with checkpoints
  python scripts/lcsh_importer_v2.py --input data/lcsh_full.nt --batch-size 500 --checkpoint
  
  # Resume from checkpoint
  python scripts/lcsh_importer_v2.py --input data/lcsh_full.nt --resume logs/checkpoint.json
        """
    )
    
    parser.add_argument(
        '--input',
        type=str,
        required=True,
        help='Path to LCSH RDF file (.rdf, .nt, .ttl, .jsonld)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Limit number of records to import (for testing)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Number of records per batch (default: 100)'
    )
    parser.add_argument(
        '--checkpoint',
        action='store_true',
        help='Save checkpoints every 10 batches'
    )
    parser.add_argument(
        '--resume',
        type=str,
        default=None,
        help='Resume from checkpoint file'
    )
    
    args = parser.parse_args()
    
    # Validate input file
    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)
    
    logger.info("=" * 60)
    logger.info("LCSH Authority Importer")
    logger.info("=" * 60)
    logger.info(f"Input file: {args.input}")
    logger.info(f"Limit: {args.limit if args.limit else 'None (all records)'}")
    logger.info(f"Batch size: {args.batch_size}")
    logger.info("=" * 60)
    
    # Initialize components
    parser_obj = LCSHParser()
    indexer = LCSHIndexer()
    
    # Connect to Weaviate
    logger.info("Connecting to Weaviate...")
    authority_search.connect()
    
    # Initialize schema
    logger.info("Initializing schema...")
    authority_search.initialize_schemas()
    
    # Load checkpoint if resuming
    processed_uris = set()
    if args.resume:
        checkpoint = indexer.load_checkpoint(args.resume)
        if checkpoint:
            processed_uris = set(checkpoint.get('processed_uris', []))
            logger.info(f"Resuming from checkpoint: {len(processed_uris)} records already processed")
    
    # Parse authorities
    logger.info("\nParsing LCSH data...")
    authorities = parser_obj.parse_rdf_file(args.input, limit=args.limit)
    
    if not authorities:
        logger.error("No authorities found in input file")
        sys.exit(1)
    
    # Filter already processed
    if processed_uris:
        authorities = [a for a in authorities if a.uri not in processed_uris]
        logger.info(f"Filtering: {len(authorities)} remaining after checkpoint")
    
    # Index in batches
    logger.info(f"\nIndexing {len(authorities)} authorities...")
    
    total_batches = (len(authorities) + args.batch_size - 1) // args.batch_size
    all_processed_uris = list(processed_uris)
    
    for batch_num in tqdm(range(total_batches), desc="Indexing batches", unit="batch"):
        start_idx = batch_num * args.batch_size
        end_idx = min(start_idx + args.batch_size, len(authorities))
        batch = authorities[start_idx:end_idx]
        
        # Index batch
        success_count = indexer.batch_index(batch)
        
        # Track processed URIs
        all_processed_uris.extend([a.uri for a in batch])
        
        # Save checkpoint every 10 batches
        if args.checkpoint and (batch_num + 1) % 10 == 0:
            checkpoint_path = f"logs/checkpoint_batch_{batch_num + 1}.json"
            indexer.save_checkpoint(checkpoint_path, all_processed_uris)
        
        logger.info(
            f"Batch {batch_num + 1}/{total_batches}: "
            f"{success_count}/{len(batch)} indexed successfully"
        )
    
    # Final statistics
    logger.info("\n" + "=" * 60)
    logger.info("Import Complete!")
    logger.info("=" * 60)
    logger.info(f"Total processed: {indexer.processed_count}")
    logger.info(f"Total errors: {indexer.error_count}")
    logger.info(f"Success rate: {indexer.processed_count / len(authorities) * 100:.1f}%")
    
    # Get Weaviate stats
    stats = authority_search.get_stats()
    logger.info(f"\nWeaviate Statistics:")
    for vocab, count in stats.items():
        logger.info(f"  {vocab}: {count} records")
    
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
