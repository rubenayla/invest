# Quick Training Setup

## 1. Install Dependencies

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh  # Linux/Mac
# OR
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"  # Windows

# Install project dependencies
uv sync --all-groups
```

## 2. Run Training

```bash
# Default training (2015-2024, 5000 samples)
uv run python scripts/comprehensive_neural_training.py

# Monitor progress
tail -f comprehensive_training.log
```

## 3. Package Models

```bash
# Create archive of trained models
tar -czf trained_models_$(date +%Y%m%d).tar.gz *.pt comprehensive_training.log

# Transfer back to your Mac
# scp trained_models_*.tar.gz user@mac-ip:~/repos/invest/
```

## Hardware Requirements

- **Minimum**: 8GB RAM, any CPU (training will be slow)
- **Recommended**: 16GB RAM, NVIDIA GPU with 8GB+ VRAM
- **Optimal**: 32GB RAM, NVIDIA RTX 3080+ or A100

## Troubleshooting

**"Module not found"**
- Make sure you use `uv run` prefix
- Run `uv sync --all-groups` again

**Out of memory**
- Reduce target_samples in scripts/comprehensive_neural_training.py
- Or increase system RAM/swap

**Training too slow**
- Use a machine with GPU
- Reduce target_samples temporarily
- Check CPU/GPU usage with `htop` or `nvidia-smi`

For full documentation, see: `docs/portable_training_guide.md`
