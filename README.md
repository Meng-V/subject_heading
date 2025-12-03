## AI Subject Heading Assistant V2 - Multi-Image & 65X Support

**Enhanced backend with multi-image OCR, page classification, topic types, multi-vocabulary authority search, and full MARC 65X family support.**

## 🆕 What's New in V2

### Multi-Image Input
- Upload **multiple page images** (front cover, back cover, inner flaps, TOC pages, preface pages)
- **Automatic page classification** (front_cover, back_cover, flap, toc, preface, other)
- **Aggregated metadata extraction** from all pages

### Topic Type Classification
- Topics classified as:
  - **topical** - subject matter, themes, concepts
  - **geographic** - places, regions, countries  
  - **genre** - form/genre terms

### Multi-Vocabulary Support
- Search across multiple authority vocabularies:
  - **LCSH** (Library of Congress Subject Headings)
  - **FAST** (Faceted Application of Subject Terminology)
  - **GTT**, **RERO**, **SWD**, **idszbz**, **ram**, and more
- Unified vector search across all vocabularies

### Full 65X MARC Family
- Generate **650** (Topical Terms)
- Generate **651** (Geographic Names)
- Generate **655** (Genre/Form Terms)
- Automatic tag selection based on topic type
- Proper indicators and $2 subfields for each vocabulary

### Vocabulary-Aware MARC Generation
```
LCSH:      650 _0 $a Calligraphy, Chinese $y Ming-Qing dynasties, 1368-1912 $0 http://id.loc.gov/...
FAST:      650 _7 $a Calligraphy, Chinese $2 fast $0 (OCoLC)fst00844437
Geographic: 651 _0 $a China $x Civilization
Genre:     655 _7 $a Conference papers $2 fast
```

## 📦 New Modules

### Core V2 Files

- **`ocr_multi.py`** - Multi-image OCR with page classification
- **`authority_search.py`** - Multi-vocabulary vector search (replaces `lcsh_index.py`)
- **`marc_65x_builder.py`** - Full 65X family builder (650/651/655)
- **`routes_v2.py`** - Enhanced API endpoints
- **`main_v2.py`** - V2 FastAPI app with both v1 and v2 routes
- **`test_workflow_v2.py`** - V2 workflow testing

### Updated Existing Files

- **`models.py`** - Added PageImage, AuthorityCandidate, MARCField65X, topic types
- **`llm_topics.py`** - Added topic type classification

## 🚀 Quick Start V2

### 1. Start the V2 Server

```bash
cd backend
python main_v2.py
```

Server runs on http://localhost:8000

### 2. Initialize V2 Data

```bash
python test_workflow_v2.py init
```

This initializes:
- Multi-vocabulary Weaviate schemas (LCSHSubject, FASTSubject, etc.)
- Sample LCSH and FAST authority data

### 3. Run V2 Test Workflow

```bash
python test_workflow_v2.py
```

## 📚 V2 API Endpoints

### Core Workflow

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v2/api/ingest-images` | POST | Multi-image OCR with page hints |
| `/v2/api/generate-topics` | POST | Generate typed topics |
| `/v2/api/authority-match-typed` | POST | Multi-vocabulary authority search |
| `/v2/api/build-65x` | POST | Build 65X MARC fields |
| `/v2/api/submit-final` | POST | Save final record |

### Admin

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v2/api/initialize-authorities` | POST | Initialize schemas |
| `/v2/api/index-sample-authorities` | POST | Load sample data |
| `/v2/api/authority-stats` | GET | Get index statistics |

### Legacy V1 Endpoints

All original V1 endpoints still available at `/api/*` for backward compatibility.

## 🔧 V2 Workflow Example

### 1. Upload Multiple Images

```bash
curl -X POST http://localhost:8000/v2/api/ingest-images \
  -F "images=@cover.jpg" \
  -F "images=@back.jpg" \
  -F "images=@toc_page1.jpg" \
  -F "images=@toc_page2.jpg" \
  -F "images=@preface.jpg" \
  -F "images=@flap.jpg" \
  -F 'page_hints=["front_cover","back_cover","toc","toc","preface","flap"]'
```

