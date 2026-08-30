param([Parameter(Mandatory=$true)][string]$PackageRoot)
$ErrorActionPreference = "Stop"
$binding = Get-Content (Join-Path $PackageRoot "run_binding.json") | ConvertFrom-Json
$gitSha = (git -C (Join-Path $PSScriptRoot "..") rev-parse HEAD).Trim()
if ($gitSha -ne $binding.source_git_sha) { throw "SOURCE_SHA_MISMATCH expected=$($binding.source_git_sha) actual=$gitSha" }
$modelHash = (Get-FileHash (Join-Path $PackageRoot "model_manifest.csv") -Algorithm SHA256).Hash.ToLower()
$loadHash = (Get-FileHash (Join-Path $PackageRoot "load_case_manifest.csv") -Algorithm SHA256).Hash.ToLower()
if ($modelHash -ne $binding.model_manifest_sha256) { throw "MODEL_MANIFEST_HASH_MISMATCH" }
if ($loadHash -ne $binding.load_case_manifest_sha256) { throw "LOAD_MANIFEST_HASH_MISMATCH" }
$fusion = Get-Command "Fusion360.exe" -ErrorAction SilentlyContinue
$status = if ($fusion) { "FOUND_ON_PATH" } else { "NOT_ON_PATH_CHECK_STANDARD_INSTALL_OR_USER_SESSION" }
Write-Output "FUSION_WORKER_ENV_OK source=$($gitSha.Substring(0,12)) fusion=$status"
