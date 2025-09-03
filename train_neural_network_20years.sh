#!/bin/bash

echo "🧠 Neural Network Training with 20 Years of Data"
echo "================================================="
echo ""
echo "This will train a neural network model using:"
echo "• 20 years of historical stock data (2004-2024)"
echo "• 5,000 random samples across time and stocks"
echo "• Intelligent early stopping when progress plateaus"
echo "• 82 diverse stocks from different sectors"
echo "• 2-year forward return prediction"
echo ""
echo "Expected training time: 2-6 hours depending on hardware"
echo "The system will automatically stop when:"
echo "  - Model stops improving (patience: 50 epochs)"
echo "  - Maximum epochs reached (300)"
echo "  - Correlation target achieved (>0.5)"
echo ""

read -p "Continue with training? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Training cancelled."
    exit 0
fi

echo "🚀 Starting comprehensive neural network training..."
echo "📊 Monitor progress in another terminal with:"
echo "    poetry run python scripts/training_monitor.py"
echo ""

# Run training in background so user can monitor
poetry run python scripts/comprehensive_neural_training.py

echo ""
echo "🎉 Training completed! Check the results:"
echo "  • Log file: comprehensive_training.log"
echo "  • Results: comprehensive_training_results_*.json"
echo "  • Best model: best_comprehensive_nn_2year_*.pt"
echo ""
echo "📊 To visualize results:"
echo "    poetry run python scripts/training_monitor.py --plot"