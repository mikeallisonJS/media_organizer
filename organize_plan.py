#!/usr/bin/env python3
"""
Headless source scan and destination path planning for Archimedius.

Preview and organize runs share this module for recursive source scan rules
and template-based destination path resolution.
"""

from __future__ import annotations

import logging
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Literal, Mapping, Sequence

import defaults
from destination_path import resolve_destination_path
from metadata_extract import detect_media_type, extract_metadata

logger = logging.getLogger("Archimedius")

MetadataExtractor = Callable[
    [Path, Mapping[str, Sequence[str]]],
    tuple[str, dict],
]
DestinationPathResolver = Callable[[dict, str, str, bool], str]


@dataclass(frozen=True)
class FilePlan:
    """A planned organize operation for one file."""

    source_path: Path
    destination_path: str
    media_type: str


CollisionAction = Literal["rename", "overwrite", "skip"]
CollisionResolver = Callable[[FilePlan, Path], CollisionAction]


@dataclass(frozen=True)
class ScanResult:
    """Outcome of scanning a source and building file plans."""

    plans: list[FilePlan]
    total_count: int


def all_supported_extensions(supported_extensions: Mapping[str, Sequence[str]]) -> set[str]:
    """Return the union of every configured extension (lowercase, with dot)."""
    extensions: set[str] = set()
    for extension_list in supported_extensions.values():
        extensions.update(ext.lower() for ext in extension_list)
    return extensions


def normalize_selected_extensions(selected_extensions: Iterable[str]) -> set[str]:
    """Normalize extension strings for comparison."""
    return {ext.lower() for ext in selected_extensions}


def _validate_source_path(source_path: Path) -> None:
    if not source_path.exists():
        raise ValueError(f"Source path does not exist: {source_path}")
    if not source_path.is_dir():
        raise ValueError(f"Source path is not a directory: {source_path}")


def _validate_destination_path(destination_path: Path | None) -> None:
    if destination_path is None:
        return
    if destination_path.exists() and not destination_path.is_dir():
        raise ValueError(f"Destination path is not a directory: {destination_path}")


def _validate_scan_inputs(
    supported_extensions: Mapping[str, Sequence[str]],
    selected_extensions: Iterable[str],
    max_files: int | None,
) -> set[str]:
    if not supported_extensions:
        raise ValueError("supported_extensions cannot be empty")

    selected = normalize_selected_extensions(selected_extensions)
    if not selected:
        raise ValueError("selected_extensions cannot be empty")

    if max_files is not None and max_files < 0:
        raise ValueError("max_files must be zero or greater")

    return selected


def is_recognized_extension(
    suffix: str, supported_extensions: Mapping[str, Sequence[str]]
) -> bool:
    """Return True when the suffix belongs to a configured media type."""
    return suffix.lower() in all_supported_extensions(supported_extensions)


def is_destination_inside_source(source: Path, destination: Path | None) -> bool:
    """Return True when destination is a strict subdirectory of source."""
    if destination is None:
        return False

    try:
        abs_source = source.resolve()
        abs_destination = destination.resolve()
        if abs_destination == abs_source:
            return False
        abs_destination.relative_to(abs_source)
        return True
    except (ValueError, OSError):
        return False


def should_skip_file_under_destination(
    file_path: Path,
    source: Path,
    destination: Path,
    *,
    dest_in_source: bool,
) -> bool:
    """Return True when a file lives under the destination tree inside source."""
    if not dest_in_source:
        return False

    try:
        if not file_path.is_file():
            return False
        return file_path.is_relative_to(destination)
    except (PermissionError, OSError, ValueError):
        return False


def iter_matching_files(
    source: Path,
    *,
    selected_extensions: Iterable[str],
    supported_extensions: Mapping[str, Sequence[str]],
    destination: Path | None = None,
) -> list[Path]:
    """
    Recursively scan source and return matching file paths in walk order.

    Files are skipped when:
    - not a regular file
    - extension is not in selected_extensions
    - extension is unrecognized (not in supported_extensions)
    - file is under destination while destination is inside source
    """
    _validate_source_path(source)
    _validate_destination_path(destination)

    selected = _validate_scan_inputs(supported_extensions, selected_extensions, max_files=None)
    recognized = all_supported_extensions(supported_extensions)
    dest_in_source = is_destination_inside_source(source, destination)
    matches: list[Path] = []

    for file_path in source.rglob("*"):
        try:
            if not file_path.is_file():
                continue

            suffix = file_path.suffix.lower()
            if suffix not in selected:
                continue

            if suffix not in recognized:
                continue

            if destination is not None and should_skip_file_under_destination(
                file_path,
                source,
                destination,
                dest_in_source=dest_in_source,
            ):
                continue

            matches.append(file_path)
        except (PermissionError, OSError) as exc:
            logger.debug("Skipping inaccessible path during scan: %s (%s)", file_path, exc)
            continue

    return matches


