"""Basic tests to verify test setup is working correctly."""

import pytest
from pathlib import Path


def test_test_directory_structure():
    """Verify test directory structure is correct."""
    test_dir = Path(__file__).parent
    
    # Check main directories exist
    assert (test_dir / "unit").is_dir()
    assert (test_dir / "integration").is_dir()
    assert (test_dir / "e2e").is_dir()
    assert (test_dir / "fixtures").is_dir()
    
    # Check key files exist
    assert (test_dir / "conftest.py").is_file()
    assert (test_dir / "README.md").is_file()
    assert (test_dir / "run_tests.py").is_file()


def test_fixtures_available(temp_data_dir, sample_focus_data, sample_log_lines):
    """Verify that fixtures are available and working."""
    # Test temp_data_dir fixture
    assert temp_data_dir.exists()
    assert temp_data_dir.is_dir()
    
    # Test sample_focus_data fixture
    assert isinstance(sample_focus_data, dict)
    assert "2025-08-10" in sample_focus_data
    assert sample_focus_data["2025-08-10"]["total_time_minutes"] == 45
    
    # Test sample_log_lines fixture
    assert isinstance(sample_log_lines, list)
    assert len(sample_log_lines) > 0
    assert "Start focus session" in sample_log_lines[0]


def test_imports_work():
    """Verify that all modules can be imported successfully."""
    import sys
    from pathlib import Path
    
    # Add project root to path
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    
    # Test imports - these should not raise any errors
    from raycast_focus_tracker import data_access
    from raycast_focus_tracker import log_to_json  
    from raycast_focus_tracker import streak_calculation
    
    # Verify key functions exist
    assert hasattr(data_access, 'get_today_minutes')
    assert hasattr(log_to_json, 'parse_log_file')
    assert hasattr(streak_calculation, 'update_streaks')


def test_create_test_files_fixtures(temp_data_dir, create_test_json_file, create_test_log_file):
    """Test that file creation fixtures work correctly."""
    # Test JSON file creation
    test_data = {"test": "data"}
    json_file = create_test_json_file(temp_data_dir, "test.json", test_data)
    
    assert json_file.exists()
    import json
    with open(json_file) as f:
        loaded_data = json.load(f)
    assert loaded_data == test_data
    
    # Test log file creation
    test_lines = ["line 1", "line 2", "line 3"]
    log_file = create_test_log_file(temp_data_dir, "test.log", test_lines)
    
    assert log_file.exists()
    with open(log_file) as f:
        content = f.read()
    assert content == "\n".join(test_lines)


def test_pytest_markers():
    """Test that pytest markers are working."""
    # This test itself can be used to verify marker functionality
    pass


# Mark this as a unit test
pytestmark = pytest.mark.unit