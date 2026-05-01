param(
  [switch]$SmokeLaunch,
  [int]$SmokePort = 8010,
  [string]$SmokeStateName = "smoke-check",
  [string]$SmokeDataDir = ""
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$backendDir = Join-Path $repoRoot "backend"
$pythonExe = Join-Path $backendDir ".venv\Scripts\python.exe"
$nodeCommand = Get-Command node -ErrorAction Stop
$startScript = Join-Path $PSScriptRoot "start-zivra.ps1"
$stopScript = Join-Path $PSScriptRoot "stop-zivra.ps1"
$defaultSmokeDataDir = Join-Path $backendDir "data\test-runs\smoke-check"
$resolvedSmokeDataDir = ([string]$SmokeDataDir).Trim()
if (-not $resolvedSmokeDataDir) {
  $resolvedSmokeDataDir = $defaultSmokeDataDir
}

if (-not (Test-Path $pythonExe)) {
  throw "Missing backend virtual environment at $pythonExe. Create the backend .venv first."
}

Write-Host "Running backend unit tests..."
Push-Location $backendDir
try {
  & $pythonExe -m unittest discover -s tests
  if ($LASTEXITCODE -ne 0) {
    throw "Backend tests failed."
  }
} finally {
  Pop-Location
}

Write-Host "Checking dashboard JavaScript..."
& $nodeCommand.Source --check (Join-Path $repoRoot "dashboard\app.js")
if ($LASTEXITCODE -ne 0) {
  throw "dashboard/app.js syntax check failed."
}

Write-Host "Checking mobile companion JavaScript..."
& $nodeCommand.Source --check (Join-Path $repoRoot "dashboard\mobile.js")
if ($LASTEXITCODE -ne 0) {
  throw "dashboard/mobile.js syntax check failed."
}

Write-Host "Checking mobile service worker JavaScript..."
& $nodeCommand.Source --check (Join-Path $repoRoot "dashboard\sw.js")
if ($LASTEXITCODE -ne 0) {
  throw "dashboard/sw.js syntax check failed."
}

if ($SmokeLaunch) {
  Write-Host "Running launcher smoke test..."
  & $startScript -NoOpenBrowser -ForceRestart -Port $SmokePort -StateName $SmokeStateName -DataDir $resolvedSmokeDataDir
  try {
    $health = Invoke-RestMethod -Uri "http://127.0.0.1:$SmokePort/health" -TimeoutSec 5
    if ($health.status -ne "ok") {
      throw "Launcher smoke test did not receive a healthy response."
    }
  } finally {
    & $stopScript -Quiet -StateName $SmokeStateName
  }
}

Write-Host "All Zivra checks passed."
