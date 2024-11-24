# Python Linting Setup Guide

## Common Python Linters

1. **Flake8**
   - Combines PyFlakes, pycodestyle (formerly pep8), and McCabe complexity checker
   - Enforces PEP 8 style guide
   - Checks for logical errors and complexity

2. **pylint**
   - More comprehensive but stricter linter
   - Checks for coding standards, error detection, and refactoring help
   - Highly configurable but can be overwhelming at first

3. **black**
   - Code formatter that enforces a consistent style
   - Non-configurable by design
   - Popular choice for automated formatting

4. **isort**
   - Specifically for sorting and formatting imports
   - Works well with black

## Local Setup

### 1. Installation
```bash
pip install flake8 pylint black isort
```

### 2. Configuration Files

**.flake8**
```ini
[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = .git,__pycache__,build,dist
per-file-ignores =
    __init__.py:F401
```

**pyproject.toml**
```toml
[tool.black]
line-length = 88
target-version = ['py37']
include = '\.pyi?$'
extend-exclude = '''
# A regex preceded with ^/ will apply only to files and directories
# in the root of the project.
^/foo.py  # exclude a file named foo.py in the root of the project
'''

[tool.isort]
profile = "black"
multi_line_output = 3
```

**.pylintrc**
```ini
[MASTER]
disable=
    C0114, # missing-module-docstring
    C0115, # missing-class-docstring
    C0116, # missing-function-docstring
    R0903, # too-few-public-methods
    C0103  # invalid-name

[FORMAT]
max-line-length=88
```

## GitHub Actions Setup

Create `.github/workflows/lint.yml`:

```yaml
name: Lint

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.x'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install flake8 pylint black isort
    
    - name: Check formatting with black
      run: black . --check
    
    - name: Sort imports with isort
      run: isort . --check-only --diff
    
    - name: Lint with flake8
      run: flake8 .
    
    - name: Lint with pylint
      run: pylint $(git ls-files '*.py')
```

## Pre-commit Setup (Optional)

1. Install pre-commit:
```bash
pip install pre-commit
```

2. Create `.pre-commit-config.yaml`:
```yaml
repos:
-   repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
    - id: black
      language_version: python3

-   repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
    - id: isort

-   repo: https://github.com/PyCQA/flake8
    rev: 7.0.0
    hooks:
    - id: flake8

-   repo: local
    hooks:
    - id: pylint
      name: pylint
      entry: pylint
      language: system
      types: [python]
```

3. Install the pre-commit hooks:
```bash
pre-commit install
```

## Usage Examples

### Command Line Usage

```bash
# Format code with black
black .

# Sort imports
isort .

# Run flake8
flake8 .

# Run pylint
pylint your_package_name

# Run all checks
black . && isort . && flake8 . && pylint your_package_name
```

### VS Code Integration

Add to your `.vscode/settings.json`:
```json
{
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    }
}
```
