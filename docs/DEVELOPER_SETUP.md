# 🔧 Developer Setup Guide

**Complete technical installation and configuration guide**

---

## 📋 Prerequisites

### System Requirements
- **OS:** macOS, Linux, or Windows with WSL2
- **Python:** 3.11+ (3.14 tested and recommended)
- **Docker:** Docker Desktop 4.0+
- **RAM:** Minimum 8GB, 16GB recommended
- **Disk:** 10GB free space (20GB for full LCSH dataset)

### Required Accounts
- **OpenAI API Account** - Get key from https://platform.openai.com/api-keys
- **Git** - For version control

---

## 🚀 Quick Installation

### 1. Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/subject_heading.git
cd subject_heading
```

### 2. Create Virtual Environment

```bash
# Create venv
python3 -m venv venv

# Activate (macOS/Linux)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**requirements.txt contents:**
```
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
python-multipart>=0.0.6
pydantic>=2.5.3
pydantic-settings>=2.1.0
openai>=1.30.0              # Required for o4-mini Responses API
weaviate-client>=4.4.1
python-dotenv>=1.0.0
Pillow>=10.4.0
httpx>=0.26.0
aiofiles>=23.2.1
rdflib>=7.0.0               # For LCSH N-Triples import
tqdm>=4.66.0
```

### 4. Configure Environment

```bash
# Copy template
cp .env.example .env

# Edit with your settings
nano .env  # or vim, code, etc.
```

**.env Configuration:**
```bash
# OpenAI API Configuration (REQUIRED)
OPENAI_API_KEY=sk-proj-your-key-here

# Model Configuration
DEFAULT_MODEL=o4-mini                    # Text & image processing
OCR_MODEL=o4-mini                       # Image OCR
TOPIC_MODEL=o4-mini                     # Topic generation
EXPLANATION_MODEL=o4-mini               # MARC explanations
EMBEDDING_MODEL=text-embedding-3-large  # Vector embeddings

# Responses API Setting (replaces temperature for o4-mini)
REASONING_EFFORT=high                   # Options: low, medium, high

# Weaviate Configuration
WEAVIATE_URL=http://localhost:8081      # Match docker-compose port

# Application Settings
DATA_DIR=./data/records
SAMPLES_DIR=./samples
MAX_TOPICS=10
```

### 5. Start Weaviate Database

```bash
# Start Weaviate container
docker-compose up -d

# Verify it's running
docker ps
# Should show: semitechnologies/weaviate:latest

# Check logs
docker-compose logs -f weaviate

# Wait for ready message:
# "Weaviate is ready!"
```

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  weaviate:
    image: semitechnologies/weaviate:latest
    container_name: weaviate_subject_heading
    ports:
      - "8081:8080"  # Expose on 8081 to avoid conflicts
    environment:
      QUERY_DEFAULTS_LIMIT: 25
      AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: 'true'
      PERSISTENCE_DATA_PATH: '/var/lib/weaviate'
      DEFAULT_VECTORIZER_MODULE: 'none'
      ENABLE_MODULES: ''
      CLUSTER_HOSTNAME: 'node1'
    volumes:
      - weaviate_data:/var/lib/weaviate
    restart: unless-stopped

volumes:
  weaviate_data:
    driver: local
```

### 6. Initialize Weaviate Schema

```bash
# Python console
python

>>> from authority_search import authority_search
>>> authority_search.connect()
>>> authority_search.initialize_schemas()
>>> exit()
```

**Expected output:**
```
✅ Schema initialized for LCSHSubject
✅ Schema initialized for FASTSubject
```

### 7. Import Sample Data (Testing)

```bash
# Import 1,000 test records (~$0.13)
./venv/bin/python scripts/lcsh_importer_streaming.py \
    --input subjects.nt \
    --limit 1000 \
    --batch-size 100
```

**Progress output:**
```
📊 Processing subjects.nt
🎯 Target: 1000 records
📦 Batch size: 100

Importing: 100%|████████| 1000/1000 [01:23<00:00, 12.0it/s]

