# Pre-commit Setup Guide

This guide covers the pre-commit configuration and usage for the FastAPI MVC project.

## Overview

Pre-commit is a framework for managing and maintaining multi-language pre-commit hooks. It ensures code quality and consistency by running various checks before each commit.

## Installed Hooks

### General Hooks
- **trailing-whitespace**: Removes trailing whitespace
- **end-of-file-fixer**: Ensures files end with newline
- **check-yaml**: Validates YAML syntax
- **check-json**: Validates JSON syntax
- **check-toml**: Validates TOML syntax
- **check-merge-conflict**: Detects merge conflict markers
- **check-added-large-files**: Prevents large files from being committed
- **check-case-conflict**: Detects case conflicts in filenames
- **check-docstring-first**: Ensures docstrings appear before code
- **debug-statements**: Detects debugger imports and breakpoints
- **name-tests-test**: Validates test file naming conventions

### Python Code Quality
- **black**: Code formatting with Black (line length: 88)
- **isort**: Import sorting with isort (Black-compatible profile)
- **flake8**: Linting with Flake8 (extended ignore for Black compatibility)
- **mypy**: Type checking with MyPy (ignores missing imports)

### Security
- **bandit**: Security linting for Python code
- **safety**: Dependency vulnerability checking

### Docker
- **hadolint**: Dockerfile linting

## Configuration Files

### `.pre-commit-config.yaml`
Main configuration file defining all hooks and their settings.

### `pyproject.toml` Tool Configurations
- **Black**: Code formatting settings
- **isort**: Import sorting settings
- **MyPy**: Type checking settings
- **Bandit**: Security linting settings
- **Pytest**: Test configuration

## Usage

### Initial Setup
```bash
# Install pre-commit hooks
poetry run pre-commit install

# Install pre-commit hooks for all environments
poetry run pre-commit install --install-hooks
```

### Running Hooks

#### On All Files
```bash
# Run all hooks on all files
poetry run pre-commit run --all-files

# Run specific hook on all files
poetry run pre-commit run black --all-files
```

#### On Specific Files
```bash
# Run all hooks on specific files
poetry run pre-commit run --files app/config/settings.py

# Run specific hook on specific files
poetry run pre-commit run black --files app/config/settings.py
```

#### On Staged Files (Default)
```bash
# Run hooks on staged files (happens automatically on commit)
poetry run pre-commit run
```

### Updating Hooks
```bash
# Update all hooks to latest versions
poetry run pre-commit autoupdate

# Update specific hook
poetry run pre-commit autoupdate --repo https://github.com/psf/black
```

## Hook Details

### Black (Code Formatting)
- **Purpose**: Consistent Python code formatting
- **Line Length**: 88 characters
- **Target Versions**: Python 3.9+
- **Configuration**: `pyproject.toml` under `[tool.black]`

### isort (Import Sorting)
- **Purpose**: Consistent import organization
- **Profile**: Black-compatible
- **Line Length**: 88 characters
- **Configuration**: `pyproject.toml` under `[tool.isort]`

### Flake8 (Linting)
- **Purpose**: Code style and error detection
- **Line Length**: 88 characters
- **Ignores**: E203, W503 (Black compatibility)
- **Configuration**: Command line arguments

### MyPy (Type Checking)
- **Purpose**: Static type checking
- **Settings**: Ignores missing imports, no strict optional
- **Configuration**: `pyproject.toml` under `[tool.mypy]`

### Bandit (Security)
- **Purpose**: Security vulnerability detection
- **Excludes**: Tests and migrations directories
- **Skips**: B101 (assert_used), B601 (shell_injection)
- **Configuration**: `pyproject.toml` under `[tool.bandit]`

## Workflow Integration

### Git Hooks
Pre-commit automatically installs Git hooks that run before each commit:
- Hooks run on staged files only
- Failed hooks prevent commit
- Fixed files are automatically staged

### CI/CD Integration
Pre-commit can be integrated into CI/CD pipelines:
```yaml
# GitHub Actions example
- name: Run pre-commit
  uses: pre-commit/action@v3.0.0
```

### IDE Integration
Many IDEs support pre-commit:
- **VS Code**: Pre-commit extension
- **PyCharm**: Built-in support
- **Vim/Neovim**: Various plugins available

## Troubleshooting

### Common Issues

#### Hook Failures
```bash
# Skip hooks for a specific commit
git commit --no-verify -m "Emergency fix"

# Run hooks manually to see detailed output
poetry run pre-commit run --verbose
```

#### Performance Issues
```bash
# Run hooks in parallel (faster)
poetry run pre-commit run --all-files --jobs 4

# Skip slow hooks during development
poetry run pre-commit run --hook-stage manual
```

#### Dependency Issues
```bash
# Clean pre-commit cache
poetry run pre-commit clean

# Reinstall hooks
poetry run pre-commit install --install-hooks
```

### Debugging
```bash
# Verbose output
poetry run pre-commit run --verbose

# Debug mode
poetry run pre-commit run --debug

# Check hook configuration
poetry run pre-commit run --help
```

## Best Practices

### Development Workflow
1. **Install hooks** after cloning repository
2. **Run hooks** before committing
3. **Fix issues** automatically when possible
4. **Review changes** before committing fixes

### Team Collaboration
1. **Consistent configuration** across team
2. **Regular updates** of hook versions
3. **Documentation** of custom hooks
4. **CI/CD integration** for enforcement

### Performance Optimization
1. **Selective hooks** for different file types
2. **Parallel execution** when possible
3. **Caching** for repeated runs
4. **Skip hooks** for emergency commits

## Customization

### Adding New Hooks
Edit `.pre-commit-config.yaml`:
```yaml
repos:
  - repo: https://github.com/example/hook-repo
    rev: v1.0.0
    hooks:
      - id: custom-hook
        args: ['--custom-arg']
```

### Modifying Existing Hooks
```yaml
- id: black
  args: ['--line-length=100']  # Override default
```

### Excluding Files
```yaml
- id: black
  exclude: '^migrations/.*\.py$'  # Skip migration files
```

## Maintenance

### Regular Tasks
1. **Update hooks** monthly
2. **Review configurations** quarterly
3. **Test new hooks** before adding
4. **Monitor performance** impact

### Version Management
- Pin hook versions for stability
- Test updates in development
- Document breaking changes
- Maintain compatibility matrix

This pre-commit setup ensures consistent code quality and helps maintain high standards across the FastAPI MVC project.
