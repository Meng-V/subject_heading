# Subject Heading Assistant - Development Roadmap

## Current Status (MVP - ✅ Complete)

- ✅ Multi-image OCR with o4-mini Responses API
- ✅ Topic generation with reasoning
- ✅ Vector search against sample LCSH + FAST (5 + 3 entries)
- ✅ Basic 650/651/655 MARC generation
- ✅ End-to-end API workflow

## Phase 1: Expand Authority Data 📚

### Goal
Replace sample authorities with comprehensive LCSH and FAST datasets.

### Tasks

#### 1.1 LCSH Full Import
**File**: `scripts/lcsh_importer.py`

- Download LCSH RDF/JSON dumps from `id.loc.gov`
- Parse and extract:
  - `prefLabel` (primary label)
  - `altLabel` (alternative labels)
  - `broader` (broader terms)
  - `narrower` (narrower terms)
  - `scopeNote` (usage notes)
  - `uri` (authority URI)
- Generate embeddings using `text-embedding-3-large`:
  - Concatenate: `prefLabel + altLabels + broader + narrower + scopeNote`
  - Rich semantic context for better matching
- Batch insert into Weaviate `LCSHSubject` collection

#### 1.2 FAST Full Import
**File**: `scripts/fast_importer.py`

- Download FAST authority dump from OCLC
- Parse similar structure to LCSH
- Insert into Weaviate `FASTSubject` collection

#### 1.3 Multi-Vocabulary Schema
**Update**: `authority_search.py`

- Extend schema to support:
  - `vocabulary`: "lcsh" | "fast" | "gtt" | "rero" | "swd" | ...
  - `subject_type`: "topical" | "geographic" | "genre_form"
  - `alt_labels`: array of alternative labels
  - `broader_terms`: array of broader term URIs
  - `narrower_terms`: array of narrower term URIs
  - `scope_note`: usage guidance
- MVP: only populate LCSH + FAST
- Structure ready for future vocabulary expansion

**Estimated Data Volume**:
- LCSH: ~460,000 headings
- FAST: ~1.9 million headings
- Total: ~2.3M authority records

---

## Phase 2: Improve Matching Quality 🎯

### Goal
Move from simple vector search to hybrid search + LLM re-ranking.

### 2.1 Hybrid Search (Vector + Lexical)
**File**: `authority_search.py`

**Algorithm**:
```python
def hybrid_search(topic, top_k=50):
    # Step 1: Vector search (semantic similarity)
    vector_candidates = weaviate_vector_search(topic, limit=50)
    
    # Step 2: Lexical matching (BM25-like)
    for candidate in vector_candidates:
        lexical_score = compute_token_overlap(
            topic, 
            candidate.label + ' '.join(candidate.alt_labels)
        )
        
        # Combine scores (tunable weights)
        candidate.final_score = (
            0.7 * candidate.vector_score + 
            0.3 * lexical_score
        )
    
    # Step 3: Re-rank and return top K
    return sorted(vector_candidates, key=lambda x: x.final_score)[:top_k]
```

**Benefits**:
- Better handling of proper nouns ("China", "Beijing")
- Precise year/date matching ("960-1644")
- Acronyms and technical terms
- Reduces semantic drift

### 2.2 LLM Re-ranking
**File**: `llm_reranker.py`

**New Module**: `LLMReranker`

```python
class LLMReranker:
    """Use o4-mini to re-rank authority candidates."""
    
    async def rerank_candidates(
        self,
        topic: str,
        book_metadata: BookMetadata,
        candidates: List[AuthorityCandidate],
        top_n: int = 3
    ) -> List[RankedCandidate]:
        """
        Ask o4-mini to evaluate candidates in context.
        
        Returns:
            Ranked candidates with explanations
        """
```

