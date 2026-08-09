"""Selected extensions filter panel for the main window."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING

from gui.media_type_config import MEDIA_TYPE_SECTIONS
from settings import MEDIA_TYPES

if TYPE_CHECKING:
    from archimedius_gui import ArchimediusGUI
    from settings import Settings


class ExtensionFilterPanel:
    """Per-run extension filter checkboxes (File Type Filters tab)."""

    def __init__(self, app: ArchimediusGUI) -> None:
        self.app = app
        self.extension_vars: dict[str, dict[str, tk.BooleanVar]] = {
            media_type: {} for media_type in MEDIA_TYPES
        }
        self.all_vars: dict[str, tk.BooleanVar] = {}
        self.file_types_frame: ttk.Frame | None = None

    def build(self, parent: ttk.Frame) -> None:
        """Create extension filter widgets inside *parent*."""
        self.file_types_frame = ttk.Frame(parent)
        self.file_types_frame.pack(fill=tk.X, pady=2)
        self._build_media_type_sections(self.settings_supported_extensions())

    def settings_supported_extensions(self) -> dict[str, list[str]]:
        return self.app.settings.supported_extensions

    def _build_media_type_sections(
        self,
        supported_extensions: dict[str, list[str]],
        *,
        current_selections: dict[str, dict[str, bool]] | None = None,
        current_all_selections: dict[str, bool] | None = None,
    ) -> None:
        assert self.file_types_frame is not None
        current_selections = current_selections or {}
        current_all_selections = current_all_selections or {}

        for media_type, frame_title, all_label in MEDIA_TYPE_SECTIONS:
            type_frame = ttk.LabelFrame(self.file_types_frame, text=frame_title)
            type_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

            all_selected = current_all_selections.get(media_type, True)
            all_var = tk.BooleanVar(value=all_selected)
            self.all_vars[media_type] = all_var
            ttk.Checkbutton(
                type_frame,
                text=all_label,
                variable=all_var,
                command=lambda mt=media_type: self.toggle_all(mt),
            ).pack(anchor=tk.W)

            extensions_frame = ttk.Frame(type_frame)
            extensions_frame.pack(fill=tk.X, padx=10)

            self.extension_vars[media_type] = {}
            for index, ext in enumerate(supported_extensions[media_type]):
                selected = all_selected or current_selections.get(media_type, {}).get(ext, True)
                var = tk.BooleanVar(value=selected)
                self.extension_vars[media_type][ext] = var
                ttk.Checkbutton(
                    extensions_frame,
                    text=ext.lstrip("."),
                    variable=var,
                    command=self.update_selection,
                ).grid(row=index // 2, column=index % 2, sticky=tk.W, padx=5)

    def refresh(self) -> None:
        """Rebuild checkboxes from current supported extensions."""
        assert self.file_types_frame is not None

        current_selections = {
            file_type: {ext: var.get() for ext, var in self.extension_vars[file_type].items()}
            for file_type in MEDIA_TYPES
        }
        current_all_selections = {
            media_type: self.all_vars[media_type].get() for media_type in MEDIA_TYPES
        }

        for frame in self.file_types_frame.winfo_children():
            frame.destroy()

        self._build_media_type_sections(
            self.settings_supported_extensions(),
            current_selections=current_selections,
            current_all_selections=current_all_selections,
        )

    def toggle_all(self, file_type: str) -> None:
        """Toggle all extensions for a media type."""
        value = self.all_vars[file_type].get()
        for var in self.extension_vars[file_type].values():
            var.set(value)
        if getattr(self.app, "auto_save_enabled", True):
            self.app._save_settings()
        self.app._filter_preview()

    def update_selection(self) -> None:
        """Update parent 'All' checkboxes and re-filter preview."""
        for media_type in MEDIA_TYPES:
            all_selected = all(var.get() for var in self.extension_vars[media_type].values())
            self.all_vars[media_type].set(all_selected)
        if getattr(self.app, "auto_save_enabled", True):
            self.app._save_settings()
        self.app._filter_preview()

    def get_selected_extensions(self) -> list[str]:
        """Return extensions currently selected for this run."""
        selected: list[str] = []
        for extensions_list in self.extension_vars.values():
            for ext, var in extensions_list.items():
                if var.get():
                    selected.append(ext)
        return selected

    def get_extension_selections(self) -> dict[str, dict[str, bool]]:
        """Return per-media-type extension selection flags."""
        return {
            file_type: {ext: var.get() for ext, var in self.extension_vars[file_type].items()}
            for file_type in MEDIA_TYPES
        }

    def read_settings(self, settings: Settings) -> None:
        """Read the extension selections into *settings*."""
        settings.extension_selections = self.get_extension_selections()

    def apply_settings(self, settings: Settings) -> None:
        """Apply the extension-selection slice of *settings* to the checkboxes."""
        self.apply_extension_selections(settings.extension_selections)

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable all filter controls."""
        assert self.file_types_frame is not None
        state = tk.NORMAL if enabled else tk.DISABLED
        for frame in self.file_types_frame.winfo_children():
            for widget in frame.winfo_children():
                if isinstance(widget, (ttk.Checkbutton, ttk.Frame)):
                    if isinstance(widget, ttk.Frame):
                        for checkbox in widget.winfo_children():
                            if isinstance(checkbox, ttk.Checkbutton):
                                checkbox.config(state=state)
                    else:
                        widget.config(state=state)

    def apply_extension_selections(self, selections: dict[str, dict[str, bool]]) -> None:
        """Apply saved extension selections from settings."""
        for file_type in MEDIA_TYPES:
            for ext, value in selections.get(file_type, {}).items():
                if ext in self.extension_vars[file_type]:
                    self.extension_vars[file_type][ext].set(value)
            if self.extension_vars[file_type]:
                all_selected = all(var.get() for var in self.extension_vars[file_type].values())
                self.all_vars[file_type].set(all_selected)

    def reset_all_selected(self) -> None:
        """Select all extensions for every media type."""
        for media_type in MEDIA_TYPES:
            self.all_vars[media_type].set(True)
            self.toggle_all(media_type)
