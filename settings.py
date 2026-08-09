"""
Settings model and persistence for Archimedius.

Centralizes load/save of user preferences to the settings JSON file.
"""

from __future__ import annotations

import copy
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

import defaults

MEDIA_TYPES = ("audio", "video", "image", "ebook")
LOGGER_NAME = "Archimedius"


def settings_path() -> Path:
    """Return the path to the user settings file."""
    return Path.home() / defaults.DEFAULT_PATHS["settings_file"]


def _default_supported_extensions() -> dict[str, list[str]]:
    return copy.deepcopy(defaults.DEFAULT_EXTENSIONS)


def _default_extension_selections(
    supported: Mapping[str, list[str]] | None = None,
) -> dict[str, dict[str, bool]]:
    """All extensions selected by default."""
    supported = supported or _default_supported_extensions()
    return {
        media_type: {ext: True for ext in supported.get(media_type, [])}
        for media_type in MEDIA_TYPES
    }


@dataclass
class Settings:
    """Persisted application settings."""

    source_dir: str = ""
    output_dir: str = ""
    templates: dict[str, str] = field(default_factory=lambda: copy.deepcopy(defaults.DEFAULT_TEMPLATES))
    supported_extensions: dict[str, list[str]] = field(
        default_factory=_default_supported_extensions
    )
    extension_selections: dict[str, dict[str, bool]] = field(default_factory=dict)
    exclude_unknown: dict[str, bool] = field(
        default_factory=lambda: copy.deepcopy(defaults.DEFAULT_EXCLUDE_UNKNOWN)
    )
    operation_mode: str = "copy"
    show_full_paths: bool = defaults.DEFAULT_SETTINGS["show_full_paths"]
    auto_save_enabled: bool = defaults.DEFAULT_SETTINGS["auto_save_enabled"]
    auto_preview_enabled: bool = defaults.DEFAULT_SETTINGS["auto_preview_enabled"]
    logging_level: str = defaults.DEFAULT_SETTINGS["logging_level"]
    dark_mode: bool = defaults.DEFAULT_SETTINGS["dark_mode"]
    window_geometry: str = defaults.DEFAULT_WINDOW_SIZES["main_window"]
    collision_policy: str = defaults.DEFAULT_SETTINGS["collision_policy"]

    def __post_init__(self) -> None:
        if not self.extension_selections:
            self.extension_selections = _default_extension_selections(self.supported_extensions)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to the on-disk JSON format (backward compatible)."""
        audio_template = self.templates.get("audio", defaults.DEFAULT_TEMPLATES["audio"])
        return {
            "source_dir": self.source_dir,
            "output_dir": self.output_dir,
            "templates": copy.deepcopy(self.templates),
            "template": audio_template,
            "extensions": copy.deepcopy(self.extension_selections),
            "exclude_unknown": copy.deepcopy(self.exclude_unknown),
            "custom_extensions": copy.deepcopy(self.supported_extensions),
            "show_full_paths": self.show_full_paths,
            "auto_save_enabled": self.auto_save_enabled,
            "auto_preview_enabled": self.auto_preview_enabled,
            "logging_level": self.logging_level,
            "dark_mode": self.dark_mode,
            "window_geometry": self.window_geometry,
            "operation_mode": self.operation_mode,
            "collision_policy": self.collision_policy,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Settings:
        """Deserialize from saved JSON, applying defaults for missing keys."""
        supported = _merge_custom_extensions(data.get("custom_extensions"))
        templates = copy.deepcopy(defaults.DEFAULT_TEMPLATES)
        if "templates" in data and isinstance(data["templates"], dict):
            for media_type in MEDIA_TYPES:
                if media_type in data["templates"] and data["templates"][media_type]:
                    templates[media_type] = str(data["templates"][media_type])
        elif data.get("template"):
            templates["audio"] = str(data["template"])

        extension_selections = _merge_extension_selections(
            data.get("extensions"), supported
        )

        exclude_unknown = copy.deepcopy(defaults.DEFAULT_EXCLUDE_UNKNOWN)
        if isinstance(data.get("exclude_unknown"), dict):
            for media_type in MEDIA_TYPES:
                if media_type in data["exclude_unknown"]:
                    exclude_unknown[media_type] = bool(data["exclude_unknown"][media_type])

        return cls(
            source_dir=str(data.get("source_dir", "") or ""),
            output_dir=str(data.get("output_dir", "") or ""),
            templates=templates,
            supported_extensions=supported,
            extension_selections=extension_selections,
            exclude_unknown=exclude_unknown,
            operation_mode=str(data.get("operation_mode", "copy") or "copy"),
            show_full_paths=bool(
                data.get("show_full_paths", defaults.DEFAULT_SETTINGS["show_full_paths"])
            ),
            auto_save_enabled=bool(
                data.get("auto_save_enabled", defaults.DEFAULT_SETTINGS["auto_save_enabled"])
            ),
            auto_preview_enabled=bool(
                data.get(
                    "auto_preview_enabled",
                    defaults.DEFAULT_SETTINGS["auto_preview_enabled"],
                )
            ),
            logging_level=str(
                data.get("logging_level", defaults.DEFAULT_SETTINGS["logging_level"])
            ),
            dark_mode=bool(data.get("dark_mode", defaults.DEFAULT_SETTINGS["dark_mode"])),
            window_geometry=str(
                data.get("window_geometry", defaults.DEFAULT_WINDOW_SIZES["main_window"])
                or defaults.DEFAULT_WINDOW_SIZES["main_window"]
            ),
            collision_policy=_normalize_collision_policy(
                data.get("collision_policy", defaults.DEFAULT_SETTINGS["collision_policy"])
            ),
        )


def _normalize_collision_policy(value: str | None) -> str:
    policy = str(value or defaults.DEFAULT_SETTINGS["collision_policy"])
    if policy in defaults.COLLISION_POLICIES:
        return policy
    return defaults.DEFAULT_SETTINGS["collision_policy"]


def default_settings() -> Settings:
    """Return a fresh Settings instance with application defaults."""
    return Settings()


def _merge_custom_extensions(
    custom_extensions: Mapping[str, Any] | None,
) -> dict[str, list[str]]:
    merged = copy.deepcopy(defaults.DEFAULT_EXTENSIONS)
    if not custom_extensions:
        return merged
    for media_type, exts in custom_extensions.items():
        if media_type in merged and exts:
            merged[media_type] = list(exts)
    return merged


def _merge_extension_selections(
    saved_extensions: Mapping[str, Any] | None,
    supported: Mapping[str, list[str]],
) -> dict[str, dict[str, bool]]:
    selections = _default_extension_selections(supported)
    if not saved_extensions:
        return selections
    for media_type in MEDIA_TYPES:
        if media_type not in saved_extensions:
            continue
        saved_for_type = saved_extensions[media_type]
        if not isinstance(saved_for_type, dict):
            continue
        for ext, value in saved_for_type.items():
            if ext in selections[media_type]:
                selections[media_type][ext] = bool(value)
    return selections


def load_settings(path: Path | None = None) -> Settings:
    """Load settings from disk, or return defaults if the file is missing."""
    config_file = path or settings_path()
    if not config_file.exists():
        return default_settings()
    try:
        with open(config_file, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, dict):
            return default_settings()
        return Settings.from_dict(data)
    except (OSError, json.JSONDecodeError) as exc:
        logging.getLogger(LOGGER_NAME).error("Error loading settings: %s", exc)
        return default_settings()


def save_settings(settings: Settings, path: Path | None = None) -> None:
    """Persist settings to disk."""
    config_file = path or settings_path()
    with open(config_file, "w", encoding="utf-8") as handle:
        json.dump(settings.to_dict(), handle)
    logging.getLogger(LOGGER_NAME).info("Settings saved to %s", config_file)


def sync_gui_from_settings(gui: Any, settings: Settings) -> None:
    """Copy Settings values onto GUI instance attributes used by widgets."""
    gui.settings = settings
    gui.show_full_paths = settings.show_full_paths
    gui.auto_save_enabled = settings.auto_save_enabled
    gui.auto_preview_enabled = settings.auto_preview_enabled
    gui.logging_level = settings.logging_level
    gui.dark_mode = settings.dark_mode
    gui.operation_mode = settings.operation_mode
    gui.collision_policy = settings.collision_policy


def collect_settings_from_gui(gui: Any) -> Settings:
    """Build a Settings instance from the current GUI state.

    Each panel reads its own slice of the settings via ``read_settings`` rather
    than this function reaching into scattered widget references. The main
    window only owns the directory entries and run/window state directly.
    """
    settings = Settings(
        source_dir=gui.source_entry.get().strip(),
        output_dir=gui.output_entry.get().strip(),
        operation_mode=getattr(gui, "operation_mode", "copy"),
        window_geometry=gui.root.geometry(),
    )
    gui.template_panel.read_settings(settings)
    gui.extension_filter_panel.read_settings(settings)
    gui.preferences_panel.read_settings(settings)
    return settings


def configure_logging(settings: Settings | None = None) -> None:
    """Apply the saved logging level to the application logger."""
    settings = settings or load_settings()
    app_logger = logging.getLogger(LOGGER_NAME)
    numeric_level = defaults.LOGGING_LEVELS.get(
        settings.logging_level, logging.INFO
    )
    app_logger.setLevel(numeric_level)
    for handler in logging.root.handlers:
        if isinstance(handler, logging.FileHandler):
            handler.setLevel(numeric_level)
    logging.getLogger("pypdf").setLevel(logging.ERROR)
