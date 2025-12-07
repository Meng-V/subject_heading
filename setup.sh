#!/bin/bash
# East Asian Subject Heading Assistant - Setup Script

set -e  # Exit on error

echo "=========================================="
echo "East Asian Subject Heading Assistant v2.0"
echo "Setup Script"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  No .env file found${NC}"
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo -e "${GREEN}✅ Created .env file${NC}"
    echo -e "${YELLOW}⚠️  Please edit .env and add your OPENAI_API_KEY${NC}"
    echo ""
fi

# Install backend dependencies
echo "📦 Installing backend dependencies..."
pip install -r requirements.txt
echo -e "${GREEN}✅ Backend dependencies installed${NC}"
echo ""

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
cd frontend
npm install
cd ..
echo -e "${GREEN}✅ Frontend dependencies installed${NC}"
echo ""

# Check if Docker is running
echo "🐳 Checking Docker..."
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running${NC}"
    echo "Please start Docker Desktop and run this script again."
    exit 1
fi
echo -e "${GREEN}✅ Docker is running${NC}"
echo ""

# Start Weaviate
echo "🚀 Starting Weaviate..."
docker-compose up -d
echo "⏳ Waiting for Weaviate to be ready..."
sleep 10

# Check if Weaviate is ready
for i in {1..30}; do
    if curl -s http://localhost:8081/v1/.well-known/ready > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Weaviate is ready${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}❌ Weaviate failed to start${NC}"
        echo "Check logs with: docker-compose logs"
        exit 1
    fi
    echo "Waiting... ($i/30)"
    sleep 2
done
echo ""

# Start backend temporarily to initialize schemas
echo "🔧 Initializing Weaviate schemas..."
python3 main.py > /dev/null 2>&1 &
BACKEND_PID=$!
echo "Backend started with PID: $BACKEND_PID"
sleep 5

# Initialize schemas
echo "Creating LCSH and FAST collections..."
if curl -s -X POST http://localhost:8000/api/initialize-authorities | grep -q "success"; then
    echo -e "${GREEN}✅ Schemas initialized${NC}"
else
    echo -e "${RED}❌ Failed to initialize schemas${NC}"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

# Load sample data
echo "Loading sample authority data..."
if curl -s -X POST http://localhost:8000/api/index-sample-authorities | grep -q "success"; then
    echo -e "${GREEN}✅ Sample data loaded${NC}"
else
    echo -e "${YELLOW}⚠️  Failed to load sample data (optional)${NC}"
fi

# Check stats
echo ""
echo "📊 Authority Statistics:"
curl -s http://localhost:8000/api/authority-stats | python3 -m json.tool
echo ""

# Stop temporary backend
echo "Stopping temporary backend..."
kill $BACKEND_PID 2>/dev/null || true
sleep 2
echo ""

# Summary
echo "=========================================="
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "🚀 To start the application:"
echo ""
echo "Terminal 1 - Backend:"
echo "  python3 main.py"
echo ""
echo "Terminal 2 - Frontend:"
echo "  cd frontend"
echo "  npm run dev"
echo ""
echo "Then visit: http://localhost:3000"
echo ""
echo "📚 Documentation:"
echo "  - Quick Start: QUICK_START_GUIDE.md"
echo "  - Workflow: WORKFLOW_DOCUMENTATION.md"
echo "  - Upgrade Info: UPGRADE_SUMMARY.md"
echo ""
echo "🌏 East Asian Collection Features:"
echo "  ✓ Topic generation with East Asian focus"
echo "  ✓ +10% boost for East Asian subjects"
echo "  ✓ Specialized for China, Korea, Japan, Taiwan"
echo ""
echo "Happy cataloging! 🎉"
echo ""