def default_metadata_extractor(
    file_path: Path,
    supported_extensions: Mapping[str, Sequence[str]],
) -> tuple[str, dict]:
    """Extract media type and metadata for organize-plan path building."""
    media_type = detect_media_type(file_path, supported_extensions)
    metadata = extract_metadata(
        file_path,
        media_type=media_type,
        supported_extensions=supported_extensions,
    )
    return media_type, metadata


def build_file_plan(
    file_path: Path,
    *,
    templates: Mapping[str, str],
    supported_extensions: Mapping[str, Sequence[str]],
    exclude_unknown: Mapping[str, bool],
    metadata_extractor: MetadataExtractor = default_metadata_extractor,
    path_resolver: DestinationPathResolver = resolve_destination_path,
) -> FilePlan:
    """Build a destination path plan for a single source file."""
    media_type, metadata = metadata_extractor(file_path, supported_extensions)
    template = templates.get(media_type, templates.get("audio", "{filename}"))
    exclude = exclude_unknown.get(media_type, False)
    destination_path = path_resolver(
        metadata,
        media_type,
        template,
        exclude_unknown=exclude,
    )

    return FilePlan(
        source_path=file_path,
        destination_path=destination_path,
        media_type=media_type,
    )


def scan_source(
    source: str | Path,
    destination: str | Path | None,
    templates: Mapping[str, str],
    supported_extensions: Mapping[str, Sequence[str]],
    selected_extensions: Iterable[str],
    exclude_unknown: Mapping[str, bool],
    *,
    max_files: int | None = None,
    metadata_extractor: MetadataExtractor = default_metadata_extractor,
    path_resolver: DestinationPathResolver = resolve_destination_path,
) -> ScanResult:
    """
    Scan source and produce file plans with computed destination paths.

    Args:
        source: Root folder to scan recursively.
        destination: Destination root (used to skip files already organized there).
        templates: Per-media-type path templates.
        supported_extensions: Full extension lists by media type.
        selected_extensions: Subset of extensions to include in this run.
        exclude_unknown: Per-media-type exclude-unknown flags.
        max_files: Optional cap on returned plans (total_count is still complete).
        metadata_extractor: Injectable metadata extraction hook for tests.
        path_resolver: Injectable destination path resolver for tests.

    Returns:
        ScanResult with plans (possibly limited) and total matching file count.
    """
    source_path = Path(source)
    destination_path = Path(destination) if destination else None

    _validate_source_path(source_path)
    _validate_destination_path(destination_path)
    _validate_scan_inputs(supported_extensions, selected_extensions, max_files)

    matching_files = iter_matching_files(
        source_path,
        selected_extensions=selected_extensions,
        supported_extensions=supported_extensions,
        destination=destination_path,
    )

    total_count = len(matching_files)
    if max_files is not None:
        matching_files = matching_files[:max_files]

    plans = [
        build_file_plan(
            file_path,
            templates=templates,
            supported_extensions=supported_extensions,
            exclude_unknown=exclude_unknown,
            metadata_extractor=metadata_extractor,
            path_resolver=path_resolver,
        )
        for file_path in matching_files
    ]

    return ScanResult(plans=plans, total_count=total_count)


@dataclass(frozen=True)
class PlanTransferOutcome:
    """Result of transferring one planned file."""

    plan: FilePlan
    destination_path: Path | None
    error: str | None = None
    skipped: bool = False

    @property
    def success(self) -> bool:
        return self.error is None and self.destination_path is not None and not self.skipped


@dataclass(frozen=True)
class OrganizeResult:
    """Result of executing one or more file plans."""

    outcomes: list[PlanTransferOutcome]
    stopped_early: bool = False

    @property
    def attempted(self) -> int:
        return len(self.outcomes)

    @property
    def successful(self) -> int:
        return sum(1 for outcome in self.outcomes if outcome.success)


def build_plans_for_paths(
    source_paths: Iterable[str | Path],
    *,
    templates: Mapping[str, str],
    supported_extensions: Mapping[str, Sequence[str]],
    exclude_unknown: Mapping[str, bool],
    metadata_extractor: MetadataExtractor = default_metadata_extractor,
    path_resolver: DestinationPathResolver = resolve_destination_path,
) -> list[FilePlan]:
    """Build destination path plans for explicit source file paths."""
    return [
        build_file_plan(
            Path(source_path),
            templates=templates,
            supported_extensions=supported_extensions,
            exclude_unknown=exclude_unknown,
            metadata_extractor=metadata_extractor,
            path_resolver=path_resolver,
        )
        for source_path in source_paths
    ]


def destination_path_is_occupied(
    destination_path: Path,
    occupied_paths: set[Path],
) -> bool:
    """Return True when a destination path already exists on disk or in the run."""
    try:
        resolved = destination_path.resolve()
    except OSError:
        resolved = destination_path
    return resolved in occupied_paths or destination_path.exists()


