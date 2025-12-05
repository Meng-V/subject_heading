# 🔌 API Endpoints Reference

**Complete API documentation for developers**

---

## 📡 Base URL

```
http://localhost:8000
```

**Production:** Replace with your deployed domain

---

## 🚀 Quick Start

### Test Server

```bash
# Health check
curl http://localhost:8000/api/health

# Expected response:
{
  "status": "healthy",
  "weaviate": "connected",
  "model": "o4-mini",
  "embedding_model": "text-embedding-3-large",
  "collections": {
    "lcsh": 20000,
    "fast": 0
  }
}
```

### Interactive Documentation

**Swagger UI:**
```
http://localhost:8000/docs
```

**ReDoc:**
```
http://localhost:8000/redoc
```

---

## 📚 Endpoints Overview

| Method | Endpoint | Purpose | Cost |
|--------|----------|---------|------|
| GET | `/` | Serve frontend | Free |
| GET | `/api/health` | Health check | Free |
| POST | `/api/ingest-images` | OCR processing | ~$0.001 |
| POST | `/api/enhanced-search` | Search with metadata | ~$0.0001 |
| POST | `/api/generate-topics` | Extract topics | ~$0.0003 |
| POST | `/api/authority-match` | Find LCSH/FAST matches | ~$0.0001 |
| POST | `/api/build-65x` | Generate MARC fields | Free |
| POST | `/api/submit-final` | Complete workflow | ~$0.001 |

---

## 🔍 Detailed Endpoint Documentation

### 1. Health Check

**GET** `/api/health`

Check system status and connectivity.

**Request:**
```bash
curl http://localhost:8000/api/health
```

**Response:**
```json
{
  "status": "healthy",
  "weaviate": "connected",
  "weaviate_url": "http://localhost:8081",
  "model": "o4-mini",
  "embedding_model": "text-embedding-3-large",
  "collections": {
    "lcsh": 20000,
    "fast": 0
  },
  "version": "1.0.0"
}
```

**Status Codes:**
- `200 OK` - All systems operational
- `503 Service Unavailable` - Weaviate disconnected

---

### 2. Image Ingestion (OCR)

**POST** `/api/ingest-images`

Process book images and extract metadata using OCR.

**Request:**
```bash
curl -X POST http://localhost:8000/api/ingest-images \
  -F "images=@cover.jpg" \
  -F "images=@back.jpg" \
  -F "images=@toc.jpg"
```

**Request (with page hints):**
```bash
curl -X POST http://localhost:8000/api/ingest-images \
  -F "images=@cover.jpg" \
  -F "images=@back.jpg" \
  -F "images=@toc.jpg" \
  -F 'page_hints=["front_cover","back_cover","table_of_contents"]'
```

**Request Body:**
- `images` (File[], required): Multiple image files (JPG, PNG, PDF)
- `page_hints` (JSON string, optional): Array of page type hints

**Response:**
```json
{
  "success": true,
  "metadata": {
    "title": "Chinese Calligraphy: An Essential Guide",
    "author": "Wang Xizhi",
    "publisher": "University Press",
    "pub_place": "Beijing",
    "pub_year": "2023",
    "summary": "This comprehensive guide explores the art and history of Chinese calligraphy...",
    "table_of_contents": [
      "Chapter 1: Introduction to Chinese Calligraphy",
      "Chapter 2: Historical Development",
      "Chapter 3: Major Styles and Schools"
    ],
    "preface_snippets": [
      "Calligraphy has been central to Chinese culture for millennia..."
    ],
    "raw_pages": [
      {
        "page_type": "front_cover",
        "text": "Chinese Calligraphy\\nWang Xizhi",
        "confidence": 0.95
      }
    ]
  },
  "message": "Processed 3 images, identified 3 pages"
}
```

**Status Codes:**
- `200 OK` - Success
- `400 Bad Request` - Invalid image format
- `500 Internal Server Error` - OCR processing failed

**Cost:** ~$0.001 per image (using o4-mini vision)

---

### 3. Enhanced Search

**POST** `/api/enhanced-search`

Search for MARC subjects using rich book metadata.

**Request:**
```bash
curl -X POST http://localhost:8000/api/enhanced-search \
  -F "title=Chinese Calligraphy" \
  -F "author=Wang Xizhi" \
  -F "abstract=This book explores the history and techniques of Chinese calligraphy" \
  -F "keywords=calligraphy, art, China" \
  -F "limit=5" \
  -F "min_score=0.75"
```

