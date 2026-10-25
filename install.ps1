$ErrorActionPreference = "Stop"
& python (Join-Path $PSScriptRoot "tools/deploy.py") @args
exit $LASTEXITCODE
