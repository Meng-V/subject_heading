# Weaviate Monitoring & Cost Guide

## ✅ Your System Status

**Current Data**: 25 LCSH records with embeddings  
**Status**: ✅ Working perfectly  
**Embeddings**: ✅ Cached in Weaviate (permanent, no re-generation needed)

---

## 💰 Embedding Cost Model (IMPORTANT!)

### **Embeddings are ONE-TIME ONLY**

```
┌─────────────────────────────────────────────────────────┐
│  IMPORT (One-time cost)                                 │
│  ───────────────────────                                │
│  1. Download LCSH data (free)                           │
│  2. Generate embedding via OpenAI → $$$  (ONCE!)        │
│  3. Store in Weaviate → permanent cache                 │
│                                                          │
│  Cost: $0.13 per 1,000 records                          │
│  Your 25 records: ~$0.003 (already paid)                │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  SEARCH (Ongoing usage)                                 │
│  ──────────────────                                     │
│  1. User searches "Chinese calligraphy"                 │
│  2. Generate embedding for query → $0.00013             │
│  3. Compare with cached vectors → FREE!                 │
│  4. Return matches → FREE!                              │
│                                                          │
│  Cost: $0.00013 per search query                        │
│  100 searches: $0.013                                   │
│  1,000 searches: $0.13                                  │
└─────────────────────────────────────────────────────────┘
```

### **Cost Breakdown**

| Operation | Calls OpenAI API? | Cost | Frequency |
|-----------|------------------|------|-----------|
| **Import 1,000 LCSH records** | ✅ Yes (1,000 calls) | $0.13 | **Once** |
| **Store in Weaviate** | ❌ No | $0.00 | Once |
| **Search for topic** | ✅ Yes (1 call) | $0.00013 | Per search |
| **Re-search same topic** | ✅ Yes (1 call) | $0.00013 | Per search |
| **Match against stored records** | ❌ No | $0.00 | Every search |

### **Real-World Example**

```
Scenario: Import 460,000 LCSH records, use for 1 year

Import cost (one-time):
  460,000 records × $0.00013 = $59.80 (ONCE)

Search cost (ongoing):
  - 10 searches/day × 365 days = 3,650 searches/year
  - 3,650 × $0.00013 = $0.47/year

Total first year: $60.27
Total second year: $0.47 (just searches!)
Total third year: $0.47

✅ Embeddings are CACHED FOREVER in Weaviate!
```

---

## 🎛️ How to Monitor Your Data

### Method 1: Command-Line Tool (Recommended)

I created `scripts/monitor_weaviate.py` for you:

```bash
# Show statistics
./venv/bin/python scripts/monitor_weaviate.py stats

# View sample records
./venv/bin/python scripts/monitor_weaviate.py sample lcsh --limit 5

# Test search (costs $0.00013)
./venv/bin/python scripts/monitor_weaviate.py search "Chinese calligraphy"

# Verify embeddings are cached
./venv/bin/python scripts/monitor_weaviate.py check-embeddings
```

**Output Example**:
```
📊 Weaviate Statistics
============================================================
  LCSH      : 25 records
  FAST      : 0 records
============================================================
  TOTAL     : 25 records

📦 LCSHSubject
  Vector dimensions: 3072 (text-embedding-3-large)
  ✅ Embeddings are CACHED - no API calls for matching!
```

### Method 2: Weaviate Web Console

```bash
# Open in browser:
http://localhost:8081/v1/console
```

**Features**:
- Visual schema explorer
- Record browser
- Query builder
- Real-time statistics

### Method 3: Python Script

```python
from authority_search import authority_search

# Connect
authority_search.connect()

# Get stats
stats = authority_search.get_stats()
print(f"LCSH: {stats['lcsh']} records")
print(f"FAST: {stats['fast']} records")

# View a record
collection = authority_search.client.collections.get("LCSHSubject")
result = collection.query.fetch_objects(limit=1, include_vector=True)

record = result.objects[0]
print(f"Label: {record.properties['label']}")
print(f"Has embedding: {record.vector is not None}")
print(f"Vector dimensions: {len(record.vector)}")

# Close connection
authority_search.client.close()
```

---

## 🔍 Where Are Embeddings Stored?

### **Weaviate Database**

Location: Docker volume `subject_heading_weaviate_data`

```bash
# View Docker volumes
docker volume ls

# Check Weaviate container
docker ps | grep weaviate
```

### **Data Structure**

