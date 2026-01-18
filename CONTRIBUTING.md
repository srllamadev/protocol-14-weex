# Contributing to Protocol-14 WEEX Trading Bot

Thank you for your interest in contributing to this project! This document provides guidelines and information for contributors.

## 🚀 Getting Started

### Prerequisites

- Python 3.12 or higher
- Git
- WEEX API credentials (for testing)

### Development Setup

1. **Fork the repository**

```bash
git fork https://github.com/protocol-14-weex/protocol-14-weex.git
```

2. **Clone your fork**

```bash
git clone https://github.com/YOUR_USERNAME/protocol-14-weex.git
cd protocol-14-weex
```

3. **Create a virtual environment**

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows
```

4. **Install dependencies**

```bash
pip install -r requirements.txt
```

5. **Configure environment**

```bash
cp .env.example .env
# Edit .env with your credentials
```

## 📝 Code Style

### Python Style Guide

- Follow [PEP 8](https://pep8.org/) conventions
- Use type hints for function parameters and return values
- Write docstrings for all public functions and classes
- Maximum line length: 100 characters

### Example

```python
def calculate_rsi(prices: List[float], period: int = 14) -> IndicatorSignal:
    """
    Calculate Relative Strength Index (RSI)
    
    Args:
        prices: List of closing prices
        period: RSI calculation period (default: 14)
        
    Returns:
        IndicatorSignal with RSI value and trading signal
    """
    # Implementation here
    pass
```

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Classes | PascalCase | `GridTradingStrategy` |
| Functions | snake_case | `calculate_rsi()` |
| Variables | snake_case | `current_price` |
| Constants | UPPER_SNAKE | `MAX_LEVERAGE` |
| Private | _prefix | `_generate_signature()` |

## 🔀 Branching Strategy

- `main` - Production-ready code
- `develop` - Integration branch for features
- `feature/*` - New features
- `bugfix/*` - Bug fixes
- `hotfix/*` - Urgent production fixes

### Creating a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

## 📋 Pull Request Process

1. **Update your branch**

```bash
git fetch origin
git rebase origin/main
```

2. **Test your changes**

```bash
python -m pytest tests/
python check_ip.py  # Verify API works
```

3. **Write a clear PR description**

Include:
- What changes were made
- Why the changes were needed
- How to test the changes
- Screenshots (if applicable)

4. **Request review**

Assign at least one reviewer before merging.

## 🧪 Testing

### Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/api_test.py

# Run with coverage
python -m pytest --cov=. tests/
```

### Writing Tests

- Place tests in the `tests/` directory
- Name test files with `test_` prefix
- Use descriptive test function names

```python
def test_rsi_overbought_signal():
    """Test that RSI > 70 generates sell signal"""
    # Test implementation
    pass
```

## 📁 Project Structure

When adding new files, follow this structure:

```
protocol-14-weex/
├── strategies/          # Trading strategies
│   └── new_strategy.py  # Your new strategy
├── utils/               # Utility modules
│   └── new_util.py      # Your new utility
├── tests/               # Test files
│   └── test_new.py      # Tests for new code
└── docs/                # Documentation
    └── new_feature.md   # Feature documentation
```

## 🔐 Security

### Credentials

- **NEVER** commit API keys or secrets
- Use `.env` files for local development
- Add sensitive files to `.gitignore`

### Reporting Vulnerabilities

If you discover a security vulnerability, please:

1. **Do NOT** open a public issue
2. Email the maintainers directly
3. Include detailed steps to reproduce

## 📝 Documentation

### What to Document

- New strategies or features
- API changes
- Configuration options
- Breaking changes

### Documentation Style

- Use Markdown format
- Include code examples
- Add diagrams when helpful
- Keep language clear and concise

## 🐛 Bug Reports

When reporting bugs, include:

1. **Environment**
   - Python version
   - Operating system
   - Dependencies version

2. **Steps to Reproduce**
   - Clear, numbered steps
   - Include code if applicable

3. **Expected vs Actual Behavior**
   - What you expected to happen
   - What actually happened

4. **Logs/Screenshots**
   - Error messages
   - Relevant log output

## 💡 Feature Requests

When suggesting features:

1. **Problem Statement** - What problem does this solve?
2. **Proposed Solution** - How would it work?
3. **Alternatives** - Other approaches considered
4. **Impact** - Who would benefit?

## 📜 Code of Conduct

### Our Standards

- Be respectful and inclusive
- Accept constructive criticism
- Focus on what's best for the community
- Show empathy towards others

### Unacceptable Behavior

- Harassment or discrimination
- Trolling or insulting comments
- Publishing private information
- Unprofessional conduct

## 🙏 Recognition

Contributors will be:

- Listed in the README
- Credited in release notes
- Mentioned in documentation

## 📞 Contact

- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Email**: protocol14team@example.com

---

Thank you for contributing to Protocol-14! 🎉
