import pytest
import os
from mp3chaps2.mp3chaps import (
    to_milliseconds,
    parse_chapters_file,
    Chapter,
    TimeFormatError,
    ChapterFileError,
)


# Fixtures
@pytest.fixture
def test_data_dir():
    """Return path to test data directory."""
    return os.path.join(os.path.dirname(__file__), "test_data")


@pytest.fixture
def simple_mp3(tmp_path, test_data_dir):
    """Create a test MP3 file with simple chapters."""
    mp3_path = tmp_path / "simple.mp3"
    mp3_path.write_text("")  # Create empty MP3 file
    chapters_path = tmp_path / "simple.chapters.txt"

    # Read content from the actual test file
    with open(os.path.join(test_data_dir, "simple.chapters.txt"), "r") as f:
        content = f.read()
    chapters_path.write_text(content)
    return str(mp3_path)


@pytest.fixture
def out_of_order_mp3(tmp_path, test_data_dir):
    """Create a test MP3 file with out-of-order chapters."""
    mp3_path = tmp_path / "out_of_order.mp3"
    mp3_path.write_text("")
    chapters_path = tmp_path / "out_of_order.chapters.txt"

    # Read content from the actual test file
    with open(os.path.join(test_data_dir, "out_of_order.chapters.txt"), "r") as f:
        content = f.read()
    chapters_path.write_text(content)
    return str(mp3_path)


@pytest.fixture
def invalid_format_mp3(tmp_path, test_data_dir):
    """Create a test MP3 file with invalid format chapters."""
    mp3_path = tmp_path / "invalid.mp3"
    mp3_path.write_text("")
    chapters_path = tmp_path / "invalid.chapters.txt"

    # Read content from the actual test file
    with open(os.path.join(test_data_dir, "empty_lines.chapters.txt"), "r") as f:
        content = f.read()
    chapters_path.write_text(content)
    return str(mp3_path)


# Time conversion tests
@pytest.mark.parametrize(
    ["time_str", "expected"],
    [
        ("00:00:00.000", 0),
        ("01:00:00.000", 3600000),
        ("00:01:00.000", 60000),
        ("00:00:01.000", 1000),
        ("00:00:00.500", 500),
        ("01:23:45.678", 5025678),
    ],
)
def test_to_milliseconds(time_str, expected):
    assert to_milliseconds(time_str) == expected


def test_to_milliseconds_completely_invalid_format():
    with pytest.raises(TimeFormatError, match="Invalid time format"):
        to_milliseconds("invalid")


def test_to_milliseconds_wrong_format():
    with pytest.raises(TimeFormatError, match="Invalid time format"):
        to_milliseconds("1:2:3")


def test_to_milliseconds_invalid_hours():
    with pytest.raises(TimeFormatError, match="Expected format"):
        to_milliseconds("25:00:00")  # Valid but unsupported format


def test_to_milliseconds_invalid_hours_correct_format():
    with pytest.raises(TimeFormatError, match="Hours must be between"):
        to_milliseconds("25:00:00.000")


def test_to_milliseconds_no_colons():
    with pytest.raises(TimeFormatError):
        to_milliseconds("000000")


def test_to_milliseconds_empty_string():
    with pytest.raises(TimeFormatError):
        to_milliseconds("")


def test_to_milliseconds_none():
    with pytest.raises(TimeFormatError):
        to_milliseconds(None)  # Type error should be converted to TimeFormatError


# Chapter parsing tests
def test_parse_simple_chapters(simple_mp3):
    chapters = parse_chapters_file(simple_mp3)
    assert len(chapters) == 4
    assert chapters[0] == Chapter(start_time=0, title="Introduction")
    assert chapters[1] == Chapter(start_time=150000, title="Getting Started")  # 2:30
    assert chapters[2] == Chapter(start_time=345500, title="Main Content")  # 5:45.5
    assert chapters[3] == Chapter(start_time=900000, title="Conclusion")  # 15:00


def test_parse_out_of_order_chapters(out_of_order_mp3):
    chapters = parse_chapters_file(out_of_order_mp3)
    # Verify chapters are returned in file order (not automatically sorted)
    assert len(chapters) == 5
    assert chapters[0].title == "Welcome to the Show"
    assert chapters[1].title == "Behind the Scenes Stories"
    assert chapters[2].title == "Deep Dive into Complex Topics"
    assert chapters[3].title == "Q&A Session with Special Guest"
    assert chapters[4].title == "Wrap Up and Credits"


def test_parse_empty_lines(invalid_format_mp3):
    chapters = parse_chapters_file(invalid_format_mp3)
    assert len(chapters) == 4  # Should skip empty lines
    assert chapters[0].title == "Introduction"
    assert chapters[1].title == "Getting Started"
    assert chapters[2].title == "Main Content"
    assert chapters[3].title == "Conclusion"


def test_missing_chapters_file(tmp_path):
    mp3_path = tmp_path / "missing.mp3"
    mp3_path.write_text("")
    with pytest.raises(ChapterFileError, match="Chapters file not found"):
        parse_chapters_file(str(mp3_path))


def test_empty_chapters_file(tmp_path):
    mp3_path = tmp_path / "empty.mp3"
    mp3_path.write_text("")
    chapters_path = tmp_path / "empty.chapters.txt"
    chapters_path.write_text("")

    with pytest.raises(ChapterFileError, match="Chapter file is empty"):
        parse_chapters_file(str(mp3_path))


def test_whitespace_only_chapters_file(tmp_path):
    mp3_path = tmp_path / "whitespace.mp3"
    mp3_path.write_text("")
    chapters_path = tmp_path / "whitespace.chapters.txt"
    chapters_path.write_text("   \n  \n\t  \n")

    with pytest.raises(ChapterFileError, match="Chapter file is empty"):
        parse_chapters_file(str(mp3_path))


def test_malformed_time_format(tmp_path):
    mp3_path = tmp_path / "malformed.mp3"
    mp3_path.write_text("")
    chapters_path = tmp_path / "malformed.chapters.txt"
    chapters_path.write_text("1:2:3 Invalid Time Format\n")

    with pytest.raises(ChapterFileError, match="Invalid time format"):
        parse_chapters_file(str(mp3_path))


def test_missing_chapter_title(tmp_path):
    mp3_path = tmp_path / "notitle.mp3"
    mp3_path.write_text("")
    chapters_path = tmp_path / "notitle.chapters.txt"
    chapters_path.write_text("00:00:00.000\n")

    with pytest.raises(ChapterFileError, match="Missing chapter title"):
        parse_chapters_file(str(mp3_path))


# Test handling of mixed valid and invalid lines
def test_mixed_valid_invalid_lines(tmp_path):
    mp3_path = tmp_path / "mixed.mp3"
    mp3_path.write_text("")
    chapters_path = tmp_path / "mixed.chapters.txt"
    content = """

00:00:00.000 Valid Chapter 1

00:05:00.000 Valid Chapter 2

"""
    chapters_path.write_text(content)

    chapters = parse_chapters_file(str(mp3_path))
    assert len(chapters) == 2
    assert chapters[0].title == "Valid Chapter 1"
    assert chapters[1].title == "Valid Chapter 2"
