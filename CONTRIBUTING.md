# Contributing to curam-cer-ontology-agent

Thank you for your interest in contributing!

## Reporting Bugs

Use [GitHub Issues](https://github.com/cloudbadal007/curam-cer-ontology-agent/issues) with:

- **Description**: Clear summary of the bug
- **Steps to reproduce**: Numbered list
- **Expected vs actual behavior**
- **Environment**: Python version, OS, ontology version

## Suggesting Features

Open an issue with:

- **Problem it solves**
- **Proposed solution**
- **Which program/rule type it affects**
- **Willing to contribute?** Yes/No

## Development Setup

```bash
git clone https://github.com/cloudbadal007/curam-cer-ontology-agent.git
cd curam-cer-ontology-agent
pip install -e ".[dev]"
cp .env.example .env
# Add OPENAI_API_KEY or ANTHROPIC_API_KEY if needed
```

## Running Tests Before Submitting a PR

```bash
pytest tests/ -v --cov=src
black --check src/ tests/
isort --check-only src/ tests/
mypy src/
```

## Code Style

- **Formatter**: Black (line length 88)
- **Import sorting**: isort (profile=black)
- **Type hints**: Required on all function signatures
- **Docstrings**: Module and public function docstrings expected

## Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `test:` Tests
- `refactor:` Code refactor

Example: `feat: add Medicaid state-specific thresholds`
