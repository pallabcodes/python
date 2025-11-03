# Conventional Commits

## MANDATORY: All commits MUST follow Conventional Commits specification

### Commit Message Format

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Commit Types

#### Required Types
- **feat**: A new feature
- **fix**: A bug fix
- **docs**: Documentation only changes
- **style**: Changes that do not affect the meaning of the code (white-space, formatting, missing semi-colons, etc.)
- **refactor**: A code change that neither fixes a bug nor adds a feature
- **perf**: A code change that improves performance
- **test**: Adding missing tests or correcting existing tests
- **build**: Changes that affect the build system or external dependencies
- **ci**: Changes to CI configuration files and scripts
- **chore**: Other changes that don't modify src or test files
- **revert**: Reverts a previous commit

### Examples

#### Feature Commit
```bash
feat(threading): add thread pool implementation

Add ThreadPool class with support for task submission and
result retrieval. Includes proper resource management and
error handling.

Closes #123
```

#### Bug Fix Commit
```bash
fix(multiprocessing): resolve deadlock in process pool

Fix deadlock issue that occurred when all worker processes
were busy and new tasks were submitted. Added timeout
mechanism for task submission.

Fixes #456
```

#### Documentation Commit
```bash
docs(readme): update installation instructions

Update README with new dependency installation steps and
virtual environment setup instructions.
```

#### Refactoring Commit
```bash
refactor(asyncio): extract event loop management

Extract event loop creation and management into separate
EventLoopManager class to improve code organization and
testability.
```

#### Performance Commit
```bash
perf(threading): optimize thread pool task distribution

Optimize task distribution algorithm to reduce contention
and improve throughput by 30%.

Closes #789
```

### Commit Message Guidelines

#### Description
- **Required**: Must be present
- **Format**: Imperative mood ("add" not "added" or "adds")
- **Length**: 50 characters or less
- **Capitalization**: First letter lowercase (unless starts with proper noun)
- **Punctuation**: No period at the end

#### Body
- **Optional**: Use for detailed explanation
- **Format**: Wrap at 72 characters
- **Content**: Explain what and why, not how
- **Separate**: Blank line between description and body

#### Footer
- **Optional**: Reference issues, breaking changes
- **Format**: `Closes #123`, `Fixes #456`, `BREAKING CHANGE: ...`
- **Breaking Changes**: Must include `BREAKING CHANGE:` in footer

### Scope

#### Scope Format
- **Optional**: Use parentheses after type
- **Format**: `type(scope): description`
- **Examples**: `feat(threading):`, `fix(asyncio):`, `docs(readme):`

#### Common Scopes
- `threading`: Thread-related changes
- `multiprocessing`: Process-related changes
- `asyncio`: Async-related changes
- `gil`: GIL-related changes
- `sync`: Synchronization-related changes
- `examples`: Example code changes
- `exercises`: Exercise code changes
- `tests`: Test-related changes
- `docs`: Documentation changes
- `ci`: CI/CD changes
- `build`: Build system changes

### Breaking Changes

#### Breaking Change Format
```
feat(api): change thread pool interface

BREAKING CHANGE: ThreadPool.submit() now returns Future
instead of Result. Use Future.result() to get the result.
```

#### Breaking Change in Footer
```
feat(api): change thread pool interface

BREAKING CHANGE: ThreadPool.submit() now returns Future
instead of Result. Use Future.result() to get the result.

Closes #123
```

### Commit Message Examples

#### Good Examples
```bash
# Simple feature
feat(threading): add thread pool class

# Feature with scope and body
feat(multiprocessing): add process pool executor

Add ProcessPoolExecutor class with support for concurrent
task execution across multiple processes.

# Bug fix
fix(asyncio): resolve event loop cleanup issue

Fix event loop not being properly closed when exceptions
occur during task execution.

# Documentation
docs(readme): add installation instructions

# Style
style(black): format code with black

# Refactoring
refactor(threading): extract thread management logic

Extract thread creation and management into separate
ThreadManager class.

# Performance
perf(threading): optimize lock contention

Reduce lock contention by using read-write locks for
read-heavy operations.

# Test
test(threading): add thread pool unit tests

Add comprehensive unit tests for ThreadPool class covering
all public methods and error cases.

# Breaking change
feat(api): change executor interface

BREAKING CHANGE: Executor.submit() signature changed.
Old code must be updated to use new signature.

Closes #123
```

#### Bad Examples
```bash
# ❌ Too vague
fix: fix bug

# ❌ Wrong format
Added thread pool
Fixed deadlock
Updates documentation

# ❌ Too long description
feat(threading): add thread pool implementation with support for task submission and result retrieval

# ❌ No type
thread pool implementation

# ❌ Wrong capitalization
feat(threading): Add thread pool

# ❌ Period at end
feat(threading): add thread pool.
```

### Commit Best Practices

#### Do's
- ✅ Use imperative mood
- ✅ Keep description under 50 characters
- ✅ Use body for detailed explanation
- ✅ Reference issues in footer
- ✅ Use appropriate type
- ✅ Include scope when relevant

#### Don'ts
- ❌ Don't use past tense
- ❌ Don't exceed 50 characters in description
- ❌ Don't forget the colon after type
- ❌ Don't use periods at end of description
- ❌ Don't mix multiple concerns in one commit
- ❌ Don't use vague descriptions

### Commit Message Template

```
<type>(<scope>): <short description>

<optional detailed explanation>

<optional footer with issue references>
```

### Automated Validation

#### Pre-commit Hook
The project includes a pre-commit hook that validates commit messages against Conventional Commits format.

#### Manual Validation
```bash
# Validate commit message
git commit -m "feat(threading): add thread pool"

# Check last commit message
git log -1 --pretty=%B
```

### References

- [Conventional Commits Specification](https://www.conventionalcommits.org/)
- [Angular Commit Message Guidelines](https://github.com/angular/angular/blob/main/CONTRIBUTING.md#commit)

