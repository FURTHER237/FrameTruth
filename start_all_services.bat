@echo off
echo Starting FrameTruth Services...
echo.

REM Start the backend server in the first terminal
start "Backend Server" cmd /k "cd /d C:\Users\danie\OneDrive\Documents\GitHub\FrameTruth\Ai_forensic_tool && python backend_server.py"

REM Start the frontend development server in the second terminal
start "Frontend Dev Server" cmd /k "cd /d C:\Users\danie\OneDrive\Documents\GitHub\FrameTruth\Forensic-Tool-UI && npm run dev"

REM Start the database/API server in the third terminal
start "Database/API Server" cmd /k "cd /d C:\Users\danie\OneDrive\Documents\GitHub\FrameTruth\Ai_forensic_tool && python -m uvicorn core.main:app --reload --host 127.0.0.1 --port 8000"

echo All services are starting in separate terminal windows...
echo.
echo Terminal 1: Backend Server (backend_server.py)
echo Terminal 2: Frontend Dev Server (npm run dev)
echo Terminal 3: Database/API Server (uvicorn on port 8000)
echo.

REM Wait a moment for services to start
echo Waiting for services to initialize...
timeout /t 5 /nobreak >nul

REM Open frontend URL in browser
echo Opening frontend in browser...
start http://localhost:5173

echo.
echo Services started and frontend opened in browser!
echo - Frontend: http://localhost:5173
echo.
pause
