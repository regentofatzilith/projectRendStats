# PowerShell script to run the Rend Stats Dashboard
# Bypasses execution policy for this session only

Write-Host "Starting Rend Stats Dashboard..." -ForegroundColor Green

# Activate virtual environment and run app
& "$PSScriptRoot\.venv\Scripts\python.exe" "$PSScriptRoot\app.py"
