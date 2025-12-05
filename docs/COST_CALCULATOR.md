# 💰 Cost Calculator & Budget Planning

**Detailed cost analysis for OpenAI API usage**

---

## 📊 Pricing Overview (December 2024)

### OpenAI Models Used

| Model | Purpose | Input Cost | Output Cost |
|-------|---------|------------|-------------|
| **o4-mini** | Text processing, OCR, topics | ~$0.15/1M tokens | ~$0.60/1M tokens |
| **text-embedding-3-large** | Vector embeddings | $0.13/1M tokens | N/A (no output) |

**Note:** Prices are approximate. Check [OpenAI Pricing](https://openai.com/api/pricing/) for current rates.

---

## 🔢 Cost Breakdown by Operation

### 1. Image OCR (o4-mini Vision)

**Per image:**
- Average input: ~1,000 tokens (image + prompt)
- Average output: ~500 tokens (extracted text)
- **Cost:** ~$0.0004 per image

**Example calculations:**
```
Cover image OCR:
  Input:  1,000 tokens × $0.15/1M = $0.00015
  Output:   500 tokens × $0.60/1M = $0.00030
  Total:  $0.00045

3 images (cover + back + TOC):
  Total: 3 × $0.00045 = $0.00135 ≈ $0.0014
```

### 2. Embedding Generation (text-embedding-3-large)

**Per embedding:**
- Average input: ~100 tokens (subject heading text)
- **Cost:** $0.000013 per embedding

**Example calculations:**
```
Single subject heading:
  "Calligraphy, Chinese--History"
  ~100 tokens × $0.13/1M = $0.000013

Search query embedding:
  "Book about Chinese calligraphy history"
  ~50 tokens × $0.13/1M = $0.0000065

Importing 20,000 subjects:
  20,000 × $0.000013 = $0.26
  BUT: This is ONE-TIME cost, embeddings cached forever
```

### 3. Topic Generation (o4-mini)

**Per book:**
- Input: Book metadata (~500-1000 tokens)
- Output: Topic list (~200 tokens)
- **Cost:** ~$0.0002 per book

**Example:**
```
Input:  1,000 tokens × $0.15/1M = $0.00015
Output:   200 tokens × $0.60/1M = $0.00012
Total:  $0.00027 ≈ $0.0003
```

### 4. Subject Search (Vector Search)

**Per search:**
- Query embedding: ~50 tokens
- Weaviate search: FREE (no API calls)
- **Cost:** $0.0000065 per search

**Example:**
```
Search embedding:
  50 tokens × $0.13/1M = $0.0000065 ≈ $0.000007

Note: Cached subject embeddings = FREE
      Only query embedding costs money
```

---

## 📈 Complete Workflow Costs

### Workflow 1: Image Upload → Search

**Steps:**
1. Upload 3 images (cover, back, TOC)
2. OCR processing
3. Extract topics
4. Search LCSH/FAST
5. Generate MARC fields

**Cost breakdown:**
```
OCR (3 images):        $0.0014
Topic extraction:      $0.0003
Search embedding:      $0.000007
MARC generation:       $0 (no API call)
────────────────────────────
Total per book:        $0.0017 ≈ $0.002
```

**Annual costs (1,000 books):**
```
1,000 books × $0.002 = $2.00/year
```

### Workflow 2: Manual Entry → Search

**Steps:**
1. Type metadata manually
2. Search LCSH/FAST
3. Generate MARC fields

**Cost breakdown:**
```
Search embedding:      $0.000007
MARC generation:       $0 (no API call)
────────────────────────────
Total per book:        $0.000007 ≈ $0.00001
```

**Annual costs (1,000 books):**
```
1,000 books × $0.00001 = $0.01/year
```

### Workflow 3: Enhanced Search (Form Data)

**Using the `/api/enhanced-search` endpoint:**

**Cost breakdown:**
```
Query embedding:       $0.000007
Vector search:         $0 (Weaviate, free)
MARC formatting:       $0 (local processing)
────────────────────────────
Total per search:      $0.000007 ≈ $0.00001
```

---

## 💵 One-Time Setup Costs

### LCSH Data Import

**Cost = Number of records × $0.000013**

| Records | Cost | Time | Coverage | Recommended For |
|---------|------|------|----------|-----------------|
| 1,000 | $0.013 | 2 min | 40% | Testing only |
| 5,000 | $0.065 | 7 min | 65% | Small collections |
| 10,000 | $0.13 | 14 min | 75% | Small libraries |
| **20,000** | **$0.26** | **28 min** | **85%** | **Most libraries** ✅ |
| 50,000 | $0.65 | 70 min | 95% | Large collections |
| 100,000 | $1.30 | 140 min | 99% | Research libraries |
| 500,000 | $6.50 | 12 hrs | 100% | Comprehensive |

**Note:** This is ONE-TIME cost. Embeddings are cached permanently.

---

## 📊 Monthly Budget Calculator

### Usage Scenario 1: Small Library

**Profile:**
- 100 new books/month
- 50% use image upload, 50% manual entry
- Average 2 searches per book (refinement)

**Monthly cost:**
```
Image-based (50 books):
  50 × $0.002 = $0.10

Manual entry (50 books):
  50 × $0.00001 = $0.0005

Additional searches (200):
  200 × $0.00001 = $0.002

────────────────────────────
Total/month:     $0.10
Total/year:      $1.20
```

### Usage Scenario 2: Medium Library

**Profile:**
- 500 new books/month
- 70% use image upload, 30% manual
- Average 3 searches per book

**Monthly cost:**
```
Image-based (350 books):
  350 × $0.002 = $0.70

Manual entry (150 books):
  150 × $0.00001 = $0.0015

Additional searches (1,500):
  1,500 × $0.00001 = $0.015

────────────────────────────
Total/month:     $0.72
Total/year:      $8.64
```

### Usage Scenario 3: Large Research Library

**Profile:**
- 2,000 new books/month
- 80% image upload, 20% manual
- Average 4 searches per book
- Additional topic generation for 50% of books

**Monthly cost:**
```
Image-based (1,600 books):
  1,600 × $0.002 = $3.20

Manual entry (400 books):
  400 × $0.00001 = $0.004

Topic generation (1,000 books):
  1,000 × $0.0003 = $0.30

Additional searches (8,000):
  8,000 × $0.00001 = $0.08

────────────────────────────
Total/month:     $3.58
Total/year:      $42.96
```

---

## 🎯 Total Cost of Ownership (3 Years)

### Scenario: Medium Academic Library

**Setup (Year 0):**
```
Import 20,000 LCSH subjects:     $0.26
Initial testing (100 books):     $0.20
Staff training time:             $0
────────────────────────────────
Setup total:                     $0.46
```

**Ongoing (Years 1-3):**
```
Year 1: 500 books/month × 12    = $8.64
Year 2: 500 books/month × 12    = $8.64
Year 3: 500 books/month × 12    = $8.64
────────────────────────────────
3-year total:                    $25.92
```

**Total 3-year cost:**
```
Setup + 3 years = $0.46 + $25.92 = $26.38
```

**Compare to:**
- Manual cataloging: 500 books/month × $2.50/book × 12 × 3 = **$45,000**
- **Savings: $44,973.62 (99.9%)**

---

## 📉 Cost Optimization Strategies

### 1. Batch Processing

**Instead of real-time:**
```
Process images in batches during off-hours
- Collect 50 books
- Upload all at once
- Review results together
```

**Benefit:** No cost savings (API charges same), but better workflow efficiency

### 2. Manual Entry for Simple Books

**When to skip OCR:**
```
Book has:
  ✓ Simple title (5 words or less)
  ✓ Clear subject matter
  ✓ No special characters
  
Use manual entry instead:
  Saves $0.0014 per book
  1,000 books/year = $1.40 saved
```

### 3. Adjust Search Threshold

**Higher confidence threshold = fewer results:**
```
min_score=0.80 instead of 0.70
- Returns fewer candidates
- Slightly faster processing
- Minimal cost savings (~5%)
```

### 4. Limit Results

**Request fewer matches:**
```
limit=3 instead of limit=10
- Faster response
- Same embedding cost
- Saves review time (not money)
```

### 5. Reuse Embeddings (Already Automatic)

**System automatically:**
- Caches all subject embeddings forever
- Never re-embeds same subject
- Only generates NEW query embeddings

**Result:** 99% of costs are query embeddings, not subject database

---

## 🔍 Cost Monitoring

### Track API Usage

**Monitor in OpenAI Dashboard:**
1. Go to https://platform.openai.com/usage
2. View usage by day/month
3. Check costs by model
4. Set budget alerts

**Budget alerts recommended:**
```
Warning at: $5/month
Hard limit: $10/month

This allows ~4,000 image-based book processes/month
Far more than most libraries need
```

### Application Logging

**Track in your system:**

```python
# Add to main.py
import logging

logging.basicConfig(
    filename='logs/api_costs.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

# Log each API call
logging.info(f"OCR: 3 images, est. $0.0014")
logging.info(f"Search: 1 query, est. $0.000007")
```

**Analyze monthly:**
```bash
# Count operations
grep "OCR" logs/api_costs.log | wc -l
grep "Search" logs/api_costs.log | wc -l

# Estimate total
# OCR count × $0.0014 + Search count × $0.000007
```

---

## 💡 ROI Analysis

### Cost vs. Time Savings

**Manual cataloging:**
```
Cataloger salary: $30/hour
Time per book: 5 minutes = $2.50 per book
1,000 books/year = $2,500
```

**With AI tool:**
```
API costs: $2.00/year (1,000 books)
Cataloger time: 1 min/book = $0.50 per book
Total: $2.00 + $500 = $502
```

**Annual savings:**
```
$2,500 - $502 = $1,998 saved
ROI: 398% return
Payback period: Immediate (first book)
```

### Labor Cost Comparison

| Method | Time/Book | Labor Cost (@$30/hr) | API Cost | Total |
|--------|-----------|---------------------|----------|-------|
| Manual | 5 min | $2.50 | $0 | $2.50 |
| AI + Review | 1 min | $0.50 | $0.002 | $0.502 |
| **Savings** | **80%** | **$2.00** | **-$0.002** | **$1.998** |

---

## 📋 Budget Template

### Annual Budget Request

**For:** AI Subject Heading Assistant  
**Period:** FY 2025 (January - December)

**One-Time Costs:**
```
LCSH database import (20,000 records):    $0.26
System setup & configuration:             $0
Staff training (no API cost):             $0
───────────────────────────────────────────────
One-time total:                           $0.26
```

**Recurring Costs (Annual):**
```
Expected volume: 1,200 books/year
Image processing (70%): 840 books         $1.68
Manual entry (30%): 360 books             $0.004
Additional searches (20% refinement):     $0.10
Contingency (20%):                        $0.36
───────────────────────────────────────────────
Annual total:                             $2.14
```

**Total First Year:**
```
Setup + First year = $0.26 + $2.14 = $2.40
```

**Cost Per Book:**
```
$2.40 ÷ 1,200 books = $0.002 per book
```

**Projected Savings:**
```
Manual cost: 1,200 books × $2.50 = $3,000
AI cost: $2.40
Net savings: $2,997.60 (99.9%)
```

---

## 🎯 Cost Control Measures

### 1. Set OpenAI Budget Limits

```python
# In OpenAI dashboard
Monthly budget limit: $10
Email alerts at: $5, $8, $10
Hard stop at: $10
```

### 2. Implement Usage Quotas

```python
# In application config
MAX_BOOKS_PER_DAY = 100
MAX_IMAGES_PER_UPLOAD = 5
MAX_SEARCH_RESULTS = 10
```

### 3. Monitor Unusual Patterns

**Alert if:**
- Daily cost >$1 (unusual spike)
- >500 API calls/hour (possible loop)
- Error rate >5% (wasted calls)

### 4. Review Monthly Reports

**Generate report:**
```bash
# Monthly usage summary
./venv/bin/python scripts/generate_cost_report.py --month 2024-12

# Output:
Books processed: 420
OCR images: 1,260
Searches: 504
Total cost: $2.70
Average: $0.0064/book
```

---

## 📊 Cost Comparison: Cloud vs. Self-Hosted

### Current Setup (Cloud API)

**Pros:**
- No infrastructure costs
- Auto-scaling
- Always latest models
- No maintenance

**Costs:**
- API: $2-10/month
- Weaviate (Docker): Free
- Total: ~$5/month average

### Alternative: Self-Hosted LLM (Not Recommended)

**Pros:**
- No per-use charges
- Data stays local

**Cons:**
- Server: $500-2,000/month (GPU)
- Maintenance: $500/month (IT staff)
- Quality: Lower than OpenAI
- Total: ~$1,000+/month

**Verdict:** Cloud API is 200x cheaper for library use cases

---

## ✅ Cost Summary

### Quick Facts

**One-time:**
- LCSH import (20,000): $0.26

**Per operation:**
- Image OCR: $0.0014/book
- Manual search: $0.00001/book
- Topic generation: $0.0003/book

**Typical monthly (500 books):**
- Small library: $0.10/month
- Medium library: $0.72/month
- Large library: $3.58/month

**ROI:**
- Labor savings: $2.00/book
- API cost: $0.002/book
- Net savings: $1.998/book (99.9%)

### Budget Recommendation

**Recommended annual budget:**
```
Conservative (1,000 books):   $5/year
Standard (5,000 books):       $20/year
Large (20,000 books):         $80/year
```

**Buffer for:**
- Testing and training
- Quality improvements
- API price changes
- Usage spikes

---

## 📞 Cost Questions?

**Common questions:**

**Q: Why is setup cost so low?**  
A: We only pay for embedding generation. Weaviate storage is free (Docker).

**Q: What if OpenAI raises prices?**  
A: Historical trend is DOWN. Embedding costs dropped 90% in 2023-2024.

**Q: Can we reduce costs further?**  
A: Yes - use manual entry for simple books (saves $0.0014 each).

**Q: What's included in the cost?**  
A: All AI processing. NOT included: server hosting, staff time, ILS integration.

**Q: Hidden costs?**  
A: None. Transparent per-token pricing. No minimums, subscriptions, or fees.

---

**Last Updated:** December 5, 2025  
**Pricing Source:** OpenAI API Pricing (December 2025)  
**Next:** [NEXT_STEPS.md](NEXT_STEPS.md) - Development roadmap
