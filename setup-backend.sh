#!/bin/bash

echo "Setting up LLM Council Backend..."

cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment and install dependencies
echo "Installing dependencies..."
source venv/bin/activate
pip install -r requirements.txt

echo ""
echo "Backend setup complete!"
echo "To start the backend, run: ./start-backend.sh"
