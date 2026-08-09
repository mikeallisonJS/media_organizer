"""Organization template controls panel."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING

import defaults
from gui.media_type_config import MEDIA_TYPE_TAB_LABELS, TEMPLATE_EXAMPLES
from settings import MEDIA_TYPES

if TYPE_CHECKING:
    from archimedius_gui import ArchimediusGUI
    from settings import Settings


class TemplatePanel:
    """Per-media-type template entries and exclude-unknown options."""

    def __init__(self, app: ArchimediusGUI) -> None:
        self.app = app
        self.template_vars: dict[str, tk.StringVar] = {}
        self.template_entries: dict[str, ttk.Entry] = {}
        self.exclude_unknown_vars: dict[str, tk.BooleanVar] = {}

    def build(self, parent: ttk.Frame) -> None:
        """Create template controls inside *parent*."""
        template_frame = ttk.Frame(parent, padding=5)
        template_frame.pack(fill=tk.BOTH, expand=True, pady=2)

        header_frame = ttk.Frame(template_frame)
        header_frame.pack(fill=tk.X, pady=2)
        ttk.Label(header_frame, text="Use {placeholders} for metadata fields:").pack(
            side=tk.LEFT
        )
        ttk.Button(
            header_frame,
            text="Placeholders Help",
            command=self.app._show_placeholders_help,
        ).pack(side=tk.RIGHT)

        notebook = ttk.Notebook(template_frame)
        notebook.pack(fill=tk.X, pady=2)

        for media_type in MEDIA_TYPES:
            tab = ttk.Frame(notebook, padding=2)
            notebook.add(tab, text=MEDIA_TYPE_TAB_LABELS[media_type])
            self._build_media_type_tab(tab, media_type)

    def _build_media_type_tab(self, parent: ttk.Frame, media_type: str) -> None:
        title = MEDIA_TYPE_TAB_LABELS[media_type]
        self.exclude_unknown_vars[media_type] = tk.BooleanVar(
            value=defaults.DEFAULT_EXCLUDE_UNKNOWN[media_type]
        )
        self.template_vars[media_type] = tk.StringVar(
            value=self.app.settings.templates.get(
                media_type,
                defaults.DEFAULT_TEMPLATES[media_type],
            )
        )
        self.template_vars[media_type].trace_add(
            "write",
            lambda *_args, mt=media_type: self.app._on_template_change(mt),
        )
        self.exclude_unknown_vars[media_type].trace_add(
            "write",
            lambda *_args, mt=media_type: self.app._on_template_change(mt),
        )

        ttk.Label(parent, text=f"{title} Template:").pack(anchor=tk.W)
        entry = ttk.Entry(parent, textvariable=self.template_vars[media_type])
        entry.pack(fill=tk.X, pady=1)
        self.template_entries[media_type] = entry
        ttk.Label(parent, text=f"Example: {TEMPLATE_EXAMPLES[media_type]}").pack(anchor=tk.W)
        ttk.Checkbutton(
            parent,
            text="Exclude 'Unknown' folders from path",
            variable=self.exclude_unknown_vars[media_type],
        ).pack(anchor=tk.W, pady=(5, 0))

    def read_settings(self, settings: Settings) -> None:
        """Read the template controls into *settings* (templates, exclude-unknown)."""
        settings.templates = self.get_template_settings()
        settings.exclude_unknown = self.get_exclude_unknown_settings()

    def apply_settings(self, settings: Settings) -> None:
        """Apply the template slice of *settings* to the controls."""
        self.apply_templates(settings.templates)
        self.apply_exclude_unknown(settings.exclude_unknown)

    def get_template_settings(self) -> dict[str, str]:
        return {
            media_type: self.template_vars[media_type].get().strip()
            for media_type in MEDIA_TYPES
        }

    def get_exclude_unknown_settings(self) -> dict[str, bool]:
        return {
            media_type: self.exclude_unknown_vars[media_type].get()
            for media_type in MEDIA_TYPES
        }

    def set_enabled(self, enabled: bool) -> None:
        state = tk.NORMAL if enabled else tk.DISABLED
        for media_type in MEDIA_TYPES:
            self.template_entries[media_type].config(state=state)

    def apply_templates(self, templates: dict[str, str]) -> None:
        for media_type in MEDIA_TYPES:
            template = templates.get(media_type)
            if template:
                self.template_vars[media_type].set(template)

    def apply_exclude_unknown(self, exclude_unknown: dict[str, bool]) -> None:
        for media_type in MEDIA_TYPES:
            self.exclude_unknown_vars[media_type].set(
                exclude_unknown.get(
                    media_type,
                    defaults.DEFAULT_EXCLUDE_UNKNOWN[media_type],
                )
            )

    def reset_to_defaults(self) -> None:
        for media_type in MEDIA_TYPES:
            self.template_vars[media_type].set(defaults.DEFAULT_TEMPLATES[media_type])