**Prompt Structure**:
```
You are an expert cataloger. Given this book and topic, rank these 
authority headings by relevance:

BOOK:
- Title: {title}
- Summary: {summary}
- TOC: {toc}

TOPIC: {topic}

CANDIDATES:
1. [lcsh] Calligraphy, Chinese -- Ming-Qing dynasties, 1368-1912
2. [lcsh] Calligraphy, Chinese
3. [fast] Calligraphy, Chinese

Return JSON:
[
  {
    "rank": 1,
    "label": "...",
    "uri": "...",
    "score": 0.95,
    "reason": "Matches the book's Ming/Qing dynasty focus..."
  }
]
```

**Benefits**:
- Context-aware ranking (considers full book content)
- Handles edge cases and ambiguity
- Provides explanations for catalogers
- Can be logged for training data

### 2.3 Score Fusion
**Final ranking formula**:
```python
final_score = (
    0.4 * vector_score +      # Semantic similarity
    0.2 * lexical_score +     # Token overlap
    0.4 * llm_rerank_score    # Contextual relevance
)
```

---

## Phase 3: Smarter 65X Classification 🏷️

### Goal
Automatically determine 650/651/655 based on authority type, not hardcoded rules.

### 3.1 Authority Type Detection
**Update schema** to include `subject_type`:

```python
class AuthorityRecord:
    label: str
    uri: str
    vocabulary: str
    subject_type: Literal["topical", "geographic", "genre_form"]  # NEW
    alt_labels: List[str]
```

**Import scripts** extract type from:
- LCSH: MARC 008/09, 150/151/155 tags
- FAST: FAST facet indicators

### 3.2 Fallback LLM Classifier
**File**: `subject_type_classifier.py`

When `subject_type` is unknown:
```python
async def classify_subject_type(label: str) -> str:
    """Ask o4-mini to classify: topical / geographic / genre_form"""
    
    prompt = f"""
    Classify this authority heading:
    
    Label: {label}
    
    Return one of: topical, geographic, genre_form
    
    Examples:
    - "Calligraphy, Chinese" → topical
    - "China -- Beijing" → geographic
    - "Handbooks and manuals" → genre_form
    """
```

### 3.3 Smart Tag Assignment
**File**: `marc_65x_builder.py`

```python
def determine_tag(authority: AuthorityCandidate) -> str:
    """
    Returns: "650" | "651" | "655"
    
    Logic:
    1. If authority.subject_type exists → use it
    2. Else use LLM classifier
    3. Apply MARC rules:
       - topical → 650
       - geographic → 651
       - genre_form → 655
    """
```

---

## Phase 4: Feedback Loop & Evaluation 📊

### Goal
Enable continuous improvement through cataloger feedback and quantitative evaluation.

### 4.1 Feedback Collection
**New endpoint**: `/api/submit-final`

```python
@router.post("/submit-final")
async def submit_final(request: FinalSubmission):
    """
    Store cataloger's final decision.
    
    Request:
    {
      "metadata": {...},
      "proposed_subjects": [...],  # AI suggestions
      "final_subjects": [          # Cataloger's decisions
        {
          "tag": "650",
          "label": "...",
          "status": "accepted" | "rejected" | "modified",
          "cataloger_note": "..."
        }
      ]
    }
    """
    # Log to data/feedback/{timestamp}.json
    # Or insert into database for analysis
```

**Storage**: `data/feedback/` directory
```
feedback/
├── 20250103_120534_accepted.json
├── 20250103_120535_rejected.json
└── 20250103_120536_modified.json
```

### 4.2 Offline Evaluation Script
**File**: `scripts/evaluate.py`

