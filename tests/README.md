# Raycast Focus Tracker Tests

This directory contains comprehensive tests for the Raycast Focus Tracker application, including unit tests, integration tests, and end-to-end tests.

## Test Structure

```
tests/
├── unit/                   # Unit tests for individual modules
│   ├── test_data_access.py      # Tests for data_access.py
│   ├── test_log_to_json.py      # Tests for log_to_json.py
│   └── test_streak_calculation.py # Tests for streak_calculation.py
├── integration/            # Integration tests for component interactions
│   └── test_menubar.py           # Tests for menuBar.py integration
├── e2e/                    # End-to-end workflow tests
│   └── test_complete_workflow.py # Complete system workflow tests
├── fixtures/               # Test data and fixtures
│   └── sample_logs.txt           # Sample log file for testing
├── conftest.py            # Pytest configuration and fixtures
├── run_tests.py           # Test runner script
└── README.md              # This file
```

## Running Tests

### Prerequisites

Install test dependencies:
```bash
pip install pytest pytest-cov
```

Or use the built-in installer:
```bash
python tests/run_tests.py --install-deps
```

### Basic Usage

Run all tests:
```bash
python tests/run_tests.py
```

Run specific test categories:
```bash
python tests/run_tests.py unit        # Unit tests only
python tests/run_tests.py integration # Integration tests only
python tests/run_tests.py e2e         # End-to-end tests only
```

### Advanced Options

Run with coverage reporting:
```bash
python tests/run_tests.py --coverage
```

Run in quiet mode:
```bash
python tests/run_tests.py --quiet
```

Run using pytest directly:
```bash
pytest tests/                    # All tests
pytest tests/unit/              # Unit tests only
pytest -v tests/                # Verbose output
pytest --cov=raycast_focus_tracker tests/  # With coverage
```

## Test Categories

### Unit Tests

Test individual functions and classes in isolation:

- **test_data_access.py**: Tests for data access functions
  - `get_today_minutes()`
  - `get_today_by_goal()`
  - `get_current_streak()`, `get_longest_streak()`
  - Error handling and edge cases
  - Multi-directory data access

- **test_log_to_json.py**: Tests for log parsing functionality
  - Log line parsing and timestamp extraction
  - Session start/end handling
  - Activity summary processing
  - Duration calculation
  - Data aggregation and totals
  - Error recovery

- **test_streak_calculation.py**: Tests for streak calculation logic
  - Current streak calculation
  - Longest streak tracking
  - Streak breaking scenarios
  - Data loading/saving
  - Edge cases and performance

### Integration Tests

Test component interactions and data flow:

- **test_menubar.py**: Tests for menu bar application integration
  - FocusApp initialization
  - Menu building with real data
  - Data refresh mechanisms
  - Log parsing integration
  - Heatmap generation
  - Auto-refresh functionality
  - Multi-directory data handling

### End-to-End Tests

Test complete workflows from start to finish:

- **test_complete_workflow.py**: Complete system workflow tests
  - Log → JSON → Menu Bar data flow
  - Multi-day streak calculations
  - Error recovery scenarios
  - Concurrent session handling
  - Large dataset performance
  - Real-time data updates
  - Data migration scenarios

## Test Fixtures and Data

### Fixtures (conftest.py)

- `temp_data_dir`: Temporary directory for test data
- `sample_focus_data`: Sample focus session data
- `sample_log_lines`: Sample log file content
- `sample_streak_data`: Sample streak data
- `complex_focus_data`: Complex multi-day focus data
- `create_test_json_file`: Factory for creating JSON test files
- `create_test_log_file`: Factory for creating log test files

### Sample Data

- **fixtures/sample_logs.txt**: Realistic log file content for testing
- Programmatically generated test data for various scenarios

## Testing Best Practices

### Writing New Tests

1. **Use descriptive test names**: `test_calculate_duration_with_valid_timestamps`
2. **Follow AAA pattern**: Arrange, Act, Assert
3. **Use appropriate fixtures**: Leverage existing fixtures for common test data
4. **Test edge cases**: Include error conditions and boundary values
5. **Mock external dependencies**: Use unittest.mock for system calls, file operations

### Test Data Management

1. **Use temporary directories**: All tests use `temp_data_dir` fixture
2. **Clean up after tests**: Fixtures handle cleanup automatically
3. **Realistic test data**: Use representative log content and data structures
4. **Avoid test dependencies**: Each test should be independent

### Performance Considerations

1. **Mock expensive operations**: Mock file I/O, network calls, subprocess calls
2. **Use small datasets**: Keep test data minimal but representative
3. **Performance tests marked**: Use `@pytest.mark.slow` for long-running tests

## Debugging Tests

### Running Individual Tests

```bash
pytest tests/unit/test_data_access.py::TestDataAccess::test_get_today_minutes_success
```

### Debugging with Print Statements

```bash
pytest -s tests/unit/test_data_access.py  # Don't capture output
```

### Running with Debugger

```bash
pytest --pdb tests/unit/test_data_access.py  # Drop into debugger on failure
```

### Verbose Output

```bash
pytest -vv tests/  # Extra verbose output
```

## Coverage Reporting

Generate coverage report:
```bash
python tests/run_tests.py --coverage
```

This creates:
- Terminal coverage report
- HTML coverage report in `htmlcov/` directory

View HTML coverage:
```bash
open htmlcov/index.html  # macOS
```

## Continuous Integration

The test suite is designed to work in CI environments:

- No external dependencies required
- All tests use temporary directories
- Mocked system interactions
- Fast execution (< 30 seconds for full suite)
- Clear pass/fail indicators

Example GitHub Actions workflow:
```yaml
- name: Run tests
  run: |
    pip install pytest pytest-cov
    python tests/run_tests.py --coverage
```

## Troubleshooting

### Common Issues

1. **Import errors**: Ensure the project root is in Python path
2. **Permission errors**: Tests create temporary files; ensure write permissions
3. **Module not found**: Run tests from project root directory
4. **Fixture errors**: Check that conftest.py is being loaded correctly

### Getting Help

1. Run tests with verbose output: `pytest -vv`
2. Check individual test files for specific test documentation
3. Review conftest.py for available fixtures
4. Use `pytest --fixtures` to see all available fixtures

## Contributing

When adding new features:

1. Write tests first (TDD approach)
2. Include unit tests for individual functions
3. Add integration tests for component interactions
4. Create end-to-end tests for user workflows
5. Update this README with new test descriptions
6. Ensure all tests pass before submitting changes