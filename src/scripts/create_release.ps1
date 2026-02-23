<#
.SYNOPSIS
 Create a GitHub release using the `gh` CLI or the GitHub API.

 USAGE
 powershell -File .\scripts\create_release.ps1 -Tag "fix/folder-selection-2026-02-23"

 This script prefers an existing `GITHUB_TOKEN` environment variable. If missing,
 it prompts for a token (input hidden) and offers to save it permanently via `setx`.

#>

param(
    [string]$Tag = "fix/folder-selection-2026-02-23",
    [string]$Title = "Fix: folder selection & parent navigation",
    [string]$NotesFile = "README.md"
)

function Get-RepoSluggified() {
    # Try to derive owner/repo from git remote
    try {
        $url = git config --get remote.origin.url 2>$null
        if (-not $url) { return $null }
        $url = $url.Trim()
        # handle https and ssh forms
        if ($url -match "github.com[:/](.+?)(\.git)?$") { return $matches[1] }
        return $null
    } catch { return $null }
}

if (-not $env:GITHUB_TOKEN) {
    Write-Host "GITHUB_TOKEN not set. Enter PAT (input is hidden):"
    $secure = Read-Host -AsSecureString
    $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    $token = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)

    $save = Read-Host "Save token permanently to user environment (setx)? [y/N]"
    if ($save -match '^[Yy]') {
        setx GITHUB_TOKEN $token | Out-Null
        Write-Host "GITHUB_TOKEN saved (available in new shells)."
    } else {
        $env:GITHUB_TOKEN = $token
        Write-Host "GITHUB_TOKEN set for this session only."
    }
} else {
    Write-Host "Using existing GITHUB_TOKEN from environment."
}

# Load release notes
if (Test-Path $NotesFile) {
    $notes = Get-Content $NotesFile -Raw
} else {
    $notes = "Release created via scripts/create_release.ps1"
}

# Prefer gh CLI if available
$gh = Get-Command gh -ErrorAction SilentlyContinue
if ($gh) {
    Write-Host "Creating release via gh CLI..."
    gh release create $Tag -t $Title -n $notes
    if ($LASTEXITCODE -eq 0) { Write-Host "Release created with gh." } else { Write-Host "gh failed (exit $LASTEXITCODE)." }
    return
}

# Fallback: use GitHub API directly
$repo = Get-RepoSluggified
if (-not $repo) { Write-Error "Could not determine repo from git remote. Please run this inside a cloned repo with origin set."; exit 1 }

$payload = @{ tag_name = $Tag; name = $Title; body = $notes } | ConvertTo-Json -Depth 5
$headers = @{ Authorization = "token $env:GITHUB_TOKEN"; Accept = 'application/vnd.github+json' }

try {
    $resp = Invoke-RestMethod -Uri "https://api.github.com/repos/$repo/releases" -Method Post -Headers $headers -Body $payload
    Write-Host "Release created: $($resp.html_url)"
} catch {
    Write-Error "Failed to create release: $_"
    exit 1
}
