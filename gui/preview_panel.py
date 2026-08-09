"""Preview tree panel for analyze results."""

from __future__ import annotations

import os
import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from archimedius_gui import ArchimediusGUI


class PreviewPanel:
    """Preview tree, action buttons, and client-side extension filtering."""

    def __init__(self, app: ArchimediusGUI) -> None:
        self.app = app
        self.preview_tree: ttk.Treeview | None = None
        self.preview_button_frame: ttk.Frame | None = None
        self.preview_files: dict[str, dict[str, Any]] = {}
        self.full_preview_data: list[tuple[str, str, str]] = []
        self.full_preview_count = 0

    def build(self, parent: ttk.Frame) -> None:
        preview_frame = ttk.Frame(parent, padding=5)
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=2)

        self.preview_button_frame = ttk.Frame(preview_frame)
        self.preview_button_frame.pack(fill=tk.X, pady=(0, 5))

        buttons = [
            ("Analyze", self.app._generate_preview, "Refresh the preview based on current settings"),
            (
                "Copy Selected",
                lambda: self.app._process_selected_files("copy"),
                "Copy only the selected files to the destination",
            ),
            (
                "Move Selected",
                lambda: self.app._process_selected_files("move"),
                "Move only the selected files to the destination",
            ),
            ("Select All", self.select_all_files, "Select all files in the preview"),
            ("Deselect All", self.deselect_all_files, "Deselect all files in the preview"),
        ]
        for label, command, tooltip in buttons:
            button = ttk.Button(self.preview_button_frame, text=label, command=command)
            button.pack(side=tk.LEFT, padx=5)
            self.app._create_tooltip(button, tooltip)

        preview_container = ttk.Frame(preview_frame)
        preview_container.pack(fill=tk.BOTH, expand=True)

        self.preview_tree = ttk.Treeview(
            preview_container,
            columns=("selected", "source", "destination"),
            show="headings",
            selectmode="extended",
        )
        self.preview_tree.heading("selected", text="Select ☑")
        self.preview_tree.heading("source", text="Source Path")
        self.preview_tree.heading("destination", text="Destination Path")

        preview_container.update_idletasks()
        width = preview_container.winfo_width()
        self.preview_tree.column("selected", width=60, stretch=False)
        self.preview_tree.column("source", width=(width - 60) // 2, stretch=True)
        self.preview_tree.column("destination", width=(width - 60) // 2, stretch=True)

        self.preview_tree.bind("<ButtonRelease-1>", self.toggle_selection)
        self.preview_tree.bind("<Double-1>", self.toggle_selection)

        scrollbar_y = ttk.Scrollbar(
            preview_container, orient="vertical", command=self.preview_tree.yview
        )
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_x = ttk.Scrollbar(
            preview_container, orient="horizontal", command=self.preview_tree.xview
        )
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.preview_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.preview_tree.configure(
            yscrollcommand=scrollbar_y.set,
            xscrollcommand=scrollbar_x.set,
        )

    def clear(self) -> None:
        assert self.preview_tree is not None
        for item in self.preview_tree.get_children():
            self.preview_tree.delete(item)
        self.full_preview_data = []
        self.full_preview_count = 0
        self.preview_files.clear()

    def update_results(self, preview_data: list[tuple[str, str, str]], count: int) -> None:
        self.full_preview_data = list(preview_data)
        self.full_preview_count = count
        self.display(preview_data, count)

    def display(self, preview_data: list[tuple[str, str, str]], count: int) -> None:
        assert self.preview_tree is not None
        for item in self.preview_tree.get_children():
            self.preview_tree.delete(item)

        self.preview_files.clear()
        for display_source, display_dest, full_path in preview_data:
            item_id = self.preview_tree.insert(
                "",
                "end",
                values=("☐", display_source, display_dest),
            )
            self.preview_files[item_id] = {
                "source_path": display_source,
                "dest_path": display_dest,
                "selected": False,
                "full_path": full_path,
            }

        if count == 0:
            self.app.status_var.set("No media files found in the source directory.")
            self.app.file_var.set("")
            return

        media_types: dict[str, int] = {}
        for _display_source, _display_dest, full_path in preview_data:
            ext = os.path.splitext(full_path)[1].lower()
            media_type = None
            for type_name, extensions in self.app.settings.supported_extensions.items():
                if ext in extensions:
                    media_type = type_name
                    break
            if media_type:
                media_types[media_type] = media_types.get(media_type, 0) + 1

        type_counts = ", ".join(
            f"{type_count} {media_type}" for media_type, type_count in media_types.items()
        )
        self.app.status_var.set(f"Preview generated for {len(preview_data)} files.")
        self.app.file_var.set(f"Found: {type_counts}")

    def filter_by_selected_extensions(self) -> None:
        if not self.full_preview_data:
            return
        selected_extensions = self.app._get_selected_extensions()
        filtered = [
            (src, dest, path)
            for src, dest, path in self.full_preview_data
            if os.path.splitext(path)[1].lower() in selected_extensions
        ]
        self.display(filtered, len(filtered))

    def toggle_selection(self, event: tk.Event) -> None:
        assert self.preview_tree is not None
        if self.preview_tree.identify_region(event.x, event.y) != "cell":
            return

        item = self.preview_tree.identify_row(event.y)
        if not item:
            return

        column_index = int(self.preview_tree.identify_column(event.x).replace("#", "")) - 1
        if column_index != 0:
            return

        values = list(self.preview_tree.item(item, "values"))
        if values[0] == "☐":
            values[0] = "☑"
            self.preview_files[item]["selected"] = True
        else:
            values[0] = "☐"
            self.preview_files[item]["selected"] = False
        self.preview_tree.item(item, values=values)

    def select_all_files(self) -> None:
        assert self.preview_tree is not None
        for item in self.preview_tree.get_children():
            values = list(self.preview_tree.item(item, "values"))
            values[0] = "☑"
            self.preview_tree.item(item, values=values)
            self.preview_files[item]["selected"] = True

    def deselect_all_files(self) -> None:
        assert self.preview_tree is not None
        for item in self.preview_tree.get_children():
            values = list(self.preview_tree.item(item, "values"))
            values[0] = "☐"
            self.preview_tree.item(item, values=values)
            self.preview_files[item]["selected"] = False

    def set_processing_state(self, is_processing: bool) -> None:
        assert self.preview_tree is not None and self.preview_button_frame is not None
        button_state = tk.DISABLED if is_processing else tk.NORMAL
        for widget in self.preview_button_frame.winfo_children():
            if isinstance(widget, ttk.Button):
                widget.config(state=button_state)
        self.preview_tree.config(selectmode="none" if is_processing else "extended")