Response includes classified pages:
```json
{
  "success": true,
  "metadata": {
    "title": "...",
    "summary": "...",
    "table_of_contents": [...],
    "preface_snippets": [...],
    "raw_pages": [
      {"page_type": "front_cover", "text": "..."},
      {"page_type": "back_cover", "text": "..."},
      ...
    ]
  }
}
```

### 2. Generate Typed Topics

```bash
curl -X POST http://localhost:8000/v2/api/generate-topics \
  -H "Content-Type: application/json" \
  -d '{
    "metadata": {...}
  }'
```

Response includes topic types:
```json
{
  "topics": [
    {"topic": "Chinese calligraphy techniques", "type": "topical"},
    {"topic": "China", "type": "geographic"},
    {"topic": "Handbooks and manuals", "type": "genre"}
  ]
}
```

### 3. Multi-Vocabulary Authority Search

```bash
curl -X POST http://localhost:8000/v2/api/authority-match-typed \
  -H "Content-Type: application/json" \
  -d '{
    "topics": [
      {"topic": "Chinese calligraphy", "type": "topical"},
      {"topic": "China", "type": "geographic"}
    ],
    "vocabularies": ["lcsh", "fast", "gtt"]
  }'
```

Response includes matches from all vocabularies:
```json
{
  "matches": [
    {
      "topic": "Chinese calligraphy",
      "topic_type": "topical",
      "authority_candidates": [
        {
          "label": "Calligraphy, Chinese",
          "uri": "http://id.loc.gov/authorities/subjects/sh85018909",
          "vocabulary": "lcsh",
          "score": 0.93
        },
        {
          "label": "Calligraphy, Chinese",
          "uri": "(OCoLC)fst00844437",
          "vocabulary": "fast",
          "score": 0.89
        }
      ]
    }
  ]
}
```

### 4. Build 65X MARC Fields

```bash
curl -X POST http://localhost:8000/v2/api/build-65x \
  -H "Content-Type: application/json" \
  -d '{
    "topics_with_candidates": [...]
  }'
```

Response includes full 65X fields:
```json
{
  "subjects_65x": [
    {
      "tag": "650",
      "ind1": "_",
      "ind2": "0",
      "subfields": [
        {"code": "a", "value": "Calligraphy, Chinese"},
        {"code": "0", "value": "http://id.loc.gov/..."}
      ],
      "vocabulary": "lcsh",
      "explanation": "Primary subject focusing on Chinese calligraphy art form."
    },
    {
      "tag": "651",
      "ind1": "_",
      "ind2": "0",
      "subfields": [
        {"code": "a", "value": "China"},
        {"code": "x", "value": "Civilization"}
      ],
      "vocabulary": "lcsh",
      "explanation": "Geographic focus on Chinese civilization."
    },
    {
      "tag": "650",
      "ind1": "_",
      "ind2": "7",
      "subfields": [
        {"code": "a", "value": "Calligraphy, Chinese"},
        {"code": "0", "value": "(OCoLC)fst00844437"},
        {"code": "2", "value": "fast"}
      ],
      "vocabulary": "fast",
      "explanation": "FAST topical term for Chinese calligraphy."
    }
  ]
}
```

## 🗂️ Vocabulary Mapping Table

| Vocabulary | ind2 | $2 subfield | URI Pattern |
|------------|------|-------------|-------------|
| **lcsh** | 0 | (none) | http://id.loc.gov/authorities/subjects/... |
| **fast** | 7 | fast | (OCoLC)fst... |
| **gtt** | 7 | gtt | ... |
| **rero** | 7 | rero | ... |
| **swd** | 7 | swd | ... |
| **idszbz** | 7 | idszbz | ... |
| **ram** | 7 | ram | ... |

## 📊 Subfield Codes

