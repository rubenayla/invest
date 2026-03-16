#!/bin/bash
# Train wider network: 3 layers [512, 256, 128]
cd ~/repos/invest
export PATH=$HOME/.local/bin:$PATH
export ARCH_NAME="wider_3layer"
export HIDDEN_DIMS="512,256,128"
uv run python neural_network/training/parallel_architecture_experiments.py > training_wider.log 2>&1