✅ Import complete!
📊 Total imported: 1000
💰 Estimated cost: $0.13
⏱️ Time: 1m 23s
```

### 8. Start Application Server

```bash
# Start with auto-reload (development)
./venv/bin/python main.py

# Or use uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Server output:**
```
🚀 Starting AI Subject Heading Assistant...
📁 Data directory: data/records
🔗 Weaviate URL: http://localhost:8081
🤖 Model: o4-mini (reasoning_effort=high)
✅ Connected to Weaviate (LCSH + FAST)
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### 9. Test Installation

**Browser test:**
```bash
# Open browser
open http://localhost:8000

# Should see: Enhanced MARC Subject Search interface
```

**API test:**
```bash
# Test health endpoint
curl http://localhost:8000/api/health

# Expected response:
{
  "status": "healthy",
  "weaviate": "connected",
  "model": "o4-mini"
}
```

**Command-line test:**
```bash
# Search for a subject
./venv/bin/python scripts/search_to_marc.py "Chinese calligraphy"

# Expected output:
650 _0 $a Calligraphy, Chinese $0 http://id.loc.gov/authorities/subjects/sh85018909.
Confidence: 82.3%
```

---

## 📦 Project Structure

```
subject_heading/
├── README.md                     # User-facing documentation
├── docs/                        # Developer documentation
│   ├── DEVELOPER_SETUP.md      # This file
│   ├── API_ENDPOINTS.md        # API reference
│   ├── IMPORTING_DATA.md       # Data import guide
│   ├── COST_CALCULATOR.md      # Cost analysis
│   └── NEXT_STEPS.md           # Development roadmap
│
├── requirements.txt             # Python dependencies
├── .env.example                # Environment template
├── .env                        # Your configuration (gitignored)
├── docker-compose.yml          # Weaviate setup
├── .gitignore                  # Git ignore rules
│
├── main.py                     # FastAPI application entry
├── routes.py                   # API endpoint definitions
├── models.py                   # Pydantic data models
├── config.py                   # Configuration management
│
├── authority_search.py         # Vector search implementation
├── marc_65x_builder.py         # MARC field generation
├── llm_topics.py              # Topic extraction with LLM
├── ocr_multi.py               # Multi-image OCR processing
│
├── scripts/                    # Command-line tools
│   ├── lcsh_importer_streaming.py    # Import LCSH data
│   ├── search_to_marc.py            # Search CLI
│   ├── search_to_marc_enhanced.py   # Enhanced search CLI
│   ├── monitor_weaviate.py          # Database monitoring
│   ├── generate_test_sample.py      # Generate test data
│   └── loc_realtime_search.py       # LC real-time API search
│
├── static/                     # Frontend files
│   └── index.html             # Web interface
│
├── data/                      # Data storage
│   └── records/              # Processed records
│
├── samples/                   # Sample images (gitignored)
├── logs/                     # Application logs (gitignored)
└── backups/                  # Weaviate backups (gitignored)
```

---

## 🔍 Core Components Explained

### 1. main.py
**FastAPI application server**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from routes import router
from authority_search import authority_search
from config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    print(f"🚀 Starting AI Subject Heading Assistant...")
    print(f"🤖 Model: {settings.default_model}")
    authority_search.connect()
    yield
    # Shutdown
    print(f"👋 Shutting down...")
    authority_search.disconnect()

app = FastAPI(
    title="AI Subject Heading Assistant",
    version="1.0.0",
    lifespan=lifespan
)

# CORS for browser access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)

# Serve static frontend
app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
```

### 2. config.py
**Centralized configuration**

Key features:
- Environment variable loading
- Type-safe settings with Pydantic
- O4-mini specific configuration (reasoning_effort)
- Automatic directory creation

### 3. authority_search.py
**Vector search engine**

Core methods:
- `connect()` - Connect to Weaviate
- `initialize_schemas()` - Create collections
- `index_authority_entry()` - Add single record
- `batch_index_authorities()` - Bulk import
- `search_authorities()` - Semantic search
- `_generate_embedding()` - Create vectors with OpenAI

### 4. routes.py
**API endpoints**

