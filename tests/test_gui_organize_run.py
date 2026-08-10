#!/usr/bin/env python3
"""
Tests that both GUI Organize entry points share one run path.

"Copy/Move All" (source scan) and "Copy/Move Selected" (preview selection)
must both build an OrganizeRequest and hand it to the same organize-run
module, differing only in whether the request carries selected paths.
"""

from pathlib import Path
from types import SimpleNamespace

import pytest

import defaults
from organize_run import OrganizeRequest, OrganizeRunResult


# The ``gui`` fixture is provided by tests/conftest.py.


@pytest.fixture()
def wired(gui, tmp_path, monkeypatch):
    """A GUI pointed at real directories, with runs and settings saves intercepted."""
    source = tmp_path / "source"
    source.mkdir()
    output = tmp_path / "output"

    gui.source_entry.delete(0, "end")
    gui.source_entry.insert(0, str(source))
    gui.output_entry.delete(0, "end")
    gui.output_entry.insert(0, str(output))

    monkeypatch.setattr(gui, "_save_settings", lambda: None)

    started = []
    monkeypatch.setattr(gui, "_begin_organize_run", lambda request: started.append(request))

    return SimpleNamespace(gui=gui, source=source, output=output, started=started)


def select_preview_files(wired, *full_paths):
    """Populate the preview panel with selected rows for the given paths."""
    wired.gui.preview_panel.preview_files = {
        f"row{index}": {"full_path": str(path), "selected": True}
        for index, path in enumerate(full_paths)
    }


def test_copy_all_starts_a_source_scan_run(wired):
    wired.gui._start_organization("copy")

    (request,) = wired.started
    assert isinstance(request, OrganizeRequest)
    assert request.is_selection_run is False
    assert request.operation_mode == "copy"
    assert Path(request.source_dir) == wired.source
    assert request.selected_extensions


def test_copy_selected_starts_a_selection_run(wired):
    chosen = wired.source / "a.mp3"
    chosen.write_text("audio")
    select_preview_files(wired, chosen)

    wired.gui._process_selected_files("copy")

    (request,) = wired.started
    assert isinstance(request, OrganizeRequest)
    assert request.is_selection_run is True
    assert request.selected_paths == [str(chosen)]


def test_both_entry_points_build_the_same_request_apart_from_selection(wired):
    chosen = wired.source / "a.mp3"
    chosen.write_text("audio")
    select_preview_files(wired, chosen)

    wired.gui._start_organization("copy")
    wired.gui._process_selected_files("copy")

    scan_request, selection_request = wired.started
    shared = ("source_dir", "destination_dir", "operation_mode", "templates", "collision_policy")
    for field_name in shared:
        assert getattr(scan_request, field_name) == getattr(selection_request, field_name)


def test_both_entry_points_create_the_output_directory(wired):
    chosen = wired.source / "a.mp3"
    chosen.write_text("audio")
    select_preview_files(wired, chosen)

    wired.gui._start_organization("copy")
    assert wired.output.is_dir()

    wired.output.rmdir()
    wired.gui._process_selected_files("copy")
    assert wired.output.is_dir()


def test_selection_run_with_nothing_selected_does_not_start(wired, monkeypatch):
    notices = []
    monkeypatch.setattr(
        "archimedius_gui.messagebox.showinfo", lambda *args, **kwargs: notices.append(args)
    )
    select_preview_files(wired)

    wired.gui._process_selected_files("copy")

    assert wired.started == []
    assert notices


def test_missing_source_directory_does_not_start_a_run(wired, monkeypatch):
    errors = []
    monkeypatch.setattr(
        "archimedius_gui.messagebox.showerror", lambda *args, **kwargs: errors.append(args)
    )
    wired.gui.source_entry.delete(0, "end")
    wired.gui.source_entry.insert(0, str(wired.source / "missing"))

    wired.gui._start_organization("copy")

    assert wired.started == []
    assert errors


def test_declining_the_move_confirmation_does_not_start_a_run(wired, monkeypatch):
    monkeypatch.setattr("archimedius_gui.messagebox.askyesno", lambda *args, **kwargs: False)

    wired.gui._start_organization("move")

    assert wired.started == []


def test_declining_the_move_confirmation_leaves_no_destination_directory(wired, monkeypatch):
    """The destination root is only created once the run is actually going ahead."""
    monkeypatch.setattr("archimedius_gui.messagebox.askyesno", lambda *args, **kwargs: False)

    wired.gui._start_organization("move")

    assert not wired.output.exists()


def test_move_confirmation_for_a_selection_run_names_the_file_count(wired, monkeypatch):
    chosen = wired.source / "a.mp3"
    chosen.write_text("audio")
    select_preview_files(wired, chosen)

    asked = []

    def fake_askyesno(title, message, **kwargs):
        asked.append(message)
        return True

    monkeypatch.setattr("archimedius_gui.messagebox.askyesno", fake_askyesno)

    wired.gui._process_selected_files("move")

    assert "Moving 1 files" in asked[0]
    assert wired.started


def test_request_carries_the_configured_collision_policy(wired):
    wired.gui.collision_policy = defaults.COLLISION_POLICY_RENAME

    wired.gui._start_organization("copy")

    (request,) = wired.started
    assert request.collision_policy == defaults.COLLISION_POLICY_RENAME


def finish_run(wired, monkeypatch, *, stopped_early, mode="copy", successful=0):
    """Drive the completion handler and return the (title, message) dialog shown."""
    shown = []
    monkeypatch.setattr(
        "archimedius_gui.messagebox.showinfo",
        lambda title, message, **kwargs: shown.append((title, message)),
    )
    outcomes = [SimpleNamespace(success=True)] * successful
    result = OrganizeRunResult(outcomes=outcomes, total_count=3, stopped_early=stopped_early)

    wired.gui._organize_run_complete(wired.gui._build_organize_request(mode), result)

    return shown[0]


def test_finished_run_reports_completion(wired, monkeypatch):
    title, message = finish_run(wired, monkeypatch, stopped_early=False, successful=3)

    assert title == "Complete"
    assert "Organization complete!" in message
    assert "Copied 3 files" in message


def test_stopped_run_is_not_reported_as_complete(wired, monkeypatch):
    """Stop ends a run early, so its partial counts must not read as a finished run."""
    title, message = finish_run(wired, monkeypatch, stopped_early=True, successful=1)

    assert title == "Stopped"
    assert "Organization complete!" not in message
    assert "Organization stopped." in message
    assert "Copied 1 files" in message
    assert wired.gui.file_var.get() == "Organization stopped."


def test_prompt_policy_supplies_a_collision_resolver(wired):
    assert wired.gui._collision_resolver_for_policy(defaults.COLLISION_POLICY_PROMPT) is not None
    assert wired.gui._collision_resolver_for_policy(defaults.COLLISION_POLICY_SKIP) is None
