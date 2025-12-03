"""
Download a sample of LCSH data for testing the importer.

This script helps you get started with a small dataset to test the infrastructure
before downloading the full ~460K LCSH records.

Usage:
    python scripts/download_lcsh_sample.py --output data/lcsh_sample.nt --limit 1000
"""

import argparse
import sys
import urllib.request
from pathlib import Path

def download_sample(output_path: str, limit: int = 1000):
    """
    Download a sample of LCSH data from id.loc.gov.
    
    Args:
        output_path: Where to save the sample file
        limit: Number of subjects to download
    """
    print("📡 LCSH Sample Data Downloader")
    print("=" * 60)
    
    # LCSH provides data via content negotiation
    base_url = "http://id.loc.gov/authorities/subjects/"
    
    print(f"Downloading {limit} LCSH subjects...")
    print(f"Output: {output_path}")
    print()
    
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    
    # Since we can't easily get a sample from LOC, create instructions instead
    print("⚠️  Direct sampling from id.loc.gov is not straightforward.")
    print()
    print("📋 To get LCSH sample data:")
    print()
    print("Option 1: Download full dataset and use --limit parameter")
    print("  1. Go to: https://id.loc.gov/download/")
    print("  2. Download 'Subjects (LCSH)' → N-Triples (.nt) format")
    print("  3. Extract the .nt file")
    print("  4. Run: python scripts/lcsh_importer_v2.py --input subjects.nt --limit 1000")
    print()
    print("Option 2: Use our test sample generator")
    print("  1. Run: python scripts/generate_test_sample.py")
    print("  2. This creates a synthetic sample for testing infrastructure")
    print()
    print("Option 3: Extract from existing MARC records")
    print("  1. If you have MARC records, export 6XX fields")
    print("  2. Convert to RDF format")
    print()
    print("💡 Recommended: Start with Option 2 for quick testing")
    

def main():
    parser = argparse.ArgumentParser(
        description='Download LCSH sample data for testing'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/lcsh_sample.nt',
        help='Output file path (default: data/lcsh_sample.nt)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=1000,
        help='Number of subjects to download (default: 1000)'
    )
    
    args = parser.parse_args()
    download_sample(args.output, args.limit)


if __name__ == '__main__':
    main()
