# Telegram Spotify Bio Monitor

> Automatically tracks the song currently playing in Spotify, downloads it as MP3, sends it to your Telegram Saved Messages, and saves it to your Telegram music library.

This project provides two platform-specific implementations:

- `windows.py` — Windows version using the Windows Global System Media Transport Controls API
- `linux.py` — Linux version using MPRIS2 via `playerctl`, with an optional direct D-Bus fallback

> **Note:** Despite the project name, the current implementation does not update your Telegram bio.  
> It currently syncs the currently playing Spotify track into Telegram as an audio file and saves it to your music library.

---

## Overview

The script runs in a loop and checks what Spotify is currently playing every few seconds. When it detects a new track, it searches for the song on YouTube using `yt-dlp`, downloads the audio as an MP3 file, writes proper ID3 metadata, sends the file to your Telegram **Saved Messages**, and then saves it into Telegram's built-in music section.

If playback stops or the track changes, the previously sent Telegram message is deleted automatically. This keeps your Saved Messages from filling up with outdated auto-uploaded tracks.

The project is essentially a small automation bridge between:

- Spotify track detection
- local file caching
- YouTube audio download
- ID3 tagging
- Telegram media upload
- Telegram music library sync

---

## Features

- Detects the currently playing Spotify track
- Supports both Windows and Linux
- Uses system-native playback APIs:
  - Windows media session API on Windows
  - MPRIS2 via `playerctl` on Linux
- Downloads audio from YouTube with `yt-dlp`
- Converts audio to MP3
- Writes ID3 tags using `mutagen`
- Uploads the file to Telegram Saved Messages
- Saves the uploaded file into Telegram Music
- Deletes the previously uploaded track when playback changes
- Avoids repeated downloads with memory and disk cache
- Cancels active downloads cleanly if the track changes quickly
- Handles subprocess timeout and cancellation safely

---

## How it works

The main loop behaves like this:

1. Poll Spotify every `POLL_SECONDS`
2. Detect the currently playing track
3. If nothing is playing:
   - optionally log idle state
   - delete the previously uploaded message
4. If a new track is detected:
   - cancel any in-progress download
   - remove the previous Telegram message
   - check whether the file already exists in cache
   - if not cached, search and download it via `yt-dlp`
   - write ID3 tags
   - send the file to Saved Messages
   - save it into Telegram Music

---

## Project structure

```text
.
├── windows.py
├── linux.py
└── README.md
```

---

## Requirements

### General

- Python 3.10+
- Telegram account
- Spotify desktop application
- Internet connection
- `yt-dlp`
- A browser profile available for cookie extraction (`firefox` in current code)

### Python packages

Install the common dependencies:

```bash
pip install telethon mutagen yt-dlp
```

---

## Platform-specific setup

### Windows

Install the Windows-specific dependency:

```bash
pip install winsdk
```

Run:

```bash
python windows.py
```

### Linux

Install Python dependencies:

```bash
pip install telethon mutagen yt-dlp
```

Install `playerctl` with your package manager.

#### Debian / Ubuntu

```bash
sudo apt install playerctl
```

#### Arch Linux

```bash
sudo pacman -S playerctl
```

#### Fedora

```bash
sudo dnf install playerctl
```

Run:

```bash
python linux.py
```

### Snap note for Linux

If Spotify was installed via Snap, `playerctl` may not see it until the MPRIS interface is connected:

```bash
sudo snap connect spotify:mpris
```

---

## Telegram API setup

Before running the script, you must provide your Telegram API credentials.

Get them from:

