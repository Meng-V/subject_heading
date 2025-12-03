# AI Subject Heading Assistant - Backend

An AI-powered backend system for automating library subject heading generation using OpenAI, Weaviate vector search, and LCSH (Library of Congress Subject Headings).

## 🚀 Features

- **OCR Module**: Extract book metadata from cover images using OpenAI Vision (o4-mini)
- **Topic Generation**: Generate semantic topics using OpenAI o4-mini
- **Vector Search**: Match topics to LCSH authority headings using Weaviate
- **MARC Builder**: Automatically generate MARC 650 fields
- **Data Storage**: Store librarian selections as JSON for continual improvement

## 📋 Requirements

- Python 3.10+
- Docker & Docker Compose (for Weaviate)
- OpenAI API key

## 🛠️ Installation

### 1. Clone and Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

Copy the example environment file and add your OpenAI API key:

```bash
cp .env.example .env
```

Edit `.env` and add your credentials:

```env
OPENAI_API_KEY=your_actual_openai_api_key_here
```

### 3. Start Weaviate

Start the Weaviate vector database using Docker Compose:

```bash
docker-compose up -d
```

Verify Weaviate is running:

```bash
curl http://localhost:8080/v1/meta
```

### 4. Initialize LCSH Schema

Start the FastAPI server:

```bash
python main.py
```

Initialize the LCSH schema (one-time setup):

```bash
curl -X POST http://localhost:8000/api/initialize-lcsh
```

### 5. Index Sample LCSH Data

Index sample LCSH entries for testing:

```bash
curl -X POST http://localhost:8000/api/index-lcsh-sample
```

## 🎯 Usage

### Starting the Server

```bash
# Development mode with auto-reload
python main.py

# Production mode
uvicorn main:app --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Complete Workflow Example

#### 1. Upload Images and Extract Metadata

```bash
curl -X POST http://localhost:8000/api/ingest-images \
  -F "cover=@samples/cover.jpg" \
  -F "back=@samples/back.jpg" \
  -F "toc=@samples/toc.jpg"
```

#### 2. Generate Topic Candidates

```bash
curl -X POST http://localhost:8000/api/generate-topics \
  -H "Content-Type: application/json" \
  -d '{
    "metadata": {
      "title": "Chinese Calligraphy",
      "author": "Zhang Wei",
      "summary": "A comprehensive guide to Chinese calligraphy...",
      "toc": ["Introduction", "History", "Techniques"]
    }
  }'
```

#### 3. Match LCSH Headings

```bash
curl -X POST http://localhost:8000/api/lcsh-match \
  -H "Content-Type: application/json" \
  -d '{
    "topics": [
      "Chinese calligraphy techniques",
      "History of Chinese brush painting"
    ]
  }'
```

#### 4. Generate MARC 650 Fields

```bash
curl -X POST http://localhost:8000/api/marc650 \
  -H "Content-Type: application/json" \
  -d '{
    "lcsh_selections": [
      {
        "label": "Calligraphy, Chinese -- Ming-Qing dynasties, 1368-1912",
        "uri": "http://id.loc.gov/authorities/subjects/sh85018910",
        "certainty": 0.89
      }
    ]
  }'
```

#### 5. Submit Final Record

```bash
curl -X POST http://localhost:8000/api/submit-final \
  -H "Content-Type: application/json" \
  -d @final_record.json
```

## 📁 Project Structure

```
backend/
├── main.py              # FastAPI application entry point
├── config.py            # Configuration management
├── models.py            # Pydantic models
├── routes.py            # API endpoints
├── ocr.py              # OCR module (OpenAI Vision)
├── llm_topics.py       # Topic generation (OpenAI o1-mini)
├── lcsh_index.py       # Weaviate vector search
├── marc_builder.py     # MARC 650 field builder
├── requirements.txt    # Python dependencies
├── docker-compose.yml  # Weaviate deployment
├── .env.example        # Environment template
├── data/               # JSON storage directory
│   └── records/        # Saved cataloging records
└── samples/            # Sample test images
```

## 🔧 API Endpoints

### Core Workflow

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/ingest-images` | POST | Extract metadata from book images |
| `/api/generate-topics` | POST | Generate semantic topic candidates |
| `/api/lcsh-match` | POST | Find LCSH authority matches |
| `/api/marc650` | POST | Build MARC 650 fields |
| `/api/submit-final` | POST | Save final librarian selection |

### Admin & Utilities

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/lcsh-stats` | GET | Get LCSH index statistics |
| `/api/initialize-lcsh` | POST | Initialize LCSH schema |
| `/api/index-lcsh-sample` | POST | Index sample LCSH data |

## 🧪 Testing

Test the complete workflow:

```bash
# 1. Check health
curl http://localhost:8000/api/health

# 2. Check LCSH stats
curl http://localhost:8000/api/lcsh-stats

# 3. Run workflow with sample data
# (See Usage section above)
```

## 📊 Indexing LCSH Authority Data

To index real LCSH data from Library of Congress:

1. Download LCSH data from https://id.loc.gov/download/
2. Parse the RDF/XML or NT format
3. Use the `lcsh_index.batch_index_lcsh()` method

Example parsing script (create `scripts/index_lcsh.py`):

```python
import asyncio
from lcsh_index import lcsh_search

async def index_from_file(filepath):
    """Parse and index LCSH from downloaded data."""
    lcsh_search.connect()
    lcsh_search.initialize_schema()
    
    entries = []
    # Parse your LCSH file here
    # Each entry should have: label, uri, broader, narrower
    
    lcsh_search.batch_index_lcsh(entries)
    print(f"Indexed {len(entries)} LCSH entries")

if __name__ == "__main__":
    asyncio.run(index_from_file("path/to/lcsh_data.nt"))
```

## 🔒 Security Notes

- Never commit `.env` file with real API keys
- Use environment variables for production deployment
- Implement rate limiting for production use
- Add authentication/authorization as needed
- Validate and sanitize file uploads

## 🐛 Troubleshooting

### Weaviate Connection Issues

```bash
# Check if Weaviate is running
docker ps | grep weaviate

# View Weaviate logs
docker-compose logs weaviate

# Restart Weaviate
docker-compose restart weaviate
```

### OpenAI API Errors

- Verify your API key is correct in `.env`
- Check your OpenAI account has sufficient credits
- Ensure you have access to the required models (gpt-4o-mini, o1-mini)

### Module Import Errors

```bash
# Reinstall dependencies
pip install -r requirements.txt --upgrade
```

## 📚 Technology Stack

- **FastAPI**: Modern Python web framework
- **OpenAI API**: 
  - `gpt-4o-mini`: Vision OCR
  - `o1-mini`: Topic generation
  - `text-embedding-3-large`: Embeddings
- **Weaviate**: Vector database for semantic search
- **Pydantic**: Data validation
- **Uvicorn**: ASGI server

## 🤝 Contributing

This is a library cataloging tool. Contributions welcome for:
- Additional LCSH parsing improvements
- MARC field validation enhancements
- Frontend integration
- Performance optimizations

## 📄 License

[Specify your license here]

## 🙏 Acknowledgments

- Library of Congress Subject Headings (LCSH)
- OpenAI for AI models
- Weaviate for vector search capabilities
