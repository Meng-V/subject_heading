# Testing Guide: LCSH Importer Implementation

This guide walks you through testing the new LCSH importer infrastructure.

## 🎯 What Was Implemented

✅ **Enhanced Weaviate Schema**:
- `subject_type`: "topical" | "geographic" | "genre_form"
- `alt_labels`: Array of alternative labels
- `broader_terms`: Array of broader term URIs
- `narrower_terms`: Array of narrower term URIs
- `scope_note`: Usage notes and scope description

✅ **Comprehensive LCSH Importer** (`scripts/lcsh_importer_v2.py`):
- RDF/XML, N-Triples, Turtle, JSON-LD format support
- Automatic subject type detection
- Rich embeddings (label + altLabels + scopeNote)
- Progress tracking with tqdm
- Error handling and logging
- Checkpoint/resume support
- Batch processing for memory efficiency

✅ **Test Data Generator** (`scripts/generate_test_sample.py`):
- Creates synthetic LCSH data for testing
- No need to download full dataset initially
- Realistic subject relationships and metadata

---

## 🚀 Quick Start: Test with Synthetic Data

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs the new requirements:
- `rdflib>=7.0.0` - RDF parsing
- `tqdm>=4.66.0` - Progress bars

### Step 2: Generate Test Data

```bash
# Generate 100 synthetic LCSH subjects
python scripts/generate_test_sample.py --output data/test_lcsh.rdf --count 100
```

**Output**:
```
🧪 Generating synthetic LCSH test data...
   Count: 100
   Format: xml
   Output: data/test_lcsh.rdf
✅ Generated 424 triples
✅ Saved to: data/test_lcsh.rdf
```

### Step 3: Reset Weaviate Schema (if needed)

```bash
# Stop and remove volumes to reset
docker-compose down -v
docker-compose up -d
```

Wait 5-10 seconds for Weaviate to start.

### Step 4: Test the Importer

```bash
# Import test data with limit
python scripts/lcsh_importer_v2.py --input data/test_lcsh.rdf --limit 50 --batch-size 10
```

**Expected Output**:
```
============================================================
LCSH Authority Importer
============================================================
Input file: data/test_lcsh.rdf
Limit: 50
Batch size: 10
============================================================
INFO - Connecting to Weaviate...
INFO - Initializing schema...
INFO - Parsing LCSH data...
INFO - Loaded 424 triples
INFO - Found 100 SKOS concepts
Parsing authorities: 100%|████████████| 100/100
INFO - Successfully parsed 100 authorities
INFO - Indexing 50 authorities...
Indexing batches: 100%|████████████| 5/5
INFO - Batch 1/5: 10/10 indexed successfully
INFO - Batch 2/5: 10/10 indexed successfully
...
============================================================
Import Complete!
============================================================
Total processed: 50
Total errors: 0
Success rate: 100.0%

Weaviate Statistics:
  lcsh: 50 records
  fast: 0 records
============================================================
```

### Step 5: Verify the Data

```python
# Test search with new schema fields
from authority_search import authority_search

authority_search.connect()

# Search for a test subject
results = await authority_search.search_authorities(
    "Chinese calligraphy",
    vocabularies=["lcsh"],
    limit=3
)

for r in results:
    print(f"Label: {r.label}")
    print(f"Type: {r.subject_type}")  # NEW!
    print(f"Alt labels: {r.alt_labels}")  # NEW!
    print(f"Scope: {r.scope_note}")  # NEW!
    print(f"Score: {r.score}")
    print()
```

---

## 📊 Testing Checklist

### ✅ Infrastructure Tests

- [ ] **Schema Creation**
  ```bash
  python -c "from authority_search import authority_search; authority_search.connect(); authority_search.initialize_schemas()"
  ```
  - Should create LCSHSubject and FASTSubject collections
  - Should include new fields: subject_type, alt_labels, broader_terms, narrower_terms, scope_note

- [ ] **Synthetic Data Generation**
  ```bash
  python scripts/generate_test_sample.py --count 100
  ```
  - Should create data/test_lcsh.rdf
  - Should generate ~400-500 RDF triples

- [ ] **Import 50 Records**
  ```bash
  python scripts/lcsh_importer_v2.py --input data/test_lcsh.rdf --limit 50
  ```
  - Should process without errors
  - Success rate should be 100%
  - Weaviate stats should show 50 LCSH records

- [ ] **Search with New Fields**
  - Search for "Calligraphy, Chinese"
  - Verify subject_type is "topical"
  - Verify alt_labels contains "Chinese calligraphy"
  - Verify scope_note is not empty

### ✅ Edge Case Tests

- [ ] **Empty Alt Labels**
  - Some subjects have no alt labels
  - Should not cause errors

- [ ] **No Broader/Narrower Terms**
  - Top-level subjects have no broader terms
  - Should handle gracefully

- [ ] **Long Scope Notes**
  - Some scope notes are multi-paragraph
  - Should embed and store correctly

- [ ] **Special Characters**
  - Subject labels with dashes, parentheses
  - "China -- History -- Ming dynasty, 1368-1644"
  - Should parse and embed correctly

