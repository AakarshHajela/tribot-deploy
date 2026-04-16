#!/bin/bash
# Move to the folder where this script is located
cd "$(dirname "$0")"

echo "--- Starting TRIBOT Frontend ---"
cd frontend
npm install
# This opens a new Terminal tab for the frontend
osascript -e 'tell application "Terminal" to do script "cd \"'$(pwd)'\"; npm run dev"'

echo "--- Starting TRIBOT Backend ---"
cd ../backend
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload