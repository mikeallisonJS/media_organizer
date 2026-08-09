#!/usr/bin/env python3
"""Round-trip Settings through the main-window panels.

Verifies that applying a Settings instance to the panels and then collecting
it back yields the same values, and that this matches the save/load file
behavior. This guards the decoupling of Settings persistence from widget
introspection: ``collect_settings_from_gui`` delegates to each panel's
``read_settings`` rather than reaching into scattered widget references.
"""

import os
import sys

# Ensure project root is on sys.path so imports resolve
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from settings import (  # noqa: E402
    Settings,
    collect_settings_from_gui,
    load_settings,
    save_settings,
    sync_gui_from_settings,
)

# Fields owned by the panels / directory entries that survive a UI round-trip.
# ``window_geometry`` is excluded because it reflects the live (withdrawn) root.
PANEL_FIELDS = (
    "source_dir",
    "output_dir",
    "templates",
    "supported_extensions",
    "extension_selections",
    "exclude_unknown",
    "operation_mode",
    "show_full_paths",
    "auto_save_enabled",
    "auto_preview_enabled",
    "logging_level",
    "dark_mode",
    "collision_policy",
)


# The ``gui`` fixture is provided by tests/conftest.py.


def _custom_settings() -> Settings:
    """A Settings instance with non-default, internally consistent values."""
    return Settings(
        source_dir=os.path.join("data", "in"),
        output_dir=os.path.join("data", "out"),
        templates={
            "audio": "{year}/{artist}/{filename}",
            "video": "{creation_year}/{filename}",
            "image": "{creation_year}/{creation_month}/{filename}",
            "ebook": "{author}/{title}/{filename}",
        },
        supported_extensions={
            "audio": [".mp3", ".flac"],
            "video": [".mp4"],
            "image": [".jpg"],
            "ebook": [".epub"],
        },
        extension_selections={
            "audio": {".mp3": True, ".flac": False},
            "video": {".mp4": True},
            "image": {".jpg": False},
            "ebook": {".epub": True},
        },
        exclude_unknown={"audio": True, "video": False, "image": True, "ebook": False},
        operation_mode="move",
        show_full_paths=True,
        auto_save_enabled=False,
        auto_preview_enabled=False,
        logging_level="DEBUG",
        dark_mode=True,
        collision_policy="rename",
    )


def _apply_to_gui(gui, settings: Settings) -> None:
    """Push *settings* into the GUI exactly as ``_load_settings`` would."""
    sync_gui_from_settings(gui, settings)
    gui._apply_settings_to_widgets(settings)


def test_collect_after_apply_matches_source(gui):
    """Applying a Settings to the panels and collecting yields the same values."""
    original = _custom_settings()

    _apply_to_gui(gui, original)
    collected = collect_settings_from_gui(gui)

    for field in PANEL_FIELDS:
        assert getattr(collected, field) == getattr(original, field), field


def test_panel_round_trip_matches_file_round_trip(gui, tmp_path):
    """A round-trip through panels matches a save/load through the file."""
    original = _custom_settings()

    _apply_to_gui(gui, original)
    collected = collect_settings_from_gui(gui)

    config_file = tmp_path / "archimedius_settings.json"
    save_settings(collected, config_file)
    loaded = load_settings(config_file)

    for field in PANEL_FIELDS:
        assert getattr(loaded, field) == getattr(original, field), field


def test_preferences_apply_settings_consumes_argument(gui):
    """PreferencesPanel.apply_settings must push the passed Settings into the
    controls, not silently read from the app shell."""
    panel = gui.preferences_panel
    target = _custom_settings()

    # Make the committed app state deliberately disagree with *target* so a
    # regression to "ignore the argument and read from app" would be caught.
    gui.dark_mode = not target.dark_mode
    gui.show_full_paths = not target.show_full_paths
    gui.collision_policy = "skip"
    gui.logging_level = "ERROR"
    gui.settings.supported_extensions = {
        "audio": [".wav"],
        "video": [".mkv"],
        "image": [".png"],
        "ebook": [".mobi"],
    }

    panel.apply_settings(target)

    collected = Settings()
    panel.read_settings(collected)

    for field in (
        "dark_mode",
        "show_full_paths",
        "collision_policy",
        "logging_level",
        "supported_extensions",
    ):
        assert getattr(collected, field) == getattr(target, field), field


def test_collect_does_not_depend_on_mirrored_widget_refs(gui):
    """collect_settings_from_gui must not rely on legacy mirrored attributes."""
    original = _custom_settings()
    _apply_to_gui(gui, original)

    # The old state-bag mirrors should no longer exist on the app shell.
    for attr in ("template_vars", "extension_vars", "exclude_unknown_vars"):
        assert not hasattr(gui, attr), attr

    # Collection still succeeds purely via the panel interfaces.
    collected = collect_settings_from_gui(gui)
    assert collected.templates == original.templates
    assert collected.extension_selections == original.extension_selections