| Code | Description | Example |
|------|-------------|---------|
| **$a** | Main heading | Calligraphy, Chinese |
| **$x** | General subdivision | Techniques |
| **$y** | Chronological subdivision | Ming-Qing dynasties, 1368-1912 |
| **$z** | Geographic subdivision | Beijing |
| **$v** | Form subdivision | Congresses |
| **$0** | Authority record URI | http://id.loc.gov/... |
| **$2** | Source of heading | fast, gtt, rero, etc. |

## 🔄 Migration from V1 to V2

### V1 Code (Legacy)
```python
# Single image
response = await client.post("/api/ingest-images",
    files={"cover": cover_bytes})

# Single vocabulary
response = await client.post("/api/lcsh-match",
    json={"topics": ["Chinese art"]})

# Only 650 fields
response = await client.post("/api/marc650",
    json={"lcsh_selections": [...]})
```

### V2 Code (Enhanced)
```python
# Multiple images with hints
response = await client.post("/v2/api/ingest-images",
    files=[("images", cover), ("images", back), ("images", toc)],
    data={"page_hints": '["front_cover","back_cover","toc"]'})

# Multiple vocabularies with types
response = await client.post("/v2/api/authority-match-typed",
    json={
        "topics": [{"topic": "Chinese art", "type": "topical"}],
        "vocabularies": ["lcsh", "fast", "gtt"]
    })

# Full 65X family
response = await client.post("/v2/api/build-65x",
    json={"topics_with_candidates": [...]})
```

## 🧪 Testing

### Run All Tests

```bash
# Initialize V2 data
python test_workflow_v2.py init

# Run V2 workflow test
python test_workflow_v2.py

# Run V1 compatibility test
python test_workflow.py
```

### Interactive API Docs

Visit http://localhost:8000/docs for interactive Swagger UI with:
- All V1 and V2 endpoints
- Request/response schemas
- Try-it-out functionality

## 📂 Project Structure (V2)

```
backend/
├── main_v2.py              # V2 FastAPI app
├── routes_v2.py            # V2 API routes
├── ocr_multi.py            # Multi-image OCR
├── authority_search.py     # Multi-vocabulary search
├── marc_65x_builder.py     # 65X field builder
├── test_workflow_v2.py     # V2 testing script
├── models.py               # Updated models (v1+v2)
├── llm_topics.py           # Updated with types
├── config.py               # Configuration
├── main.py                 # V1 app (legacy)
├── routes.py               # V1 routes (legacy)
├── ocr.py                  # V1 OCR (legacy)
├── lcsh_index.py           # V1 LCSH only (legacy)
├── marc_builder.py         # V1 650 only (legacy)
└── test_workflow.py        # V1 testing (legacy)
```

## 🎯 Key Improvements

### Accuracy
- ✅ Topic types improve authority matching precision
- ✅ Multi-vocabulary search increases coverage
- ✅ Page classification extracts better metadata

### Flexibility
- ✅ Support any vocabulary via extensible design
- ✅ Automatic tag selection (650/651/655)
- ✅ Proper $2 subfield for non-LCSH sources

### Usability
- ✅ Natural language explanations for each field
- ✅ Confidence scores for all matches
- ✅ Structured JSON for frontend integration

## 🚧 Future Enhancements

- [ ] Add more vocabularies (GTT, RERO, SWD real data)
- [ ] LLM-based page hint refinement
- [ ] Batch processing for multiple books
- [ ] Export to MARCXML format
- [ ] Authority record linking and validation

## 📖 Documentation

- Full API docs: http://localhost:8000/docs
- V1 README: [README.md](README.md)
- Quick start: [QUICKSTART.md](QUICKSTART.md)
- Original spec: [../guide.md](../guide.md)

## ⚙️ Configuration

Same `.env` file as V1, no additional configuration needed.

## 🎓 Need Help?

- Check interactive docs: http://localhost:8000/docs
- Run test script: `python test_workflow_v2.py`
- Review V2 spec in user request
- Check V1 docs: [README.md](README.md)
