#!/usr/bin/env python3
"""
Unit tests for core Archimedius behavior.
"""

import pytest

from archimedius import Archimedius


def test_template_management_updates_expected_media_type():
    organizer = Archimedius()
    original_video_template = organizer.get_template("video")

    organizer.set_template("Music/{artist}/{album}/{filename}", media_type="audio")

    assert organizer.get_template("audio") == "Music/{artist}/{album}/{filename}"
    assert organizer.template == "Music/{artist}/{album}/{filename}"
    assert organizer.get_template("video") == original_video_template


def test_setting_template_without_media_type_updates_audio_for_compatibility():
    organizer = Archimedius()

    organizer.set_template("{genre}/{filename}")

    assert organizer.template == "{genre}/{filename}"
    assert organizer.get_template("audio") == "{genre}/{filename}"


def test_get_template_falls_back_to_audio_template_for_unknown_type():
    organizer = Archimedius()
    organizer.set_template("Fallback/{filename}", media_type="audio")

    assert organizer.get_template("not-a-real-type") == "Fallback/{filename}"


def test_set_operation_mode_accepts_only_copy_or_move():
    organizer = Archimedius()
    organizer.set_operation_mode("move")
    assert organizer.operation_mode == "move"

    organizer.set_operation_mode("copy")
    assert organizer.operation_mode == "copy"

    with pytest.raises(ValueError, match="Operation mode must be 'copy' or 'move'"):
        organizer.set_operation_mode("delete")


def test_stop_sets_stop_requested_flag():
    organizer = Archimedius()
    assert organizer.stop_requested is False

    organizer.stop()

    assert organizer.stop_requested is True
