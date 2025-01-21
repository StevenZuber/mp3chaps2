#!/usr/bin/env python3
"""
Usage:
  mp3chaps.py -h
  mp3chaps.py (-l | -i | -r) <filename>

Options:
  -h  Show this help text
  -l  List chapters in <filename>
  -i  Import chapters from <filename>.chapters.txt
  -r  Remove chapters from <filename>
"""

from dataclasses import dataclass
import logging
import os
import sys

from eyed3.id3 import Tag
from eyed3 import core
from docopt import docopt
import warnings


# Set up logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# ignore the warning from eye3d about the LAME tag. It's either because
# 1) The MP3 file wasn't originally encoded with LAME, but has a LAME tag
# (which sometimes happens when files are processed by different tools).
# Or more likely,
# 2) We're modifying the file's chapters, the modification is changing something
# that makes the original LAME CRC check fail. Either way, ignore.
warnings.filterwarnings("ignore", "Lame tag CRC check failed")


class MP3ChaptersError(Exception):
    """Base exception for MP3 chapters operations."""

    pass


class ChapterFileError(MP3ChaptersError):
    """Raised when there are issues with the chapters file."""

    pass


class TimeFormatError(MP3ChaptersError):
    """Raised when time format is invalid."""

    pass


class MP3FileError(MP3ChaptersError):
    """Raised when there are issues with the MP3 file."""

    pass


@dataclass
class Chapter:
    """Represents a single chapter with timing and title."""

    start_time: int  # milliseconds
    title: str


def to_milliseconds(time: str) -> int:
    """
    Convert time string to milliseconds.

    Args:
        time: Time string in format "HH:MM:SS.mmm"

    Returns:
        Integer representing milliseconds

    Raises:
        TimeFormatError: If time string is malformed
    """
    if not isinstance(time, str):
        raise TimeFormatError("Input must be a string")

    if not time.count(":") == 2:
        raise TimeFormatError(
            f"Invalid time format: {time}. Expected format: HH:MM:SS.mmm"
        )

    parts = time.split(":")

    # Validate format of each part
    if len(parts) != 3:
        raise TimeFormatError(
            f"Invalid time format: {time}. Expected format: HH:MM:SS.mmm"
        )

    # Validate that seconds part has the .mmm format
    if "." not in parts[2]:
        raise TimeFormatError(
            f"Invalid time format: {time}. Expected format: HH:MM:SS.mmm"
        )

    try:
        h = int(parts[0])  # Hours should be integers
        m = int(parts[1])  # Minutes should be integers
        s = float(parts[2])  # Seconds can have a decimal

        # Validate ranges
        if h < 0 or h >= 24:
            raise TimeFormatError("Hours must be between 0 and 23")
        if m < 0 or m >= 60:
            raise TimeFormatError("Minutes must be between 0 and 59")
        if s < 0 or s >= 60:
            raise TimeFormatError("Seconds must be between 0 and 59.999")

        return int(1000 * (s + m * 60 + h * 60 * 60))

    except ValueError:
        raise TimeFormatError(
            f"Invalid time format: {time}. Expected format: HH:MM:SS.mmm"
        )


