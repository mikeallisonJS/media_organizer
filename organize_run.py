#!/usr/bin/env python3
"""
Headless Organize run orchestration for Archimedius.

One module owns the whole Organize run: validate the request, build file plans
(either from a full source scan or from an explicit list of paths selected in
the Preview), execute the transfers under the run's collision policy, and
report progress. The GUI supplies the request, a collision resolver, a stop
predicate, and a progress callback; everything else happens here so both
Organize entry points share one code path.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Mapping, Sequence

import defaults
from destination_path import resolve_destination_path
from organize_plan import (
    CollisionResolver,
    DestinationPathResolver,
    FilePlan,
    MetadataExtractor,
    PlanTransferOutcome,
    default_metadata_extractor,
    build_plans_for_paths,
    execute_plans,
    scan_source,
)

logger = logging.getLogger("Archimedius")

OPERATION_MODES = ("copy", "move")

ProgressReporter = Callable[[int, int, str], None]


class OrganizeRunError(ValueError):
    """A run cannot proceed. The message is safe to show the user."""


class OrganizeRunNotice(OrganizeRunError):
    """A run cannot proceed for a benign reason (nothing selected to organize)."""


@dataclass(frozen=True)
class OrganizeRequest:
    """Everything an Organize run needs, independent of the GUI."""

    source_dir: str | Path
    destination_dir: str | Path
    operation_mode: str
    templates: Mapping[str, str]
    supported_extensions: Mapping[str, Sequence[str]]
    selected_extensions: Sequence[str] = ()
    exclude_unknown: Mapping[str, bool] = field(default_factory=dict)
    selected_paths: Sequence[str | Path] | None = None
    collision_policy: str = defaults.DEFAULT_SETTINGS["collision_policy"]

    @property
    def is_selection_run(self) -> bool:
        """True when the run covers explicit paths chosen in the Preview."""
        return self.selected_paths is not None

    @property
    def source_path(self) -> Path:
        return Path(str(self.source_dir).strip())

    @property
    def destination_root(self) -> Path:
        return Path(str(self.destination_dir).strip())


@dataclass(frozen=True)
class RunPlan:
    """The file plans an Organize run will execute."""

    plans: list[FilePlan]
    total_count: int


@dataclass(frozen=True)
class OrganizeRunResult:
    """Outcome of a complete Organize run."""

    outcomes: list[PlanTransferOutcome]
    total_count: int
    stopped_early: bool = False

    @property
    def attempted(self) -> int:
        return len(self.outcomes)

    @property
    def successful(self) -> int:
        return sum(1 for outcome in self.outcomes if outcome.success)


def validate_request(request: OrganizeRequest) -> None:
    """
    Raise when the request cannot produce a run.

    Raises:
        OrganizeRunNotice: nothing was selected to organize.
        OrganizeRunError: the request is otherwise unusable.
    """
    if not str(request.source_dir).strip() or not str(request.destination_dir).strip():
        raise OrganizeRunError("Please select both source and output directories.")

    if not all(request.templates.values()):
        raise OrganizeRunError("Please provide templates for all media types.")

    if not request.source_path.exists():
        raise OrganizeRunError("Source directory does not exist.")

    if request.operation_mode not in OPERATION_MODES:
        raise OrganizeRunError("Operation mode must be 'copy' or 'move'.")

    if request.is_selection_run:
        if not request.selected_paths:
            raise OrganizeRunNotice("No files selected for processing.")
    elif not request.selected_extensions:
        raise OrganizeRunNotice("No file types selected. Please select at least one file type.")


def prepare_destination_root(request: OrganizeRequest) -> Path:
    """Create the destination root, raising a user-facing error on failure."""
    destination_root = request.destination_root
    try:
        destination_root.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise OrganizeRunError(f"Failed to create output directory: {exc}") from exc
    return destination_root


def build_plans(
    request: OrganizeRequest,
    *,
    metadata_extractor: MetadataExtractor = default_metadata_extractor,
    path_resolver: DestinationPathResolver = resolve_destination_path,
) -> RunPlan:
    """Build the file plans for a run: full source scan or selected paths."""
    if request.is_selection_run:
        plans = build_plans_for_paths(
            request.selected_paths or (),
            templates=request.templates,
            supported_extensions=request.supported_extensions,
            exclude_unknown=request.exclude_unknown,
            metadata_extractor=metadata_extractor,
            path_resolver=path_resolver,
        )
        return RunPlan(plans=plans, total_count=len(plans))

    scan_result = scan_source(
        request.source_path,
        request.destination_root,
        request.templates,
        request.supported_extensions,
        request.selected_extensions,
        request.exclude_unknown,
        metadata_extractor=metadata_extractor,
        path_resolver=path_resolver,
    )
    return RunPlan(plans=scan_result.plans, total_count=scan_result.total_count)


def _log_outcome(
    plan: FilePlan,
    outcome: PlanTransferOutcome,
    *,
    operation_mode: str,
    destination_root: Path,
) -> None:
    if outcome.success:
        logger.info(
            f"{operation_mode.capitalize()}d {plan.source_path} to {outcome.destination_path}"
        )
    elif outcome.skipped:
        logger.info(
            f"Skipped {plan.source_path} due to path collision at "
            f"{destination_root / plan.destination_path}"
        )
    else:
        logger.error(f"Error processing file {plan.source_path}: {outcome.error}")


def run_organize(
    request: OrganizeRequest,
    *,
    collision_resolver: CollisionResolver | None = None,
    should_stop: Callable[[], bool] | None = None,
    on_progress: ProgressReporter | None = None,
    metadata_extractor: MetadataExtractor = default_metadata_extractor,
    path_resolver: DestinationPathResolver = resolve_destination_path,
) -> OrganizeRunResult:
    """
    Validate, plan, and execute one Organize run.

    Args:
        request: The run to perform.
        collision_resolver: Called per path collision under the prompt policy.
        should_stop: Polled between files; True ends the run early.
        on_progress: Called after each file with (processed, total, source path).
        metadata_extractor: Injectable metadata extraction hook for tests.
        path_resolver: Injectable destination path resolver for tests.

    Raises:
        OrganizeRunError: the request is unusable (see :func:`validate_request`).
    """
    validate_request(request)
    destination_root = prepare_destination_root(request)

    run_plan = build_plans(
        request,
        metadata_extractor=metadata_extractor,
        path_resolver=path_resolver,
    )
    total_count = run_plan.total_count
    processed = 0

    def on_each(plan: FilePlan, outcome: PlanTransferOutcome) -> None:
        nonlocal processed
        _log_outcome(
            plan,
            outcome,
            operation_mode=request.operation_mode,
            destination_root=destination_root,
        )
        processed += 1
        if on_progress is not None:
            on_progress(processed, total_count, str(plan.source_path))

    organize_result = execute_plans(
        run_plan.plans,
        destination_root,
        operation_mode=request.operation_mode,
        collision_policy=request.collision_policy,
        collision_resolver=collision_resolver,
        should_stop=should_stop,
        on_each=on_each,
    )

    if organize_result.stopped_early:
        logger.info("Organization stopped by user")

    logger.info(
        f"{request.operation_mode.capitalize()} operation complete. "
        f"Processed {organize_result.successful} files successfully out of "
        f"{organize_result.attempted} attempted."
    )

    return OrganizeRunResult(
        outcomes=organize_result.outcomes,
        total_count=total_count,
        stopped_early=organize_result.stopped_early,
    )
