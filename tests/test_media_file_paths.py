#!/usr/bin/env python3
"""
Unit tests for MediaFile type detection and path formatting behavior.
"""

import os

import extensions
from media_file import MediaFile


def test_detects_file_type_case_insensitive_extension():
    media = MediaFile("Track.MP3", extensions.DEFAULT_EXTENSIONS)

    assert media.file_type == "audio"
    assert media.metadata["extension"] == "mp3"
    assert media.metadata["filename_with_extension"] == "Track.MP3"


def test_unknown_extension_maps_to_unknown_type():
    media = MediaFile("notes.xyz", extensions.DEFAULT_EXTENSIONS)

    assert media.file_type == "unknown"
    assert media.metadata["filename"] == "notes"


def test_get_formatted_path_sanitizes_reserved_characters_in_metadata():
    media = MediaFile("song.mp3", extensions.DEFAULT_EXTENSIONS)
    media.file_type = "audio"
    media.metadata.update(
        {
            "artist": 'AC/DC:Live*Band?',
            "title": 'Hit<>:"Song"|',
            "filename_with_extension": "song.mp3",
            "extension": "mp3",
        }
    )

    formatted = media.get_formatted_path("{artist}/{title}")

    assert "AC_DC_Live_Band_" in formatted
    assert "Hit____Song__" in formatted
    assert formatted.endswith(os.path.join("Hit____Song__", "song.mp3"))


def test_get_formatted_path_exclude_unknown_removes_unknown_segments():
    media = MediaFile("cover.jpg", extensions.DEFAULT_EXTENSIONS)
    media.file_type = "image"
    media.metadata.update(
        {
            "filename_with_extension": "cover.jpg",
            "extension": "jpg",
        }
    )

    formatted = media.get_formatted_path("{camera_make}/{camera_model}", exclude_unknown=True)

    assert "Unknown" not in formatted
    assert formatted == os.path.join("image", "cover.jpg")


def test_get_formatted_path_adds_extension_when_template_has_filename_only():
    media = MediaFile("clip.mp4", extensions.DEFAULT_EXTENSIONS)
    media.metadata.update({"filename": "clip", "extension": "mp4"})

    formatted = media.get_formatted_path("{filename}")

    assert formatted == "clip.mp4"