Each LCSH record in Weaviate contains:
```json
{
  "label": "Calligraphy, Chinese",
  "uri": "http://id.loc.gov/authorities/subjects/sh85018909",
  "vocabulary": "lcsh",
  "subject_type": "topical",
  "alt_labels": ["Chinese calligraphy", "Shufa"],
  "broader_terms": ["sh85023424"],
  "narrower_terms": ["sh85018910"],
  "scope_note": "Here are entered works...",
  
  // ⭐ THE EXPENSIVE PART (generated once, cached forever)
  "vector": [0.123456, -0.234567, ..., 0.345678]  // 3,072 dimensions
}
```

**Storage Size**:
- 1 record with embedding: ~15 KB
- 1,000 records: ~15 MB
- 460,000 LCSH records: ~6.9 GB
- 1.9M FAST records: ~28.5 GB

---

## ❓ FAQ: Embeddings & Caching

### Q: Do I pay every time I search?
**A**: Only $0.00013 to embed the search query. Matching against stored records is FREE.

### Q: Do embeddings expire?
**A**: No! They're stored permanently in Weaviate until you delete them.

### Q: What if I restart Docker?
**A**: Embeddings persist in the Docker volume. Safe to restart anytime.

### Q: What if I delete the volume?
**A**: You lose all embeddings. Must re-import and pay again.

### Q: Can I backup embeddings?
**A**: Yes! Backup the Docker volume:
```bash
# Export Weaviate data
docker run --rm \
  -v subject_heading_weaviate_data:/data \
  -v $(pwd)/backup:/backup \
  alpine tar czf /backup/weaviate_backup.tar.gz /data
```

### Q: Can I export embeddings to avoid re-generating?
**A**: Yes! Create a checkpoint file during import:
```bash
python scripts/lcsh_importer_v2.py \
  --input lcsh_full.nt \
  --checkpoint  # Saves progress + can resume
```

---

## 📊 Monitoring Best Practices

### 1. **Check Stats Regularly**
```bash
# Daily check
./venv/bin/python scripts/monitor_weaviate.py stats
```

### 2. **Monitor Import Progress**
```bash
# During large imports, check logs
tail -f logs/lcsh_import_*.log
```

### 3. **Verify Data Quality**
```bash
# Sample records after import
./venv/bin/python scripts/monitor_weaviate.py sample lcsh --limit 10
```

### 4. **Test Search Quality**
```bash
# Try real queries
./venv/bin/python scripts/monitor_weaviate.py search "China history Ming dynasty"
```

### 5. **Track Costs**

Create `logs/cost_tracking.txt`:
```
2025-12-03: Imported 25 LCSH records - $0.003
2025-12-04: 50 searches - $0.0065
2025-12-05: Imported 10,000 LCSH records - $1.30
2025-12-06: 100 searches - $0.013
---
Total: $1.32
```

---

## 🚨 Important: Don't Lose Your Embeddings!

### **Backup Strategy**

```bash
# Weekly backup
docker run --rm \
  -v subject_heading_weaviate_data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/weaviate_$(date +%Y%m%d).tar.gz /data
```

### **Restore from Backup**

```bash
# Stop Weaviate
docker-compose down

# Restore data
docker run --rm \
  -v subject_heading_weaviate_data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar xzf /backup/weaviate_20251203.tar.gz -C /

# Restart
docker-compose up -d
```

---

## 📈 Current System Status

Run this to see your current status:

```bash
./venv/bin/python scripts/monitor_weaviate.py stats
```

**Your Data** (as of Dec 3, 2025):
- ✅ 25 LCSH records indexed
- ✅ Embeddings cached (3,072 dimensions each)
- ✅ Ready for production searches
- 💰 Total cost so far: ~$0.003

**Next Steps**:
1. Import full LCSH dataset (460K records) → $59.80 one-time
2. Import FAST dataset (1.9M records) → $247.00 one-time
3. Use forever for ~$0.13 per 1,000 searches

---

## 🎯 Summary

✅ **Embeddings are cached in Weaviate - you pay ONCE per record**  
✅ **Searches only pay for query embedding (~$0.00013 each)**  
✅ **No re-generation needed - embeddings stored permanently**  
✅ **Monitor with `monitor_weaviate.py` or web console**  
✅ **Backup Docker volume to protect your investment**

**Total Cost for Production System**:
- Import: ~$306.80 (one-time, for 2.3M records)
- Search: ~$0.13 per 1,000 queries (ongoing)

**ROI**: After 1,000 searches, you've already saved vs. re-embedding each time!

---

Last Updated: 2025-12-03
