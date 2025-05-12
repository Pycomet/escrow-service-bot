# Escrow Bot Test Suite

This directory contains tests for the Escrow Bot application. The tests are organized into units that test individual components and integration tests that test the interactions between components.

## Test Structure

- `conftest.py` - Common fixtures and setup for all tests
- `test_config.py` - Test configuration override
- `test_trade.py` - Tests for trade functionality
- `test_handlers.py` - Tests for Telegram command handlers

## Running Tests

To run all tests:

```bash
pytest tests/
```

To run specific test files:

```bash
pytest tests/test_trade.py
pytest tests/test_handlers.py
```

To run with verbose output:

```bash
pytest -v tests/
```

To generate a coverage report:

```bash
pytest --cov=. tests/
```

## Writing Tests

When writing new tests, follow these guidelines:

1. Use fixtures from `conftest.py` where possible
2. Mock external dependencies (database, API calls)
3. Use descriptive test names that explain what is being tested
4. For async functions, use the `@pytest.mark.asyncio` decorator

## Creating a New Test File

To create a new test file:

1. Create a file named `test_<component>.py`
2. Import necessary modules and fixtures
3. Write test functions with the `test_` prefix

Example:

```python
import pytest
from unittest.mock import MagicMock, patch

def test_some_function():
    # Test code here
    assert True
``` 