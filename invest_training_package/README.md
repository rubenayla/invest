# Invest Neural Network Training Package

This package contains everything needed to train neural network valuation models.

## Quick Start

1. **Install dependencies**: `uv sync --all-groups`
2. **Run training**: `uv run python scripts/comprehensive_neural_training.py`
3. **Package models**: `tar -czf trained_models.tar.gz *.pt`

See **TRAINING_SETUP.md** for detailed instructions.

## What's Included

- `src/` - Source code for valuation models
- `scripts/` - Training and evaluation scripts
- `tests/` - Test suite
- `pyproject.toml` - Project dependencies
- `docs/` - Documentation

## Training Output

After training completes, you'll have:
- `*.pt` files - Trained models (transfer these back)
- `comprehensive_training.log` - Training details
- `evaluation_results/` - Performance metrics (optional)

## Support

- Training guide: `docs/portable_training_guide.md`
- Evaluation guide: `docs/neural_network_evaluation_guide.md`
- Project instructions: `CLAUDE.md`

Package created: domingo,  5 de octubre de 2025, 19:29:37 CEST
