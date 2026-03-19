$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$quickstart = Join-Path $repoRoot "scripts\setup\quickstart.py"

if (Get-Command py -ErrorAction SilentlyContinue) {
    & py $quickstart --run @args
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    & python $quickstart --run @args
} else {
    throw "Python was not found in PATH. Install Python 3.10+ first."
}
