#!/bin/bash
cd ~/repos/invest
export PATH=$HOME/.local/bin:$PATH
uv run python scripts/comprehensive_neural_training.py
