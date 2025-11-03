# Contributing Guide

## Development Setup

### 1. Install Dependencies

```bash
cd project
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Install Pre-commit Hooks

```bash
pre-commit install
```

This will install hooks that run automatically on commit:
- Code formatting (black, isort)
- Linting (flake8, pylint)
- Type checking (mypy)
- File size checks
- Function size checks

### 3. Run Pre-commit Manually

```bash
# Run on all files
pre-commit run --all-files

# Run on staged files only
pre-commit run
```

## Code Quality Tools

### Formatting

#### Black
```bash
# Format all files
black .

# Check formatting without making changes
black --check .

# Format specific file
black path/to/file.py
```

#### isort
```bash
# Sort imports
isort .

# Check import sorting
isort --check-only .
```

### Linting

#### Flake8
```bash
# Lint all files
flake8 .

# Lint specific file
flake8 path/to/file.py
```

#### Pylint
```bash
# Lint all files
pylint project/

# Lint specific file
pylint path/to/file.py
```

### Type Checking

#### mypy
```bash
# Type check all files
mypy .

# Type check specific file
mypy path/to/file.py
```

## Commit Messages

### Conventional Commits

All commits MUST follow the [Conventional Commits](https://www.conventionalcommits.org/) specification.

#### Format
```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

#### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Test changes
- `build`: Build system changes
- `ci`: CI/CD changes
- `chore`: Other changes

#### Examples
```bash
feat(threading): add thread pool implementation
fix(multiprocessing): resolve deadlock in process pool
docs(readme): update installation instructions
refactor(asyncio): extract event loop management
```

### Git Commit Template

Set up the commit message template:

```bash
git config commit.template .gitmessage
```

## Code Standards

### File Size Limits
- **Maximum file size**: 200 lines
- **Maximum function size**: 50 lines
- **Maximum class size**: 200 lines

### Code Style
- Follow PEP 8 (with line length 100)
- Use type hints for all functions
- Use Google-style docstrings
- Follow OOP principles strictly

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=project --cov-report=html

# Run specific test file
pytest tests/test_threading.py

# Run specific test
pytest tests/test_threading.py::TestThreadPool::test_submit_task
```

## Workflow

1. **Create a branch**
   ```bash
   git checkout -b feat/your-feature-name
   ```

2. **Make changes**
   - Follow code standards
   - Write tests
   - Update documentation

3. **Run checks**
   ```bash
   # Format code
   black .
   isort .
   
   # Lint code
   flake8 .
   pylint project/
   
   # Type check
   mypy .
   
   # Run tests
   pytest
   ```

4. **Commit changes**
   ```bash
   git add .
   git commit -m "feat(scope): your commit message"
   ```

5. **Push and create PR**
   ```bash
   git push origin feat/your-feature-name
   ```

## Pre-commit Hooks

Pre-commit hooks automatically run on commit:
- Code formatting
- Linting
- Type checking
- File size validation
- Function size validation

If hooks fail, fix the issues and commit again.

## Code Review Checklist

Before submitting code:
- [ ] Code follows OOP principles
- [ ] File size is under 200 lines
- [ ] All functions are under 50 lines
- [ ] Type hints are present for all functions
- [ ] Docstrings are complete
- [ ] Tests are written and passing
- [ ] Code is formatted (black, isort)
- [ ] Linting passes (flake8, pylint)
- [ ] Type checking passes (mypy)
- [ ] Commit message follows Conventional Commits

