# 🚀 Quick Start Guide

Get the AI Subject Heading Assistant running in 5 minutes!

## Prerequisites

- Python 3.10+
- Docker Desktop (or Docker + Docker Compose)
- OpenAI API key

## Setup Steps

### 1. Install Dependencies

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure API Key

```bash
cp .env.example .env
```

Edit `.env` and add your OpenAI API key:
```env
OPENAI_API_KEY=sk-your-key-here
```

### 3. Start Weaviate

```bash
docker-compose up -d
```

Verify it's running:
```bash
curl http://localhost:8080/v1/meta
```

### 4. Start the API Server

```bash
python main.py
```

You should see:
```
🚀 Starting AI Subject Heading Assistant...
✅ Connected to Weaviate
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 5. Initialize & Test

Open a new terminal and run:

```bash
# Initialize LCSH schema and load sample data
python test_workflow.py init

# Run the test workflow
python test_workflow.py
```

### 6. Explore the API

Open http://localhost:8000/docs in your browser to see the interactive API documentation.

## API Quick Test

### Test with cURL:

```bash
# Health check
curl http://localhost:8000/api/health

# Generate topics from metadata
curl -X POST http://localhost:8000/api/generate-topics \
  -H "Content-Type: application/json" \
  -d '{
    "metadata": {
      "title": "Introduction to Chinese Painting",
      "author": "Li Wei",
      "summary": "A guide to traditional Chinese painting techniques",
      "toc": ["History", "Materials", "Techniques"]
    }
  }'
```

## What's Next?

1. **Add Real LCSH Data**: See `scripts/lcsh_importer.py` to import full LCSH dataset
2. **Upload Images**: Use `/api/ingest-images` endpoint with actual book images
3. **Integrate Frontend**: Build a web UI to interact with the API
4. **Deploy**: Deploy to production with proper authentication

## Troubleshooting

**Weaviate won't start?**
```bash
docker-compose down
docker-compose up -d
```

**API errors?**
- Check `.env` has correct OpenAI API key
- Ensure you have credits in your OpenAI account
- Verify Python version >= 3.10

**Import errors?**
```bash
pip install -r requirements.txt --upgrade
```

## Common Commands

```bash
# Start everything
docker-compose up -d && python main.py

# Stop Weaviate
docker-compose down

# View logs
docker-compose logs -f weaviate

# Test workflow
python test_workflow.py
```

## Need Help?

- Check the full [README.md](README.md)
- Open the API docs: http://localhost:8000/docs
- Review the specification: [guide.md](../guide.md)
