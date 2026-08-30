param(
  [Parameter(Mandatory=$true)][string]$PackageRoot,
  [Parameter(Mandatory=$true)][string]$CaseId,
  [Parameter(Mandatory=$true)][string]$StudyType,
  [Parameter(Mandatory=$true)][string]$SolverVersion
)
$ErrorActionPreference = "Stop"
$binding = Get-Content (Join-Path $PackageRoot "run_binding.json") | ConvertFrom-Json
$case = Import-Csv (Join-Path $PackageRoot "load_case_manifest.csv") | Where-Object case_id -eq $CaseId
if (-not $case) { throw "UNKNOWN_CASE $CaseId" }
$manifest = [ordered]@{
  run_id = "$CaseId-$StudyType-$([DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ'))"
  case_id = $CaseId
  study_type = $StudyType
  source_git_sha = $binding.source_git_sha
  step_file = $case.geometry
  step_sha256 = $case.geometry_sha256
  load_case_manifest_sha256 = $binding.load_case_manifest_sha256
  solver_version = $SolverVersion
  started_utc = [DateTime]::UtcNow.ToString("o")
  completed_utc = $null
  status = "PENDING"
}
$path = Join-Path $PackageRoot "results/$($manifest.run_id).run.json"
$manifest | ConvertTo-Json -Depth 5 | Set-Content -Path $path -Encoding utf8NoBOM
Write-Output $path
