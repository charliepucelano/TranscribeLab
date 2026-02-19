# TranscribeLab Alias Configuration
# Source this file in your $PROFILE: . d:\dev\Transcribe\transcribe_aliases.ps1

function troot { Set-Location "d:\dev\Transcribe" }
function tstart { & "d:\dev\Transcribe\manage.ps1" start }
function tstop { & "d:\dev\Transcribe\manage.ps1" stop }
function tdev { & "d:\dev\Transcribe\manage.ps1" frontend }
function tlogs { & "d:\dev\Transcribe\manage.ps1" logs }
function tssh { docker exec -it transcribelab-backend /bin/bash }
function tstatus { & "d:\dev\Transcribe\manage.ps1" status }

Write-Host "TranscribeLab aliases loaded!" -ForegroundColor Green
Write-Host "  troot   - Go to project root"
Write-Host "  tstart  - Start backend + frontend"
Write-Host "  tstop   - Stop all services"
Write-Host "  tdev    - Start frontend only"
Write-Host "  tlogs   - View backend logs"
Write-Host "  tssh    - Shell into backend container"
Write-Host "  tstatus - Check service status"
Write-Host "  tstopdev       - Stop frontend (kill port 3002)"
Write-Host "  trestartdev    - Restart frontend (kill port 3002 + start)"
Write-Host "  trestartbackend - Restart backend container"

function tstopdev { & "d:\dev\Transcribe\manage.ps1" stop-frontend }
function trestartdev { & "d:\dev\Transcribe\manage.ps1" restart-frontend }
function trestartbackend { & "d:\dev\Transcribe\manage.ps1" restart-backend }