Key endpoints:
- `POST /api/ingest-images` - OCR processing
- `POST /api/enhanced-search` - Search with form data
- `POST /api/generate-topics` - Extract topics from metadata
- `POST /api/authority-match` - Find LCSH/FAST matches
- `POST /api/build-65x` - Generate MARC fields
- `GET /api/health` - Health check

### 5. models.py
**Data structures**

Key models:
- `BookMetadata` - Extracted book info
- `TopicCandidate` - Subject topic with type
- `AuthorityCandidate` - LCSH/FAST match
- `Subject65X` - MARC 650/651/655 field
- `IngestImagesResponse` - OCR result
- `LCSHMatchResponse` - Search result

### 6. ocr_multi.py
**Multi-image OCR processor**

Features:
- Page type classification (cover, back, TOC, etc.)
- Vision API integration with o4-mini
- Structured metadata extraction
- Error handling and retries

### 7. marc_65x_builder.py
**MARC field construction**

Features:
- Automatic tag selection (650/651/655)
- Subdivision parsing ($a, $x, $y, $z)
- Indicator generation
- Authority URI inclusion
- MARC string formatting

---

## 🧪 Testing

### Unit Tests (Coming Soon)

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_authority_search.py
```

### Manual Testing

**Test 1: OCR Processing**
```bash
# Prepare test image
cp path/to/book_cover.jpg samples/test.jpg

# Test via API
curl -X POST http://localhost:8000/api/ingest-images \
  -F "images=@samples/test.jpg"

# Expected: JSON with metadata
```

**Test 2: Subject Search**
```bash
# Via CLI
./venv/bin/python scripts/search_to_marc.py "Chinese literature"

# Expected: MARC 650 fields with scores
```

**Test 3: Enhanced Search**
```bash
# Via API
curl -X POST http://localhost:8000/api/enhanced-search \
  -F "title=Chinese Grammar" \
  -F "author=Yip Po-ching" \
  -F "keywords=Chinese language, grammar"

# Expected: MARC fields with metadata
```

### Load Testing

```bash
# Install locust
pip install locust

# Create locustfile.py
cat > locustfile.py << 'EOF'
from locust import HttpUser, task, between

class SubjectSearchUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def search_subject(self):
        self.client.post("/api/enhanced-search", data={
            "title": "Chinese calligraphy",
            "keywords": "art, China"
        })
EOF

# Run load test
locust -f locustfile.py --host=http://localhost:8000
```

---

## 🐛 Debugging

### Enable Debug Logging

```python
# In main.py, add:
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check Weaviate Status

```bash
# Monitor Weaviate
./venv/bin/python scripts/monitor_weaviate.py stats

# Expected output:
📊 Weaviate Statistics
━━━━━━━━━━━━━━━━━━━
Collection: LCSHSubject
  Records: 1000
  Vectors: 1000 (100%)
  
Collection: FASTSubject  
  Records: 0
  Vectors: 0
```

### View Logs

```bash
# Application logs
tail -f logs/app.log

# Weaviate logs
docker-compose logs -f weaviate

# Uvicorn logs
# Printed to console when running ./venv/bin/python main.py
```

### Common Issues

**Issue 1: Weaviate connection failed**
```bash
# Check if Weaviate is running
docker ps | grep weaviate

# Restart Weaviate
docker-compose restart weaviate

# Check port
lsof -i :8081
```

**Issue 2: OpenAI API errors**
```bash
# Verify API key
echo $OPENAI_API_KEY  # Should not be empty

# Test API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Expected: JSON list of models
```

**Issue 3: Import fails**
```bash
# Check file exists
ls -lh subjects.nt

# Check disk space
df -h

# Try smaller batch
./venv/bin/python scripts/lcsh_importer_streaming.py \
    --input subjects.nt \
    --limit 100 \
    --batch-size 10
```

---

## 🔒 Security Best Practices

### API Key Management

```bash
# NEVER commit .env to git
echo ".env" >> .gitignore

# Use environment variables in production
export OPENAI_API_KEY="sk-proj-..."

# Rotate keys regularly
# Get new key from: https://platform.openai.com/api-keys
```

### Weaviate Security

