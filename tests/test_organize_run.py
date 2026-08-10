#!/usr/bin/env python3
"""
Tests for the headless organize-run module.

The module owns validate -> plans -> execute -> progress for an Organize run,
whether the run covers a full source scan or an explicit list of paths chosen
in the Preview.
"""

from pathlib import Path

import pytest

import defaults
from organize_run import (
    OrganizeRequest,
    OrganizeRunError,
    OrganizeRunNotice,
    build_plans,
    prepare_destination_root,
    run_organize,
    validate_request,
)

SUPPORTED = {"audio": [".mp3"], "video": [".mp4"], "image": [".jpg"], "ebook": [".epub"]}
TEMPLATES = {
    "audio": "{filename}",
    "video": "{filename}",
    "image": "{filename}",
    "ebook": "{filename}",
}


def fake_extractor(file_path: Path, supported_extensions):
    """Deterministic metadata extraction that avoids real media parsing."""
    return "audio", {
        "filename": file_path.stem,
        "filename_with_extension": file_path.name,
        "extension": file_path.suffix.lower()[1:],
    }


def make_request(tmp_path: Path, **overrides) -> OrganizeRequest:
    source = overrides.pop("source_dir", None)
    output = overrides.pop("destination_dir", None)
    if source is None:
        source = tmp_path / "source"
        source.mkdir(exist_ok=True)
    if output is None:
        output = tmp_path / "output"

    fields = {
        "source_dir": str(source),
        "destination_dir": str(output),
        "operation_mode": "copy",
        "templates": TEMPLATES,
        "supported_extensions": SUPPORTED,
        "selected_extensions": [".mp3"],
        "exclude_unknown": {},
    }
    fields.update(overrides)
    return OrganizeRequest(**fields)


def write_files(source: Path, *names: str) -> list[Path]:
    paths = []
    for name in names:
        path = source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"content of {name}")
        paths.append(path)
    return paths


# --- request shape -----------------------------------------------------------


def test_request_without_selected_paths_is_a_source_scan_run(tmp_path: Path):
    assert make_request(tmp_path).is_selection_run is False


def test_request_with_selected_paths_is_a_selection_run(tmp_path: Path):
    request = make_request(tmp_path, selected_paths=[tmp_path / "source" / "a.mp3"])
    assert request.is_selection_run is True


def test_request_with_empty_selected_paths_is_still_a_selection_run(tmp_path: Path):
    assert make_request(tmp_path, selected_paths=[]).is_selection_run is True


def test_request_defaults_to_the_default_collision_policy(tmp_path: Path):
    assert make_request(tmp_path).collision_policy == defaults.DEFAULT_SETTINGS["collision_policy"]


# --- validation --------------------------------------------------------------


def test_validate_requires_source_directory(tmp_path: Path):
    request = make_request(tmp_path, source_dir="  ")
    with pytest.raises(OrganizeRunError, match="both source and output directories"):
        validate_request(request)


def test_validate_requires_output_directory(tmp_path: Path):
    request = make_request(tmp_path, destination_dir="")
    with pytest.raises(OrganizeRunError, match="both source and output directories"):
        validate_request(request)


def test_validate_requires_templates_for_all_media_types(tmp_path: Path):
    request = make_request(tmp_path, templates={**TEMPLATES, "video": ""})
    with pytest.raises(OrganizeRunError, match="templates for all media types"):
        validate_request(request)


def test_validate_requires_existing_source_directory(tmp_path: Path):
    request = make_request(tmp_path, source_dir=str(tmp_path / "nope"))
    with pytest.raises(OrganizeRunError, match="Source directory does not exist"):
        validate_request(request)


def test_validate_rejects_unknown_operation_mode(tmp_path: Path):
    request = make_request(tmp_path, operation_mode="teleport")
    with pytest.raises(OrganizeRunError, match="copy"):
        validate_request(request)


def test_validate_source_scan_run_requires_selected_extensions(tmp_path: Path):
    request = make_request(tmp_path, selected_extensions=[])
    with pytest.raises(OrganizeRunNotice, match="No file types selected"):
        validate_request(request)


def test_validate_selection_run_requires_selected_paths(tmp_path: Path):
    request = make_request(tmp_path, selected_paths=[])
    with pytest.raises(OrganizeRunNotice, match="No files selected"):
        validate_request(request)


def test_validate_selection_run_ignores_empty_selected_extensions(tmp_path: Path):
    """A selection run processes explicit paths, so extension checkboxes don't gate it."""
    source = tmp_path / "source"
    source.mkdir()
    (chosen,) = write_files(source, "a.mp3")
    request = make_request(tmp_path, selected_extensions=[], selected_paths=[chosen])
    validate_request(request)


def test_notice_is_a_run_error_so_callers_can_catch_one_type(tmp_path: Path):
    assert issubclass(OrganizeRunNotice, OrganizeRunError)


# --- output directory --------------------------------------------------------


def test_prepare_destination_root_creates_missing_directory(tmp_path: Path):
    output = tmp_path / "output" / "nested"
    prepare_destination_root(make_request(tmp_path, destination_dir=str(output)))
    assert output.is_dir()


def test_prepare_destination_root_raises_run_error_when_creation_fails(tmp_path: Path):
    blocker = tmp_path / "blocker"
    blocker.write_text("not a directory")
    request = make_request(tmp_path, destination_dir=str(blocker / "output"))
    with pytest.raises(OrganizeRunError, match="Failed to create output directory"):
        prepare_destination_root(request)


# --- planning ----------------------------------------------------------------


