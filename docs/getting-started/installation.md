# Installation

## Prerequisites

- **Python 3.8+** - The framework requires Python 3.8 or later
- **Poetry** - For dependency management
- **Git** - For cloning the repository

## Installing Poetry

If you don't have Poetry installed:

=== "Linux/macOS/WSL"

    ```bash
    curl -sSL https://install.python-poetry.org | python3 -
    ```

=== "Windows PowerShell"

    ```powershell
    (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -
    ```

=== "Alternative (pip)"

    ```bash
    pip install poetry
    ```

!!! tip "Path Configuration"
    After installing Poetry, you may need to add it to your PATH. Follow the instructions shown in the installation output.

## Clone and Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/rubenayla/invest.git
   cd invest
   ```

2. **Install dependencies**:
   ```bash
   poetry install
   ```

3. **Verify installation**:
   ```bash
   poetry run python scripts/systematic_analysis.py --help
   ```

## Optional: Documentation Development

If you want to work on documentation:

```bash
# Install documentation dependencies
poetry install --with docs

# Start documentation server
poetry run mkdocs serve
```

## Verification

Test that everything works:

```bash
# Run a simple analysis
poetry run python scripts/systematic_analysis.py configs/test_tech_giants.yaml --save-csv

# Check if results were generated
ls *.csv
```

If you see a CSV file generated, you're ready to go!

## Troubleshooting

### Common Issues

**Poetry not found**
: Make sure Poetry is in your PATH. You may need to restart your terminal or add Poetry's bin directory to your PATH manually.

**Python version conflicts**
: The framework requires Python 3.8+. Check your version with `python --version` or `python3 --version`.

**Permission errors**
: On some systems, you may need to use `python3` instead of `python`, or run with appropriate permissions.

### Getting Help

If you encounter issues:

1. Check the [troubleshooting section](../user-guide/troubleshooting.md)
2. Review existing [GitHub issues](https://github.com/rubenayla/invest/issues)
3. Create a new issue with detailed error information

## Next Steps

- [Quick Start Guide](quickstart.md) - Run your first analysis
- [Configuration](configuration.md) - Customize screening criteria