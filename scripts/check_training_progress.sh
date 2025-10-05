#!/bin/bash
# Quick training progress checker

echo "=== Neural Network Training Progress ==="
echo ""

# Check if training is running
if pgrep -f "comprehensive_neural_training.py" > /dev/null; then
    echo "✓ Training is RUNNING"
else
    echo "✗ Training is NOT running"
fi

echo ""
echo "Latest progress:"
grep -E "(Processing sample|Collected|Starting training|Epoch|MAE|converged)" comprehensive_training.log 2>/dev/null | tail -10

echo ""
echo "To monitor live:"
echo "  tail -f comprehensive_training.log | grep -E '(Processing|Epoch|MAE)'"
