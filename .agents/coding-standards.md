<!-- read in full — kept under 150 lines -->
# Coding Standards

- Single quotes: `'hello'`
- Type hints always
- Numpydoc docstrings
- Guard clauses (early returns)
- Use `@pytest.mark.parametrize` for test variations

## Testing Strategy

**When to run tests locally:**
- Logic changes in core modules: `uv run pytest`
- Testing-specific changes: `uv run pytest tests/test_file.py`
- Major refactoring: `uv run pytest`
- Skip tests for: docs, configs, small UI tweaks (let CI handle it)

**After pushing:**
- Check CI status: `gh run list --limit 1`
- If CI fails: `gh run view --log-failed` to see details

**Commit discipline:**
- Keep commits small: <100 lines changed
- One issue per commit
- Never refactor multiple files at once
