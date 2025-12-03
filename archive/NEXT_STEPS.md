# Next Steps: Making Subject Matching Production-Ready

## 🎯 Current State (December 2025)

✅ **MVP Complete and Working**:
- Multi-image OCR with o4-mini Responses API
- Topic generation with reasoning
- Vector search against sample LCSH + FAST (8 authorities)
- Basic 650/651/655 MARC generation
- End-to-end API functional

⚠️ **Limitations**:
- Only 8 sample authorities (5 LCSH + 3 FAST)
- Simple vector-only search
- No cataloger feedback mechanism
- No quantitative evaluation

---

## 📋 Implementation Priorities

### **Priority 1: Expand Authority Data** (Week 1-2)

**Why First?** 
The quality ceiling is limited by having only 8 sample authorities. Real cataloging needs comprehensive coverage.

**What to Build**:

1. **LCSH Importer** (`scripts/lcsh_importer.py`)
   ```python
   # Download from: https://id.loc.gov/download/
   # Parse LCSH RDF/JSON files
   # Extract: prefLabel, altLabel, broader, narrower, scopeNote, uri
   # Generate embeddings: text-embedding-3-large
   # Batch insert to Weaviate
   ```

2. **FAST Importer** (`scripts/fast_importer.py`)
   ```python
   # Download from: https://www.oclc.org/research/areas/data-science/fast.html
   # Similar structure to LCSH importer
   ```

3. **Enhanced Schema**
   ```python
   # Update authority_search.py schema:
   class AuthoritySubject:
       label: str
       uri: str
       vocabulary: str  # "lcsh" | "fast" | "gtt" | ...
       subject_type: str  # "topical" | "geographic" | "genre_form"
       alt_labels: List[str]  # NEW
       broader_terms: List[str]  # NEW
       narrower_terms: List[str]  # NEW
       scope_note: str  # NEW
   ```

**Expected Result**:
- ~460K LCSH + ~1.9M FAST = 2.3M authorities
- Rich metadata for better matching
- Processing time: 10-15 hours (one-time)

---

### **Priority 2: Implement Hybrid Search** (Week 3)

**Why Second?**
With real data, simple vector search will miss exact name/year matches. Hybrid search fixes this.

**What to Build**:

**File**: `authority_search.py` - Add `hybrid_search()` method

```python
async def hybrid_search(
    self,
    query: str,
    vocabularies: List[str],
    limit: int = 10
) -> List[AuthorityCandidate]:
    """
    Hybrid search: vector + lexical matching.
    
    Steps:
    1. Vector search → top 50 candidates
    2. Compute lexical overlap (token matching)
    3. Combine scores: 0.7*vector + 0.3*lexical
    4. Return top N
    """
    # Step 1: Vector search
    vector_results = await self._vector_search(query, limit=50)
    
    # Step 2: Lexical scoring
    query_tokens = set(query.lower().split())
    for candidate in vector_results:
        label_tokens = set(candidate.label.lower().split())
        overlap = len(query_tokens & label_tokens)
        total = len(query_tokens | label_tokens)
        candidate.lexical_score = overlap / total if total > 0 else 0
    
    # Step 3: Combine scores
    for candidate in vector_results:
        candidate.final_score = (
            0.7 * candidate.vector_score + 
            0.3 * candidate.lexical_score
        )
    
    # Step 4: Re-rank and return
    ranked = sorted(vector_results, key=lambda x: x.final_score, reverse=True)
    return ranked[:limit]
```

**Expected Improvement**:
- Better matching for proper nouns ("Beijing", "Ming dynasty")
- Precise year matching ("960-1644")
- Handles acronyms and technical terms
- +10-15% accuracy on test cases

---

### **Priority 3: Add LLM Re-ranking** (Week 4)

**Why Third?**
Context matters. "China" could be topical or geographic depending on the book. LLM can judge this.

**What to Build**:

**File**: `llm_reranker.py` (NEW)

