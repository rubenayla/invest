# Windows + WSL + SSH Development Setup

## Overview

This document explains how to use your Windows laptop with WSL2 Ubuntu for GPU-accelerated training while developing on your Mac.

## Architecture

```
Mac (Daily Driver)
    ↓ SSH (192.168.1.117)
Windows Laptop
    ↓ WSL2
Ubuntu Linux
    ↓ CUDA
NVIDIA GTX 1650 GPU
```

## What's Configured

### Windows Machine (192.168.1.117)
- **OS**: Windows 11
- **SSH Server**: OpenSSH (running on port 22)
- **User**: ruben
- **WSL2**: Installed with Ubuntu
- **GPU**: NVIDIA GTX 1650 (4GB VRAM)

### WSL2 Ubuntu
- **Location**: `~/repos/invest`
- **uv**: Installed at `~/.local/bin/uv`
- **Python**: Managed by uv (3.12)
- **CUDA**: 12.9 (accessible from WSL)
- **PyTorch**: Installed with CUDA 12.1 support

### SSH Access from Mac
- **SSH Key**: `~/.ssh/id_ed25519` (Mac)
- **Authorized on Windows**: `C:\ProgramData\ssh\administrators_authorized_keys`
- **Connection**: `ssh ruben@192.168.1.117`

## Directory Structure

### On Windows WSL
```
~/repos/
└── invest/              # Main project repository
    ├── src/             # Source code
    ├── scripts/         # Training scripts
    ├── tests/           # Tests
    ├── pyproject.toml   # Dependencies
    └── *.pt             # Trained models (after training)
```

### On Mac
```
~/repos/invest/          # Same structure
    └── (synchronized via git or manual transfer)
```

## Common Workflows

### 1. SSH into Windows from Mac

⚠️ **IMPORTANT**: When SSHing from Mac to Windows, commands execute in PowerShell, NOT bash. To run WSL commands, you must explicitly invoke PowerShell with the `wsl` command.

```bash
# Direct SSH to Windows (lands in PowerShell)
ssh ruben@192.168.1.117

# Access WSL from PowerShell prompt
wsl

# Run WSL commands via PowerShell from Mac
ssh ruben@192.168.1.117 'powershell.exe -Command "wsl bash -c \"pwd\""'
```

### 2. Run Training on Windows GPU

**❌ KNOWN LIMITATION: Remote execution via SSH doesn't work reliably**

SSH to Windows → PowerShell → WSL has multiple issues:
- Background processes (`nohup`, `&`) terminate when SSH disconnects
- Complex quote escaping (PowerShell uses different rules than bash)
- Session management tools (screen, tmux) can't persist across SSH disconnect

**✅ SOLUTION: Use git push/pull workflow**

```bash
# On Mac: Make code changes and push
cd ~/repos/invest
# ... make changes ...
git add .
git commit -m "Update training code"
git push

# On Windows: Pull and run (in Ubuntu app)
cd ~/repos/invest
git pull
./scripts/start_gpu_training.sh

# Or run directly:
export PATH=$HOME/.local/bin:$PATH
uv run python scripts/comprehensive_neural_training.py
```

**Monitor GPU usage:**
```bash
watch -n 1 nvidia-smi
```

### 3. Transfer Trained Models Back to Mac

**Method 1: SCP (after training completes)**
```bash
# From Mac
scp ruben@192.168.1.117:~/repos/invest/*.pt ~/repos/invest/
```

**Method 2: Via WSL to Windows to Mac**
```bash
# In WSL, copy models to Windows home
cp ~/repos/invest/*.pt /mnt/c/Users/ruben/

# From Mac
scp ruben@192.168.1.117:/Users/ruben/*.pt ~/repos/invest/
```

**Method 3: Git (recommended for version control)**
```bash
# In WSL
cd ~/repos/invest
git add *.pt
git commit -m "Add trained models from Windows GPU"
git push

# On Mac
git pull
```

### 4. Develop on Mac, Train on Windows

**Typical workflow:**
```bash
# On Mac - develop and test
cd ~/repos/invest
# make changes...
git add .
git commit -m "Update training config"
git push

# On Windows WSL - pull changes and train
ssh ruben@192.168.1.117
wsl
cd ~/repos/invest
git pull
uv run python scripts/comprehensive_neural_training.py

# After training - push models
git add *.pt comprehensive_training.log
git commit -m "Add trained models"
git push

# On Mac - pull trained models
git pull
```

## GPU Training Performance

With NVIDIA GTX 1650:
- **Data collection**: ~10 minutes (5000 samples, CPU-bound)
- **Neural network training**: ~2-5 minutes (GPU-accelerated)
- **Total training time**: ~15-20 minutes
- **Speedup vs Mac CPU**: 3-5x faster

## Environment Setup

### First-Time Setup on Windows WSL

```bash
# 1. Clone or setup repo
mkdir -p ~/repos
cd ~/repos
# (repo should already be at ~/repos/invest)

# 2. Setup uv (already done)
export PATH=$HOME/.local/bin:$PATH
echo 'export PATH=$HOME/.local/bin:$PATH' >> ~/.bashrc

# 3. Install dependencies
cd ~/repos/invest
uv sync --all-groups

# 4. Install PyTorch with CUDA
uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# 5. Verify GPU
uv run python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"
nvidia-smi
```

