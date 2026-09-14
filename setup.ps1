<#
.SYNOPSIS
    Fill in placeholders and regenerate assets for Nitin Patidar's profile README.

.EXAMPLE
    .\setup.ps1 -Image assets\jacket.png -Color
#>
[CmdletBinding()]
param(
    [string]$Username = 'Programmer-NITIN',
    [string]$Name = 'Nitin Patidar',
    [string]$Image = 'assets\jacket.png',
    [ValidateSet('dots', 'binary', 'ascii', 'braille')]
    [string]$Mode = 'dots',
    [int]$Cols = 100,
    [switch]$Circle,
    [switch]$Color = $true,
    [switch]$Animate,
    [switch]$Invert,
    [switch]$Square,
    [string]$Focus = '0.5,0.5'
)

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot

Write-Host "`n[1/3] drawing the skill radar" -ForegroundColor Cyan
python (Join-Path $root 'scripts\radar.py') --data (Join-Path $root 'assets\skills.json') -o (Join-Path $root 'assets\radar')

if ($Username) {
    Write-Host "      drawing the language radar from the GitHub API" -ForegroundColor Cyan
    try {
        python (Join-Path $root 'scripts\radar.py') --github $Username -o (Join-Path $root 'assets\radar-langs') --values
    } catch {
        Write-Warning "language radar skipped: $_"
    }

    Write-Host "      generating stat and repo cards" -ForegroundColor Cyan
    try {
        python (Join-Path $root 'scripts\cards.py') --user $Username --projects (Join-Path $root 'assets\projects.json') --out (Join-Path $root 'assets')
    } catch {
        Write-Warning "cards skipped: $_"
    }
}

if ($Image -and (Test-Path (Join-Path $root $Image))) {
    Write-Host "`n[2/3] dot-matrixing $Image" -ForegroundColor Cyan
    $dotArgs = @(
        (Join-Path $root 'scripts\dotify.py'), (Join-Path $root $Image),
        '-o', (Join-Path $root 'assets\portrait'),
        '--mode', $Mode, '--cols', $Cols,
        '--equalize', '--detail', '0.5'
    )
    if ($Square)  { $dotArgs += @('--square', '--focus', $Focus) }
    if ($Circle)  { $dotArgs += '--circle' }
    if ($Color)   { $dotArgs += '--color' }
    if ($Animate) { $dotArgs += '--animate' }
    if ($Invert)  { $dotArgs += '--invert' }
    $dotArgs += '--reveal'
    python @dotArgs
} else {
    Write-Host "`n[2/3] no image found at $Image, skipping the portrait" -ForegroundColor DarkGray
}

Write-Host "`n[3/3] done. Open preview.html to check assets, then read SETUP.md to push to GitHub!`n" -ForegroundColor Green
