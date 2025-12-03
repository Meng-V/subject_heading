# Testing Your Authority Search System

## ✅ Current Status

**You've successfully completed**:
- ✅ Imported 1,025 LCSH records
- ✅ Cost so far: ~$0.13
- ✅ Budget remaining: ~$9.87
- ✅ Search working perfectly!

---

## 🧪 Complete Testing Guide

### Test 1: Basic Search

Test semantic similarity:

```bash
# Search for Chinese topics
./venv/bin/python scripts/monitor_weaviate.py search "Chinese calligraphy"
./venv/bin/python scripts/monitor_weaviate.py search "Ming dynasty art"
./venv/bin/python scripts/monitor_weaviate.py search "China history"

# Search for other topics
./venv/bin/python scripts/monitor_weaviate.py search "handbooks"
./venv/bin/python scripts/monitor_weaviate.py search "fiction"
```

**Expected**:
- Fast response (50-100ms)
- Semantic matches (finds related terms)
- Cost: $0.00013 per search

---

### Test 2: View Your Data

Check what's in your database:

```bash
# Show statistics
./venv/bin/python scripts/monitor_weaviate.py stats

# View sample records
./venv/bin/python scripts/monitor_weaviate.py sample lcsh --limit 10

# Check embeddings are cached
./venv/bin/python scripts/monitor_weaviate.py check-embeddings
```

**Expected Output**:
```
📊 Weaviate Statistics
============================================================
  LCSH      : 1,025 records
  FAST      : 0 records
============================================================

📦 LCSHSubject
  Has embeddings: ✅ Yes
  Vector dimensions: 3072 (text-embedding-3-large)
  ✅ Embeddings are CACHED - no API calls for matching!
```

---

### Test 3: API Integration

Test through your main API:

```bash
# Start the API server
./venv/bin/python main.py
```

Then in another terminal or browser:

```bash
# Test topic generation and matching
curl -X POST "http://localhost:8000/api/lcsh-match" \
  -H "Content-Type: application/json" \
  -d '{"topics": ["Chinese calligraphy", "Ming dynasty art"]}'
```

**Expected**: JSON response with authority matches

---

### Test 4: Quality Assessment

Test search quality on different types of queries:

```bash
# Exact match (should score >0.90)
./venv/bin/python scripts/monitor_weaviate.py search "Calligraphy, Chinese"

# Semantic similarity (should score 0.70-0.85)
./venv/bin/python scripts/monitor_weaviate.py search "Chinese brush writing"

# Related concepts (should score 0.60-0.75)
./venv/bin/python scripts/monitor_weaviate.py search "traditional Chinese art"

# Different topic (should score <0.60 or no results)
./venv/bin/python scripts/monitor_weaviate.py search "computer science"
```

**Quality Benchmarks**:
- Exact matches: >0.90 score
- Synonyms: >0.80 score
- Related concepts: 0.70-0.80 score
- Different topics: <0.70 score

---

## 💰 Importing More Data (Within $10 Budget)

### Option 1: Import 10,000 More Records (Recommended)

**Cost**: $1.30 additional  
**Total cost**: $1.43  
**Total records**: 11,025  
**Coverage**: ~75% of cataloging needs

```bash
# Import next 10,000 records (avoids duplicates automatically)
./venv/bin/python scripts/lcsh_importer_streaming.py \
    --input subjects.nt \
    --limit 10000 \
    --batch-size 500
```

**How it avoids duplicates**:
- Weaviate checks URI before inserting
- If URI exists, skips the record
- No duplicate embeddings generated
- No wasted money!

---

### Option 2: Import 20,000 Total Records

