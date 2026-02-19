<#
.SYNOPSIS
    Management script for TranscribeLab application.

.DESCRIPTION
    Easily manage backend (Docker) and frontend (Next.js) services.

.EXAMPLE
    .\manage.ps1 start
    .\manage.ps1 stop
    .\manage.ps1 frontend
    .\manage.ps1 backend-logs

#>

param (
    [Parameter(Mandatory = $false, Position = 0)]
    [ValidateSet("start", "stop", "restart", "frontend", "backend", "logs", "status", "clean", "stop-frontend", "restart-frontend", "restart-backend")]
    [string[]]$Command = "status"
)

# Configuration - Absolute Paths
$ProjectRoot = "d:\dev\Transcribe"
$FrontendPath = "$ProjectRoot\frontend"

# Ensure we operate in the project root for docker-compose
Set-Location -Path $ProjectRoot

function Show-Status {
    Write-Host "--- Docker Containers ---" -ForegroundColor Cyan
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | Select-String "transcribelab"
    
    Write-Host "`n--- Frontend ---" -ForegroundColor Cyan
    Write-Host "To check frontend, look for 'node' processes or check your open terminals."
}

function Start-Backend {
    Write-Host "Starting Backend Services (Docker)..." -ForegroundColor Green
    docker-compose up -d
}

function Start-Frontend {
    Write-Host "Starting Frontend (npm run dev)..." -ForegroundColor Green
    Write-Host "Opening in a new terminal window..." -ForegroundColor Yellow
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$FrontendPath'; npm run dev"
}

function Stop-All {
    Write-Host "Stopping Docker Services..." -ForegroundColor Yellow
    docker-compose stop
}

function Show-Logs {
    docker-compose logs -f backend
}

function Restart-Backend {
    Write-Host "Restarting Backend Container..." -ForegroundColor Yellow
    docker-compose restart backend
}

function Stop-Frontend {
    Write-Host "Stopping Frontend (Port 3002)..." -ForegroundColor Yellow
    
    # PowerShell Core/7+ uses Get-NetTCPConnection more reliably
    # Filtering by port 3002
    try {
        $connections = Get-NetTCPConnection -LocalPort 3002 -ErrorAction Stop
        foreach ($conn in $connections) {
            $pid_to_kill = $conn.OwningProcess
            if ($pid_to_kill -gt 0) {
                Write-Host "Killing process $pid_to_kill on port 3002..." -ForegroundColor Red
                Stop-Process -Id $pid_to_kill -Force -ErrorAction SilentlyContinue
            }
        }
    }
    catch {
        Write-Host "No process found on port 3002 (or access denied)." -ForegroundColor Gray
    }
}

switch ($Command) {
    "start" {
        Start-Backend
        Start-Frontend
    }
    "stop" {
        Stop-All
    }
    "restart" {
        Stop-All
        Start-Backend
        Start-Frontend
    }
    "frontend" {
        Start-Frontend
    }
    "backend" {
        Start-Backend
    }
    "logs" {
        Show-Logs
    }
    "status" {
        Show-Status
    }
    "stop-frontend" {
        Stop-Frontend
    }
    "restart-frontend" {
        Stop-Frontend
        Start-Frontend
    }
    "restart-backend" {
        Restart-Backend
    }
    "clean" {
        Write-Host "Removing containers and orphans..." -ForegroundColor Red
        docker-compose down --remove-orphans
    }
}
