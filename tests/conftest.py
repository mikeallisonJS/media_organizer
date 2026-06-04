"""Ensure project root is importable during test collection."""

import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
root_str = str(ROOT)
if root_str not in sys.path:
    sys.path.insert(0, root_str)


@pytest.fixture(scope="session")
def tk_root():
    """A single hidden Tk root shared across the whole test session.

    Creating and destroying multiple Tk interpreters within one process can
    fail to re-initialize the Tcl/Tk library on some platforms, so GUI tests
    must share this one root rather than each spinning up their own.
    """
    import tkinter as tk

    root = tk.Tk()
    root.withdraw()
    yield root
    root.destroy()


@pytest.fixture()
def gui(tk_root):
    """A fresh ArchimediusGUI on the shared session root, isolated per test.

    Because the Tk root lives for the whole session, each test's widget tree
    and any pending ``after`` debounce timers would otherwise pile up on it.
    Teardown cancels the known debounce timers and destroys the widgets so the
    next test starts from a clean root.
    """
    import tkinter as tk
    from unittest.mock import patch

    with patch("archimedius_gui.ArchimediusGUI._load_settings"):
        from archimedius_gui import ArchimediusGUI

        app = ArchimediusGUI(tk_root)
    try:
        yield app
    finally:
        for timer_attr in ("_preview_timer", "_template_timer"):
            timer = getattr(app, timer_attr, None)
            if timer is not None:
                try:
                    tk_root.after_cancel(timer)
                except tk.TclError:
                    pass
        for child in tk_root.winfo_children():
            child.destroy()


def write_minimal_epub(epub_path: Path) -> None:
    """Write a minimal valid EPUB zip for metadata extraction tests."""
    container_xml = """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>"""
    content_opf = """<?xml version="1.0"?>
<package xmlns="http://www.idpf.org/2007/opf" version="2.0">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>Sample Book</dc:title>
    <dc:creator>Jane Author</dc:creator>
    <dc:date>2022-01-01</dc:date>
    <dc:publisher>Test Press</dc:publisher>
    <dc:language>en</dc:language>
  </metadata>
</package>"""

    with zipfile.ZipFile(epub_path, "w") as epub:
        epub.writestr("META-INF/container.xml", container_xml)
        epub.writestr("content.opf", content_opf)