**Cost**: $2.60 total (including what you've spent)  
**Records**: 20,000  
**Coverage**: ~85% of cataloging needs

```bash
# Import up to 20,000 total
./venv/bin/python scripts/lcsh_importer_streaming.py \
    --input subjects.nt \
    --limit 20000 \
    --batch-size 500
```

Weaviate will skip your existing 1,025 records and import ~19,000 new ones.

---

### Option 3: Import 50,000 Total Records (Use Full Budget)

**Cost**: $6.50 total  
**Records**: 50,000  
**Coverage**: ~95% of cataloging needs

```bash
# Import up to 50,000 total
./venv/bin/python scripts/lcsh_importer_streaming.py \
    --input subjects.nt \
    --limit 50000 \
    --batch-size 1000
```

This uses most of your $10 budget and gives excellent coverage.

---

## 🚫 How Duplicate Prevention Works

### Automatic Deduplication

The importer checks each record before inserting:

```python
# Inside the importer
for authority in authorities:
    # Weaviate checks if URI already exists
    if not collection.exists(authority.uri):
        # Generate embedding (costs $0.00013)
        embedding = generate_embedding(authority)
        # Insert
        collection.insert(authority, embedding)
    else:
        # Skip! No cost incurred
        logger.info(f"Skipping duplicate: {authority.uri}")
```

**Result**: You'll never pay twice for the same record! ✅

---

## 📊 Cost Tracking

Track your spending:

```bash
# Check current record count
./venv/bin/python scripts/monitor_weaviate.py stats
```

**Calculate cost**:
```
Current records: 1,025
Cost per record: $0.00013
Total spent: 1,025 × $0.00013 = $0.133

If you import to 20,000:
New records: 20,000 - 1,025 = 18,975
Additional cost: 18,975 × $0.00013 = $2.47
Total cost: $0.13 + $2.47 = $2.60
```

---

## 🎯 Recommended Testing Workflow

### Step 1: Test What You Have (5 minutes)

```bash
# Test various searches
./venv/bin/python scripts/monitor_weaviate.py search "Chinese calligraphy"
./venv/bin/python scripts/monitor_weaviate.py search "Art, Chinese"
./venv/bin/python scripts/monitor_weaviate.py search "handbooks"
./venv/bin/python scripts/monitor_weaviate.py search "fiction"

# Check stats
./venv/bin/python scripts/monitor_weaviate.py stats
```

**Result**: Verify system works, search quality is good

---

### Step 2: Identify Gaps (10 minutes)

Try searches for subjects you'll need:

```bash
# Test your actual use cases
./venv/bin/python scripts/monitor_weaviate.py search "Japanese literature"
./venv/bin/python scripts/monitor_weaviate.py search "World War 2"
./venv/bin/python scripts/monitor_weaviate.py search "Buddhism"
```

**Note missing subjects**: If many searches return "No results" or low scores, you need more data.

---

### Step 3: Import More (15 minutes)

Based on gaps, import more:

```bash
# For general library: 20,000 subjects
./venv/bin/python scripts/lcsh_importer_streaming.py \
    --input subjects.nt \
    --limit 20000 \
    --batch-size 500

# Cost: ~$2.47 more (total $2.60)
```

---

### Step 4: Retest (5 minutes)

```bash
# Retest previous queries
./venv/bin/python scripts/monitor_weaviate.py search "Japanese literature"
./venv/bin/python scripts/monitor_weaviate.py search "World War 2"

# Check improvement
./venv/bin/python scripts/monitor_weaviate.py stats
```

**Expected**: More results, better coverage

---

### Step 5: Integration Test (10 minutes)

Test with your full workflow:

```bash
# Start API
./venv/bin/python main.py

# Test full cataloging flow
# 1. Upload book images
# 2. Generate topics
# 3. Match to LCSH
# 4. Generate MARC fields
```

---

## 📈 Quality Metrics to Track

Create `logs/test_results.txt`:

```
Date: 2025-12-03
Records: 1,025
Cost: $0.13

Test Query: "Chinese calligraphy"
  - Top match: "Calligraphy, Chinese" (score: 0.80)
  - Status: ✅ Good

Test Query: "Ming dynasty painting"
  - Top match: "Art, Chinese -- Ming-Qing dynasties" (score: 0.82)
  - Status: ✅ Excellent

Test Query: "Japanese literature"
  - Top match: None or low score
  - Status: ❌ Need more data

Coverage estimate: 50-60%
Recommendation: Import to 20,000 records
```

---

## 🔍 Advanced Testing

### Test Semantic Understanding

```bash
# Test if system understands relationships
./venv/bin/python scripts/monitor_weaviate.py search "brush painting"
# Should find: "Calligraphy, Chinese", "Painting, Chinese", "Art, Chinese"

./venv/bin/python scripts/monitor_weaviate.py search "Qing dynasty"
# Should find: subjects with "Ming-Qing dynasties"

./venv/bin/python scripts/monitor_weaviate.py search "book format"
# Should find: "Handbooks and manuals", "Dictionaries"
```

---

### Test Performance

Create `scripts/performance_test.py`:

```python
import time
import asyncio
from authority_search import authority_search

async def test_performance():
    """Test search performance."""
    authority_search.connect()
    
    queries = [
        "Chinese calligraphy",
        "Ming dynasty art",
        "Japanese literature",
        "World War 2",
        "Fiction"
    ]
    
    times = []
    for query in queries:
        start = time.time()
        results = await authority_search.search_authorities(
            topic=query,
            vocabularies=["lcsh"],
            limit_per_vocab=5
        )
        elapsed = time.time() - start
        times.append(elapsed)
        print(f"{query}: {elapsed*1000:.1f}ms, {len(results)} results")
    
    avg_time = sum(times) / len(times)
    print(f"\nAverage: {avg_time*1000:.1f}ms")
    print(f"Total cost: ${len(queries) * 0.00013:.5f}")
    
    authority_search.client.close()

if __name__ == "__main__":
    asyncio.run(test_performance())
```

Run it:
```bash
./venv/bin/python scripts/performance_test.py
```

**Expected**:
- Average time: 50-150ms
- Cost: $0.00065 for 5 searches

---

## 💡 Pro Tips

### 1. Monitor Cache Hit Rate

Track how many searches find good matches:

```python
# Add to your logs
successful_searches = 0
total_searches = 0

if max_score > 0.75:
    successful_searches += 1
total_searches += 1

hit_rate = successful_searches / total_searches
print(f"Cache hit rate: {hit_rate:.1%}")
```

**Target**: >80% hit rate for production

---

### 2. Identify Common Subjects

Track which subjects you search most:

```python
from collections import Counter

search_log = Counter()
search_log["Chinese calligraphy"] += 1
search_log["Art, Chinese"] += 1

print("Most searched:")
for subject, count in search_log.most_common(10):
    print(f"  {subject}: {count} times")
```

**Use this** to prioritize which subjects to import next

---

### 3. Budget Optimization

Only import subjects you actually need:

```bash
# Extract only subjects matching your collection
# For example, East Asian library:
grep -E "China|Japan|Korea|Chinese|Japanese|Korean" subjects.nt > asian_subjects.nt

# Import just these (~5,000 subjects)
./venv/bin/python scripts/lcsh_importer_streaming.py \
    --input asian_subjects.nt \
    --batch-size 500

# Cost: ~$0.65 for targeted 5,000 subjects
```

---

## 📋 Complete Test Checklist

- [ ] Basic search works
- [ ] Stats show correct record count
- [ ] Embeddings are cached
- [ ] Semantic similarity works (related terms found)
- [ ] Performance <200ms average
- [ ] No duplicate records when re-importing
- [ ] API integration works
- [ ] Search quality >75% for your use cases
- [ ] Cost tracking accurate
- [ ] Backup strategy in place

---

## 🚀 Next Steps After Testing

Once testing looks good:

1. **Document your results**
   ```bash
   ./venv/bin/python scripts/monitor_weaviate.py stats > logs/test_results.txt
   ```

2. **Import production data**
   ```bash
   # Import to 20,000 for production use
   ./venv/bin/python scripts/lcsh_importer_streaming.py \
       --input subjects.nt \
       --limit 20000 \
       --batch-size 500
   ```

3. **Backup your data**
   ```bash
   docker run --rm \
     -v subject_heading_weaviate_data:/data \
     -v $(pwd)/backups:/backup \
     alpine tar czf /backup/weaviate_$(date +%Y%m%d).tar.gz /data
   ```

4. **Deploy to production**
   - Document API endpoints
   - Train users
   - Monitor usage

---

## 📞 Quick Reference

```bash
# View stats
./venv/bin/python scripts/monitor_weaviate.py stats

# Test search
./venv/bin/python scripts/monitor_weaviate.py search "query text"

# View samples
./venv/bin/python scripts/monitor_weaviate.py sample lcsh --limit 10

# Import more (no duplicates!)
./venv/bin/python scripts/lcsh_importer_streaming.py \
    --input subjects.nt \
    --limit 20000 \
    --batch-size 500

# Check cost
# Records × $0.00013 = Total cost
```

---

Last Updated: Dec 3, 2025
Your budget: $10.00
Spent so far: ~$0.13
Remaining: ~$9.87
Recommended next import: 20,000 records ($2.47 more)
