# Claude Memory and Instructions

## CRITICAL REMINDER: Always Use Poetry

⚠️ **IMPORTANT**: This project uses Poetry dependency management. ALL Python commands must be prefixed with `poetry run`.

```bash
# Wrong:
python scripts/systematic_analysis.py
pytest

# Correct:
poetry run python scripts/systematic_analysis.py
poetry run pytest
```

## CRITICAL LESSON: The ab0fe64 Disaster

⚠️ **What happened**: Previous Claude instance attempted "comprehensive code quality improvements" and:
- Added 6,000 lines across 24 files in a single commit
- Introduced massive syntax errors and undefined variables
- Broke the entire test suite with orphaned try/except blocks
- Created architectural changes when only bug fixes were needed

## IRON RULES - Never Break These:

1. **ONE ISSUE = ONE SMALL FIX** - Fix syntax errors one file at a time, not 24 files at once
2. **NEVER commit more than 50-100 lines** - Large commits = guaranteed breakage
3. **Test after EVERY change** - If tests fail, stop and fix before continuing
4. **NO architectural changes for bug fixes** - Syntax errors don't need refactoring

## NEVER Do These:
- ❌ **NEVER** attempt "comprehensive refactoring" - this ALWAYS breaks code
- ❌ **NEVER** change more than one file for syntax fixes
- ❌ **NEVER** add new features while fixing bugs  
- ❌ **NEVER** create "modular components" when fixing syntax errors
- ❌ **NEVER** make commits with "23 major tasks completed"

## Emergency Stop Conditions:
If you find yourself doing ANY of these, STOP IMMEDIATELY:
- Creating new directories/files while fixing bugs
- Refactoring code architecture
- Adding more than 100 lines in a single change
- Working on multiple files simultaneously for "efficiency"

## COMMIT DISCIPLINE - Mandatory Rules

### Before Every Commit:
1. **Run the linter**: `poetry run ruff check src tests --select=E9,F63,F7,F82`
2. **Check for syntax errors**: Must pass with zero errors
3. **Run tests**: `poetry run pytest` (at minimum, run relevant tests)
4. **Verify changes are minimal**: `git diff --stat` should show reasonable line counts

### Good Commit Examples:
```
Fix syntax error in monte_carlo_dcf.py line 175
- Remove orphaned except block
- Fix indentation issue

Files changed: 1, +2/-5 lines
```

### BAD Commit Examples (NEVER DO):
```
Complete comprehensive code quality improvements and system refactoring
- 23 major tasks completed
- New caching system, modular dashboard, unified interfaces

Files changed: 24, +5983/-13 lines  ← THIS IS A DISASTER
```

### Commit Size Limits:
- **Bug fixes**: 1 file, <50 lines changed
- **Feature additions**: 1-3 files, <200 lines changed  
- **Refactoring**: ONLY when specifically requested, 1 file at a time

## Remember: The user values WORKING CODE above all else. Broken code helps nobody.

## Current Status: Test Suite Partially Broken

⚠️ **Known Issue**: The ab0fe64 disaster commit broke many integration tests by:
- Adding 6 new valuation models without updating test expectations
- Creating complex new components that tests don't account for
- Changing internal APIs that tests relied on

### Fixed Tests:
- ✅ `test_model_registry_initialization` - Updated to expect 11 models instead of 5

### Still Failing Tests (don't fix all at once - violates our rules):
- Integration tests expecting old model counts
- Performance tests referencing removed/changed components
- Valuation tests with outdated assumptions

### Approach for Test Fixes:
1. **Only fix tests when they block real work** - don't fix all tests at once
2. **One test at a time** - separate commits for each test fix  
3. **Document what was changed and why** - help future debugging

---

📋 **For project-specific details, see PROJECT.md**