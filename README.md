## AI Subject Heading Assistant - Multi-Image & 65X Support

AI-powered subject heading generation for library cataloging, using OpenAI gpt-4o-mini.

## Features

- **Multi-Image OCR**: Upload multiple book pages (cover, back, TOC, preface, flaps)
- **Page Classification**: Automatic detection of page types
- **Topic Generation**: AI-generated topics with type classification (topical/geographic/genre)
- **Authority Matching**: Vector search against LCSH and FAST vocabularies
- **MARC 65X Generation**: Full 650/651/655 field generation with proper indicators

## Technology Stack

| Component | Technology |
|-----------|------------|
| **AI Model** | gpt-4o-mini (Chat Completions API) |
| **Quality Control** | `temperature=0.1` for consistency |
| **Embeddings** | text-embedding-3-large |
| **Vector DB** | Weaviate (local Docker) |
| **Backend** | FastAPI + Python 3.11+ |
| **Vocabularies** | LCSH, FAST (MVP scope) |

## Quick Start

### 1. Prerequisites

- Python 3.11+
- Docker Desktop
- OpenAI API key

### 2. Clone and Setup

```bash
cd subject_heading

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
# Copy example config
cp .env.example .env

# Edit .env and add your OpenAI API key
nano .env  # or use your preferred editor
```

Your `.env` should contain:
```bash
OPENAI_API_KEY=sk-your-actual-api-key-here
WEAVIATE_URL=http://localhost:8080
REASONING_EFFORT=high
```

### 4. Start Weaviate

```bash
docker-compose up -d
```

### 5. Run the Server

```bash
python main.py
```

Or with uvicorn directly:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 6. Initialize Database

Open a new terminal and run:
```bash
# Initialize authority schemas
curl -X POST http://localhost:8000/api/initialize-authorities

# Load sample data (optional)
curl -X POST http://localhost:8000/api/index-sample-authorities
```

### 7. Access the API

- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health

## API Workflow

```
Upload Images -> Generate Topics -> Match Authority -> Build 65X -> Submit Final
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/ingest-images` | POST | Upload book images for OCR |
| `/api/generate-topics` | POST | Generate typed topic candidates |
| `/api/authority-match` | POST | Search LCSH/FAST authorities |
| `/api/build-65x` | POST | Generate Subject65X objects |
| `/api/submit-final` | POST | Save final record |
| `/api/health` | GET | Health check |
| `/api/authority-stats` | GET | Index statistics |
| `/api/initialize-authorities` | POST | Initialize Weaviate schemas |
| `/api/index-sample-authorities` | POST | Load sample data |

## Subject65X Model

The primary output format for subject headings:

```json
{
  "tag": "650",
  "ind1": "_",
  "ind2": "0",
  "vocabulary": "lcsh",
  "heading_string": "Calligraphy, Chinese -- Ming-Qing dynasties, 1368-1912",
  "subfields": [
    {"code": "a", "value": "Calligraphy, Chinese"},
    {"code": "y", "value": "Ming-Qing dynasties, 1368-1912"}
  ],
  "uri": "http://id.loc.gov/authorities/subjects/sh85018910",
  "authority_id": "sh85018910",
  "source_system": "ai_generated",
  "score": 0.92,
  "explanation": "Primary subject covering Chinese calligraphy.",
  "status": "suggested"
}
```

## MARC Examples

### LCSH (ind2=0)
```
650 _0 $a Calligraphy, Chinese $y Ming-Qing dynasties, 1368-1912.
651 _0 $a China $x Civilization.
655 _0 $a Conference papers and proceedings.
```

### FAST (ind2=7, $2 fast)
```
650 _7 $a Calligraphy, Chinese $2 fast $0 (OCoLC)fst00844437
651 _7 $a China $2 fast $0 (OCoLC)fst01206073
```

## Project Structure

```
subject_heading/
├── main.py              # FastAPI application
├── routes.py            # API endpoints
├── config.py            # Configuration settings
├── models.py            # Pydantic models
├── ocr_multi.py         # Multi-image OCR processor
├── llm_topics.py        # Topic generation
├── authority_search.py  # LCSH/FAST vector search
├── marc_65x_builder.py  # MARC 65X field builder
├── docker-compose.yml   # Weaviate service
├── requirements.txt     # Python dependencies
├── .env.example         # Environment template
└── scripts/
    └── lcsh_importer.py # LCSH data importer
```

## Configuration

All settings in `.env`:

```bash
# OpenAI
OPENAI_API_KEY=sk-...

# Models (all use gpt-4o-mini)
DEFAULT_MODEL=gpt-4o-mini
OCR_MODEL=gpt-4o-mini
TOPIC_MODEL=gpt-4o-mini
EXPLANATION_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-large

# Weaviate
WEAVIATE_URL=http://localhost:8080

# Storage
DATA_DIR=./data/records
MAX_TOPICS=10
```

## Vocabulary Scope (MVP)

| Vocabulary | ind2 | $2 | Active |
|------------|------|-----|--------|
| **LCSH** | 0 | - | Yes |
| **FAST** | 7 | fast | Yes |
| GTT | 7 | gtt | Future |
| RERO | 7 | rero | Future |

## License

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
- Request/response schemas
- Try-it-out functionality

## 📂 Project Structure

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
- Quick start: [QUICKSTART.md](QUICKSTART.md)
- Original spec: [../guide.md](../guide.md)

## ⚙️ Configuration

Same `.env` file as V1, no additional configuration needed.

## 🎓 Need Help?

- Check interactive docs: http://localhost:8000/docs
- Run test script: `python test_workflow_v2.py`
