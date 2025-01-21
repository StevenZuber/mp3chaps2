# mp3chaps2

---

A robust command-line utility for managing chapter markers in MP3 files. This is an enhanced version of the original [mp3chaps](https://github.com/dskrad/mp3chaps) project, with improved error handling and reliability.

This utilizes the excellent [eyeD3](https://github.com/nicfit/eyeD3) tagging module to read and write chapter frames and title subframes.

## Features

- Add chapter markers from a text file
- List existing chapters
- Remove chapter markers
- Robust error handling and validation
- Compatible with podcast apps on Android and iOS

### Requirements

`Python >3.7`

### Installation

---

```bash
pip install mp3chaps2
```

### Usage

---

The tool looks for chapter marks in a companion .chapters.txt file. For example, if your audio file is `episode_42.mp3`, create `episode_42.chapters.txt` in the same directory:

```bash
00:00:00.000 Introduction
00:02:00.000 Main Topic Discussion
00:42:24.123 Closing Thoughts
```

If you run into errors, try using ASCII. There have been some issue with Unicode.

### Commands

```bash
# Add chapters (remove existing chapters first with -r for best results)
mp3chaps2 -i episode_42.mp3

# List existing chapters
mp3chaps2 -l episode_42.mp3

# Remove all chapters
mp3chaps2 -r episode_42.mp3
```

### Options

```bash
-h  Show help text
-l  List chapters in <filename>
-i  Import chapters from <filename>.chapters.txt
-r  Remove chapters from <filename>
```

### Development

---
If you want to modify this project locally, you can clone the repository and install the dependencies.

```bash
git clone https://github.com/StevenZuber/mp3chaps2.git
cd mp3chaps2
pip install -e .
```

Or you can install it with dependencies directly with:

```bash
pip install mp3chaps2[dev]
```

The `requirements.txt` file is also available for poeple who prefer that approach.

`pip install -r requirements.txt`

### License

MIT License