**Request Body (Form Data):**
- `title` (string, optional): Book title
- `author` (string, optional): Author name(s)
- `abstract` (string, optional): Summary/description
- `toc` (string, optional): Table of contents (newline or comma separated)
- `keywords` (string, optional): Keywords (comma separated)
- `publisher_notes` (string, optional): Publisher description
- `limit` (integer, optional, default=5): Max results
- `min_score` (float, optional, default=0.70): Minimum confidence (0.0-1.0)

**Response:**
```json
{
  "success": true,
  "count": 3,
  "marc_fields": [
    {
      "tag": "650",
      "ind1": "_",
      "ind2": "0",
      "subfields": [
        {"code": "a", "value": "Calligraphy, Chinese"},
        {"code": "x", "value": "History"},
        {"code": "0", "value": "http://id.loc.gov/authorities/subjects/sh85018909"}
      ],
      "vocabulary": "lcsh",
      "uri": "http://id.loc.gov/authorities/subjects/sh85018909",
      "score": 0.923,
      "label": "Calligraphy, Chinese--History",
      "marc_string": "650 _0 $a Calligraphy, Chinese $x History $0 http://id.loc.gov/authorities/subjects/sh85018909."
    },
    {
      "tag": "650",
      "ind1": "_",
      "ind2": "7",
      "subfields": [
        {"code": "a", "value": "Calligraphy, Chinese"},
        {"code": "2", "value": "fast"},
        {"code": "0", "value": "(OCoLC)fst00844437"}
      ],
      "vocabulary": "fast",
      "uri": "(OCoLC)fst00844437",
      "score": 0.881,
      "label": "Calligraphy, Chinese",
      "marc_string": "650 _7 $a Calligraphy, Chinese $2 fast $0 (OCoLC)fst00844437."
    }
  ],
  "rich_query": "TITLE: Chinese Calligraphy | TOPICS: calligraphy | art | China | ABOUT: This book explores...",
  "input_fields_used": 4,
  "message": "Found 3 MARC subject heading(s)"
}
```

**Status Codes:**
- `200 OK` - Success
- `400 Bad Request` - No input fields provided
- `500 Internal Server Error` - Search failed

**Cost:** ~$0.0001 (embedding generation only)

---

### 4. Generate Topics

**POST** `/api/generate-topics`

Extract semantic topics from book metadata using LLM.

**Request:**
```bash
curl -X POST http://localhost:8000/api/generate-topics \
  -H "Content-Type: application/json" \
  -d '{
    "metadata": {
      "title": "History of Chinese Calligraphy",
      "author": "Wang Xizhi",
      "summary": "A comprehensive study of calligraphic traditions in China from ancient times to the Qing dynasty.",
      "table_of_contents": [
        "Origins and Early Development",
        "Tang Dynasty Masters",
        "Song and Yuan Innovations"
      ]
    }
  }'
```

**Request Body (JSON):**
```json
{
  "metadata": {
    "title": "string",
    "author": "string (optional)",
    "summary": "string (optional)",
    "table_of_contents": ["string"] // optional
  }
}
```

**Response:**
```json
{
  "success": true,
  "topics": [
    {
      "topic": "Calligraphy, Chinese",
      "type": "topical",
      "confidence": 0.95,
      "source": "title, summary"
    },
    {
      "topic": "China--History",
      "type": "geographic",
      "confidence": 0.88,
      "source": "summary, table_of_contents"
    },
    {
      "topic": "Art, Chinese",
      "type": "topical",
      "confidence": 0.82,
      "source": "title, summary"
    }
  ],
  "message": "Generated 3 topic candidates"
}
```

**Status Codes:**
- `200 OK` - Success
- `400 Bad Request` - Invalid metadata
- `500 Internal Server Error` - LLM processing failed

**Cost:** ~$0.0003 (o4-mini text processing)

---

### 5. Authority Match

**POST** `/api/authority-match`

Find LCSH/FAST authority matches for topics.

**Request:**
```bash
curl -X POST http://localhost:8000/api/authority-match \
  -H "Content-Type: application/json" \
  -d '{
    "topics": [
      "Chinese calligraphy",
      "Ming dynasty art"
    ],
    "vocabularies": ["lcsh", "fast"],
    "limit_per_vocab": 5,
    "min_score": 0.75
  }'
```

**Request Body (JSON):**
```json
{
  "topics": ["string"],             // Required: list of topics
  "vocabularies": ["lcsh", "fast"], // Optional: default ["lcsh", "fast"]
  "limit_per_vocab": 5,             // Optional: default 5
  "min_score": 0.70                 // Optional: default 0.70
}
```

