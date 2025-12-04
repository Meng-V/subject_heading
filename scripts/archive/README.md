# Scripts Directory

This directory contains utility scripts for data import, evaluation, and maintenance.

## Data Import Scripts

### `lcsh_importer.py` (TODO)
Import complete LCSH authority data from Library of Congress.

**Usage**:
```bash
python scripts/lcsh_importer.py --input data/lcsh_dump.rdf --batch-size 1000
```

**What it does**:
1. Downloads/parses LCSH RDF/JSON files from id.loc.gov
2. Extracts prefLabel, altLabel, broader, narrower, scopeNote
3. Generates embeddings using text-embedding-3-large
4. Batch inserts into Weaviate LCSHSubject collection

**Expected output**:
- ~460,000 LCSH authority records indexed
- Embedding time: ~2-3 hours (with batching)
- Storage: ~5-10 GB in Weaviate

---

### `fast_importer.py` (TODO)
Import complete FAST authority data from OCLC.

**Usage**:
```bash
python scripts/fast_importer.py --input data/fast_dump.nt --batch-size 1000
```

**What it does**:
1. Parses FAST authority files
2. Extracts similar fields to LCSH
3. Batch inserts into Weaviate FASTSubject collection

**Expected output**:
- ~1.9 million FAST authority records indexed
- Embedding time: ~8-10 hours
- Storage: ~20-30 GB in Weaviate

---

## Evaluation Scripts

### `evaluate.py` (TODO)
Evaluate system performance against gold-standard MARC records.

**Usage**:
```bash
# Evaluate against test set
python scripts/evaluate.py --gold-data data/gold_records.json --output results.json

# Verbose mode with examples
python scripts/evaluate.py --gold-data data/gold_records.json --verbose
```

**Metrics reported**:
- Precision / Recall
- Top-1 accuracy
- Top-3 coverage
- Per-vocabulary breakdown (LCSH vs FAST)
- Per-subject-type breakdown (topical vs geographic vs genre)
- Detailed error examples

**Output format** (`results.json`):
```json
{
  "total_books": 100,
  "total_subjects": 450,
  "exact_matches": 320,
  "top_1_accuracy": 0.71,
  "top_3_coverage": 0.89,
  "per_vocab": {
    "lcsh": {"precision": 0.75, "recall": 0.68},
    "fast": {"precision": 0.72, "recall": 0.65}
  },
  "errors": [
    {
      "book_title": "History of Ming Dynasty",
      "expected": "China -- History -- Ming dynasty, 1368-1644",
      "proposed": "China -- History",
      "reason": "Missing chronological subdivision"
    }
  ]
}
```

---

### `active_learning.py` (TODO)
Identify low-confidence cases for prioritized cataloger review.

**Usage**:
```bash
# Find cases with confidence < 0.6
python scripts/active_learning.py --threshold 0.6 --limit 50

# Export to CSV for review
python scripts/active_learning.py --threshold 0.6 --export review_queue.csv
```

**Output**:
- List of books/subjects needing human review
- Sorted by confidence score (lowest first)
- Includes all candidate authorities for comparison

---

## Maintenance Scripts

### `reindex_authorities.py` (TODO)
Re-generate embeddings for existing authorities (when switching embedding models).

**Usage**:
```bash
# Re-embed all LCSH records
python scripts/reindex_authorities.py --vocab lcsh

# Batch processing
python scripts/reindex_authorities.py --vocab fast --batch-size 500
```

---

### `validate_schema.py` (TODO)
Validate Weaviate schema and check for inconsistencies.

**Usage**:
```bash
python scripts/validate_schema.py
```

**Checks**:
- All collections exist
- Required properties present
- Vector dimensions correct
- No orphaned records

---

### `export_feedback.py` (TODO)
Export cataloger feedback logs for analysis.

**Usage**:
```bash
# Export all feedback to CSV
python scripts/export_feedback.py --output feedback_analysis.csv

# Filter by date range
python scripts/export_feedback.py --from 2025-01-01 --to 2025-03-31
```

---

## Data Sources

### LCSH
- **Source**: https://id.loc.gov/download/
- **Format**: RDF/XML, NT, JSON-LD
- **Size**: ~460,000 headings
- **Update frequency**: Weekly

### FAST
- **Source**: https://www.oclc.org/research/areas/data-science/fast.html
- **Format**: MARC, RDF, CSV
- **Size**: ~1.9 million headings
- **Update frequency**: Quarterly

---

## Environment Variables

These scripts use the same `.env` configuration as the main application:

```bash
OPENAI_API_KEY=sk-...           # For embeddings
WEAVIATE_URL=http://localhost:8081
EMBEDDING_MODEL=text-embedding-3-large
```

---

## Development Guidelines

### Adding a New Import Script

1. Create `scripts/your_vocab_importer.py`
2. Implement these functions:
   ```python
   def parse_authority_file(filepath: str) -> Iterator[AuthorityRecord]:
       """Parse source file and yield authority records."""
   
   def generate_embedding(record: AuthorityRecord) -> List[float]:
       """Generate embedding for the record."""
   
   def batch_insert(records: List[AuthorityRecord], batch_size: int = 100):
       """Insert records into Weaviate in batches."""
   ```
3. Add progress bar using `tqdm`
4. Add error handling and logging
5. Write to `logs/import_{vocab}_{timestamp}.log`

### Adding a New Evaluation Script

1. Create `scripts/evaluate_xyz.py`
2. Implement:
   ```python
   def load_gold_data(filepath: str) -> List[GoldRecord]:
       """Load gold-standard data."""
   
   def run_pipeline(record: GoldRecord) -> PipelineOutput:
       """Run the subject heading pipeline."""
   
   def compute_metrics(gold: List, proposed: List) -> Dict:
       """Compare and compute metrics."""
   
   def generate_report(metrics: Dict):
       """Print and save evaluation report."""
   ```
3. Save results to `data/evaluation/` directory

---

## Planned Scripts (Priority Order)

1. **Week 1**: `evaluate.py` - Basic evaluation framework
2. **Week 2**: `lcsh_importer.py` - LCSH data import
3. **Week 3**: `fast_importer.py` - FAST data import
4. **Week 4**: `active_learning.py` - Low-confidence detection
5. **Month 2**: `reindex_authorities.py` - Re-embedding tool
6. **Month 2**: `export_feedback.py` - Feedback analysis

---

**Last Updated**: 2025-12-03
