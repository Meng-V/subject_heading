# 📥 Data Import Guide

**Complete guide to importing LCSH and FAST authorities into Weaviate**

---

## 📊 Overview

This guide covers:
- Downloading authority data
- Importing to Weaviate
- Monitoring import progress
- Optimizing performance
- Backup and recovery

---

## 📥 Download Source Data

### LCSH (Library of Congress Subject Headings)

**Download from LC:**
```bash
# Create data directory
mkdir -p data/lcsh

# Download subjects (3.2GB compressed, ~3.3GB uncompressed)
wget http://id.loc.gov/authorities/subjects.nt.skos.gz \
    -O data/lcsh/subjects.nt.gz

# Extract
gunzip data/lcsh/subjects.nt.gz

# Verify file
ls -lh data/lcsh/subjects.nt
# Expected: ~3.3GB, ~25.8 million lines
```

**Or use direct link:**
- **URL:** http://id.loc.gov/authorities/subjects.nt.skos
- **Format:** N-Triples (RDF)
- **Size:** ~3.3GB uncompressed
- **Records:** ~500,000 subject headings

### FAST (Faceted Application of Subject Terminology)

**Download from OCLC:**
```bash
# FAST authorities
wget http://experimental.worldcat.org/fast/fast-all.nt.zip \
    -O data/lcsh/fast-all.nt.zip

# Extract
unzip data/lcsh/fast-all.nt.zip -d data/lcsh/

# Verify
ls -lh data/lcsh/fast-all.nt
```

**Alternative:** FAST is also available via API (see below)

---

## 🚀 Import Methods

### Method 1: Quick Import (Testing)

**Import 1,000 records for testing:**

```bash
./venv/bin/python scripts/lcsh_importer_streaming.py \
    --input data/lcsh/subjects.nt \
    --limit 1000 \
    --batch-size 100
```

**Expected output:**
```
📊 Streaming Import from: data/lcsh/subjects.nt
🎯 Limit: 1000 records
📦 Batch size: 100

Processing: 100%|██████████| 1000/1000 [01:23<00:00, 12.0it/s]

✅ Import Summary
━━━━━━━━━━━━━━━━━━━
✅ Imported: 1000 subjects
⏱️  Time: 1m 23s
💰 Cost: ~$0.13
📊 Rate: ~12 subjects/sec
```

**Cost:** $0.13  
**Time:** 1-2 minutes  
**Use for:** Quick testing, development

---

### Method 2: Standard Import (Most Libraries)

**Import 20,000 records (85% coverage):**

```bash
./venv/bin/python scripts/lcsh_importer_streaming.py \
    --input data/lcsh/subjects.nt \
    --limit 20000 \
    --batch-size 500
```

**Expected output:**
```
📊 Streaming Import from: data/lcsh/subjects.nt
🎯 Limit: 20000 records
📦 Batch size: 500

Processing: 100%|██████████| 20000/20000 [27:45<00:00, 12.0it/s]

✅ Import Summary
━━━━━━━━━━━━━━━━━━━
✅ Imported: 20000 subjects
⏱️  Time: 27m 45s
💰 Cost: ~$2.60
📊 Rate: ~12 subjects/sec
```

**Cost:** $2.60  
**Time:** 25-30 minutes  
**Coverage:** ~85% of common subjects  
**Use for:** Most academic and public libraries

---

### Method 3: Large Import (Research Libraries)

**Import 100,000 records (99% coverage):**

```bash
./venv/bin/python scripts/lcsh_importer_streaming.py \
    --input data/lcsh/subjects.nt \
    --limit 100000 \
    --batch-size 1000 \
    --checkpoint
```

**With checkpoint feature:**
- Saves progress every 10,000 records
- Can resume if interrupted
- Creates checkpoint files in `data/records/checkpoints/`

**Expected output:**
```
📊 Streaming Import with Checkpointing
🎯 Limit: 100000 records
📦 Batch size: 1000
💾 Checkpoint: Every 10000 records

Processing: 100%|██████████| 100000/100000 [2:18:30<00:00, 12.0it/s]

✅ Import Summary
━━━━━━━━━━━━━━━━━━━
✅ Imported: 100000 subjects
⏱️  Time: 2h 18m 30s
💰 Cost: ~$13.00
📊 Rate: ~12 subjects/sec
💾 Checkpoints: 10 saved
```

**Cost:** $13.00  
**Time:** 2-3 hours  
**Coverage:** ~99% of subjects  
**Use for:** Large research libraries, comprehensive coverage

---

### Method 4: Full Import (Complete Dataset)

**Import all 500,000 LCSH records:**

