#!/bin/bash
# Timoshenko Beam-Column Simulator - Launch Script

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
VENV_DIR="$PROJECT_ROOT/venv"

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}[INFO]${NC} Creating virtual environment if needed..."
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
    echo -e "${GREEN}[✓]${NC} Virtual environment created"
fi

echo -e "${BLUE}[INFO]${NC} Activating virtual environment..."
source "$VENV_DIR/bin/activate"

echo -e "${BLUE}[INFO]${NC} Installing dependencies..."
pip install -q -U pip setuptools wheel
pip install -q -r "$PROJECT_ROOT/requirements.txt"
echo -e "${GREEN}[✓]${NC} Dependencies installed"

echo -e "${BLUE}[INFO]${NC} Checking port 8888..."
if lsof -Pi :8888 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}[WARN]${NC} Port 8888 is in use, killing process..."
    lsof -ti :8888 | xargs kill -9 2>/dev/null || true
    sleep 1
fi

echo -e "${BLUE}[INFO]${NC} Starting backend server on port 8888..."
cd "$BACKEND_DIR"
python main.py 8888 &
BACKEND_PID=$!
echo -e "${GREEN}[✓]${NC} Backend started (PID: $BACKEND_PID)"

sleep 2

echo -e "${BLUE}[INFO]${NC} Health checking backend..."
for i in {1..10}; do
    if curl -s http://localhost:8888/health > /dev/null 2>&1; then
        echo -e "${GREEN}[✓]${NC} Backend is healthy"
        break
    fi
    if [ $i -eq 10 ]; then
        echo -e "${RED}[ERROR]${NC} Backend health check failed"
        kill $BACKEND_PID 2>/dev/null || true
        exit 1
    fi
    sleep 1
done

FRONTEND_URL="file://$FRONTEND_DIR/index.html"
echo -e "${BLUE}[INFO]${NC} Opening frontend..."

if [[ "$OSTYPE" == "darwin"* ]]; then
    open "$FRONTEND_URL" 2>/dev/null &
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    xdg-open "$FRONTEND_URL" 2>/dev/null &
fi

echo ""
echo "======================================================================"
echo "  Timoshenko Beam-Column Simulator"
echo "======================================================================"
echo ""
echo "  Backend: http://localhost:8888"
echo "  Frontend: $FRONTEND_URL"
echo ""
echo "  Press Ctrl+C to stop the server"
echo ""
echo "======================================================================"
echo ""

wait $BACKEND_PID
