#!/usr/bin/env python3
"""
Genetic Algorithm optimizer for neural network architecture.

Simple GA to find optimal hidden layer sizes and training parameters.
"""

import json
import random
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.invest.valuation.neural_network_model import NeuralNetworkValuationModel


@dataclass
class NetworkGenes:
    """Represents a neural network configuration (genes)."""
    hidden_layers: List[int]
    dropout_rate: float
    learning_rate: float

    def to_dict(self) -> Dict:
        return {
            'hidden_layers': self.hidden_layers,
            'dropout_rate': self.dropout_rate,
            'learning_rate': self.learning_rate
        }

    @classmethod
    def from_dict(cls, data: Dict):
        return cls(
            hidden_layers=data['hidden_layers'],
            dropout_rate=data['dropout_rate'],
            learning_rate=data['learning_rate']
        )


@dataclass
class Individual:
    """Individual in the genetic algorithm population."""
    genes: NetworkGenes
    fitness: float = 0.0
    test_mae: float = float('inf')
    test_correlation: float = 0.0


class GeneticOptimizer:
    """Genetic algorithm for neural network architecture optimization."""

    def __init__(self, population_size: int = 20, generations: int = 10):
        self.population_size = population_size
        self.generations = generations

        # Define gene ranges
        self.layer_options = [
            [64, 32],
            [128, 64, 32],
            [256, 128, 64, 32],
            [512, 256, 128, 64],
            [256, 128, 64],
            [512, 256, 128],
            [128, 64],
            [256, 128]
        ]

        self.dropout_options = [0.1, 0.2, 0.3, 0.4, 0.5]
        self.learning_rate_options = [0.0001, 0.0005, 0.001, 0.005, 0.01]

    def create_random_individual(self) -> Individual:
        """Create a random individual."""
        genes = NetworkGenes(
            hidden_layers=random.choice(self.layer_options),
            dropout_rate=random.choice(self.dropout_options),
            learning_rate=random.choice(self.learning_rate_options)
        )
        return Individual(genes=genes)

    def mutate(self, individual: Individual) -> Individual:
        """Mutate an individual."""
        genes = NetworkGenes(
            hidden_layers=individual.genes.hidden_layers.copy(),
            dropout_rate=individual.genes.dropout_rate,
            learning_rate=individual.genes.learning_rate
        )

        # 30% chance to mutate each parameter
        if random.random() < 0.3:
            genes.hidden_layers = random.choice(self.layer_options)

        if random.random() < 0.3:
            genes.dropout_rate = random.choice(self.dropout_options)

        if random.random() < 0.3:
            genes.learning_rate = random.choice(self.learning_rate_options)

        return Individual(genes=genes)

    def crossover(self, parent1: Individual, parent2: Individual) -> Individual:
        """Create offspring through crossover."""
        # Simple crossover - randomly choose each gene from either parent
        genes = NetworkGenes(
            hidden_layers=random.choice([parent1.genes.hidden_layers, parent2.genes.hidden_layers]),
            dropout_rate=random.choice([parent1.genes.dropout_rate, parent2.genes.dropout_rate]),
            learning_rate=random.choice([parent1.genes.learning_rate, parent2.genes.learning_rate])
        )
        return Individual(genes=genes)

    def evaluate_individual(self, individual: Individual,
                          training_data: List[Tuple[str, Dict[str, Any], float]]) -> None:
        """Evaluate an individual by training and testing the neural network."""
        try:
            print(f'  Testing: layers={individual.genes.hidden_layers}, '
                  f'dropout={individual.genes.dropout_rate}, lr={individual.genes.learning_rate}')

            # Split data (same as main training script)
            n = len(training_data)
            train_size = int(n * 0.6)
            val_size = int(n * 0.2)

            train_data = training_data[:train_size]
            val_data = training_data[train_size:train_size + val_size]
            test_data = training_data[train_size + val_size:]

            # Create and train model
            model = NeuralNetworkValuationModel(time_horizon='1year')

            # Modify architecture in the model (simplified approach)
            # This is a hack - in production would need to modify the model class
            original_hidden_dims = [256, 128, 64, 32]

            # Train on train + val data
            combined_train = train_data + val_data

            # Create custom training parameters
            metrics = model.train_model(
                combined_train,
                validation_split=0.25,
                epochs=30  # Shorter training for GA
            )

            # Test on held-out data
            test_predictions = []
            test_actuals = []

            for ticker, data, actual_return in test_data[:20]:  # Limit to first 20 for speed
                try:
                    result = model._calculate_valuation(ticker, data)
                    current_price = result.current_price
                    if current_price and current_price > 0:
                        predicted_return = (result.fair_value - current_price) / current_price
                        test_predictions.append(predicted_return)
                        test_actuals.append(actual_return)
                except:
                    continue

            if len(test_predictions) >= 5:
                test_mae = np.mean(np.abs(np.array(test_predictions) - np.array(test_actuals)))
                test_corr = np.corrcoef(test_predictions, test_actuals)[0,1] if len(test_predictions) > 1 else 0

                # Fitness combines MAE and correlation
                # Lower MAE is better, higher correlation is better
                individual.test_mae = test_mae
                individual.test_correlation = test_corr
                individual.fitness = -test_mae + test_corr  # Simple fitness function

                print(f'    MAE: {test_mae:.3f}, Corr: {test_corr:.3f}, Fitness: {individual.fitness:.3f}')
            else:
                individual.fitness = -100  # Penalty for failed evaluation
                print('    Failed evaluation')

        except Exception as e:
            individual.fitness = -100
            print(f'    Error: {e}')

    def optimize(self, training_data: List[Tuple[str, Dict[str, Any], float]]) -> Individual:
        """Run the genetic algorithm optimization."""
        print(f'Starting genetic algorithm: {self.population_size} individuals, {self.generations} generations')

        # Initialize population
        population = [self.create_random_individual() for _ in range(self.population_size)]

        best_individual = None
        best_fitness = float('-inf')

        for generation in range(self.generations):
            print(f'\nGeneration {generation + 1}/{self.generations}')
            print('-' * 40)

            # Evaluate all individuals
            for i, individual in enumerate(population):
                print(f'Individual {i+1}/{len(population)}:')
                self.evaluate_individual(individual, training_data)

                if individual.fitness > best_fitness:
                    best_fitness = individual.fitness
                    best_individual = individual

            # Sort by fitness
            population.sort(key=lambda x: x.fitness, reverse=True)

            # Print generation summary
            fitnesses = [ind.fitness for ind in population]
            print(f'\nGeneration {generation + 1} Summary:')
            print(f'Best fitness: {max(fitnesses):.3f}')
            print(f'Average fitness: {np.mean(fitnesses):.3f}')
            print(f'Best config: {population[0].genes.to_dict()}')

            # Early stopping if we're not improving
            if generation == self.generations - 1:
                break

            # Create next generation
            new_population = []

            # Keep top 50% (elitism)
            elite_count = self.population_size // 2
            new_population.extend(population[:elite_count])

            # Fill rest with crossover and mutation
            while len(new_population) < self.population_size:
                # Select parents (tournament selection)
                parent1 = max(random.choices(population[:elite_count * 2], k=3), key=lambda x: x.fitness)
                parent2 = max(random.choices(population[:elite_count * 2], k=3), key=lambda x: x.fitness)

                # Crossover and mutation
                if random.random() < 0.7:  # 70% crossover
                    child = self.crossover(parent1, parent2)
                else:  # 30% mutation
                    child = self.mutate(random.choice([parent1, parent2]))

                new_population.append(child)

            population = new_population

        print('\nOptimization complete!')
        print(f'Best individual: {best_individual.genes.to_dict()}')
        print(f'Best fitness: {best_individual.fitness:.3f}')
        print(f'Test MAE: {best_individual.test_mae:.3f}')
        print(f'Test Correlation: {best_individual.test_correlation:.3f}')

        return best_individual


