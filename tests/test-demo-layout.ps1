$ErrorActionPreference = 'Stop'
$openScad = if ([string]::IsNullOrWhiteSpace($env:OPENSCAD_EXECUTABLE)) {
    'openscad'
} else {
    $env:OPENSCAD_EXECUTABLE
}
$model = Join-Path $PSScriptRoot '..\examples\demo\timetable-demo.scad'
$renderDir = Join-Path $PSScriptRoot 'renders'
New-Item -ItemType Directory -Path $renderDir -Force | Out-Null

$configurations = @(
    [pscustomobject]@{ Name = 'default'; Days = 6; Morning = 5; Afternoon = 5 },
    [pscustomobject]@{ Name = 'five-days'; Days = 5; Morning = 5; Afternoon = 5 },
    [pscustomobject]@{ Name = 'seven-days'; Days = 7; Morning = 5; Afternoon = 5 },
    [pscustomobject]@{ Name = 'morning-only'; Days = 6; Morning = 4; Afternoon = 5 },
    [pscustomobject]@{ Name = 'afternoon-only'; Days = 6; Morning = 5; Afternoon = 6 }
)
$hashes = @{}
foreach ($configuration in $configurations) {
    $output = Join-Path $renderDir "$($configuration.Name).png"
    $outputLog = & $openScad `
        -D "day_count=$($configuration.Days)" `
        -D "morning_rows=$($configuration.Morning)" `
        -D "afternoon_rows=$($configuration.Afternoon)" `
        --hardwarnings --autocenter --viewall --projection o --imgsize 1100,1100 --preview `
        -o $output $model 2>&1
    $renderExitCode = $LASTEXITCODE
    $diagnostics = @($outputLog | Where-Object { $_ -match "(?i)^(ERROR|WARNING):|^Fontconfig error:" })
    if ($renderExitCode -ne 0 -or $diagnostics.Count -gt 0 -or -not (Test-Path -LiteralPath $output)) {
        throw "OpenSCAD preview failed for $($configuration.Name): $($outputLog -join [Environment]::NewLine)"
    }
    $hashes[$configuration.Name] = (Get-FileHash -LiteralPath $output -Algorithm SHA256).Hash
    Write-Output "$($configuration.Name): $($hashes[$configuration.Name])"
}

$failures = [System.Collections.Generic.List[string]]::new()
foreach ($name in @('five-days', 'seven-days', 'morning-only', 'afternoon-only')) {
    if ($hashes['default'] -eq $hashes[$name]) {
        $failures.Add("Configuration '$name' did not change the rendered model.")
    }
}
if ($failures.Count -gt 0) {
    $failures | ForEach-Object { Write-Output "FAIL: $_" }
    exit 1
}
Write-Output 'PASS: day_count and each shift row count change the rendered model.'
