param(
  [string]$StateName = "server",
  [switch]$Quiet
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

function Get-StateFileName([string]$Name) {
  $rawName = [string]$Name
  $normalized = [regex]::Replace($rawName.Trim(), "[^A-Za-z0-9._-]", "-")
  if (-not $normalized) {
    $normalized = "server"
  }
  return "$normalized.json"
}

$statePath = Join-Path $repoRoot "backend\data\launcher\$(Get-StateFileName -Name $StateName)"

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

function Remove-LauncherState([string]$Path) {
  if (Test-Path $Path) {
    Remove-Item -Path $Path -Force -ErrorAction SilentlyContinue
  }
}

$state = Read-LauncherState -Path $statePath
if (-not $state) {
  if (-not $Quiet) {
    Write-Host "No tracked Zivra server is running."
  }
  return
}

$stopped = $false
if ($state.pid) {
  try {
    $process = Get-Process -Id ([int]$state.pid) -ErrorAction Stop
    Stop-Process -Id $process.Id -Force
    $stopped = $true
    if (-not $Quiet) {
      Write-Host "Stopped Zivra server process $($process.Id)."
    }
  } catch {
    if (-not $Quiet) {
      Write-Host "Tracked Zivra server process was not running."
    }
  }
}

Remove-LauncherState -Path $statePath
if (-not $Quiet -and -not $stopped) {
  Write-Host "Launcher state was cleaned up."
}
