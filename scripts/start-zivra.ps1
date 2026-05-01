param(
  [string]$BindHost = "127.0.0.1",
  [int]$Port = 8000,
  [string]$StateName = "server",
  [string]$DataDir = "",
  [switch]$Reload,
  [switch]$NoOpenBrowser,
  [switch]$OpenMobile,
  [switch]$ForceRestart,
  [int]$HealthTimeoutSeconds = 45
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$backendDir = Join-Path $repoRoot "backend"
$pythonExe = Join-Path $backendDir ".venv\Scripts\python.exe"
$stateDir = Join-Path $backendDir "data\launcher"

function Get-StateFileName([string]$Name) {
  $rawName = [string]$Name
  $normalized = [regex]::Replace($rawName.Trim(), "[^A-Za-z0-9._-]", "-")
  if (-not $normalized) {
    $normalized = "server"
  }
  return "$normalized.json"
}

function Resolve-OptionalPath([string]$Candidate, [string]$BasePath) {
  $value = ([string]$Candidate).Trim()
  if (-not $value) {
    return ""
  }

  if ([System.IO.Path]::IsPathRooted($value)) {
    return [System.IO.Path]::GetFullPath($value)
  }

  return [System.IO.Path]::GetFullPath((Join-Path $BasePath $value))
}

$statePath = Join-Path $stateDir (Get-StateFileName -Name $StateName)
$resolvedDataDir = Resolve-OptionalPath -Candidate $DataDir -BasePath $repoRoot

function Get-BrowserHost([string]$BoundHost) {
  if ($BoundHost -in @("0.0.0.0", "::", "[::]")) {
    return "127.0.0.1"
  }
  return $BoundHost
}

function Read-LauncherState([string]$Path) {
  if (-not (Test-Path $Path)) {
    return $null
  }

  try {
    return Get-Content -Path $Path -Raw | ConvertFrom-Json
  } catch {
    return $null
  }
}

function Get-LiveProcess([object]$State) {
  if (-not $State -or -not $State.pid) {
    return $null
  }

  try {
    return Get-Process -Id ([int]$State.pid) -ErrorAction Stop
  } catch {
    return $null
  }
}

function Remove-LauncherState([string]$Path) {
  if (Test-Path $Path) {
    Remove-Item -Path $Path -Force -ErrorAction SilentlyContinue
  }
}

function Wait-ForHealth([string]$HealthUrl, [int]$TimeoutSeconds) {
  $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
  while ((Get-Date) -lt $deadline) {
    try {
      $payload = Invoke-RestMethod -Uri $HealthUrl -TimeoutSec 3
      if ($payload.status -eq "ok") {
        return $true
      }
    } catch {
      Start-Sleep -Milliseconds 750
    }
  }

  return $false
}

if (-not (Test-Path $pythonExe)) {
  throw "Missing backend virtual environment at $pythonExe. Create the backend .venv first."
}

$existingState = Read-LauncherState -Path $statePath
$existingProcess = Get-LiveProcess -State $existingState
if ($existingProcess) {
  if ($ForceRestart) {
    Stop-Process -Id $existingProcess.Id -Force
    Start-Sleep -Milliseconds 800
    Remove-LauncherState -Path $statePath
  } else {
    Write-Host "Zivra is already running (PID $($existingProcess.Id))."
    Write-Host "UI: $($existingState.ui_url)"
    Write-Host "Mobile: $($existingState.mobile_url)"
    if (-not $NoOpenBrowser) {
      Start-Process $existingState.ui_url | Out-Null
      if ($OpenMobile) {
        Start-Process $existingState.mobile_url | Out-Null
      }
    }
    return
  }
}

$argumentList = @(
  "-m",
  "uvicorn",
  "app.main:app",
  "--host",
  $BindHost,
  "--port",
  [string]$Port
)

if ($Reload) {
  $argumentList += "--reload"
}

$browserHost = Get-BrowserHost -BoundHost $BindHost
$origin = "http://${browserHost}:${Port}"
$uiUrl = "$origin/ui/"
$mobileUrl = "$origin/mobile"
$healthUrl = "$origin/health"

New-Item -ItemType Directory -Path $stateDir -Force | Out-Null
if ($resolvedDataDir) {
  New-Item -ItemType Directory -Path $resolvedDataDir -Force | Out-Null
}

$previousDataDir = $env:ZIVRA_DATA_DIR
if ($resolvedDataDir) {
  $env:ZIVRA_DATA_DIR = $resolvedDataDir
}

try {
  $process = Start-Process -FilePath $pythonExe -ArgumentList $argumentList -WorkingDirectory $backendDir -PassThru
} finally {
  if ($resolvedDataDir) {
    if ($null -ne $previousDataDir) {
      $env:ZIVRA_DATA_DIR = $previousDataDir
    } else {
      Remove-Item Env:ZIVRA_DATA_DIR -ErrorAction SilentlyContinue
    }
  }
}

@{
  pid = $process.Id
  state_name = $StateName
  host = $BindHost
  browser_host = $browserHost
  port = $Port
  reload = [bool]$Reload
  data_dir = $resolvedDataDir
  origin = $origin
  ui_url = $uiUrl
  mobile_url = $mobileUrl
  health_url = $healthUrl
  started_at = [DateTime]::UtcNow.ToString("o")
} | ConvertTo-Json | Set-Content -Path $statePath -Encoding UTF8

if (-not (Wait-ForHealth -HealthUrl $healthUrl -TimeoutSeconds $HealthTimeoutSeconds)) {
  $liveProcess = Get-LiveProcess -State @{ pid = $process.Id }
  if ($liveProcess) {
    Stop-Process -Id $liveProcess.Id -Force -ErrorAction SilentlyContinue
  }
  Remove-LauncherState -Path $statePath
  throw "Zivra did not become healthy within $HealthTimeoutSeconds seconds."
}

Write-Host "Zivra started successfully."
Write-Host "PID: $($process.Id)"
Write-Host "UI: $uiUrl"
Write-Host "Mobile: $mobileUrl"
Write-Host "Health: $healthUrl"

if (-not $NoOpenBrowser) {
  Start-Process $uiUrl | Out-Null
  if ($OpenMobile) {
    Start-Process $mobileUrl | Out-Null
  }
}
