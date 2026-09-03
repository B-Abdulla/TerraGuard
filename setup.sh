#!/bin/bash
# Setup script for TerraGuard

echo "Setting up backend..."
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python seed.py

echo "Starting backend..."
nohup python run.py > backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend running with PID $BACKEND_PID"

echo "Setting up frontend..."
cd ../frontend
npm install

echo "Starting frontend..."
nohup npm run dev > frontend.log 2>&1 &
FRONTEND_PID=$!
echo "Frontend running with PID $FRONTEND_PID"

echo "TerraGuard is online."
echo "Frontend: http://localhost:5173"
echo "Backend API: http://localhost:8000"