```bash
./venv/bin/python scripts/lcsh_importer_streaming.py \
    --input data/lcsh/subjects.nt \
    --batch-size 1000 \
    --checkpoint \
    --parallel 4
```

**Expected:**
```
📊 Full LCSH Import (Parallel Mode)
🎯 Records: ~500000
📦 Batch size: 1000
💾 Checkpoint: Enabled
🔄 Workers: 4

Processing: 100%|██████████| 500000/500000 [6:55:20<00:00, 20.1it/s]

✅ Import Summary
━━━━━━━━━━━━━━━━━━━
✅ Imported: 500000 subjects
⏱️  Time: 6h 55m
💰 Cost: ~$65.00
📊 Rate: ~20 subjects/sec
💾 Checkpoints: 50 saved
```

**Cost:** $65.00  
**Time:** 6-8 hours  
**Coverage:** 100%  
**Use for:** National libraries, specialized research

---

## 📊 Import Script Options

### Command-Line Arguments

```bash
./venv/bin/python scripts/lcsh_importer_streaming.py --help
```

**Available options:**

| Argument | Default | Description |
|----------|---------|-------------|
| `--input` | Required | Path to N-Triples file |
| `--limit` | None | Max records to import (None = all) |
| `--batch-size` | 100 | Records per batch (100-1000) |
| `--checkpoint` | False | Enable checkpoint saving |
| `--checkpoint-interval` | 10000 | Records between checkpoints |
| `--resume` | None | Resume from checkpoint file |
| `--vocabulary` | lcsh | Vocabulary: lcsh or fast |
| `--parallel` | 1 | Number of parallel workers |
| `--skip-validation` | False | Skip RDF validation (faster) |
| `--verbose` | False | Detailed logging |

### Examples

**Resume interrupted import:**
```bash
./venv/bin/python scripts/lcsh_importer_streaming.py \
    --resume data/records/checkpoints/checkpoint_20000.json
```

**Import with verbose logging:**
```bash
./venv/bin/python scripts/lcsh_importer_streaming.py \
    --input data/lcsh/subjects.nt \
    --limit 5000 \
    --verbose
```

**Fast import (skip validation):**
```bash
./venv/bin/python scripts/lcsh_importer_streaming.py \
    --input data/lcsh/subjects.nt \
    --limit 50000 \
    --batch-size 1000 \
    --skip-validation
```

---

## 🔍 Monitoring Import

### Real-Time Progress

The import script shows:
- **Progress bar** with percentage and ETA
- **Current rate** (subjects/second)
- **Estimated cost** (updated in real-time)
- **Time elapsed**

```
Processing: 45%|████▌     | 9000/20000 [12:30<13:45, 12.0it/s]
💰 Estimated cost so far: $1.17
```

### Check Weaviate Status

**During import:**
```bash
# In another terminal
./venv/bin/python scripts/monitor_weaviate.py stats
```

**Output:**
```
📊 Weaviate Statistics
━━━━━━━━━━━━━━━━━━━━━━
Collection: LCSHSubject
  Total Records: 9123
  With Vectors: 9123 (100%)
  
Collection: FASTSubject
  Total Records: 0
  With Vectors: 0
```

### View Sample Records

```bash
# View 5 recently imported records
./venv/bin/python scripts/monitor_weaviate.py sample lcsh --limit 5
```

**Output:**
```
📚 Sample LCSH Records (5)
━━━━━━━━━━━━━━━━━━━━━━━

1. Calligraphy, Chinese
   URI: http://id.loc.gov/authorities/subjects/sh85018909
   Type: topical
   Vector: [0.234, -0.123, ...] (3072 dims)
   
2. Art, Chinese -- Ming-Qing dynasties, 1368-1912
   URI: http://id.loc.gov/authorities/subjects/sh85011304
   Type: topical
   Vector: [0.456, -0.234, ...] (3072 dims)
```

---

## ⚙️ Performance Optimization

### Batch Size Tuning

**Small batches (100-200):**
- ✅ Lower memory usage
- ✅ More stable
- ❌ Slower overall

**Large batches (500-1000):**
- ✅ Faster import
- ✅ Better throughput
- ❌ Higher memory usage
- ❌ Larger rollback on error

**Recommended:**
- Development: 100
- Production: 500-1000
- Memory-constrained: 250

### Parallel Processing

**Single worker (default):**
```bash
--parallel 1  # ~12 subjects/sec
```

**Multi-worker:**
```bash
--parallel 4  # ~20-25 subjects/sec
```

**Considerations:**
- More workers = faster but more API costs (parallel calls)
- OpenAI has rate limits (check your tier)
- Weaviate can handle 10+ workers