[https://my.telegram.org](https://my.telegram.org)

### Steps

1. Sign in to `my.telegram.org`
2. Open **API Development Tools**
3. Create a new application
4. Copy your `api_id`
5. Copy your `api_hash`
6. Put them into the script

Example:

```python
API_ID = 12345678
API_HASH = "your_api_hash_here"
```

---

## Configuration

The main configuration values are defined near the top of the script.

### `API_ID`

Your Telegram API ID.

```python
API_ID = 12345678
```

### `API_HASH`

Your Telegram API hash.

```python
API_HASH = "your_api_hash_here"
```

### `SESSION_NAME`

Telethon session file name.

```python
SESSION_NAME = "tg_spotify_bio"
```

This creates a local session file such as:

```text
tg_spotify_bio.session
```

### `DOWNLOAD_DIR`

Directory used for downloaded tracks.

Windows version example:

```python
DOWNLOAD_DIR = Path(r"C:\status")
```

Linux version example:

```python
DOWNLOAD_DIR = Path.home() / "tg_music_status"
```

### `POLL_SECONDS`

How often Spotify is checked.

```python
POLL_SECONDS = 3
```

### `PREFIX`

Prefix used in the uploaded message caption.

```python
PREFIX = "🎵"
```

Caption format:

```text
🎵 Artist — Title
```

or, if artist is missing:

```text
🎵 Title
```

---

## Download behavior

When a new track is detected, the script builds a search query like this:

```text
ytsearch1:Artist - Title lyrics
```

Then it runs `yt-dlp` with audio extraction enabled. The output is converted to MP3 and stored under a sanitized filename.

Current logic includes:

- no playlist download
- audio extraction
- MP3 conversion
- best audio format selection
- retry support
- browser cookie extraction
- timeout handling
- safe process cleanup on cancel

---

## Caching

The project uses two layers of cache.

### In-memory cache

A dictionary called `_file_cache` stores a mapping like:

```python
"Artist - Title" -> Path(...)
```

This avoids repeated filesystem lookups during the same session.

### Disk cache

Before downloading, the script checks:

- exact `.mp3` path
- any matching file with the same sanitized base name

This means if a track was already downloaded earlier, even in a previous run, it can be reused without downloading again.

---

## ID3 tagging

After download, the script updates metadata using `mutagen.id3`.

It writes:

- `TIT2` — track title
- `TPE1` — artist name

If the file already contains matching metadata, the update is skipped.

This helps Telegram display the track correctly as music instead of a generic file.

---

## Telegram upload flow

After the file is ready, the script sends it to:

```python
"me"
```

That means your own **Saved Messages** chat.

It uses `send_file(...)` with `DocumentAttributeAudio(...)` so Telegram recognizes it as an audio track. After that, the uploaded file is wrapped into `InputDocument` and passed into:

```python
functions.account.SaveMusicRequest(...)
```

This saves the song into Telegram's music library.

---

## Track switching and cleanup

If Spotify switches to a different track while the previous one is still downloading:

- the current async task is cancelled
- the `yt-dlp` subprocess is terminated
- if it does not exit quickly, it is killed

If nothing is playing anymore:

- the previously uploaded Telegram message is deleted
- internal track state is reset

This keeps the Telegram side synchronized with the current playback state.

---

## Console log examples

Typical logs look like this:

```text
[download] 🎵 Artist — Title
[cache hit] Artist - Title
[disk cache] Artist - Title
[meta] Artist — Title
[meta skip] Artist — Title
[music] Saved: 🎵 Artist — Title
[cleanup] Deleted id=12345
[status] Nothing is playing
[yt-dlp] timeout
[process error] ...
[error] ...
```

These logs make it easy to understand where the process is currently failing or succeeding.

---

## Linux fallback without playerctl

The Linux file includes an alternative commented-out implementation using direct D-Bus access through `dbus-python`.

If you want to use that version instead of `playerctl`:

1. Install:

```bash
pip install dbus-python
```

2. Open `linux.py`
3. Comment out the `playerctl`-based `get_current_track()`
4. Uncomment the D-Bus version below it

This is useful if you want fewer external CLI dependencies.

---

## Usage

Run the script for your platform.

### Windows

```bash
python windows.py
```

### Linux

```bash
python linux.py
```

On first launch, Telethon may ask you to:

- enter your phone number
- enter the login code
- confirm 2FA password if enabled

After that, the session is saved locally.

---

## Running in background on Linux

You can run the Linux version as a user `systemd` service.

Create:

```text
~/.config/systemd/user/tsbm.service
```

Example service:

```ini
[Unit]
Description=Telegram Spotify Bio Monitor

[Service]
ExecStart=/usr/bin/python3 /path/to/tsbm/linux.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
```

Enable and start it:

```bash
systemctl --user enable --now tsbm
```

Check logs:

```bash
journalctl --user -u tsbm -f
```

---

## Limitations

- Works with **Spotify desktop app**, not the web player
- Linux version requires a valid user session with MPRIS support
- Headless servers usually will not work for the Linux playback detection part
- YouTube search results may not always match the Spotify version perfectly
- Browser cookie extraction depends on a usable local browser profile
- The current implementation does not edit Telegram bio text, despite the project name

---

## Warning

Do not set the polling interval too aggressively. Very frequent Telegram actions may be unnecessary and could eventually trigger unwanted behavior or rate limiting.

A practical range is usually:

```python
POLL_SECONDS = 3
```

to

```python
POLL_SECONDS = 10
```

---


## License

Use and modify this project freely for personal use.
