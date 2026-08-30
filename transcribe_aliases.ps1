# TranscribeLab Alias Configuration
# Source this file in your $PROFILE: . d:\dev\Transcribe\transcribe_aliases.ps1

function troot { Set-Location "d:\dev\Transcribe" }
function tstart { & "d:\dev\Transcribe\manage.ps1" start }
function tstop { & "d:\dev\Transcribe\manage.ps1" stop }
function tdev { & "d:\dev\Transcribe\manage.ps1" frontend }
function tlogs { & "d:\dev\Transcribe\manage.ps1" logs }
function tssh { docker exec -it transcribelab-backend /bin/bash }
function tstatus { & "d:\dev\Transcribe\manage.ps1" status }

function tstopdev { & "d:\dev\Transcribe\manage.ps1" stop-frontend }
function trestartdev { & "d:\dev\Transcribe\manage.ps1" restart-frontend }
function trestartbackend { & "d:\dev\Transcribe\manage.ps1" restart-backend }
