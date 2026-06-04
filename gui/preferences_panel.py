"""Preferences tab panel."""

from __future__ import annotations

import copy
import logging
import tkinter as tk
from tkinter import messagebox, ttk
from typing import TYPE_CHECKING

import defaults
from gui.media_type_config import MEDIA_TYPE_TAB_LABELS
from settings import MEDIA_TYPES

if TYPE_CHECKING:
    from archimedius_gui import ArchimediusGUI
    from settings import Settings

logger = logging.getLogger("Archimedius")


class PreferencesPanel:
    """Inline preferences controls (General and File Types)."""

    def __init__(self, app: ArchimediusGUI) -> None:
        self.app = app
        self.pref_auto_preview_var = tk.BooleanVar()
        self.pref_auto_save_var = tk.BooleanVar()
        self.pref_show_full_paths_var = tk.BooleanVar()
        self.pref_dark_mode_var = tk.BooleanVar()
        self.pref_logging_level_var = tk.StringVar()
        self.pref_collision_policy_var = tk.StringVar()
        self.pref_extension_texts: dict[str, tk.Text] = {}

    def build(self, parent: ttk.Frame) -> None:
        preferences_frame = ttk.Frame(parent)
        preferences_frame.pack(fill=tk.BOTH, expand=True)

        prefs_notebook = ttk.Notebook(preferences_frame)
        prefs_notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        general_tab = ttk.Frame(prefs_notebook, padding=10)
        file_types_tab = ttk.Frame(prefs_notebook, padding=10)
        prefs_notebook.add(general_tab, text="General")
        prefs_notebook.add(file_types_tab, text="File Types")

        self._sync_vars_from_app()
        self._build_general_tab(general_tab)
        self._build_file_types_tab(file_types_tab)

        buttons_frame = ttk.Frame(preferences_frame)
        buttons_frame.pack(fill=tk.X)
        ttk.Button(
            buttons_frame,
            text="Save Preferences",
            command=self.save,
        ).pack(side=tk.RIGHT, padx=5)
        ttk.Button(
            buttons_frame,
            text="Reload From Saved Settings",
            command=self.app._load_settings,
        ).pack(side=tk.RIGHT, padx=5)

    def _sync_vars_from_app(self) -> None:
        self.pref_auto_preview_var.set(self.app.auto_preview_enabled)
        self.pref_auto_save_var.set(self.app.auto_save_enabled)
        self.pref_show_full_paths_var.set(self.app.show_full_paths)
        self.pref_dark_mode_var.set(self.app.dark_mode)
        self.pref_logging_level_var.set(self.app.logging_level)
        self.pref_collision_policy_var.set(
            defaults.COLLISION_POLICY_LABELS.get(
                self.app.collision_policy,
                defaults.COLLISION_POLICY_LABELS[
                    defaults.DEFAULT_SETTINGS["collision_policy"]
                ],
            )
        )

    def _build_general_tab(self, parent: ttk.Frame) -> None:
        ttk.Checkbutton(
            parent,
            text="Automatically generate preview when settings change",
            variable=self.pref_auto_preview_var,
            command=self.on_general_change,
        ).pack(anchor=tk.W, pady=4)
        ttk.Checkbutton(
            parent,
            text="Automatically save settings when inputs change",
            variable=self.pref_auto_save_var,
            command=self.on_general_change,
        ).pack(anchor=tk.W, pady=4)
        ttk.Checkbutton(
            parent,
            text="Show full file paths in preview",
            variable=self.pref_show_full_paths_var,
            command=self.on_general_change,
        ).pack(anchor=tk.W, pady=4)
        ttk.Checkbutton(
            parent,
            text="Enable dark mode",
            variable=self.pref_dark_mode_var,
            command=self.on_dark_mode_toggle,
        ).pack(anchor=tk.W, pady=4)

        logging_row = ttk.Frame(parent)
        logging_row.pack(fill=tk.X, pady=(10, 0))
        ttk.Label(logging_row, text="Logging Level:").pack(side=tk.LEFT, padx=(0, 10))
        logging_combobox = ttk.Combobox(
            logging_row,
            textvariable=self.pref_logging_level_var,
            values=list(defaults.LOGGING_LEVELS.keys()),
            state="readonly",
            width=10,
        )
        logging_combobox.pack(side=tk.LEFT)
        logging_combobox.bind("<<ComboboxSelected>>", lambda _event: self.on_general_change())

        collision_row = ttk.Frame(parent)
        collision_row.pack(fill=tk.X, pady=(10, 0))
        ttk.Label(collision_row, text="Path collision policy:").pack(side=tk.LEFT, padx=(0, 10))
        collision_combobox = ttk.Combobox(
            collision_row,
            textvariable=self.pref_collision_policy_var,
            values=list(defaults.COLLISION_POLICY_LABELS.values()),
            state="readonly",
            width=28,
        )
        collision_combobox.pack(side=tk.LEFT)
        collision_combobox.bind("<<ComboboxSelected>>", lambda _event: self.on_general_change())

    def _build_file_types_tab(self, parent: ttk.Frame) -> None:
        filetype_notebook = ttk.Notebook(parent)
        filetype_notebook.pack(fill=tk.BOTH, expand=True)

        for media_type in MEDIA_TYPES:
            frame = ttk.Frame(filetype_notebook, padding=10)
            filetype_notebook.add(frame, text=MEDIA_TYPE_TAB_LABELS[media_type])
            ttk.Label(
                frame,
                text=f"Extensions for {media_type} files (one per line):",
                wraplength=500,
            ).pack(anchor=tk.W, pady=(0, 5))

            text_frame = ttk.Frame(frame)
            text_frame.pack(fill=tk.BOTH, expand=True)
            text_widget = tk.Text(text_frame, height=10)
            scrollbar = ttk.Scrollbar(
                text_frame, orient="vertical", command=text_widget.yview
            )
            text_widget.configure(yscrollcommand=scrollbar.set)
            text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            text_widget.insert(
                "1.0",
                "\n".join(
                    ext.lstrip(".")
                    for ext in self.app.settings.supported_extensions[media_type]
                ),
            )
            self.pref_extension_texts[media_type] = text_widget

            ttk.Button(
                frame,
                text="Reset to Default",
                command=lambda mt=media_type: self.reset_extensions_to_default(mt),
            ).pack(anchor=tk.E, pady=5)

    def read_settings(self, settings: Settings) -> None:
        """Read the preferences slice into *settings* from the panel controls.

        The general-preference controls (toggles, logging level, collision
        policy) are the source of truth and are read directly from their
        widgets. The supported extension lists come from the in-memory model
        rather than the editable text boxes, because those are validated and
        committed only on Save.
        """
        settings.supported_extensions = copy.deepcopy(self.app.settings.supported_extensions)
        settings.show_full_paths = self.pref_show_full_paths_var.get()
        settings.auto_save_enabled = self.pref_auto_save_var.get()
        settings.auto_preview_enabled = self.pref_auto_preview_var.get()
        settings.logging_level = self.pref_logging_level_var.get()
        settings.dark_mode = self.pref_dark_mode_var.get()
        settings.collision_policy = self._collision_policy_from_label(
            self.pref_collision_policy_var.get()
        )

    def apply_settings(self, settings: Settings) -> None:
        """Apply the preferences slice of *settings* to the panel controls."""
        self.pref_auto_preview_var.set(settings.auto_preview_enabled)
        self.pref_auto_save_var.set(settings.auto_save_enabled)
        self.pref_show_full_paths_var.set(settings.show_full_paths)
        self.pref_dark_mode_var.set(settings.dark_mode)
        self.pref_logging_level_var.set(settings.logging_level)
        self.pref_collision_policy_var.set(
            defaults.COLLISION_POLICY_LABELS.get(
                settings.collision_policy,
                defaults.COLLISION_POLICY_LABELS[
                    defaults.DEFAULT_SETTINGS["collision_policy"]
                ],
            )
        )
        self._sync_extension_texts(settings.supported_extensions)

    def reset_extensions_to_default(self, media_type: str) -> None:
        default_extensions = [
            ext.lstrip(".") for ext in defaults.DEFAULT_EXTENSIONS[media_type]
        ]
        if media_type in self.pref_extension_texts:
            self.pref_extension_texts[media_type].delete("1.0", tk.END)
            self.pref_extension_texts[media_type].insert("1.0", "\n".join(default_extensions))

    def save(self) -> None:
        try:
            self.apply_general_preferences()
            self.app.apply_theme(self.app.dark_mode)

            new_extensions = {}
            for media_type, text_widget in self.pref_extension_texts.items():
                extensions_text = text_widget.get("1.0", "end-1c").split("\n")
                extensions_list = [ext.strip() for ext in extensions_text if ext.strip()]
                extensions_list = [
                    ext if ext.startswith(".") else f".{ext}" for ext in extensions_list
                ]
                if not extensions_list:
                    messagebox.showerror(
                        "Error",
                        f"Please provide at least one extension for {media_type}.",
                    )
                    return
                new_extensions[media_type] = extensions_list

            self.app.settings.supported_extensions = new_extensions
            self.app._refresh_extension_filters()
            self.app._save_settings()
            self.app._auto_generate_preview()
            self.app.status_var.set("Preferences saved.")
        except Exception as exc:
            logger.error("Error saving inline preferences: %s", exc)
            messagebox.showerror("Error", f"Failed to save preferences: {exc}")

    def on_dark_mode_toggle(self) -> None:
        self.on_general_change()

    def on_general_change(self) -> None:
        previous_show_full_paths = self.app.show_full_paths
        self.apply_general_preferences()
        self.app.apply_theme(self.app.dark_mode)
        self.app._save_settings()

        if previous_show_full_paths != self.app.show_full_paths:
            import os

            source_dir = self.app.source_entry.get().strip()
            if source_dir and os.path.exists(source_dir):
                self.app._generate_preview()

    def apply_general_preferences(self) -> None:
        self.app.auto_preview_enabled = self.pref_auto_preview_var.get()
        self.app.auto_save_enabled = self.pref_auto_save_var.get()
        self.app.show_full_paths = self.pref_show_full_paths_var.get()
        self.app.logging_level = self.pref_logging_level_var.get()
        self.app.dark_mode = self.pref_dark_mode_var.get()
        self.app.collision_policy = self._collision_policy_from_label(
            self.pref_collision_policy_var.get()
        )

    def _sync_extension_texts(self, supported_extensions: dict[str, list[str]]) -> None:
        """Refresh the editable extension text boxes from *supported_extensions*."""
        for media_type, text_widget in self.pref_extension_texts.items():
            if media_type in supported_extensions:
                text_widget.delete("1.0", tk.END)
                text_widget.insert(
                    "1.0",
                    "\n".join(
                        ext.lstrip(".") for ext in supported_extensions[media_type]
                    ),
                )

    @staticmethod
    def _collision_policy_from_label(label: str) -> str:
        for policy, policy_label in defaults.COLLISION_POLICY_LABELS.items():
            if policy_label == label:
                return policy
        return defaults.DEFAULT_SETTINGS["collision_policy"]
