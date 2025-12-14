# Version Control Guide

## Overview

This document explains how to manage different versions of the NAMO platform. We use **Git** for version control and semantic versioning (v0.1.0, v0.2.0, etc.) for releases.

## Current Version: v0.1.0

**Release Date:** December 2024  
**Status:** Initial release

### Features in v0.1.0:
- ✅ Basic dashboard with Overview, Country Analysis, and Topic Analysis pages
- ✅ Data quality filtering using `clean_articles` view
- ✅ Enhanced metrics: data freshness, articles per outlet, growth rate
- ✅ Outlet concentration analysis
- ✅ Comparative metrics across countries
- ✅ Multi-country time series comparisons
- ✅ Category, sentiment, and entity analysis

---

## Version Management

### Creating a New Version

When you want to save the current state and start working on new features:

```bash
# 1. Commit current changes
git add .
git commit -m "Release v0.1.0 - Initial dashboard with enhanced metrics"

# 2. Create a version tag
git tag -a v0.1.0 -m "Version 0.1.0 - Initial release"

# 3. Create a branch for the new version
git checkout -b v0.2.0-dev

# 4. Update version numbers in code
# - backend/app/config.py: API_VERSION = "0.2.0"
# - frontend/app.py: DASHBOARD_VERSION = "0.2.0"
```

### Switching Between Versions

```bash
# View all versions
git tag

# Switch to a specific version
git checkout v0.1.0

# Switch to latest development
git checkout main  # or master

# Switch to a development branch
git checkout v0.2.0-dev
```

### Viewing Version History

```bash
# See all commits
git log --oneline

# See changes in a version
git show v0.1.0

# Compare versions
git diff v0.1.0 v0.2.0
```

---

## Version Numbering

We follow **Semantic Versioning** (SemVer):

- **MAJOR** (1.0.0): Breaking changes, major rewrites
- **MINOR** (0.2.0): New features, backward compatible
- **PATCH** (0.1.1): Bug fixes, small improvements

### Examples:
- `v0.1.0` → `v0.1.1`: Fixed a bug
- `v0.1.0` → `v0.2.0`: Added new analytics features
- `v0.2.0` → `v1.0.0`: Major rewrite or production release

---

## Version Locations in Code

### Backend Version
**File:** `backend/app/config.py`
```python
API_VERSION: str = "0.1.0"
```

### Frontend Version
**File:** `frontend/app.py`
```python
DASHBOARD_VERSION = "0.1.0"
```

### Update Both When Creating New Version!

---

## Workflow Example

### Scenario: Adding new features to v0.2.0

```bash
# 1. Make sure you're on main branch with latest changes
git checkout main
git pull

# 2. Create a development branch
git checkout -b v0.2.0-dev

# 3. Update version numbers
# Edit backend/app/config.py: API_VERSION = "0.2.0"
# Edit frontend/app.py: DASHBOARD_VERSION = "0.2.0"

# 4. Make your changes
# ... implement new features ...

# 5. Test thoroughly
# ... run tests, check dashboard ...

# 6. Commit changes
git add .
git commit -m "Add feature X and Y for v0.2.0"

# 7. When ready, merge to main and tag
git checkout main
git merge v0.2.0-dev
git tag -a v0.2.0 -m "Version 0.2.0 - Added features X and Y"
```

---

## Quick Reference Commands

```bash
# Initialize git (if not already done)
git init

# Check current status
git status

# See current version
git describe --tags

# Create a backup branch
git branch backup-$(date +%Y%m%d)

# List all branches
git branch -a

# List all tags (versions)
git tag -l
```

---

## Best Practices

1. **Always commit before switching versions** - Don't lose work!
2. **Tag releases** - Makes it easy to go back
3. **Use descriptive commit messages** - "Fixed bug" is not helpful
4. **Test before tagging** - Make sure the version works
5. **Update version numbers** - Both backend and frontend
6. **Document changes** - Update CHANGELOG.md (if you create one)

---

## Troubleshooting

### "I lost my changes!"
```bash
# Check recent commits
git log --oneline -10

# See what changed
git diff

# Recover from stash
git stash list
git stash pop
```

### "I want to go back to v0.1.0"
```bash
git checkout v0.1.0
# Note: This puts you in "detached HEAD" state
# Create a branch if you want to make changes:
git checkout -b restore-v0.1.0
```

### "How do I see what changed between versions?"
```bash
git diff v0.1.0 v0.2.0
```

---

## Next Steps

1. ✅ Git repository initialized
2. ✅ Version 0.1.0 tagged (when you're ready)
3. 🔄 Create v0.2.0 branch for new features
4. 📝 Document changes in this file

---

**Remember:** Version control is your safety net. Use it liberally!
