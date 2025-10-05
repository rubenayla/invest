#!/bin/bash
cd ~/repos/invest
export PATH=$HOME/.local/bin:$PATH
uv run python neural_network/training/comprehensive_neural_training.py
