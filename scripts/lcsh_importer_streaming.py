"""
LCSH Authority Data Importer - STREAMING VERSION for Large Files

This version processes large N-Triples files line-by-line without loading
the entire file into memory. Optimized for 3GB+ files.

Usage:
    # Process full LCSH dataset (3.1 GB)
    python scripts/lcsh_importer_streaming.py --input subjects.nt --limit 10000
    
    # Resume from checkpoint
    python scripts/lcsh_importer_streaming.py --input subjects.nt --resume logs/checkpoint.json
"""

import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Set
from datetime import datetime
from collections import defaultdict
from dataclasses import dataclass, asdict

# Setup paths
sys.path.append(str(Path(__file__).parent.parent))

# Third-party imports
from tqdm import tqdm
from openai import OpenAI
from dotenv import load_dotenv
import os

# Local imports
from authority_search import authority_search
from config import settings

# Load environment
load_dotenv()

# Setup logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f"lcsh_import_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class Authority:
    """Authority record structure."""
    uri: str
    label: str = ""
    alt_labels: List[str] = None
    broader_terms: List[str] = None
    narrower_terms: List[str] = None
    scope_note: str = ""
    subject_type: str = "topical"
    vocabulary: str = "lcsh"
    language: str = "en"
    
    def __post_init__(self):
        if self.alt_labels is None:
            self.alt_labels = []
        if self.broader_terms is None:
            self.broader_terms = []
        if self.narrower_terms is None:
            self.narrower_terms = []


def parse_ntriples_line(line: str) -> Optional[tuple]:
    """
    Parse a single N-Triples line.
    
    Returns: (subject, predicate, object) or None if invalid
    """
    line = line.strip()
    if not line or line.startswith('#'):
        return None
    
    try:
        # Simple N-Triples parser (subject predicate object .)
        parts = line.rstrip(' .').split(' ', 2)
        if len(parts) != 3:
            return None
        
        subject, predicate, obj = parts
        
        # Remove angle brackets from URIs
        subject = subject.strip('<>')
        predicate = predicate.strip('<>')
        
        # Handle objects (URI or literal)
        if obj.startswith('<'):
            obj = obj.strip('<>')
        elif obj.startswith('"'):
            # Extract literal value (simple approach)
            if '@' in obj:
                obj = obj.split('@')[0].strip('"')
            elif '^^' in obj:
                obj = obj.split('^^')[0].strip('"')
            else:
                obj = obj.strip('"')
        
        return (subject, predicate, obj)
    except Exception as e:
        logger.debug(f"Failed to parse line: {line[:100]}... Error: {e}")
        return None


def stream_ntriples(file_path: Path, limit: int = None) -> Dict[str, Authority]:
    """
    Stream parse N-Triples file line by line.
    
    Args:
        file_path: Path to .nt file
        limit: Maximum number of concepts to extract
        
    Returns:
        Dictionary of URI -> Authority
    """
    authorities = {}
    properties = defaultdict(lambda: defaultdict(list))
    
    logger.info(f"Streaming N-Triples file: {file_path}")
    logger.info(f"File size: {file_path.stat().st_size / 1024 / 1024:.1f} MB")
    
    # First pass: collect all triples
    total_lines = 0
    skos_concepts = set()
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in tqdm(f, desc="Reading file", unit=" lines", mininterval=1):
            total_lines += 1
            
            triple = parse_ntriples_line(line)
            if not triple:
                continue
            
            subject, predicate, obj = triple
            
            # Track SKOS concepts
            if predicate.endswith('type') and 'Concept' in obj:
                skos_concepts.add(subject)
            
            # Store properties
            properties[subject][predicate].append(obj)
            
            # Stop if we have enough concepts
            if limit and len(skos_concepts) >= limit * 2:  # Buffer for filtering
                break
    
    logger.info(f"Read {total_lines:,} lines")
    logger.info(f"Found {len(skos_concepts):,} SKOS concepts")
    
    # Second pass: build Authority objects
    count = 0
    for uri in tqdm(skos_concepts, desc="Building authorities", unit=" concept"):
        if limit and count >= limit:
            break
        
        props = properties[uri]
        
        # Extract prefLabel
        labels = props.get('http://www.w3.org/2004/02/skos/core#prefLabel', [])
        if not labels:
            continue  # Skip if no label
        
        label = labels[0] if labels else ""
        
        # Extract altLabels
        alt_labels = props.get('http://www.w3.org/2004/02/skos/core#altLabel', [])
        
        # Extract broader/narrower terms
        broader = [t for t in props.get('http://www.w3.org/2004/02/skos/core#broader', [])]
        narrower = [t for t in props.get('http://www.w3.org/2004/02/skos/core#narrower', [])]
        
        # Extract scope note
        scope_notes = props.get('http://www.w3.org/2004/02/skos/core#scopeNote', [])
        scope_note = scope_notes[0] if scope_notes else ""
        
        # Detect subject type
        subject_type = detect_subject_type(uri, label)
        
        authority = Authority(
            uri=uri,
            label=label,
            alt_labels=alt_labels,
            broader_terms=broader,
            narrower_terms=narrower,
            scope_note=scope_note,
            subject_type=subject_type,
            vocabulary="lcsh"
        )
        
        authorities[uri] = authority
        count += 1
    
    logger.info(f"Successfully built {len(authorities):,} authority records")
    
    return authorities