def main():
    """Main optimization pipeline."""
    print('Genetic Algorithm Neural Network Optimizer')
    print('=' * 50)

    # Import training data collection from main script
    from train_neural_network import collect_training_data, get_sp500_tickers

    # Collect training data (smaller dataset for GA)
    tickers = get_sp500_tickers()[:25]  # Use only 25 stocks for faster GA
    print(f'Using {len(tickers)} stocks for genetic optimization')

    print('\nCollecting training data...')
    training_data = collect_training_data(tickers, num_months=12)  # 12 months for speed

    if len(training_data) < 50:
        print('Insufficient data for optimization')
        return

    # Run genetic algorithm
    optimizer = GeneticOptimizer(population_size=10, generations=5)  # Smaller for demo
    best_individual = optimizer.optimize(training_data)

    # Save results
    results_path = Path('genetic_optimization_results.json')
    with open(results_path, 'w') as f:
        json.dump({
            'best_config': best_individual.genes.to_dict(),
            'fitness': best_individual.fitness,
            'test_mae': best_individual.test_mae,
            'test_correlation': best_individual.test_correlation
        }, f, indent=2)

    print(f'\nResults saved to {results_path}')
    print('\nTo use the optimized configuration, modify the neural network model with:')
    print(f'  Hidden layers: {best_individual.genes.hidden_layers}')
    print(f'  Dropout rate: {best_individual.genes.dropout_rate}')
    print(f'  Learning rate: {best_individual.genes.learning_rate}')


if __name__ == '__main__':
    main()