**Response:**
```json
{
  "success": true,
  "matches": [
    {
      "topic": "Chinese calligraphy",
      "topic_type": "topical",
      "authority_candidates": [
        {
          "label": "Calligraphy, Chinese",
          "uri": "http://id.loc.gov/authorities/subjects/sh85018909",
          "vocabulary": "lcsh",
          "score": 0.923,
          "subject_type": "topical"
        },
        {
          "label": "Calligraphy, Chinese",
          "uri": "(OCoLC)fst00844437",
          "vocabulary": "fast",
          "score": 0.881,
          "subject_type": "topical"
        }
      ],
      "matches": []  // Legacy field (deprecated)
    }
  ],
  "message": "Found LCSH/FAST matches for 2 topics"
}
```

**Status Codes:**
- `200 OK` - Success
- `400 Bad Request` - Invalid topic format
- `500 Internal Server Error` - Search failed

**Cost:** ~$0.0001 per topic (embedding generation)

---

### 6. Build MARC 65X Fields

**POST** `/api/build-65x`

Convert authority candidates to formatted MARC 650/651/655 fields.

**Request:**
```bash
curl -X POST http://localhost:8000/api/build-65x \
  -H "Content-Type: application/json" \
  -d '{
    "candidates": [
      {
        "label": "Calligraphy, Chinese--History",
        "uri": "http://id.loc.gov/authorities/subjects/sh85018909",
        "vocabulary": "lcsh",
        "score": 0.92,
        "subject_type": "topical"
      }
    ],
    "include_explanation": true
  }'
```

**Request Body (JSON):**
```json
{
  "candidates": [
    {
      "label": "string",
      "uri": "string",
      "vocabulary": "lcsh or fast",
      "score": 0.0-1.0,
      "subject_type": "topical, geographic, or genre_form (optional)"
    }
  ],
  "include_explanation": false  // Optional: add LLM-generated explanation
}
```

**Response:**
```json
{
  "success": true,
  "marc_fields": [
    {
      "tag": "650",
      "ind1": "_",
      "ind2": "0",
      "subfields": [
        {"code": "a", "value": "Calligraphy, Chinese"},
        {"code": "x", "value": "History"},
        {"code": "0", "value": "http://id.loc.gov/authorities/subjects/sh85018909"}
      ],
      "vocabulary": "lcsh",
      "uri": "http://id.loc.gov/authorities/subjects/sh85018909",
      "score": 0.92,
      "explanation": "This subject heading represents works about the historical development and evolution of Chinese calligraphic traditions."
    }
  ],
  "message": "Generated 1 MARC 65X field(s)"
}
```

**Status Codes:**
- `200 OK` - Success
- `400 Bad Request` - Invalid candidate format
- `500 Internal Server Error` - MARC generation failed

**Cost:** Free (no AI calls), or ~$0.0002 if `include_explanation=true`

---

### 7. Submit Final Record

**POST** `/api/submit-final`

Complete workflow: validate and prepare final record for cataloging system.

**Request:**
```bash
curl -X POST http://localhost:8000/api/submit-final \
  -H "Content-Type: application/json" \
  -d '{
    "metadata": {
      "title": "Chinese Calligraphy",
      "author": "Wang Xizhi"
    },
    "marc_fields": [
      {
        "tag": "650",
        "ind1": "_",
        "ind2": "0",
        "subfields": [
          {"code": "a", "value": "Calligraphy, Chinese"}
        ]
      }
    ],
    "cataloger_notes": "Verified against LC authorities"
  }'
```

**Request Body (JSON):**
```json
{
  "metadata": {
    "title": "string",
    "author": "string (optional)"
  },
  "marc_fields": [
    {
      "tag": "650/651/655",
      "ind1": "string",
      "ind2": "string",
      "subfields": [
        {"code": "a/x/y/z/0/2", "value": "string"}
      ]
    }
  ],
  "cataloger_notes": "string (optional)"
}
```

**Response:**
```json
{
  "success": true,
  "record": {
    "metadata": {...},
    "marc_fields": [...],
    "cataloger_notes": "...",
    "timestamp": "2024-12-05T14:30:00Z",
    "workflow_status": "completed"
  },
  "message": "Record prepared for cataloging system"
}
```

**Status Codes:**
- `200 OK` - Success
- `400 Bad Request` - Validation failed
- `500 Internal Server Error` - Processing failed

**Cost:** Free (validation only)

---

## 🔐 Authentication (Future)

Currently, the API has no authentication (local use only).

**For production deployment, implement:**

```python
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

@router.post("/api/enhanced-search")
async def enhanced_search(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    ...
):
    # Verify token
    if not verify_token(credentials.credentials):
        raise HTTPException(status_code=401, detail="Invalid token")
    ...
```

---

## 📊 Rate Limiting (Future)

**Recommended limits:**

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/api/ingest-images")
@limiter.limit("10/minute")  # 10 requests per minute
async def ingest_images(...):
    ...
