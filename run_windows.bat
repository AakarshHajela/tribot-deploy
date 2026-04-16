@echo off
echo --- Starting TRIBOT Frontend ---
cd frontend
call npm install
:: This opens a new terminal window for the frontend
start cmd /k "npm run dev"

echo --- Starting TRIBOT Backend ---
cd ../backend
call .\venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
pause