# Quick Start: LCSH Importer

**5-minute guide to get started with the new authority importer**

---

## ✅ Prerequisites

```bash
# You should already have:
- Python 3.11+ with venv
- Docker + docker-compose running
- OpenAI API key in .env
```

---

## 🚀 Quick Test (5 minutes)

### Step 1: Install Dependencies (30 seconds)
```bash
./venv/bin/pip install rdflib tqdm
```

### Step 2: Generate Test Data (10 seconds)
```bash
./venv/bin/python scripts/generate_test_sample.py --count 50
```

Output: `data/test_lcsh.rdf` created with 50 test subjects

### Step 3: Reset Weaviate (20 seconds)
```bash
docker-compose down -v && docker-compose up -d
sleep 10  # Wait for Weaviate to start
```

### Step 4: Import Test Data (30 seconds)
```bash
./venv/bin/python scripts/lcsh_importer_v2.py \
    --input data/test_lcsh.rdf \
    --limit 20 \
    --batch-size 5
```

**Expected Output**:
```
✅ Total processed: 20
✅ Total errors: 0
✅ Success rate: 100.0%

Weaviate Statistics:
  lcsh: 20 records
```

### Step 5: Verify (30 seconds)
```bash
./venv/bin/python -c "
from authority_search import authority_search
authority_search.connect()
stats = authority_search.get_stats()
print(f'✅ LCSH records: {stats.get(\"lcsh\", 0)}')
"
```

---

## 📋 What You Just Did

✅ **Enhanced Schema**: Added subject_type, alt_labels, broader_terms, narrower_terms, scope_note  
✅ **Test Data**: Generated synthetic LCSH subjects with realistic relationships  
✅ **Import Infrastructure**: Successfully imported 20 records with embeddings  
✅ **Verification**: Confirmed records are searchable in Weaviate

---

## 🎯 Next Steps

### Option A: Import More Test Data
```bash
# Try 100 records
./venv/bin/python scripts/generate_test_sample.py --count 100
./venv/bin/python scripts/lcsh_importer_v2.py --input data/test_lcsh.rdf --limit 100
```

### Option B: Download Real LCSH Data
1. Visit: https://id.loc.gov/download/
2. Download "Subjects (LCSH)" → N-Triples format
3. Extract the .nt file
4. Import:
   ```bash
   ./venv/bin/python scripts/lcsh_importer_v2.py \
       --input subjects.nt \
       --limit 10000 \
       --batch-size 500 \
       --checkpoint
   ```

### Option C: Test API with New Data
```bash
# Start API server
./venv/bin/python main.py

# In another terminal, run tests
./venv/bin/python test_api.py
```

The API should now have better authority matching due to:
- More comprehensive data
- Alternative labels improving recall
- Subject types for smarter 650/651/655 tagging

---

## 🐛 Troubleshooting

**Import fails?**
```bash
# Check Weaviate is running
docker ps

# Check logs
tail -f logs/lcsh_import_*.log
```

**No embeddings generated?**
```bash
# Verify OpenAI API key
grep OPENAI_API_KEY .env

# Test API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

**Out of memory?**
```bash
# Reduce batch size
./venv/bin/python scripts/lcsh_importer_v2.py \
    --input data/test_lcsh.rdf \
    --batch-size 10  # Smaller batches
```

---

## 📚 Full Documentation

- **Detailed Testing**: [TESTING_GUIDE.md](TESTING_GUIDE.md)
- **Implementation Details**: [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)
- **Next Features**: [NEXT_STEPS.md](NEXT_STEPS.md)
- **Full Roadmap**: [ROADMAP.md](ROADMAP.md)

---

## ✨ What's New

**Schema Enhancements**:
- `subject_type`: Enables smart 650/651/655 classification
- `alt_labels`: Improves search recall
- `broader_terms` / `narrower_terms`: Future hierarchical browsing
- `scope_note`: Context for better embeddings

**Importer Features**:
- Multi-format RDF support (XML, N-Triples, Turtle, JSON-LD)
- Automatic subject type detection
- Progress bars and logging
- Checkpoint/resume for long imports
- Batch processing for memory efficiency

---

**Time to complete**: 5 minutes  
**Cost**: ~$0.002 for 20 test records  
**Result**: Production-ready authority import system ✅
