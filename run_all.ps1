# Powershell Launch Script for GST ReconcileAI
$ProjectRoot = $PSScriptRoot

Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "⚡ Starting GST ReconcileAI Full Stack Environment" -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan

# 1. Start Neo4j Database
Write-Host "[1/3] Starting Neo4j Knowledge Graph Server..." -ForegroundColor Yellow
$env:JAVA_HOME = "C:\neo4j\jdk-21.0.5+11"
Start-Process -FilePath "cmd.exe" -ArgumentList "/c set JAVA_HOME=C:\neo4j\jdk-21.0.5+11&& C:\neo4j\neo4j-community-5.26.0\bin\neo4j.bat console" -WindowStyle Minimized

# 2. Start FastAPI Backend
Write-Host "[2/3] Starting FastAPI Backend API (http://localhost:8000)..." -ForegroundColor Yellow
Start-Process -FilePath "python" -ArgumentList "main.py" -WorkingDirectory "$ProjectRoot\backend" -WindowStyle Normal

# 3. Start Frontend Vite Server
Write-Host "[3/3] Starting Frontend React UI (http://localhost:5173)..." -ForegroundColor Yellow
Start-Process -FilePath "npm" -ArgumentList "run dev" -WorkingDirectory "$ProjectRoot" -WindowStyle Normal

Start-Sleep -Seconds 3
Write-Host "====================================================" -ForegroundColor Green
Write-Host "✅ All services launched!" -ForegroundColor Green
Write-Host "• Frontend UI:     http://localhost:5173" -ForegroundColor Green
Write-Host "• Backend API:    http://localhost:8000" -ForegroundColor Green
Write-Host "• Neo4j Browser:  http://localhost:7474" -ForegroundColor Green
Write-Host "====================================================" -ForegroundColor Green
