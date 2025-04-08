Here’s the full `INSTALL.md` file content you can copy and save directly in your project root:

```markdown
# Install Instructions

This project uses Python 3.12 managed with `pyenv`, and is structured for editable installs using `setup.py`.

---

## 1. Install `pyenv` (if not already)

### On Unix/macOS:
```bash
git clone https://github.com/pyenv/pyenv.git ~/.pyenv

# Add to shell startup file
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init --path)"' >> ~/.bashrc

# Reload shell
exec "$SHELL"
```

> Use `.zshrc` instead of `.bashrc` if using Zsh.

---

## 2. Install Python 3.12.x via `pyenv`

```bash
pyenv install 3.12.2
```

> Make sure system build dependencies are installed:
> Ubuntu/Debian: `sudo apt install build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev`

---

## 3. Clone the Repo

```bash
git clone <REPO_URL> invest
cd invest
```

---

## 4. Set Local Python Version

```bash
pyenv local 3.12.2
```

This creates a `.python-version` file.

---

## 5. Create Virtual Environment

### Option A: Standard `venv`
```bash
python -m venv .venv
source .venv/bin/activate
```

### Option B: Using `uv` (recommended for speed)
```bash
uv venv .venv
source .venv/bin/activate
```

---

## 6. Install Project (Editable Mode)

```bash
pip install -e .
```

> Dependencies (`yfinance`, `pandas`, `numpy`) are specified in `setup.py`.

---

## 7. Run Example Script

```bash
python scripts/run_valuation.py
```

---

## 8. (Optional) Lint Code

```bash
uv pip install ruff
ruff check src/
```

---

## 9. (Optional) VS Code Configuration

Create `.vscode/settings.json`:
```json
{
  "python.pythonPath": ".venv/bin/python"
}
```
```

Let me know if you want this exported as a file or want a `.sh` script version for automation.