```python
from openai import OpenAI
from models import BookMetadata, AuthorityCandidate, RankedCandidate

class LLMReranker:
    """Use o4-mini to re-rank authority candidates based on book context."""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.default_model
        self.reasoning_effort = settings.reasoning_effort
    
    async def rerank_candidates(
        self,
        topic: str,
        book_metadata: BookMetadata,
        candidates: List[AuthorityCandidate],
        top_n: int = 3
    ) -> List[RankedCandidate]:
        """
        Ask o4-mini to evaluate and rank candidates in context.
        
        Args:
            topic: The topic string to match
            book_metadata: Full book context (title, summary, TOC)
            candidates: List of authority candidates from hybrid search
            top_n: Number of top candidates to return
            
        Returns:
            Ranked candidates with scores and explanations
        """
        prompt = self._build_reranking_prompt(topic, book_metadata, candidates)
        
        response = self.client.responses.create(
            model=self.model,
            input=[{
                "role": "user",
                "content": [{"type": "input_text", "text": prompt}]
            }],
            reasoning={"effort": self.reasoning_effort},
            max_output_tokens=1500
        )
        
        # Parse response (expects JSON array of ranked candidates)
        ranked = self._parse_reranking_response(response)
        return ranked[:top_n]
    
    def _build_reranking_prompt(
        self,
        topic: str,
        metadata: BookMetadata,
        candidates: List[AuthorityCandidate]
    ) -> str:
        """Build prompt for LLM re-ranking."""
        
        return f"""You are an expert library cataloger. Given this book and topic, rank these authority headings by relevance.

**BOOK METADATA**:
- Title: {metadata.title}
- Author: {metadata.author}
- Summary: {metadata.summary[:300]}...
- TOC: {', '.join(metadata.table_of_contents[:5])}

**TOPIC TO MATCH**: "{topic}"

**AUTHORITY CANDIDATES**:
{self._format_candidates(candidates)}

**TASK**:
Rank these candidates from most to least relevant for this specific book. Consider:
1. Does the heading accurately describe THIS book's content?
2. Is the specificity appropriate (not too broad, not too narrow)?
3. Do geographic/chronological subdivisions match the book's scope?
4. For ambiguous terms, does the context clarify the intended meaning?

Return JSON array:
[
  {{
    "rank": 1,
    "label": "...",
    "uri": "...",
    "vocabulary": "lcsh",
    "score": 0.95,
    "reason": "Explanation of why this is the best match..."
  }},
  ...
]

Return ONLY the JSON array."""
        
    def _format_candidates(self, candidates: List[AuthorityCandidate]) -> str:
        """Format candidates for prompt."""
        lines = []
        for i, c in enumerate(candidates[:10], 1):
            lines.append(
                f"{i}. [{c.vocabulary}] {c.label} "
                f"(vector: {c.vector_score:.2f}, lexical: {c.lexical_score:.2f})"
            )
        return "\n".join(lines)
```

**Update**: `llm_topics.py` to use re-ranker

```python
# After hybrid search, add re-ranking:
if len(candidates) > 1:
    reranker = LLMReranker()
    ranked_candidates = await reranker.rerank_candidates(
        topic=topic,
        book_metadata=metadata,
        candidates=candidates[:10]  # Top 10 from hybrid search
    )
else:
    ranked_candidates = candidates
```

**Expected Improvement**:
- Context-aware ranking
- Better handling of ambiguous terms
- Explanations for catalogers
- +15-20% accuracy on complex cases

---

### **Priority 4: Feedback & Evaluation** (Week 5-6)

**Why Fourth?**
Need to measure improvements and collect training data.

**What to Build**:

1. **Feedback Endpoint** (`routes.py`)
   ```python
   @router.post("/submit-final")
   async def submit_final_subjects(request: FinalSubmissionRequest):
       """
       Store cataloger's final decisions for learning.
       
       Request body:
       {
         "metadata": {...},
         "proposed_subjects": [...],  # AI suggestions
         "final_subjects": [          # Cataloger decisions
           {
             "tag": "650",
             "label": "...",
             "uri": "...",
             "status": "accepted" | "rejected" | "modified",
             "cataloger_note": "..."
           }
         ]
       }
       """
       # Log to data/feedback/{timestamp}.json
       feedback_path = Path(settings.data_dir) / "feedback" / f"{datetime.now().isoformat()}.json"
       feedback_path.parent.mkdir(parents=True, exist_ok=True)
       
       with open(feedback_path, 'w') as f:
           json.dump(request.dict(), f, indent=2)
       
       return {"success": True, "message": "Feedback recorded"}
   ```

