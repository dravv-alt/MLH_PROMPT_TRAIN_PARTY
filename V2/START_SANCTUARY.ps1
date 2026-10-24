param([int]$BackendPort = 8000, [int]$FrontendPort = 5173)
$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$backendRoot = Join-Path $projectRoot 'backend'
$frontendRoot = Join-Path $projectRoot 'frontend'
$runtimeRoot = Join-Path $projectRoot '.runtime'
New-Item -ItemType Directory -Force -Path $runtimeRoot | Out-Null
$pythonPath = if (Test-Path 'C:\Python312\python.exe') { 'C:\Python312\python.exe' } elseif (Test-Path (Join-Path $backendRoot '.venv_nlp\Scripts\python.exe')) { Join-Path $backendRoot '.venv_nlp\Scripts\python.exe' } else { (Get-Command python).Source }
if (!(Test-Path (Join-Path $frontendRoot 'node_modules\vite'))) { throw 'Frontend dependencies are absent. Run npm install in V2/frontend first.' }
$env:SANCTUARY_BACKEND_URL = "http://127.0.0.1:$BackendPort"
$env:VITE_API_BASE_URL = '/api'
$env:SANCTUARY_NEURAL_THREADS = '2'
# Pin verification to the configured frontend Clerk instance when the backend
# issuer is not explicitly configured. Only the public key is read here.
if (!$env:CLERK_ISSUER) {
  $frontEnv = Join-Path $frontendRoot '.env.local'
  if (Test-Path $frontEnv) {
    $publicLine = Get-Content -LiteralPath $frontEnv | Where-Object { $_ -match '^VITE_CLERK_PUBLISHABLE_KEY=' } | Select-Object -First 1
    if ($publicLine) {
      $publicValue = ($publicLine -split '=',2)[1].Trim().Trim('"').Trim("'")
      if ($publicValue -match '^pk_(?:test|live)_(.+)$') {
        try {
          $encoded = $Matches[1]; $encoded += '=' * ((4 - $encoded.Length % 4) % 4)
          $clerkHost = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($encoded)).TrimEnd('$')
          if ($clerkHost -match '^[a-zA-Z0-9.-]+$') { $env:CLERK_ISSUER = "https://$clerkHost" }
        } catch { Write-Warning 'Could not derive Clerk issuer; configure CLERK_ISSUER in backend/.env.' }
      }
    }
  }
}
$backendReady = $false
try { $health = Invoke-RestMethod "http://127.0.0.1:$BackendPort/health" -TimeoutSec 2; $backendReady = $health.service -eq 'sanctuary-v2-backend' } catch {}
if (!$backendReady) {
  $backendProcess = Start-Process -FilePath $pythonPath -ArgumentList "-m uvicorn main:app --host 127.0.0.1 --port $BackendPort" -WorkingDirectory $backendRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $runtimeRoot 'backend.log') -RedirectStandardError (Join-Path $runtimeRoot 'backend.error.log')
  Write-Host "Backend starting (PID $($backendProcess.Id))."
}
$frontendReady = $false
try { $response = Invoke-WebRequest "http://127.0.0.1:$FrontendPort" -UseBasicParsing -TimeoutSec 2; $frontendReady = $response.StatusCode -eq 200 } catch {}
if (!$frontendReady) {
  $frontendProcess = Start-Process -FilePath 'cmd.exe' -ArgumentList "/c npm.cmd run dev:integrated -- --host 127.0.0.1 --port $FrontendPort" -WorkingDirectory $frontendRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $runtimeRoot 'frontend.log') -RedirectStandardError (Join-Path $runtimeRoot 'frontend.error.log')
  Write-Host "Frontend starting (PID $($frontendProcess.Id))."
}
Write-Host "Open http://127.0.0.1:$FrontendPort"
Write-Host "API docs: http://127.0.0.1:$BackendPort/docs"
Write-Host "Logs: $runtimeRoot"