### Weaviate Performance

**Increase Weaviate memory:**

Edit `docker-compose.yml`:
```yaml
services:
  weaviate:
    environment:
      LIMIT_RESOURCES: 'false'
    deploy:
      resources:
        limits:
          memory: 8G    # Increase from default
```

**Restart Weaviate:**
```bash
docker-compose down
docker-compose up -d
```

---

## 💰 Cost Planning

### Cost Breakdown

**Per record:**
- Embedding generation: $0.00013 per subject
- OpenAI API only (Weaviate is free)

**Bulk costs:**

| Records | Cost | Time (est.) | Coverage |
|---------|------|-------------|----------|
| 1,000 | $0.13 | 1-2 min | 40% |
| 5,000 | $0.65 | 7 min | 65% |
| 10,000 | $1.30 | 14 min | 75% |
| **20,000** | **$2.60** | **28 min** | **85%** ✅ |
| 50,000 | $6.50 | 70 min | 95% |
| 100,000 | $13.00 | 2.3 hrs | 99% |
| 500,000 | $65.00 | 7 hrs | 100% |

### Budget Planning

**Recommended approach:**

1. **Start small** (1,000 records, $0.13)
   - Test system
   - Verify quality
   - Train users

2. **Scale to recommended** (20,000 records, $2.60)
   - Good coverage for most libraries
   - One-time cost
   - Permanent storage

3. **Expand as needed** (50,000+, $6.50+)
   - Based on usage patterns
   - Analyze search miss rate
   - Budget approved

---

## 🔄 Incremental Updates

### Add More Records Later

```bash
# Check current count
./venv/bin/python scripts/monitor_weaviate.py stats

# Import 10,000 more (on top of existing)
./venv/bin/python scripts/lcsh_importer_streaming.py \
    --input data/lcsh/subjects.nt \
    --limit 10000 \
    --skip-existing
```

**Note:** `--skip-existing` prevents duplicate imports

### Update Existing Records

```bash
# Re-import with updated data
./venv/bin/python scripts/lcsh_importer_streaming.py \
    --input data/lcsh/subjects_updated.nt \
    --limit 5000 \
    --update-mode
```

---

## 📦 Checkpoint System

### How Checkpoints Work

**Automatic saving:**
- Every 10,000 records (configurable)
- Saves to `data/records/checkpoints/`
- Includes: progress, batch state, statistics

**Checkpoint file format:**
```json
{
  "timestamp": "2024-12-05T14:30:00",
  "records_processed": 20000,
  "records_imported": 19987,
  "batch_size": 500,
  "vocabulary": "lcsh",
  "input_file": "data/lcsh/subjects.nt",
  "cost_estimate": 2.60,
  "last_uri": "http://id.loc.gov/authorities/subjects/sh85123456"
}
```

### Resume from Checkpoint

```bash
# List checkpoints
ls -lh data/records/checkpoints/

# Resume from specific checkpoint
./venv/bin/python scripts/lcsh_importer_streaming.py \
    --resume data/records/checkpoints/checkpoint_20000.json
```

**The script will:**
1. Load checkpoint state
2. Skip already-imported records
3. Continue from last position
4. Maintain same batch size and settings

---

## 🐛 Troubleshooting

### Issue 1: Out of Memory

**Symptoms:**
```
MemoryError: Unable to allocate array
```

**Solutions:**
```bash
# Reduce batch size
--batch-size 100

# Stop other applications
# Increase Docker memory allocation

# Use checkpointing
--checkpoint
```

### Issue 2: API Rate Limits

**Symptoms:**
```
openai.error.RateLimitError: Rate limit exceeded
```

**Solutions:**
```bash
# Reduce parallel workers
--parallel 1

# Add delays between batches (edit script)
# Upgrade OpenAI API tier

# Use smaller batches
--batch-size 250
```

### Issue 3: Connection Timeout

**Symptoms:**
```
weaviate.exceptions.WeaviateException: Connection timeout
```

**Solutions:**
```bash
# Restart Weaviate
docker-compose restart weaviate

# Check Weaviate logs
docker-compose logs weaviate

# Verify network
curl http://localhost:8081/v1/meta
```

### Issue 4: Corrupted Data

**Symptoms:**
```
ValueError: Invalid N-Triples format
```

**Solutions:**
```bash
# Skip validation (if you trust the source)
--skip-validation

# Download fresh copy
rm data/lcsh/subjects.nt
wget http://id.loc.gov/authorities/subjects.nt.skos

# Check file integrity
wc -l data/lcsh/subjects.nt
# Should be ~25.8 million lines
```

---

## 💾 Backup Before Large Imports

