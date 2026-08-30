def test_environment_setup():
    """A simple test to ensure pytest is running correctly."""
    assert True

def test_pylite_import():
    """Ensure the pylite package is discoverable."""
    try:
        import pylite.cli
        assert True
    except ImportError:
        assert False, "Failed to import pylite.cli. Check your PYTHONPATH."