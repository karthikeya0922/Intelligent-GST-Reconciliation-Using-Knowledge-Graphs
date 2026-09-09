@echo off
title GST ReconcileAI Launcher
echo ====================================================
echo ⚡ Starting GST ReconcileAI Full Stack Environment
echo ====================================================

set PROJECT_ROOT=%~dp0
if exist "C:\neo4j\neo4j-community-5.26.0\bin\neo4j.bat" (
    echo [1/3] Starting Neo4j Knowledge Graph...
    start "Neo4j Server" cmd /c "set JAVA_HOME=C:\neo4j\jdk-21.0.5+11&& C:\neo4j\neo4j-community-5.26.0\bin\neo4j.bat console"
) else (
    echo [1/3] Standalone Neo4j not found at C:\neo4j (optional). Use 'docker compose up -d' if graph DB is needed.
)

echo [2/3] Starting FastAPI Backend API...
start "FastAPI Backend" cmd /c "cd /d "%PROJECT_ROOT%\backend" && python main.py"

echo [3/3] Starting React Frontend...
start "React Frontend" cmd /c "cd /d "%PROJECT_ROOT%" && npm run dev"

echo.
echo ====================================================
echo ✅ All services launched!
echo • Frontend UI:     http://localhost:5173
echo • Backend API:    http://localhost:8000
echo • Neo4j Browser:  http://localhost:7474
echo ====================================================
