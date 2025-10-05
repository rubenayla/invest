#!/bin/bash
# WSL GPU Setup Script - Enable CUDA for GTX 1650

set -e

echo "🔧 Installing CUDA for WSL..."
echo ""

# Download CUDA keyring
echo "Downloading CUDA keyring..."
wget -q https://developer.download.nvidia.com/compute/cuda/repos/wsl-ubuntu/x86_64/cuda-keyring_1.1-1_all.deb

# Install keyring (will prompt for password)
echo "Installing CUDA keyring (sudo password required)..."
sudo dpkg -i cuda-keyring_1.1-1_all.deb

# Update package list
echo "Updating package list..."
sudo apt-get update

# Install CUDA toolkit
echo "Installing CUDA toolkit (this may take 5-10 minutes)..."
sudo apt-get install -y cuda-toolkit-12-6

# Add CUDA to PATH
echo "Adding CUDA to PATH..."
echo 'export PATH=/usr/local/cuda/bin:$PATH' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
export PATH=/usr/local/cuda/bin:$PATH
export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH

# Test GPU
echo ""
echo "Testing GPU access..."
nvidia-smi

echo ""
echo "✅ CUDA installation complete!"
echo ""
echo "Now installing PyTorch with CUDA support..."

# Go to project and install PyTorch with CUDA
cd ~/invest_training_package
export PATH="$HOME/.local/bin:$PATH"

echo "Installing PyTorch with CUDA 12.1 support..."
uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Test PyTorch CUDA
echo ""
echo "Testing PyTorch CUDA..."
uv run python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}'); print(f'GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"None\"}')"

echo ""
echo "🎉 Setup complete! You can now train with GPU acceleration in WSL."
echo ""
echo "To use GPU in training:"
echo "  cd ~/invest_training_package"
echo "  uv run python neural_network/training/comprehensive_neural_training.py"
echo ""
echo "The training will automatically use your GTX 1650 GPU!"
