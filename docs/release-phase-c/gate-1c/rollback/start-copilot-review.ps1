$ErrorActionPreference = 'Stop'
$geoaiMutex = [System.Threading.Mutex]::new($false, 'Local\GeoAI-Local-Development-Launcher')
if (-not $geoaiMutex.WaitOne(0)) {
    $geoaiMutex.Dispose()
    throw 'Another GeoAI launcher is starting or running. Use its existing frontend on localhost:3001.'
}
try {
function Assert-GeoAIPortFree([int]$Port) {
    $geoaiProbe = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $Port)
    try { $geoaiProbe.Start() }
    catch { throw "Port $Port is occupied but its GeoAI health check failed. No duplicate server was started." }
    finally { $geoaiProbe.Stop() }
}
$geoaiRoot = $PSScriptRoot
$geoaiLogs = Join-Path $geoaiRoot 'docs/copilot-milestone-2'
New-Item -ItemType Directory -Force -Path $geoaiLogs | Out-Null

# Existing process-local mock provider, zero budget and backend-only credentials.
$geoaiReady = $false
try { $geoaiReady = (Invoke-RestMethod 'http://127.0.0.1:8001/api/health' -TimeoutSec 2).status -eq 'ok' } catch {}
if (-not $geoaiReady) {
    Assert-GeoAIPortFree 8001
    Start-Process -FilePath (Join-Path $geoaiRoot 'backend/.venv/Scripts/python.exe') -ArgumentList 'scripts/serve_copilot_review_local.py' -WorkingDirectory (Join-Path $geoaiRoot 'backend') -WindowStyle Hidden -RedirectStandardOutput (Join-Path $geoaiLogs 'review-start.log') -RedirectStandardError (Join-Path $geoaiLogs 'review-start.err.log')
    # Do not open the frontend against a backend still initializing its database.
    for ($geoaiAttempt = 0; $geoaiAttempt -lt 60; $geoaiAttempt++) {
        try { $geoaiReady = (Invoke-RestMethod 'http://127.0.0.1:8001/api/health' -TimeoutSec 2).status -eq 'ok' } catch {}
        if ($geoaiReady) { break }
        Start-Sleep -Seconds 1
    }
    if (-not $geoaiReady) { throw 'Offline backend did not become ready. See docs/copilot-milestone-2/review-start.err.log. Frontend was not started.' }
}

# Reuse a healthy frontend only when its same-origin proxy reaches this backend.
# A second launcher must not race another Next process for port 3001.
$geoaiFrontendReady = $false
try { $geoaiFrontendReady = (Invoke-RestMethod 'http://localhost:3001/local-api/api/health' -TimeoutSec 3).status -eq 'ok' } catch {}
if ($geoaiFrontendReady) {
    Write-Host 'GeoAI local review is already running: http://localhost:3001/projects/793/workspace'
    Write-Host 'Nebius Assistant available; inference remains disabled until explicit budget approval.'
    return
}
Assert-GeoAIPortFree 3001

$env:GEOAI_LOCAL_REVIEW = 'true'
$env:NEXT_PUBLIC_API_URL = '/local-api'
Write-Host 'Local review: http://localhost:3001/projects/793/workspace'
Write-Host 'Nebius Assistant available; inference remains disabled until explicit budget approval.'
Push-Location (Join-Path $geoaiRoot 'frontend')
try { & node node_modules/next/dist/bin/next dev -p 3001 -H 127.0.0.1 } finally { Pop-Location }
} finally {
    $geoaiMutex.ReleaseMutex()
    $geoaiMutex.Dispose()
}