### ✅ Performance Tests

- [ ] **Batch Processing**
  ```bash
  python scripts/lcsh_importer_v2.py --input data/test_lcsh.rdf --batch-size 5
  ```
  - Should process in multiple batches
  - Each batch should show progress

- [ ] **Checkpoint Save/Resume**
  ```bash
  # First run (will be interrupted)
  python scripts/lcsh_importer_v2.py --input data/test_lcsh.rdf --checkpoint &
  sleep 10
  kill %1
  
  # Resume
  python scripts/lcsh_importer_v2.py --input data/test_lcsh.rdf --resume logs/checkpoint_batch_*.json
  ```
  - Should resume from where it left off
  - Should not re-process already indexed records

- [ ] **Memory Usage**
  - Monitor with: `python scripts/lcsh_importer_v2.py --input data/test_lcsh.rdf --limit 100`
  - Should stay under 500MB for 100 records

---

## 🔍 Verification Queries

### Check Schema

```python
from authority_search import authority_search
import weaviate

authority_search.connect()
collection = authority_search.client.collections.get("LCSHSubject")

# Get collection config
config = collection.config.get()
print("Properties:")
for prop in config.properties:
    print(f"  - {prop.name}: {prop.data_type}")
```

**Expected Properties**:
- label (TEXT)
- uri (TEXT)
- vocabulary (TEXT)
- subject_type (TEXT) ← **NEW**
- alt_labels (TEXT_ARRAY) ← **NEW**
- broader_terms (TEXT_ARRAY) ← **NEW**
- narrower_terms (TEXT_ARRAY) ← **NEW**
- scope_note (TEXT) ← **NEW**
- language (TEXT)

### Check Data Quality

```python
# Get a random record and inspect
collection = authority_search.client.collections.get("LCSHSubject")
result = collection.query.fetch_objects(limit=1)

for obj in result.objects:
    props = obj.properties
    print(f"Label: {props['label']}")
    print(f"Type: {props.get('subject_type', 'unknown')}")
    print(f"Alt labels ({len(props.get('alt_labels', []))}): {props.get('alt_labels', [])}")
    print(f"Broader terms: {len(props.get('broader_terms', []))}")
    print(f"Narrower terms: {len(props.get('narrower_terms', []))}")
    print(f"Scope note length: {len(props.get('scope_note', ''))}")
```

---

## 🐛 Troubleshooting

### Issue: "rdflib not installed"
```bash
pip install rdflib tqdm
```

### Issue: "Collection already exists" error
```bash
# Reset Weaviate
docker-compose down -v
docker-compose up -d
# Wait 10 seconds
python scripts/lcsh_importer_v2.py --input data/test_lcsh.rdf --limit 10
```

### Issue: Embeddings taking too long
- Check OpenAI API key in `.env`
- Verify OPENAI_API_KEY is valid
- Check rate limits: https://platform.openai.com/account/rate-limits
- Reduce batch size: `--batch-size 10`

### Issue: Out of memory
- Reduce batch size: `--batch-size 50`
- Use --limit for testing: `--limit 100`
- Close other applications

### Issue: Parser can't find subjects
- Check RDF format matches file extension
- Try different format: `--format nt` or `--format xml`
- Validate RDF file with online tools

---

## 📈 Next Steps After Testing

Once all tests pass with synthetic data:

1. **Download Real LCSH Sample** (10-50K records)
   - Go to: https://id.loc.gov/download/
   - Download "Subjects (LCSH)" in N-Triples format
   - Test with: `--limit 10000`

2. **Benchmark Performance**
   - Time import of 10K records
   - Extrapolate to full dataset (460K)
   - Plan indexing window (overnight? weekend?)

3. **Full Import**
   - Schedule during low-usage period
   - Use `--checkpoint` for safety
   - Monitor logs in `logs/` directory

4. **Verify Quality**
   - Run evaluation script (when ready)
   - Compare search results before/after
   - Test with real cataloging use cases

---

## 🎓 Understanding the Data Model

### Subject Type Detection

The importer automatically detects subject types:

| Type | Detection Method | Example |
|------|------------------|---------|
| **topical** | Default, or subject matter | "Calligraphy, Chinese" |
| **geographic** | Place names, subdivisions | "China -- Beijing" |
| **genre_form** | Keywords: handbooks, manuals, fiction | "Handbooks and manuals" |

### Embedding Generation

Embeddings are created from:
```
label + alt_labels[0] + alt_labels[1] + ... + scope_note
```

This creates rich semantic context for better matching.

Example:
```
"Calligraphy, Chinese | Chinese calligraphy | Shufa | Here are entered works on the art of writing Chinese characters."
```

### Broader/Narrower Relationships

Stored as URI arrays:
```python
broader_terms: [
    "http://id.loc.gov/authorities/subjects/sh85023424",  # Calligraphy
    "http://id.loc.gov/authorities/subjects/sh85011303"   # Art, Chinese
]
```

Future enhancement: Resolve URIs to labels for better embedding.

---

**Last Updated**: 2025-12-03
**Status**: Ready for testing!