2. **Evaluation Script** (`scripts/evaluate.py`)
   ```python
   """
   Evaluate subject heading generation against gold records.
   
   Usage:
       python scripts/evaluate.py --gold data/gold_records.json
   """
   
   async def evaluate_book(gold_record: MARCRecord) -> EvaluationResult:
       # Extract metadata from MARC
       metadata = extract_metadata_from_marc(gold_record)
       
       # Run pipeline
       proposed = await generate_subjects_pipeline(metadata)
       
       # Extract gold subjects from MARC 6XX fields
       gold_subjects = extract_gold_subjects(gold_record)
       
       # Compare
       return compare_subjects(proposed, gold_subjects)
   
   def compute_metrics(results: List[EvaluationResult]):
       """Compute precision, recall, top-K accuracy."""
       total_proposed = sum(len(r.proposed) for r in results)
       total_gold = sum(len(r.gold) for r in results)
       exact_matches = sum(r.exact_matches for r in results)
       
       precision = exact_matches / total_proposed
       recall = exact_matches / total_gold
       
       # Top-1 accuracy: is best proposal correct?
       top_1 = sum(r.proposed[0] in r.gold for r in results) / len(results)
       
       # Top-3 coverage: is ANY of top 3 correct?
       top_3 = sum(any(p in r.gold for p in r.proposed[:3]) for r in results) / len(results)
       
       return {
           "precision": precision,
           "recall": recall,
           "top_1_accuracy": top_1,
           "top_3_coverage": top_3
       }
   ```

3. **Gold Test Set**
   - Export 50-100 real MARC records with subject headings
   - Save to `data/gold_records.json`
   - Use for regression testing

**Expected Output**:
- Baseline metrics (current system)
- Quantify improvements from each change
- Identify weak areas (e.g., "East Asian history harder than science")

---

## 🚀 Quick Win Checklist (First 2 Weeks)

For immediate impact, focus on:

- [ ] **Week 1**: Create evaluation script with 20 test cases
- [ ] **Week 1**: Import 50K LCSH records (10% sample) to test infrastructure
- [ ] **Week 2**: Implement hybrid search (vector + lexical)
- [ ] **Week 2**: Run evaluation, measure improvement

This gives you:
1. Real data (not just 8 samples)
2. Better search algorithm
3. Quantifiable metrics
4. Confidence to continue full import

---

## 💡 Tips for Implementation

### For Windsurf/AI Assistant

When asking Windsurf to implement:
1. **Be specific**: "Implement hybrid_search() in authority_search.py with 70% vector + 30% lexical weighting"
2. **Reference existing code**: "Follow the same pattern as _vector_search() but add lexical scoring"
3. **Specify tests**: "Add test case for year matching: '960-1644' should prefer exact match over semantic similarity"

### For LCSH/FAST Import

Start small:
1. Download 1 LCSH file (~50K records)
2. Parse and insert to test
3. Measure time/memory
4. Then scale to full dataset

### For Evaluation

Start with edge cases:
1. Books with clear subject headings
2. Ambiguous topics (e.g., "China" - country or topic?)
3. Specialized subjects (East Asian history)
4. Multi-subject books

---

## 📊 Success Metrics

**Immediate Goals (Week 2)**:
- [ ] 50K+ authorities indexed
- [ ] Hybrid search implemented
- [ ] 20 test cases with metrics

**Short-term Goals (Month 1)**:
- [ ] Full LCSH + FAST indexed (2.3M records)
- [ ] Top-3 coverage: 75%+
- [ ] Processing time: <5 seconds/book

**Medium-term Goals (Month 3)**:
- [ ] LLM re-ranking live
- [ ] 100+ cataloger feedback logs
- [ ] Top-3 coverage: 90%+
- [ ] Cataloger acceptance: 75%+

---

## 🔗 Resources

- **LCSH Data**: https://id.loc.gov/download/
- **FAST Data**: https://www.oclc.org/research/areas/data-science/fast.html
- **Weaviate Hybrid Search Docs**: https://weaviate.io/developers/weaviate/search/hybrid
- **OpenAI Responses API**: https://platform.openai.com/docs/api-reference/responses

---

**Questions?** See [ROADMAP.md](ROADMAP.md) for the full strategic plan.

**Last Updated**: 2025-12-03
