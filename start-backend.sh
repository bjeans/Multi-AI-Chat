#!/bin/bash

echo "Starting LLM Council Backend..."
cd backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Please run ./setup-backend.sh first"
    exit 1
fi

# Activate virtual environment and start server
source venv/bin/activate
python main.py
