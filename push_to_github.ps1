# PowerShell script to push to GitHub
# Usage: .\push_to_github.ps1 YOUR_GITHUB_USERNAME REPO_NAME

param(
    [Parameter(Mandatory=$true)]
    [string]$GitHubUsername,
    
    [Parameter(Mandatory=$false)]
    [string]$RepoName = "uk-property-trawler"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Pushing to GitHub" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if remote already exists
$remoteExists = git remote get-url origin 2>$null
if ($remoteExists) {
    Write-Host "Remote 'origin' already exists: $remoteExists" -ForegroundColor Yellow
    $overwrite = Read-Host "Do you want to update it? (y/n)"
    if ($overwrite -eq 'y') {
        git remote remove origin
    } else {
        Write-Host "Aborted." -ForegroundColor Red
        exit
    }
}

# Add remote
$repoUrl = "https://github.com/$GitHubUsername/$RepoName.git"
Write-Host "Adding remote: $repoUrl" -ForegroundColor Green
git remote add origin $repoUrl

# Rename branch to main if needed
$currentBranch = git branch --show-current
if ($currentBranch -ne "main") {
    Write-Host "Renaming branch from '$currentBranch' to 'main'..." -ForegroundColor Yellow
    git branch -M main
}

# Push
Write-Host ""
Write-Host "Pushing to GitHub..." -ForegroundColor Green
git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Success! Your code is on GitHub!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Repository URL: https://github.com/$GitHubUsername/$RepoName" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Next step: Deploy on Render.com!" -ForegroundColor Yellow
} else {
    Write-Host ""
    Write-Host "Error pushing to GitHub. Make sure:" -ForegroundColor Red
    Write-Host "1. The repository exists on GitHub" -ForegroundColor Red
    Write-Host "2. You have access to it" -ForegroundColor Red
    Write-Host "3. You're authenticated (may need to enter credentials)" -ForegroundColor Red
}

