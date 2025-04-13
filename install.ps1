#Requires -Version 5.1
<#
.SYNOPSIS
    Installs the 'faw' command and Python dependencies for PowerShell.

.DESCRIPTION
    This script installs the required Python packages from requirements.txt and
    adds a function named 'faw' to your PowerShell profile ($PROFILE).
    This function allows you to run the find_a_workinator.py script from anywhere
    in PowerShell by simply typing 'faw' followed by any arguments.

.NOTES
    File Name: install.ps1
    Requires : PowerShell 5.1+, Python 3+ with pip available in PATH.
               A 'requirements.txt' file must exist in the same directory.
    Usage    : Run with elevated privileges if installing packages globally, or ensure
               pip installs packages for the current user.
               Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
               .\install.ps1
#>

# --- Configuration ---
$ScriptPythonName = "find_a_workinator.py"
$RequirementsFileName = "requirements.txt"
$FunctionName = "faw"

# --- Script Logic ---

Write-Host "Starting installation for '$FunctionName' command..." -ForegroundColor Cyan

# Get the directory where this installation script is located
try {
    $InstallDir = Split-Path -Parent -Path $MyInvocation.MyCommand.Definition -ErrorAction Stop
} catch {
    Write-Error "Could not determine the script installation directory."
    exit 1
}

# Construct the full path to the target Python script and requirements file
$TargetScriptPath = Join-Path -Path $InstallDir -ChildPath $ScriptPythonName
$RequirementsPath = Join-Path -Path $InstallDir -ChildPath $RequirementsFileName

# Verify that the target Python script exists
if (-not (Test-Path -LiteralPath $TargetScriptPath -PathType Leaf)) {
    Write-Error "Could not find Python script '$ScriptPythonName' at: $TargetScriptPath"
    exit 1
}
Write-Host "Python script found at: $TargetScriptPath"

# --- Install Dependencies ---
Write-Host "Checking for requirements file: $RequirementsPath"
if (-not (Test-Path -LiteralPath $RequirementsPath -PathType Leaf)) {
    Write-Warning "Requirements file '$RequirementsFileName' not found at '$RequirementsPath'."
    Write-Warning "Skipping dependency installation. The '$FunctionName' command might fail if dependencies are missing."
} else {
    Write-Host "Found '$RequirementsFileName'. Attempting to install dependencies..."
    # Check if python exists and has pip
    $pythonExe = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonExe) {
        Write-Error "Python command was not found in your system PATH. Cannot install dependencies."
        Write-Error "Please ensure Python is installed and added to PATH."
        exit 1
    }

    # Check if pip is available
    $pipTest = Invoke-Expression "$($pythonExe.Source) -m pip --version" -ErrorAction SilentlyContinue
    if ($LASTEXITCODE -ne 0) {
         Write-Error "Could not execute 'python -m pip'. Ensure pip is installed for your Python environment."
         Write-Error "Cannot install dependencies."
         exit 1
    }

    Write-Host "Running: python -m pip install -r '$RequirementsPath'"
    # Use Invoke-Expression to run pip, capture output/errors might be needed for better diagnostics
    python -m pip install -r "$RequirementsPath"

    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to install Python dependencies from '$RequirementsFileName'. Please check pip output above."
        Write-Error "The '$FunctionName' command might not work correctly."
        exit 1
    } else {
        Write-Host "Python dependencies installed successfully." -ForegroundColor Green
    }
}
# --- End Install Dependencies ---


# Define the PowerShell function
$functionDefinition = @"

# Function added by find-a-workinator installer to run the script easily
# Usage: $FunctionName [arguments_for_python_script]
function $FunctionName {
    param(
        [Parameter(ValueFromRemainingArguments=$true)]
        [string[]]`$arguments # Capture all remaining arguments
    )
    `$scriptToRun = "$TargetScriptPath" # Path embedded by installer
    `$pythonExe = Get-Command python -ErrorAction SilentlyContinue
    if (-not `$pythonExe) {
        Write-Warning "Python command was not found in your system PATH."
        return
    }
    Write-Verbose "Executing: python `"`$scriptToRun`" `$arguments"
    python "`$scriptToRun" `$arguments
}

"@

# Find and update the PowerShell profile
$profilePath = $PROFILE.CurrentUserAllHosts
if (-not $profilePath) { $profilePath = $PROFILE.CurrentUserCurrentHost }
if (-not $profilePath) {
     $profilePath = Join-Path -Path $HOME -ChildPath "Documents\WindowsPowerShell\Microsoft.PowerShell_profile.ps1"
     Write-Warning "Could not automatically determine profile path, using default: $profilePath"
}
Write-Host "Target PowerShell profile path: $profilePath"
$profileDir = Split-Path -Parent -Path $profilePath
if (-not (Test-Path -Path $profileDir -PathType Container)) {
    Write-Host "Profile directory '$profileDir' not found. Creating..." -ForegroundColor Yellow
    try { New-Item -ItemType Directory -Path $profileDir -Force -ErrorAction Stop | Out-Null; Write-Host "Profile directory created." -ForegroundColor Green }
    catch { Write-Error "Failed to create profile directory '$profileDir'."; exit 1 }
}
if (-not (Test-Path -LiteralPath $profilePath -PathType Leaf)) {
    Write-Host "Profile file '$profilePath' not found. Creating..." -ForegroundColor Yellow
    try { New-Item -ItemType File -Path $profilePath -Force -ErrorAction Stop | Out-Null; Write-Host "Profile file created." -ForegroundColor Green }
    catch { Write-Error "Failed to create profile file '$profilePath'."; exit 1 }
}

# Add function to profile if it doesn't exist
try {
    $profileContent = Get-Content -LiteralPath $profilePath -Raw -ErrorAction SilentlyContinue
    if ($profileContent -match "function\s+$FunctionName\s*{") {
        Write-Warning "Function '$FunctionName' seems to already exist in '$profilePath'."
        Write-Warning "Dependencies were checked/installed, but the function was not added again."
        Write-Host "To update the function, manually remove it from the profile and re-run this script." -ForegroundColor Yellow
    } else {
        Write-Host "Adding '$FunctionName' function to profile '$profilePath'..."
        Add-Content -Path $profilePath -Value $functionDefinition -Encoding UTF8
        Write-Host "'$FunctionName' function added successfully." -ForegroundColor Green
        Write-Host "Please restart PowerShell or run '. `"$profilePath`"' to activate the '$FunctionName' command." -ForegroundColor Green
    }
} catch {
    Write-Error "An error occurred while accessing the profile '$profilePath'."
    Write-Error $_.Exception.Message
    exit 1
}

Write-Host "Installation process complete." -ForegroundColor Cyan