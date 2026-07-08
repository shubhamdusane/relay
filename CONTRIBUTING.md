# Contributing to Relay

Welcome, and thank you for your interest in contributing to **Relay**! Every contribution helps shape the future of this project. Whether you're fixing a bug, proposing a feature, or improving documentation, your effort is valued.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How to Contribute](#how-to-contribute)
- [Development Setup](#development-setup)
- [Running Tests](#running-tests)
- [Code Style](#code-style)
- [Commit Messages](#commit-messages)
- [Pull Request Guidelines](#pull-request-guidelines)
- [Issue Templates](#issue-templates)
- [License & Contribution Terms](#license--contribution-terms)

---

## Code of Conduct

This project follows a strict Code of Conduct. By participating, you agree to uphold an inclusive, respectful, and harassment-free environment for everyone. Please read the [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before contributing.

---

## How to Contribute

### 1. Fork the Repository

```bash
# Navigate to the Relay repository on GitHub and click "Fork"
# Then clone your fork locally
git clone https://github.com/<your-username>/relay.git
cd relay
```

### 2. Create a Feature Branch

```bash
git checkout -b feat/your-feature-name
```

Branch naming conventions:

| Prefix | Purpose |
|--------|---------|
| `feat/` | New features |
| `fix/` | Bug fixes |
| `docs/` | Documentation changes |
| `refactor/` | Code refactoring |
| `test/` | Adding or updating tests |
| `chore/` | Maintenance and tooling |

### 3. Make Your Changes

- Write clean, maintainable code.
- Follow the project's code style (see below).
- Add tests for new functionality.
- Ensure all existing tests pass before submitting.

### 4. Commit Your Changes

```bash
git add .
git commit -m "feat: add new validation rule for input sanitization"
```

### 5. Push and Open a Pull Request

```bash
git push origin feat/your-feature-name
```

Then open a Pull Request on the main repository against the `main` branch.

---

## Development Setup

### Prerequisites

- Python 3.10 or higher
- pip or [uv](https://github.com/astral-sh/uv) (recommended)
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/relay.git
cd relay

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install in editable mode with dev dependencies
pip install -e ".[dev]"
```

This installs all runtime dependencies plus development tools including `pytest`, `ruff`, and type checkers.

---

## Running Tests

```bash
# Run the full test suite
pytest

# Run with verbose output
pytest -v

# Run a specific test file
pytest tests/test_core.py

# Run with coverage
pytest --cov=relay --cov-report=term-missing
```

All tests must pass before a Pull Request can be merged. Aim for clear, focused test cases that validate both expected behavior and edge cases.

---

## Code Style

This project enforces consistent formatting and linting using [Ruff](https://github.com/astral-sh/ruff).

### Formatting

```bash
# Auto-format all files
ruff format .

# Check formatting without modifying files
ruff format --check .
```

### Linting

```bash
# Run linter and auto-fix issues
ruff check --fix .

# Check without modifying files
ruff check .
```

### Guidelines

- Use type hints for all public functions and methods.
- Keep functions focused and under 50 lines where practical.
- Prefer explicit names over abbreviations.
- Follow PEP 8 conventions unless otherwise specified.
- Write docstrings for all public APIs (Google or NumPy style).

---

## Commit Messages

This project follows [Conventional Commits](https://www.conventionalcommits.org/). Every commit message must be structured as follows:

```
<type>(<scope>): <description>
```

### Types

| Type | Description |
|------|-------------|
| `feat` | A new feature |
| `fix` | A bug fix |
| `docs` | Documentation only changes |
| `style` | Code style changes (formatting, no logic change) |
| `refactor` | Code refactoring without behavior change |
| `test` | Adding or updating tests |
| `chore` | Maintenance tasks, CI/CD, tooling |
| `perf` | Performance improvements |
| `build` | Changes to build system or dependencies |

### Examples

```
feat(auth): add OAuth2 token refresh mechanism
fix(cache): resolve race condition in concurrent eviction
docs: update installation guide for Windows users
test(core): add edge case tests for input validation
```

### Rules

- Use the imperative mood ("add" not "added" or "adds").
- Keep the subject line under 72 characters.
- Use the body to explain *what* and *why*, not *how*.
- Reference issues in the body: `Closes #42`.

---

## Pull Request Guidelines

### Before Submitting

1. Ensure your branch is up to date with `main`.
2. Run the full test suite and verify all tests pass.
3. Run `ruff format` and `ruff check` with no errors.
4. Review your own PR as if you were a reviewer.

### PR Description

Use the provided PR template. Include:

- **Summary**: A concise description of what changed.
- **Motivation**: Why the change is needed.
- **Testing**: How the change was tested.
- **Screenshots**: If applicable, for UI changes.
- **Related Issues**: Link to related issues using `Closes #`, `Fixes #`, or `Relates to #`.

### Review Process

- All PRs require at least one approval before merging.
- Maintainers may request changes or ask clarifying questions.
- Address all feedback, then re-request review.
- Keep the PR focused — one logical change per PR.

### Merging

- PRs are squash-merged to maintain a clean commit history.
- The PR title becomes the commit message — ensure it follows Conventional Commits.

---

## Issue Templates

When opening a new issue, please use one of the provided templates:

### Bug Report

```markdown
**Describe the bug**
A clear and concise description of the bug.

**To reproduce**
Steps to reproduce the behavior.

**Expected behavior**
What you expected to happen.

**Environment**
- OS: [e.g., Windows 11, macOS 14, Ubuntu 22.04]
- Python version: [e.g., 3.11.4]
- Relay version: [e.g., 0.1.0]

**Additional context**
Any other context, screenshots, or logs.
```

### Feature Request

```markdown
**Is your feature request related to a problem?**
A clear description of the problem. Ex. "I'm frustrated when..."

**Describe the solution you'd like**
A clear description of what you want to happen.

**Describe alternatives you've considered**
Any alternative solutions or features you've thought about.

**Additional context**
Any other context or screenshots.
```

### Documentation

```markdown
**What documentation is affected?**
File path or section.

**What improvement would you suggest?**
Describe the change you'd like to see.
```

---

## License & Contribution Terms

By contributing to Relay, you agree that your contributions will be licensed under the same license as the project — [MIT License](LICENSE) (or the applicable license for this repository).

You retain copyright ownership of your contributions. By submitting a Pull Request, you grant the project maintainers a perpetual, irrevocable, worldwide, royalty-free license to use, modify, and redistribute your contributions.

---

## Questions?

If you have questions about contributing, feel free to:

1. Open a [Discussion](https://github.com/your-org/relay/discussions) on GitHub.
2. Reach out to the maintainers.
3. Review existing issues and PRs for context.

Thank you for helping make **Relay** better. We look forward to your contribution!