def test_build_plans_scans_the_source_for_a_source_scan_run(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    write_files(source, "a.mp3", "nested/b.mp3", "c.txt")

    result = build_plans(make_request(tmp_path), metadata_extractor=fake_extractor)

    assert result.total_count == 2
    assert {plan.source_path.name for plan in result.plans} == {"a.mp3", "b.mp3"}


def test_build_plans_uses_only_the_selected_paths_for_a_selection_run(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    chosen, _ignored = write_files(source, "a.mp3", "b.mp3")

    request = make_request(tmp_path, selected_paths=[str(chosen)])
    result = build_plans(request, metadata_extractor=fake_extractor)

    assert result.total_count == 1
    assert [plan.source_path.name for plan in result.plans] == ["a.mp3"]


# --- execution ---------------------------------------------------------------


def test_run_organize_copies_every_scanned_file(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    write_files(source, "a.mp3", "nested/b.mp3")

    result = run_organize(make_request(tmp_path), metadata_extractor=fake_extractor)

    assert result.total_count == 2
    assert result.attempted == 2
    assert result.successful == 2
    assert result.stopped_early is False
    assert (tmp_path / "output" / "a.mp3").is_file()
    assert (tmp_path / "output" / "b.mp3").is_file()
    assert (source / "a.mp3").is_file()


def test_run_organize_moves_files_in_move_mode(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    (moved,) = write_files(source, "a.mp3")

    result = run_organize(
        make_request(tmp_path, operation_mode="move"),
        metadata_extractor=fake_extractor,
    )

    assert result.successful == 1
    assert (tmp_path / "output" / "a.mp3").is_file()
    assert not moved.exists()


def test_run_organize_selection_run_leaves_unselected_files_alone(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    chosen, _ignored = write_files(source, "a.mp3", "b.mp3")

    result = run_organize(
        make_request(tmp_path, selected_paths=[str(chosen)]),
        metadata_extractor=fake_extractor,
    )

    assert result.attempted == 1
    assert (tmp_path / "output" / "a.mp3").is_file()
    assert not (tmp_path / "output" / "b.mp3").exists()


def test_run_organize_validates_before_touching_the_filesystem(tmp_path: Path):
    request = make_request(tmp_path, source_dir=str(tmp_path / "nope"))
    with pytest.raises(OrganizeRunError, match="Source directory does not exist"):
        run_organize(request, metadata_extractor=fake_extractor)
    assert not (tmp_path / "output").exists()


def test_run_organize_creates_the_destination_root_itself(tmp_path: Path):
    """A headless caller gets the destination root without preparing it first."""
    source = tmp_path / "source"
    source.mkdir()

    run_organize(make_request(tmp_path), metadata_extractor=fake_extractor)

    assert (tmp_path / "output").is_dir()


def test_run_organize_reports_progress_for_each_file(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    write_files(source, "a.mp3", "b.mp3")

    events = []
    run_organize(
        make_request(tmp_path),
        metadata_extractor=fake_extractor,
        on_progress=lambda processed, total, current: events.append((processed, total, current)),
    )

    assert [(processed, total) for processed, total, _ in events] == [(1, 2), (2, 2)]
    assert {Path(current).name for _, _, current in events} == {"a.mp3", "b.mp3"}


def test_run_organize_stops_early_when_asked(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    write_files(source, "a.mp3", "b.mp3", "c.mp3")

    processed_count = []

    def should_stop():
        return len(processed_count) >= 1

    result = run_organize(
        make_request(tmp_path),
        metadata_extractor=fake_extractor,
        should_stop=should_stop,
        on_progress=lambda *_: processed_count.append(1),
    )

    assert result.stopped_early is True
    assert result.attempted == 1
    assert result.total_count == 3


def test_run_organize_uses_the_injected_collision_resolver_under_prompt_policy(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    write_files(source, "a.mp3", "nested/a.mp3")

    prompted = []

    def resolver(plan, destination_path):
        prompted.append(destination_path)
        return "skip"

    result = run_organize(
        make_request(tmp_path, collision_policy=defaults.COLLISION_POLICY_PROMPT),
        metadata_extractor=fake_extractor,
        collision_resolver=resolver,
    )

    assert len(prompted) == 1
    assert result.attempted == 2
    assert result.successful == 1


def test_run_organize_renames_colliding_files_under_rename_policy(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    write_files(source, "a.mp3", "nested/a.mp3")

    result = run_organize(
        make_request(tmp_path, collision_policy=defaults.COLLISION_POLICY_RENAME),
        metadata_extractor=fake_extractor,
    )

    assert result.successful == 2
    assert (tmp_path / "output" / "a.mp3").is_file()
    assert (tmp_path / "output" / "a (1).mp3").is_file()


def test_run_organize_skips_colliding_files_under_skip_policy(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    write_files(source, "a.mp3", "nested/a.mp3")

    result = run_organize(
        make_request(tmp_path, collision_policy=defaults.COLLISION_POLICY_SKIP),
        metadata_extractor=fake_extractor,
    )

    assert result.attempted == 2
    assert result.successful == 1
    assert not (tmp_path / "output" / "a (1).mp3").exists()


def test_run_organize_keeps_going_after_a_per_file_error(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    missing = source / "gone.mp3"
    (present,) = write_files(source, "a.mp3")

    result = run_organize(
        make_request(tmp_path, selected_paths=[str(missing), str(present)]),
        metadata_extractor=fake_extractor,
    )

    assert result.attempted == 2
    assert result.successful == 1
    assert (tmp_path / "output" / "a.mp3").is_file()