def find_unique_destination_path(
    destination_path: Path,
    occupied_paths: set[Path],
) -> Path:
    """Return a non-colliding path by appending (1), (2), ... before the extension."""
    if not destination_path_is_occupied(destination_path, occupied_paths):
        return destination_path

    stem = destination_path.stem
    suffix = destination_path.suffix
    parent = destination_path.parent
    counter = 1

    while True:
        candidate = parent / f"{stem} ({counter}){suffix}"
        if not destination_path_is_occupied(candidate, occupied_paths):
            return candidate
        counter += 1


def resolve_collision_action(
    policy: str,
    *,
    collision_resolver: CollisionResolver | None = None,
    plan: FilePlan | None = None,
    destination_path: Path | None = None,
) -> CollisionAction:
    """Map a collision policy (and optional resolver) to a concrete action."""
    normalized = policy if policy in defaults.COLLISION_POLICIES else defaults.DEFAULT_SETTINGS["collision_policy"]

    if normalized == defaults.COLLISION_POLICY_PROMPT:
        if collision_resolver is None or plan is None or destination_path is None:
            return "rename"
        return collision_resolver(plan, destination_path)

    if normalized == defaults.COLLISION_POLICY_RENAME:
        return "rename"
    if normalized == defaults.COLLISION_POLICY_OVERWRITE:
        return "overwrite"
    return "skip"


def resolve_transfer_destination(
    destination_path: Path,
    *,
    policy: str,
    occupied_paths: set[Path],
    collision_resolver: CollisionResolver | None = None,
    plan: FilePlan | None = None,
) -> tuple[Path | None, CollisionAction | None]:
    """
    Resolve the destination path for a planned transfer.

    Returns (path, action). path is None when the file should be skipped.
    action is None when no collision occurred.
    """
    if not destination_path_is_occupied(destination_path, occupied_paths):
        return destination_path, None

    action = resolve_collision_action(
        policy,
        collision_resolver=collision_resolver,
        plan=plan,
        destination_path=destination_path,
    )

    if action == "skip":
        return None, action
    if action == "overwrite":
        return destination_path, action
    return find_unique_destination_path(destination_path, occupied_paths), action


def transfer_plan(
    plan: FilePlan,
    output_root: str | Path,
    operation_mode: str,
    *,
    destination_path: Path | None = None,
) -> Path:
    """
    Copy or move one planned file under output_root.

    Returns the absolute destination path written.
    """
    if operation_mode not in ("copy", "move"):
        raise ValueError("operation_mode must be 'copy' or 'move'")

    source_path = plan.source_path
    if destination_path is None:
        destination_path = Path(output_root) / plan.destination_path

    if not source_path.is_file():
        raise FileNotFoundError(f"Source file does not exist: {source_path}")

    destination_path.parent.mkdir(parents=True, exist_ok=True)

    if operation_mode == "copy":
        shutil.copy2(source_path, destination_path)
    else:
        shutil.move(source_path, destination_path)

    return destination_path


def execute_plans(
    plans: Sequence[FilePlan],
    output_root: str | Path,
    *,
    operation_mode: str,
    collision_policy: str = defaults.DEFAULT_SETTINGS["collision_policy"],
    collision_resolver: CollisionResolver | None = None,
    should_stop: Callable[[], bool] | None = None,
    on_each: Callable[[FilePlan, PlanTransferOutcome], None] | None = None,
) -> OrganizeResult:
    """Execute copy or move for each plan, continuing after per-file errors."""
    outcomes: list[PlanTransferOutcome] = []
    stopped_early = False
    occupied_paths: set[Path] = set()

    for plan in plans:
        if should_stop and should_stop():
            stopped_early = True
            break

        try:
            planned_destination = Path(output_root) / plan.destination_path
            resolved_destination, _action = resolve_transfer_destination(
                planned_destination,
                policy=collision_policy,
                occupied_paths=occupied_paths,
                collision_resolver=collision_resolver,
                plan=plan,
            )

            if resolved_destination is None:
                outcome = PlanTransferOutcome(plan, None, skipped=True)
            else:
                destination_path = transfer_plan(
                    plan,
                    output_root,
                    operation_mode,
                    destination_path=resolved_destination,
                )
                try:
                    occupied_paths.add(destination_path.resolve())
                except OSError:
                    occupied_paths.add(destination_path)
                outcome = PlanTransferOutcome(plan, destination_path)
        except (OSError, ValueError) as exc:
            outcome = PlanTransferOutcome(plan, None, str(exc))

        outcomes.append(outcome)
        if on_each is not None:
            on_each(plan, outcome)

    return OrganizeResult(outcomes=outcomes, stopped_early=stopped_early)
