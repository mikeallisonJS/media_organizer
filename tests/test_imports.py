#!/usr/bin/env python3
"""
Basic tests for Archimedius.
"""

def test_imports():
    """Test that all main modules can be imported."""
    try:
        import archimedius
        import media_file
        import extensions
        import defaults
        import log_window
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

def test_extensions():
    """Test that extensions module contains expected values."""
    import extensions
    
    assert isinstance(extensions.DEFAULT_EXTENSIONS, dict)
    assert "audio" in extensions.DEFAULT_EXTENSIONS
    assert "video" in extensions.DEFAULT_EXTENSIONS
    assert "image" in extensions.DEFAULT_EXTENSIONS
    assert "ebook" in extensions.DEFAULT_EXTENSIONS
    
    # Check that each category has at least one extension
    for category, extensions_list in extensions.DEFAULT_EXTENSIONS.items():
        assert len(extensions_list) > 0 