### Verify CUDA Setup

```bash
# Check NVIDIA driver
nvidia-smi

# Check PyTorch CUDA
uv run python -c "
import torch
print(f'PyTorch version: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
print(f'CUDA version: {torch.version.cuda}')
if torch.cuda.is_available():
    print(f'GPU: {torch.cuda.get_device_name(0)}')
    print(f'GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB')
"
```

Expected output:
```
PyTorch version: 2.5.0+cu121
CUDA available: True
CUDA version: 12.1
GPU: NVIDIA GeForce GTX 1650
GPU Memory: 4.0 GB
```

## Troubleshooting

### SSH Connection Issues

**Problem**: Permission denied
```bash
# Check SSH key on Windows
ssh ruben@192.168.1.117 'powershell.exe -Command "Get-Content C:\ProgramData\ssh\administrators_authorized_keys"'

# Should show: ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIM9Amm2kUaZs91mLnoJxPp/Ua1vow5flYsomBw+Cn8KL

# Restart SSH service on Windows (PowerShell as Admin)
Restart-Service sshd
```

### WSL Path Issues

**Problem**: Can't find uv or Python
```bash
# Always export PATH first
export PATH=$HOME/.local/bin:$PATH

# Or add to .bashrc permanently
echo 'export PATH=$HOME/.local/bin:$PATH' >> ~/.bashrc
source ~/.bashrc
```

### CUDA Not Available

**Problem**: PyTorch can't see GPU
```bash
# 1. Check NVIDIA driver in WSL
nvidia-smi  # Should show GTX 1650

# 2. Reinstall PyTorch with correct CUDA version
cd ~/repos/invest
uv pip uninstall torch
uv pip install torch --index-url https://download.pytorch.org/whl/cu121

# 3. Verify
uv run python -c "import torch; print(torch.cuda.is_available())"
```

### File Permission Issues

**Problem**: Can't write to Windows filesystem from WSL
```bash
# Use WSL filesystem for development
cd ~/repos/invest  # Good - native WSL path

# Avoid Windows paths from WSL
cd /mnt/c/Users/ruben/repos/invest  # Slower, permission issues
```

## Best Practices

### 1. Use WSL Filesystem for Active Development
- **Fast**: Native Linux I/O performance
- **No permission issues**: Full Linux permissions
- **Location**: `~/repos/invest` (in WSL)

### 2. Use Git for Synchronization
- Commit on Mac → Push → Pull on Windows → Train → Push → Pull on Mac
- Keeps both environments in sync
- Version control for models

### 3. Monitor Training Progress

**From Mac (via SSH):**
```bash
# Stream training log
ssh ruben@192.168.1.117 'wsl tail -f ~/repos/invest/comprehensive_training.log'

# Check GPU usage
ssh ruben@192.168.1.117 'wsl watch -n 1 nvidia-smi'
```

**Directly on Windows (Ubuntu app):**
```bash
# Monitor log
tail -f ~/repos/invest/comprehensive_training.log | grep -E "(Epoch|MAE|Collected)"

# Watch GPU
watch -n 1 nvidia-smi
```

### 4. Manage Python Dependencies

```bash
# Always use uv, never system pip
uv pip install <package>          # Good
pip install <package>              # Bad - wrong Python

# Update dependencies
cd ~/repos/invest
uv sync --all-groups               # Sync from pyproject.toml
```

## Quick Reference

### Essential Commands

```bash
# SSH to Windows
ssh ruben@192.168.1.117

# Enter WSL
wsl

# Setup environment (run once per session)
export PATH=$HOME/.local/bin:$PATH
cd ~/repos/invest

# Run training
uv run python scripts/comprehensive_neural_training.py

# Check GPU
nvidia-smi

# Transfer models to Mac
# (from Mac)
scp ruben@192.168.1.117:~/repos/invest/*.pt ~/repos/invest/
```

### File Paths

| Location | Mac | Windows (PowerShell) | WSL Ubuntu |
|----------|-----|----------------------|------------|
| Repo | `~/repos/invest` | N/A | `~/repos/invest` |
| Home | `/Users/rubenayla` | `C:\Users\ruben` | `/home/rubenayla` |
| Windows C: from WSL | N/A | N/A | `/mnt/c/` |

### Network

| Machine | IP | Access |
|---------|-----|--------|
| Mac | 192.168.1.139 | - |
| Windows | 192.168.1.117 | SSH from Mac |
| WSL Ubuntu | (same as Windows) | Via `wsl` command |

## Summary

**Your setup:**
- **Development**: Mac (comfortable environment)
- **Training**: Windows WSL + GTX 1650 (fast GPU)
- **Connection**: SSH with key authentication
- **Sync**: Git or SCP for model transfer
- **Performance**: 3-5x faster training than Mac CPU

This gives you the best of both worlds - Mac for development, Windows GPU for training!