```python
"""
Evaluate system against gold-standard MARC records.

Usage:
    python scripts/evaluate.py --gold-data data/gold_records.json
"""

def evaluate_pipeline(gold_records: List[MARCRecord]):
    results = {
        "total_books": 0,
        "total_subjects": 0,
        "exact_matches": 0,
        "top_1_coverage": 0,
        "top_3_coverage": 0,
        "per_vocab_stats": {},
        "error_examples": []
    }
    
    for record in gold_records:
        # Extract metadata
        metadata = extract_metadata(record)
        
        # Run pipeline
        proposed = await api_generate_subjects(metadata)
        gold = extract_gold_subjects(record)
        
        # Compare
        metrics = compare_subjects(proposed, gold)
        results.update(metrics)
    
    # Print report
    print_evaluation_report(results)
    
    # Save to JSON
    save_results("evaluation_results.json", results)
```

**Metrics to Track**:
- **Precision**: What % of proposed subjects are correct?
- **Recall**: What % of gold subjects were found?
- **Top-1 accuracy**: Is the #1 suggestion correct?
- **Top-3 coverage**: Is the correct answer in top 3?
- **Per-category breakdown**: Which subject types are hardest?
- **Authority source distribution**: LCSH vs FAST usage

### 4.3 Active Learning
**File**: `scripts/active_learning.py`

Identify difficult cases for prioritized review:
```python
def identify_low_confidence_cases(threshold=0.6):
    """
    Find subjects where max(score) < threshold.
    
    These need cataloger review and are valuable training data.
    """
    return [
        subject for subject in all_subjects
        if subject.top_candidate_score < threshold
    ]
```

**UI Enhancement**:
- Red flag: score < 0.6
- Yellow flag: 0.6 ≤ score < 0.8
- Green: score ≥ 0.8

---

## Phase 5: Advanced Features (Future) 🚀

### 5.1 Subject Chain Building
Automatically build proper LCSH chains:
```
China -- History -- Ming dynasty, 1368-1644
  ├─ China (geographic)
  ├─ History (topical)
  └─ Ming dynasty, 1368-1644 (chronological)
```

### 5.2 Multi-language Support
- Add support for non-English authority files
- Cross-language mapping (LCSH ↔ RAMEAU ↔ SWD)

### 5.3 Fine-tuning
- Use accumulated feedback data to fine-tune embeddings
- Custom embedding model for library science domain

### 5.4 Confidence-based Automation
- Auto-accept subjects with score > 0.95
- Auto-reject with score < 0.4
- Human review: 0.4 ≤ score ≤ 0.95

---

## Implementation Priority

### Immediate (1-2 weeks)
1. ✅ MVP complete
2. Create feedback logging endpoint
3. Basic evaluation script with 10-20 test cases

### Short-term (1-2 months)
1. Import full LCSH dataset (~460k records)
2. Import full FAST dataset (~1.9M records)
3. Implement hybrid search (vector + lexical)

### Medium-term (3-6 months)
1. LLM re-ranking implementation
2. Subject type classification
3. Comprehensive evaluation with 500+ gold records

### Long-term (6-12 months)
1. Active learning pipeline
2. Fine-tuned embeddings
3. Multi-vocabulary expansion (GTT, RERO, SWD)
4. Production deployment with monitoring

---

## Success Metrics

**Current (MVP)**:
- ✅ End-to-end workflow functional
- ✅ 8 sample authorities indexed
- ❓ No quantitative evaluation yet

**Target (Phase 2-3)**:
- Top-1 accuracy: 70%+
- Top-3 coverage: 90%+
- Cataloger acceptance rate: 75%+
- Average processing time: <5 seconds per book

**Target (Phase 4-5)**:
- Top-1 accuracy: 85%+
- Top-3 coverage: 95%+
- Cataloger acceptance rate: 90%+
- Full LCSH + FAST coverage: 2.3M authorities

---

## References

- LCSH Data: https://id.loc.gov/download/
- FAST Data: https://www.oclc.org/research/areas/data-science/fast.html
- Weaviate Hybrid Search: https://weaviate.io/developers/weaviate/search/hybrid
- OpenAI Responses API: https://platform.openai.com/docs/api-reference/responses

---

**Last Updated**: 2025-12-03
**Status**: MVP Complete → Planning Phase 1
