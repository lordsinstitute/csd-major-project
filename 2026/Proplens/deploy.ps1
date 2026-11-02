<#
.SYNOPSIS
    PropLens AI - Automated DevOps Deployment Script for Windows PowerShell
    Deploys the web application to GitHub and Vercel.

.DESCRIPTION
    This script automates:
    1. Git repository staging, branch normalization, and committing.
    2. Remote GitHub repository configuration (proplens-ai).
    3. Vercel Serverless Function deployment with static asset routing.
#>

param(
    [Parameter(Mandatory=$false)]
    [string]$GitHubUsername = ""
)

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "       PropLens AI - GitHub & Vercel Deployment Assistant      " -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan

# ------------------------------------------------------------------------------
# STEP 1: Verify Git & Workspace Status
# ------------------------------------------------------------------------------
Write-Host "`n[1/4] Checking Git repository status..." -ForegroundColor Yellow

if (-not (Test-Path ".git")) {
    Write-Host "Initializing new Git repository..." -ForegroundColor Green
    git init
}

# Ensure standard 'main' branch
git branch -M main

# Stage modified and untracked files
Write-Host "Staging files (respecting .gitignore)..." -ForegroundColor Green
git add .

$status = git status --porcelain
if ($status) {
    Write-Host "Committing project files..." -ForegroundColor Green
    git commit -m "Deploy PropLens AI: Flask + Leaflet.js + Scikit-Learn on Vercel"
} else {
    Write-Host "Working tree clean. No new changes to commit." -ForegroundColor Gray
}

# ------------------------------------------------------------------------------
# STEP 2: Configure GitHub Remote
# ------------------------------------------------------------------------------
Write-Host "`n[2/4] Configuring GitHub remote repository..." -ForegroundColor Yellow

$existingRemote = git remote get-url origin 2>$null

if (-not $existingRemote) {
    if (-not $GitHubUsername) {
        $GitHubUsername = Read-Host "Enter your GitHub username (or press Enter to skip remote push)"
    }

    if ($GitHubUsername) {
        $remoteUrl = "https://github.com/$GitHubUsername/proplens-ai.git"
        Write-Host "Adding remote origin: $remoteUrl" -ForegroundColor Green
        git remote add origin $remoteUrl
        Write-Host "Pushing to GitHub 'main' branch..." -ForegroundColor Green
        git push -u origin main
    } else {
        Write-Host "Skipping GitHub push. You can push manually using:" -ForegroundColor Gray
        Write-Host "  git remote add origin https://github.com/<your-username>/proplens-ai.git" -ForegroundColor DarkGray
        Write-Host "  git push -u origin main" -ForegroundColor DarkGray
    }
} else {
    Write-Host "Existing remote detected: $existingRemote" -ForegroundColor Green
    Write-Host "Pushing latest commits to remote..." -ForegroundColor Green
    git push origin main
}

# ------------------------------------------------------------------------------
# STEP 3: Check Vercel CLI
# ------------------------------------------------------------------------------
Write-Host "`n[3/4] Verifying Vercel CLI..." -ForegroundColor Yellow

# Use vercel.cmd or npx vercel to avoid PowerShell execution policy blocks
$hasVercelCmd = Get-Command "vercel.cmd" -ErrorAction SilentlyContinue

if (-not $hasVercelCmd) {
    Write-Host "Vercel CLI not found globally. Installing via npm..." -ForegroundColor Green
    npm install -g vercel
}

Write-Host "Vercel CLI is ready." -ForegroundColor Green

# ------------------------------------------------------------------------------
# STEP 4: Deploy to Vercel Production
# ------------------------------------------------------------------------------
Write-Host "`n[4/4] Launching Vercel Production Deployment..." -ForegroundColor Yellow
Write-Host "Command: vercel.cmd --prod" -ForegroundColor Cyan
Write-Host "Follow on-screen prompts to confirm project name (proplens-ai) and settings.`n" -ForegroundColor Gray

# Trigger Vercel CLI deployment
vercel.cmd --prod

Write-Host "`n================================================================" -ForegroundColor Cyan
Write-Host "Deployment workflow finished!" -ForegroundColor Green
Write-Host "Expected Production URL format: https://proplens-ai.vercel.app" -ForegroundColor Yellow
Write-Host "================================================================" -ForegroundColor Cyan
