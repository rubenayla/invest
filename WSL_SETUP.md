# WSL2 Ubuntu Setup Guide

## ✅ Current Status

- WSL2 Ubuntu: **Installed and working**
- uv package manager: **Installed**
- Training package: **Extracted to ~/invest_training_package**
- GPU access: **Not yet configured** (optional)

## Quick Start (No GPU needed for development)

Open **Windows Terminal** or **Ubuntu** app and run:

```bash
# Navigate to project
cd ~/invest_training_package

# Add uv to PATH (run once per session, or add to ~/.bashrc)
export PATH="$HOME/.local/bin:$PATH"

# Install dependencies
uv sync --all-groups

# Run training (uses CPU - still works!)
uv run python neural_network/training/comprehensive_neural_training.py

# Or any other script
uv run python scripts/systematic_analysis.py
```

## Enable GPU Support (Optional - for faster training)

GPU in WSL requires NVIDIA drivers for WSL2:

### 1. Install NVIDIA Driver for WSL (on Windows)

Download from: https://www.nvidia.com/Download/index.aspx
- Select: GeForce GTX 1650
- OS: Windows 11
- **Important**: Choose "NVIDIA drivers for WSL"

### 2. Install CUDA Toolkit in WSL

```bash
# In WSL Ubuntu terminal
wget https://developer.download.nvidia.com/compute/cuda/repos/wsl-ubuntu/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
sudo apt-get update
sudo apt-get -y install cuda-toolkit-12-6

# Verify
nvidia-smi  # Should show GTX 1650
```

### 3. Install PyTorch with CUDA

```bash
cd ~/invest_training_package
uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Test GPU
uv run python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

## Advantages of WSL vs Native Windows

✅ **Same commands as Mac** - no PowerShell syntax differences
✅ **Better terminal** - proper bash, ssh, git tools
✅ **Faster file I/O** - Linux file system performance
✅ **No encoding issues** - UTF-8 by default
✅ **SSH access** - can SSH into WSL from Mac: `ssh ruben@192.168.1.117` then `wsl`

## Daily Workflow

### Option 1: Direct WSL Terminal
1. Open **Windows Terminal** → Ubuntu tab
2. `cd ~/invest_training_package`
3. `export PATH="$HOME/.local/bin:$PATH"`
4. Work normally: `uv run python ...`

### Option 2: SSH from Mac
```bash
# From your Mac
ssh ruben@192.168.1.117

# Once connected, enter WSL
wsl

# Now you're in Ubuntu with full access
cd ~/invest_training_package
uv run python neural_network/training/comprehensive_neural_training.py
```

### Option 3: VS Code Remote
- Install "Remote - WSL" extension in VS Code
- Open folder: `\\wsl$\Ubuntu\home\rubenayla\invest_training_package`
- Full IDE experience in WSL!

## File Access

### From WSL to Windows:
```bash
# Windows C: drive is mounted at /mnt/c
cd /mnt/c/Users/ruben/Documents
```

### From Windows to WSL:
```powershell
# In Windows Explorer, type:
\\wsl$\Ubuntu\home\rubenayla\invest_training_package
```

## Transfer Files Between Mac and WSL

### Mac → WSL:
```bash
# From Mac
scp file.tar.gz ruben@192.168.1.117:/tmp/
ssh ruben@192.168.1.117 'wsl cp /mnt/c/Users/ruben/AppData/Local/Temp/file.tar.gz ~/'
```

### WSL → Mac:
```bash
# From WSL
scp ~/trained_models.tar.gz ruben@192.168.1.139:~/repos/invest/
```

## Pro Tips

1. **Add uv to PATH permanently**:
   ```bash
   echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
   source ~/.bashrc
   ```

2. **Clone repo directly in WSL** (cleaner than Windows copy):
   ```bash
   cd ~
   git clone <your-repo-url> invest
   cd invest
   uv sync --all-groups
   ```

3. **Use tmux for long-running tasks**:
   ```bash
   sudo apt install tmux
   tmux new -s training
   uv run python neural_network/training/comprehensive_neural_training.py
   # Press Ctrl+B then D to detach
   # Reconnect: tmux attach -t training
   ```

## Current Training

The Windows PowerShell training is still running. Once complete, you can use WSL for all future work with a much better experience!
