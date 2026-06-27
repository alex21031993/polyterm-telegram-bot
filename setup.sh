#!/bin/bash
# Setup script for PolyTerm Telegram Bot

set -e

echo "========================================"
echo "  PolyTerm Telegram Bot Setup"
echo "========================================"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo "1. Creating virtual environment..."
python3 -m venv venv

echo ""
echo "2. Activating virtual environment..."
source venv/bin/activate

echo ""
echo "3. Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "4. Creating database directory..."
mkdir -p db

echo ""
echo "5. Checking configuration..."
if [ ! -f .env ]; then
    echo "   WARNING: .env file not found!"
    echo "   Please create .env with your BOT_TOKEN"
    echo ""
    echo "   Example:"
    echo "   BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
    echo "   ADMIN_PASSWORD=Alex1234\$"
fi

echo ""
echo "========================================"
echo "  Setup Complete!"
echo "========================================"
echo ""
echo "To run the bot:"
echo "  cd $SCRIPT_DIR"
echo "  source venv/bin/activate"
echo "  python -m src.bot.app"
echo ""
echo "Make sure to configure your .env file first!"
echo ""
