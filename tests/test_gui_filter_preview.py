#!/usr/bin/env python3
"""
Tests for GUI file-type filter ↔ preview interaction.

Verifies that toggling extension filters immediately updates the preview
tree without requiring a full re-analysis.
"""

import os
import sys
import tkinter as tk
from unittest.mock import patch, MagicMock

import pytest

# Ensure project root is on sys.path so imports resolve
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture(scope="module")
def tk_root():
    """Single Tk root shared across all tests in this module."""
    root = tk.Tk()
    root.withdraw()
    yield root
    root.destroy()


@pytest.fixture()
def gui(tk_root):
    """Create a fresh ArchimediusGUI instance for each test."""
    with patch("archimedius_gui.LicenseManager") as MockLM:
        MockLM.return_value.is_valid.return_value = True
        with patch("archimedius_gui.ArchimediusGUI._load_settings"):
            from archimedius_gui import ArchimediusGUI

            app = ArchimediusGUI(tk_root)

    yield app


# ── sample preview data covering multiple media types ──────────────────

SAMPLE_PREVIEW_DATA = [
    ("song.mp3", "2024/Rock/song.mp3", "/src/song.mp3"),
    ("song.flac", "2024/Jazz/song.flac", "/src/song.flac"),
    ("video.mp4", "2024/video.mp4", "/src/video.mp4"),
    ("photo.jpg", "2024/photo.jpg", "/src/photo.jpg"),
    ("book.epub", "Author/Title/book.epub", "/src/book.epub"),
    ("book.pdf", "Author/Title/book.pdf", "/src/book.pdf"),
]


def _tree_paths(gui_app):
    """Return a list of full_path values currently shown in the preview tree."""
    return [
        gui_app.preview_files[iid]["full_path"]
        for iid in gui_app.preview_tree.get_children()
    ]


# ── tests ──────────────────────────────────────────────────────────────


class TestFilterPreview:
    """Deselecting a file-type filter should instantly remove those files
    from the preview without re-running analysis."""

    def test_deselecting_ebooks_removes_them_from_preview(self, gui):
        gui._update_preview_results(SAMPLE_PREVIEW_DATA, len(SAMPLE_PREVIEW_DATA))

        for var in gui.extension_vars["ebook"].values():
            var.set(False)
        gui._filter_preview()

        paths = _tree_paths(gui)
        assert len(paths) == 4
        assert not any(p.endswith(".epub") or p.endswith(".pdf") for p in paths)

    def test_deselecting_audio_removes_audio_from_preview(self, gui):
        gui._update_preview_results(SAMPLE_PREVIEW_DATA, len(SAMPLE_PREVIEW_DATA))

        for var in gui.extension_vars["audio"].values():
            var.set(False)
        gui._filter_preview()

        paths = _tree_paths(gui)
        assert not any(p.endswith(".mp3") or p.endswith(".flac") for p in paths)
        assert len(paths) == 4

    def test_reselecting_filter_restores_files(self, gui):
        gui._update_preview_results(SAMPLE_PREVIEW_DATA, len(SAMPLE_PREVIEW_DATA))

        for var in gui.extension_vars["ebook"].values():
            var.set(False)
        gui._filter_preview()
        assert len(_tree_paths(gui)) == 4

        for var in gui.extension_vars["ebook"].values():
            var.set(True)
        gui._filter_preview()
        assert len(_tree_paths(gui)) == 6

    def test_toggle_all_extensions_calls_filter_preview(self, gui):
        gui._update_preview_results(SAMPLE_PREVIEW_DATA, len(SAMPLE_PREVIEW_DATA))

        gui.ebook_all_var.set(False)
        gui._toggle_all_extensions("ebook")

        paths = _tree_paths(gui)
        assert not any(p.endswith(".epub") or p.endswith(".pdf") for p in paths)

    def test_update_extension_selection_calls_filter_preview(self, gui):
        gui._update_preview_results(SAMPLE_PREVIEW_DATA, len(SAMPLE_PREVIEW_DATA))

        for var in gui.extension_vars["ebook"].values():
            var.set(False)
        gui._update_extension_selection()

        paths = _tree_paths(gui)
        assert not any(p.endswith(".epub") or p.endswith(".pdf") for p in paths)

    def test_filter_is_noop_when_no_preview_data(self, gui):
        gui._filter_preview()
        assert len(gui.preview_tree.get_children()) == 0

    def test_clear_preview_wipes_stored_data(self, gui):
        gui._update_preview_results(SAMPLE_PREVIEW_DATA, len(SAMPLE_PREVIEW_DATA))
        gui._clear_preview()

        assert gui._full_preview_data == []
        assert gui._full_preview_count == 0
        assert len(gui.preview_tree.get_children()) == 0

    def test_status_reflects_filtered_count(self, gui):
        gui._update_preview_results(SAMPLE_PREVIEW_DATA, len(SAMPLE_PREVIEW_DATA))

        for var in gui.extension_vars["ebook"].values():
            var.set(False)
        gui._filter_preview()

        assert "4" in gui.status_var.get()