```yaml
# For production, enable authentication in docker-compose.yml
services:
  weaviate:
    environment:
      AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: 'false'
      AUTHENTICATION_APIKEY_ENABLED: 'true'
      AUTHENTICATION_APIKEY_ALLOWED_KEYS: 'your-secret-key'
      AUTHENTICATION_APIKEY_USERS: 'admin'
```

### Network Security

```yaml
# Restrict to localhost only
services:
  weaviate:
    ports:
      - "127.0.0.1:8081:8080"  # Only accessible from localhost
```

---

## 📊 Performance Optimization

### Weaviate Tuning

```yaml
# Increase memory for large datasets
services:
  weaviate:
    environment:
      LIMIT_RESOURCES: 'false'
    deploy:
      resources:
        limits:
          memory: 8G
```

### Batch Import Optimization

```bash
# Larger batches = faster import (but more memory)
./venv/bin/python scripts/lcsh_importer_streaming.py \
    --input subjects.nt \
    --limit 50000 \
    --batch-size 1000  # Increased from 100
```

### Embedding Cache

Embeddings are cached in Weaviate forever. Once imported:
- Searches are FREE (no re-embedding)
- Only query embedding costs $0.00013
- 10,000 searches = $1.30/month

---

## 🔄 Backup & Restore

### Backup Weaviate Data

```bash
# Stop Weaviate
docker-compose stop weaviate

# Create backup
docker run --rm \
  -v subject_heading_weaviate_data:/data \
  -v $(pwd)/backups:/backup \
  ubuntu tar czf /backup/weaviate_$(date +%Y%m%d).tar.gz /data

# Restart Weaviate
docker-compose start weaviate
```

### Restore from Backup

```bash
# Stop and remove Weaviate
docker-compose down

# Restore data
docker run --rm \
  -v subject_heading_weaviate_data:/data \
  -v $(pwd)/backups:/backup \
  ubuntu tar xzf /backup/weaviate_20241205.tar.gz -C /

# Start Weaviate
docker-compose up -d
```

---

## 🚀 Production Deployment

### Environment-Specific Settings

```bash
# development.env
REASONING_EFFORT=medium
DEBUG=true

# production.env
REASONING_EFFORT=high
DEBUG=false
WEAVIATE_URL=http://weaviate-prod:8080
```

### Systemd Service (Linux)

```bash
# Create service file
sudo nano /etc/systemd/system/subject-heading.service
```

```ini
[Unit]
Description=AI Subject Heading Assistant
After=network.target docker.service

[Service]
Type=simple
User=library
WorkingDirectory=/opt/subject_heading
Environment="PATH=/opt/subject_heading/venv/bin"
ExecStart=/opt/subject_heading/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start
sudo systemctl enable subject-heading
sudo systemctl start subject-heading
sudo systemctl status subject-heading
```

### Nginx Reverse Proxy

```nginx
# /etc/nginx/sites-available/subject-heading
server {
    listen 80;
    server_name subjects.library.edu;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Increase upload size for images
    client_max_body_size 20M;
}
```

---

## 📚 Additional Resources

- **FastAPI Docs:** https://fastapi.tiangolo.com/
- **Weaviate Docs:** https://weaviate.io/developers/weaviate
- **OpenAI API:** https://platform.openai.com/docs/api-reference
- **LCSH Data:** https://id.loc.gov/download/
- **Pydantic:** https://docs.pydantic.dev/

---

## ✅ Setup Checklist

- [ ] Python 3.11+ installed
- [ ] Docker Desktop running
- [ ] Repository cloned
- [ ] Virtual environment created
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] .env file configured with OpenAI API key
- [ ] Weaviate started (`docker-compose up -d`)
- [ ] Weaviate schema initialized
- [ ] Test data imported (1,000+ records)
- [ ] Server starts successfully
- [ ] Browser loads http://localhost:8000
- [ ] Search test returns results
- [ ] OCR test processes images

**Next step:** Import production data (see [IMPORTING_DATA.md](IMPORTING_DATA.md))

---

**Last Updated:** December 5, 2025  
**Maintainer:** Development Team