```bash
# Backup current Weaviate data
docker-compose stop weaviate

docker run --rm \
  -v subject_heading_weaviate_data:/data \
  -v $(pwd)/backups:/backup \
  ubuntu tar czf /backup/weaviate_pre_import_$(date +%Y%m%d).tar.gz /data

docker-compose start weaviate
```

**Restore if needed:**
```bash
docker-compose down

docker run --rm \
  -v subject_heading_weaviate_data:/data \
  -v $(pwd)/backups:/backup \
  ubuntu tar xzf /backup/weaviate_pre_import_20241205.tar.gz -C /

docker-compose up -d
```

---

## 📊 Post-Import Verification

### 1. Check Record Counts

```bash
./venv/bin/python scripts/monitor_weaviate.py stats
```

**Expected output:**
```
Collection: LCSHSubject
  Total Records: 20000
  With Vectors: 20000 (100%)
```

### 2. Test Search Quality

```bash
# Test common subjects
./venv/bin/python scripts/search_to_marc.py "Chinese calligraphy"
./venv/bin/python scripts/search_to_marc.py "World War II"
./venv/bin/python scripts/search_to_marc.py "Machine learning"
```

**Good results:**
- Confidence scores >75%
- Relevant headings
- Proper MARC format

### 3. Check Embedding Coverage

```bash
./venv/bin/python scripts/monitor_weaviate.py check-embeddings
```

**Should show:**
```
✅ All records have embeddings (100%)
📊 Vector dimensions: 3072
🎯 Embedding model: text-embedding-3-large
```

### 4. Sample Random Records

```bash
./venv/bin/python scripts/monitor_weaviate.py sample lcsh --limit 10 --random
```

**Verify:**
- URIs are valid LC authority URLs
- Labels are properly formatted
- Subdivisions are present (where applicable)
- No duplicate records

---

## 📈 Import Statistics

### Track Import Metrics

The import script outputs detailed stats:

```
✅ Import Summary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total Processed: 20000
Successfully Imported: 19987
Skipped (duplicates): 8
Failed (errors): 5
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Time Elapsed: 27m 45s
Average Rate: 12.0 subjects/sec
Total API Calls: 19987
Estimated Cost: $2.60
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Peak Memory: 245 MB
Batch Success Rate: 99.98%
```

### Log Files

Import logs saved to `logs/import_YYYYMMDD_HHMMSS.log`

**Contains:**
- Timestamp for each batch
- Error messages with context
- Checkpoint information
- Performance metrics

---

## 🚀 Best Practices

### Before Import

- [ ] Backup existing Weaviate data
- [ ] Verify sufficient disk space (10GB+)
- [ ] Check OpenAI API key is valid
- [ ] Test with small import first (1,000 records)
- [ ] Ensure stable internet connection

### During Import

- [ ] Monitor progress bar and rate
- [ ] Watch for error messages
- [ ] Keep terminal window open
- [ ] Don't stop Docker/Weaviate
- [ ] Have checkpoint enabled for large imports

### After Import

- [ ] Verify record counts match
- [ ] Test search quality with sample queries
- [ ] Check embedding coverage (should be 100%)
- [ ] Backup successful import
- [ ] Document import date and count

---

## 📅 Maintenance Schedule

### Weekly
- Monitor Weaviate disk usage
- Check application logs for errors

### Monthly
- Review search quality metrics
- Consider importing more records if needed
- Update to latest LC data (optional)

### Quarterly
- Backup Weaviate data
- Review cost vs. usage
- Evaluate coverage needs

### Annually
- Full LC data refresh (download latest subjects.nt)
- Re-import with updated records
- Archive old backups

---

## ✅ Quick Reference

**Quick import (testing):**
```bash
./venv/bin/python scripts/lcsh_importer_streaming.py \
    --input data/lcsh/subjects.nt --limit 1000
```

**Standard import (recommended):**
```bash
./venv/bin/python scripts/lcsh_importer_streaming.py \
    --input data/lcsh/subjects.nt --limit 20000 --batch-size 500
```

**Large import (with checkpoints):**
```bash
./venv/bin/python scripts/lcsh_importer_streaming.py \
    --input data/lcsh/subjects.nt --limit 100000 --batch-size 1000 --checkpoint
```

**Check status:**
```bash
./venv/bin/python scripts/monitor_weaviate.py stats
```

**Test search:**
```bash
./venv/bin/python scripts/search_to_marc.py "your topic"
```

---

**Last Updated:** December 5, 2025  
**Next:** [API_ENDPOINTS.md](API_ENDPOINTS.md) | [COST_CALCULATOR.md](COST_CALCULATOR.md)