```

---

## 🔍 Error Responses

**Standard error format:**

```json
{
  "detail": "Error message describing what went wrong",
  "error_code": "SPECIFIC_ERROR_CODE",
  "timestamp": "2024-12-05T14:30:00Z"
}
```

**Common errors:**

| Status | Error | Meaning |
|--------|-------|---------|
| 400 | Invalid input | Missing or malformed request data |
| 401 | Unauthorized | Authentication required (future) |
| 403 | Forbidden | Insufficient permissions (future) |
| 404 | Not found | Endpoint or resource doesn't exist |
| 429 | Too many requests | Rate limit exceeded (future) |
| 500 | Internal error | Server-side processing failed |
| 503 | Service unavailable | Weaviate disconnected or OpenAI down |

---

## 🧪 Testing Endpoints

### Python Examples

```python
import requests

# Enhanced search
response = requests.post(
    "http://localhost:8000/api/enhanced-search",
    data={
        "title": "Chinese Calligraphy",
        "keywords": "art, China",
        "limit": 5,
        "min_score": 0.75
    }
)

result = response.json()
print(f"Found {result['count']} MARC fields")

for field in result['marc_fields']:
    print(f"{field['marc_string']} ({field['score']*100:.1f}%)")
```

### JavaScript Examples

```javascript
// Image upload with OCR
const formData = new FormData();
formData.append('images', fileInput.files[0]);
formData.append('images', fileInput.files[1]);

const response = await fetch('http://localhost:8000/api/ingest-images', {
    method: 'POST',
    body: formData
});

const data = await response.json();
console.log('Extracted:', data.metadata.title);
```

### cURL Examples

```bash
# Health check
curl http://localhost:8000/api/health

# Search with form data
curl -X POST http://localhost:8000/api/enhanced-search \
  -F "title=Chinese Art" \
  -F "keywords=painting, Ming dynasty"

# Search with JSON
curl -X POST http://localhost:8000/api/authority-match \
  -H "Content-Type: application/json" \
  -d '{"topics": ["Chinese painting"]}'
```

---

## 📈 Performance Metrics

**Typical response times:**

| Endpoint | Average | P95 | P99 |
|----------|---------|-----|-----|
| `/api/health` | 5ms | 10ms | 20ms |
| `/api/ingest-images` (1 image) | 2s | 3s | 5s |
| `/api/enhanced-search` | 150ms | 300ms | 500ms |
| `/api/generate-topics` | 800ms | 1.5s | 2s |
| `/api/authority-match` | 100ms | 200ms | 400ms |
| `/api/build-65x` | 10ms | 20ms | 50ms |

**Factors affecting performance:**
- Number of images (OCR)
- LCSH database size (search)
- OpenAI API latency (variable)
- Network conditions

---

## 🔧 CORS Configuration

**Current settings (development):**

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Production settings (recommended):**

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://catalog.library.edu",
        "https://subjects.library.edu"
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)
```

---

## 📚 Client Libraries (Future)

**Python client:**
```python
from subject_heading_client import SubjectHeadingAPI

api = SubjectHeadingAPI("http://localhost:8000")
results = api.search(title="Chinese Art", keywords="Ming dynasty")

for field in results.marc_fields:
    print(field.marc_string)
```

**JavaScript client:**
```javascript
import { SubjectHeadingAPI } from 'subject-heading-client';

const api = new SubjectHeadingAPI('http://localhost:8000');
const results = await api.search({
    title: 'Chinese Art',
    keywords: 'Ming dynasty'
});
```

---

## ✅ Quick Reference

**Most used endpoints:**

```bash
# 1. Upload images
curl -X POST http://localhost:8000/api/ingest-images \
  -F "images=@cover.jpg"

# 2. Search for subjects
curl -X POST http://localhost:8000/api/enhanced-search \
  -F "title=Your Book Title" \
  -F "keywords=topic1, topic2"

# 3. Check system health
curl http://localhost:8000/api/health
```

**Complete workflow:**

```bash
# 1. OCR → 2. Search → 3. Copy MARC fields
curl -X POST http://localhost:8000/api/ingest-images \
  -F "images=@book_cover.jpg" \
  | jq -r '.metadata | "title=\(.title)&keywords=\(.title | split(" ") | join(","))"' \
  | xargs -I {} curl -X POST http://localhost:8000/api/enhanced-search -d "{}" \
  | jq -r '.marc_fields[].marc_string'
```

---

**Last Updated:** December 5, 2024  
**API Version:** 1.0.0  
**Next:** [COST_CALCULATOR.md](COST_CALCULATOR.md) | [NEXT_STEPS.md](NEXT_STEPS.md)
