# Windows Training Setup Script
# Run this in PowerShell on your Windows machine

Write-Host "🚀 Starting Neural Network Training Setup" -ForegroundColor Green
Write-Host ""

# Check if in correct directory
if (!(Test-Path "scripts/comprehensive_neural_training.py")) {
    Write-Host "❌ Error: Must run from invest_training_package directory" -ForegroundColor Red
    exit 1
}

# Check for GPU
Write-Host "Checking for GPU..." -ForegroundColor Cyan
try {
    $gpu = nvidia-smi --query-gpu=name --format=csv,noheader 2>$null
    if ($gpu) {
        Write-Host "✅ GPU detected: $gpu" -ForegroundColor Green
        Write-Host "   Training will be 10-100x faster!" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️  No NVIDIA GPU detected - training will use CPU (slower)" -ForegroundColor Yellow
}
Write-Host ""

# Check uv installation
Write-Host "Checking uv installation..." -ForegroundColor Cyan
if (!(Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "Installing uv..." -ForegroundColor Yellow
    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

    # Add to PATH for current session
    $env:Path += ";$env:USERPROFILE\.cargo\bin"

    if (!(Get-Command uv -ErrorAction SilentlyContinue)) {
        Write-Host "❌ uv installation failed. Please close and reopen PowerShell." -ForegroundColor Red
        exit 1
    }
}
Write-Host "✅ uv is installed" -ForegroundColor Green
Write-Host ""

# Install dependencies
Write-Host "Installing dependencies (this may take a few minutes)..." -ForegroundColor Cyan
uv sync --all-groups
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Dependency installation failed" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Dependencies installed" -ForegroundColor Green
Write-Host ""

# Run training
Write-Host "🎯 Starting training..." -ForegroundColor Green
Write-Host "   Data period: 2015-2024" -ForegroundColor Cyan
Write-Host "   Macroeconomic features: Fed funds, Treasury, VIX, S&P P/E, GDP, inflation, unemployment" -ForegroundColor Cyan
Write-Host "   Expected time: 5-45 minutes (depending on GPU)" -ForegroundColor Cyan
Write-Host ""
Write-Host "Monitor progress: Open another PowerShell and run:" -ForegroundColor Yellow
Write-Host "   Get-Content comprehensive_training.log -Wait" -ForegroundColor White
Write-Host ""

$start = Get-Date
uv run python scripts/comprehensive_neural_training.py
$duration = (Get-Date) - $start

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Training completed successfully!" -ForegroundColor Green
    Write-Host "   Duration: $($duration.ToString('hh\:mm\:ss'))" -ForegroundColor Cyan
    Write-Host ""

    # List trained models
    Write-Host "📦 Trained models:" -ForegroundColor Green
    Get-ChildItem *.pt | ForEach-Object {
        $size = "{0:N2}" -f ($_.Length / 1KB)
        Write-Host "   $($_.Name) ($size KB)" -ForegroundColor White
    }
    Write-Host ""

    # Package models
    Write-Host "Creating package for transfer..." -ForegroundColor Cyan
    $date = Get-Date -Format "yyyyMMdd"
    tar -czf "trained_models_$date.tar.gz" *.pt comprehensive_training.log

    $package = Get-Item "trained_models_$date.tar.gz"
    $packageSize = "{0:N2}" -f ($package.Length / 1MB)

    Write-Host "✅ Package created: trained_models_$date.tar.gz ($packageSize MB)" -ForegroundColor Green
    Write-Host ""
    Write-Host "📤 Transfer to Mac using one of these methods:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Method 1 - HTTP (if Mac server is running):" -ForegroundColor Cyan
    Write-Host "   # On Mac, start server in invest directory:" -ForegroundColor White
    Write-Host "   python3 -m http.server 8000" -ForegroundColor White
    Write-Host "   # Then upload from Windows:" -ForegroundColor White
    Write-Host "   curl.exe -X POST -F 'file=@trained_models_$date.tar.gz' http://192.168.1.139:8000/upload" -ForegroundColor White
    Write-Host ""
    Write-Host "Method 2 - SCP (if SSH keys configured):" -ForegroundColor Cyan
    Write-Host "   scp trained_models_$date.tar.gz ruben@192.168.1.139:~/repos/invest/" -ForegroundColor White
    Write-Host ""
    Write-Host "Method 3 - AnyDesk:" -ForegroundColor Cyan
    Write-Host "   Just drag and drop trained_models_$date.tar.gz to Mac via AnyDesk" -ForegroundColor White
    Write-Host ""

} else {
    Write-Host ""
    Write-Host "❌ Training failed. Check comprehensive_training.log for details." -ForegroundColor Red
    Write-Host ""
}