def parse_chapters_file(fname: str) -> list[Chapter]:
    """
    Parse chapter information from a chapters file.

    Args:
        fname: Path to the MP3 file (will look for corresponding .chapters.txt)

    Returns:
        List of Chapter objects

    Raises:
        ChapterFileError: If file is missing or malformed
    """
    root, _ = os.path.splitext(fname)
    chapters_fname = f"{root}.chapters.txt"

    if not os.path.exists(chapters_fname):
        raise ChapterFileError(f"Chapters file not found: {chapters_fname}")

    # Check for empty file first
    try:
        with open(chapters_fname, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                raise ChapterFileError(
                    "Chapter file is empty or contains only whitespace"
                )
    except IOError as e:
        raise ChapterFileError(f"Error reading chapters file: {e}")

    chapters = []
    empty_lines = []

    try:
        with open(chapters_fname, "r", encoding="utf-8") as f:
            lines = f.readlines()

            # First pass: identify empty lines
            for line_num, line in enumerate(lines, 1):
                if not line.strip():
                    empty_lines.append(line_num)

            if empty_lines:
                empty_lines_str = ", ".join(str(x) for x in empty_lines)
                logger.warning(
                    f"Skipping empty lines at line number(s): {empty_lines_str}"
                )

            # Second pass: process valid lines
            valid_line_count = 0
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line:
                    continue

                valid_line_count += 1

                # Check for title first, outside of try block
                parts = line.split(maxsplit=1)
                if len(parts) < 2:
                    raise ChapterFileError(f"Missing chapter title on line {line_num}")

                try:
                    time_str, title = parts
                    start_time = to_milliseconds(time_str)
                    chapters.append(Chapter(start_time=start_time, title=title))
                    logger.debug(f"Parsed chapter: {title} at {time_str}")

                except TimeFormatError as e:
                    raise ChapterFileError(
                        f"Invalid time format on line {line_num}: {e}"
                    )
                except Exception as e:
                    raise ChapterFileError(
                        f"Error parsing line {line_num}: {line}"
                    ) from e

            logger.info(
                f"Successfully parsed {valid_line_count} chapters"
                + f" (skipped {len(empty_lines)} empty lines)"
                if empty_lines
                else ""
            )

    except IOError as e:
        raise ChapterFileError(f"Error reading chapters file: {e}")

    if not chapters:
        raise ChapterFileError("No valid chapters found in file")

    return chapters


def list_chaps(tag: Tag) -> None:
    """
    List all chapters in the tag.

    Args:
        tag: The ID3 tag containing chapters
    """
    if not tag.chapters:
        logger.info("No chapters found")
        return

    logger.info("Chapters:")
    for chap in tag.chapters:
        try:
            title = chap.sub_frames.get(b"TIT2")[0]._text
            logger.info(title)
        except (KeyError, IndexError, AttributeError):
            logger.warning(f"Chapter {chap.element_id} has invalid or missing title")


def remove_chaps(tag: Tag) -> None:
    """
    Remove all chapters from the tag and save.

    Args:
        tag: The ID3 tag containing chapters to remove
    """
    if not tag.chapters:
        logger.info("No chapters to remove")
        return

    chaps = [chap for chap in tag.chapters]
    for chap in chaps:
        try:
            title = chap.sub_frames.get(b"TIT2")[0]._text
            logger.info(f"Removing chapter: {title}")
            tag.chapters.remove(chap.element_id)
        except Exception as e:
            logger.warning(f"Error removing chapter {chap.element_id}: {e}")

    tag.save()
    logger.info("All chapters removed")


def add_chapters(tag: Tag, fname: str) -> None:
    """
    Add chapters to the tag from a chapters file.

    Args:
        tag: The ID3 tag to add chapters to
        fname: Path to the MP3 file

    Raises:
        MP3FileError: If there are issues with the MP3 file
    """
    try:
        chapters = parse_chapters_file(fname)
        if not chapters:
            logger.warning("No chapters found to add")
            return

        audio_file = core.load(fname)
        if not audio_file:
            raise MP3FileError("Failed to load MP3 file")

        total_length = audio_file.info.time_secs * 1000
        tag.setTextFrame(b"TLEN", str(int(total_length)))

        # Add chapters to tag
        child_ids = []
        for i, chapter in enumerate(chapters):
            element_id = f"ch{i}".encode()
            # For each chapter, find the next chapter's start time or use total_length
            next_start = (
                chapters[i + 1].start_time if i < len(chapters) - 1 else total_length
            )

            try:
                new_chap = tag.chapters.set(
                    element_id, (chapter.start_time, next_start)
                )
                new_chap.sub_frames.setTextFrame(b"TIT2", "{}".format(chapter.title))
                child_ids.append(element_id)
                logger.debug(f"Added chapter: {chapter.title}")
            except Exception as e:
                logger.error(f"Failed to add chapter {chapter.title}: {e}")

        tag.table_of_contents.set(b"toc", child_ids=child_ids)
        list_chaps(tag)
        tag.save()
        logger.info("Chapters added successfully")

    except Exception as e:
        raise MP3FileError(f"Error adding chapters: {e}")


def main():
    """Entry point for the script."""
    try:
        args = docopt(__doc__, version="mp3chaps 0.3")

        print(f"Filename: {args['<filename>']}")

        if not os.path.exists(args["<filename>"]):
            raise MP3FileError(f"MP3 file not found: {args['<filename>']}")

        tag = Tag()
        try:
            tag.parse(str(args["<filename>"]))
        except Exception as e:
            raise MP3FileError(f"Failed to parse MP3 file: {e}")

        if args["-l"]:
            print("Listing chapters")
            list_chaps(tag)
        elif args["-i"]:
            print("Inserting chapters")
            add_chapters(tag, args["<filename>"])
        elif args["-r"]:
            print("Removing chapters")
            remove_chaps(tag)

    except MP3ChaptersError as e:
        logger.error(str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