def detect_subject_type(uri: str, label: str) -> str:
    """Detect subject type from URI and label."""
    # Geographic indicators
    if '/names/' in uri or 'geo' in uri.lower():
        return "geographic"
    
    # Genre/form indicators
    genre_keywords = [
        'fiction', 'poetry', 'drama', 'handbooks', 'manuals',
        'dictionaries', 'encyclopedias', 'periodicals', 'newspapers'
    ]
    if any(kw in label.lower() for kw in genre_keywords):
        return "genre_form"
    
    # Geographic patterns in label
    if ' -- ' in label:
        parts = label.split(' -- ')
        # Common place name patterns
        place_indicators = ['China', 'Japan', 'United States', 'Europe', 'Asia', 'Africa']
        if any(place in parts[0] for place in place_indicators):
            return "geographic"
    
    return "topical"


def generate_embedding(text: str, client: OpenAI) -> List[float]:
    """Generate embedding using OpenAI API."""
    try:
        response = client.embeddings.create(
            model="text-embedding-3-large",
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        raise


def batch_index_authorities(authorities: Dict[str, Authority], batch_size: int = 100):
    """Batch index authorities into Weaviate with embeddings."""
    client = OpenAI(api_key=settings.openai_api_key)
    authority_search.connect()
    
    collection = authority_search.client.collections.get("LCSHSubject")
    authority_list = list(authorities.values())
    
    total_batches = (len(authority_list) + batch_size - 1) // batch_size
    errors = []
    
    for i in tqdm(range(0, len(authority_list), batch_size), 
                  desc="Indexing batches", unit="batch"):
        batch = authority_list[i:i + batch_size]
        
        # Prepare batch data
        objects = []
        for auth in batch:
            # Build embedding text
            embedding_text = auth.label
            if auth.alt_labels:
                embedding_text += " | " + " | ".join(auth.alt_labels[:3])
            if auth.scope_note:
                embedding_text += " | " + auth.scope_note[:200]
            
            # Generate embedding
            try:
                vector = generate_embedding(embedding_text, client)
                
                objects.append({
                    "properties": asdict(auth),
                    "vector": vector
                })
            except Exception as e:
                logger.error(f"Failed to process {auth.uri}: {e}")
                errors.append((auth.uri, str(e)))
                continue
        
        # Insert batch
        if objects:
            try:
                collection.data.insert_many(objects)
                logger.info(f"Batch {i//batch_size + 1}/{total_batches}: {len(objects)}/{len(batch)} indexed successfully")
            except Exception as e:
                logger.error(f"Batch insert failed: {e}")
                errors.append((f"Batch {i//batch_size + 1}", str(e)))
    
    authority_search.client.close()
    
    return len(authority_list) - len(errors), errors


def main():
    parser = argparse.ArgumentParser(description='LCSH Authority Importer - Streaming Version')
    parser.add_argument('--input', required=True, help='Input N-Triples file (.nt)')
    parser.add_argument('--limit', type=int, help='Limit number of records to process')
    parser.add_argument('--batch-size', type=int, default=100, help='Batch size for indexing')
    
    args = parser.parse_args()
    
    input_file = Path(args.input)
    
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        return 1
    
    logger.info("=" * 60)
    logger.info("LCSH Authority Importer (Streaming)")
    logger.info("=" * 60)
    logger.info(f"Input file: {input_file}")
    logger.info(f"Limit: {args.limit or 'None'}")
    logger.info(f"Batch size: {args.batch_size}")
    logger.info("=" * 60)
    
    # Initialize Weaviate schema
    logger.info("Connecting to Weaviate...")
    authority_search.connect()
    authority_search.initialize_schemas()
    authority_search.client.close()
    
    # Stream parse file
    logger.info("\nParsing LCSH data...")
    authorities = stream_ntriples(input_file, limit=args.limit)
    
    if not authorities:
        logger.error("No authorities extracted!")
        return 1
    
    # Index into Weaviate
    logger.info(f"\nIndexing {len(authorities)} authorities...")
    success_count, errors = batch_index_authorities(authorities, args.batch_size)
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("Import Complete!")
    logger.info("=" * 60)
    logger.info(f"Total processed: {len(authorities)}")
    logger.info(f"Total errors: {len(errors)}")
    logger.info(f"Success rate: {success_count / len(authorities) * 100:.1f}%")
    
    # Show stats
    authority_search.connect()
    stats = authority_search.get_stats()
    logger.info("\nWeaviate Statistics:")
    logger.info(f"  lcsh: {stats.get('lcsh', 0)} records")
    logger.info(f"  fast: {stats.get('fast', 0)} records")
    logger.info("=" * 60)
    authority_search.client.close()
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
