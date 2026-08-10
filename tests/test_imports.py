#!/usr/bin/env python3
"""
Basic tests for Archimedius.
"""

def test_imports():
    """Test that all main modules can be imported."""
    try:
        import run_state
        import organize_plan
        import organize_run
        import defaults
        import log_window
        import settings
        assert True
    except ImportError as e:
        assert False, f"Import error: {e}"

def test_defaults():
    """Test that defaults module contains expected values."""
    import defaults
    
    assert defaults.APP_NAME == "Archimedius"
    assert isinstance(defaults.APP_VERSION, str)
    assert isinstance(defaults.DEFAULT_TEMPLATES, dict)
    assert "audio" in defaults.DEFAULT_TEMPLATES
    assert "video" in defaults.DEFAULT_TEMPLATES
    assert "image" in defaults.DEFAULT_TEMPLATES
    assert "ebook" in defaults.DEFAULT_TEMPLATES
    assert isinstance(defaults.DEFAULT_EXTENSIONS, dict)
    assert "audio" in defaults.DEFAULT_EXTENSIONS
    assert "video" in defaults.DEFAULT_EXTENSIONS
    assert "image" in defaults.DEFAULT_EXTENSIONS
    assert "ebook" in defaults.DEFAULT_EXTENSIONS

    for _category, extensions_list in defaults.DEFAULT_EXTENSIONS.items():
        assert len(extensions_list) > 0