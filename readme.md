# Telegram Spotify Bio Monitor

This project updates your Telegram profile bio with the track you are currently listening to on Spotify.

It supports:
- `windows.py` — Windows version using the Windows media session API
- `linux.py` — Linux version using MPRIS via `playerctl`

If nothing is playing, the script can show a custom fallback text instead.

## Features

- Shows your current Spotify track in your Telegram bio
- Updates automatically every few seconds
- Supports a custom text when nothing is playing
- Lets you customize the bio prefix
- Keeps the bio within Telegram's bio length limit
- Supports both Windows and Linux

## Requirements

- Python 3.10+
- A Telegram account
- Spotify desktop app

### Platform-specific requirements

#### Windows
- `windows.py`
- `winsdk`

#### Linux
- `linux.py`
- `playerctl`

## Installation

Clone the repository:

```bash
git clone https://github.com/pon4ikisdonut/tsbm.git
cd tsbm
```

### Windows setup

Install Python dependencies:

```bash
pip install telethon winsdk
```

Run:

```bash
python windows.py
```

### Linux setup

Install Python dependencies:

```bash
pip install telethon
```

Install `playerctl` using your distro package manager.

Examples:

```bash
# Debian / Ubuntu
sudo apt install playerctl

# Arch Linux
sudo pacman -S playerctl

# Fedora
sudo dnf install playerctl
```

Run:

```bash
python linux.py
```

## Telegram API setup

Before running the script, you need to set your `API_ID` and `API_HASH`.

You can get these values from:

[https://my.telegram.org](https://my.telegram.org)

Steps:

1. Log in to your Telegram account on `my.telegram.org`
2. Open the **API Development Tools** section
3. Create an application
4. Copy your `api_id` and `api_hash`
5. Paste them into the script

Example:

```python
API_ID = 12345678
API_HASH = "your_api_hash_here"
```

## Configuration

You can customize several variables in both scripts:

### `PREFIX`
Text shown before the song title.

Example:

```python
PREFIX = "Now listening:"
```

### `NOT_PLAYING`
Text shown when Spotify is not playing anything.

Example:

```python
NOT_PLAYING = "Not playing"
```

### `POLL_SECONDS`
How often the script checks Spotify status.

Example:

```python
POLL_SECONDS = 13
```

### `BIO_LIMIT`
Maximum allowed bio length.

Example:

```python
BIO_LIMIT = 70
```

## Usage

Run the version for your platform:

```bash
python windows.py
```

or

```bash
python linux.py
```

On the first launch, Telegram may ask you to log in and confirm the session. After that, the script will keep running and update your bio automatically.

## Example output

If a track is playing:

```text
Now listening: FACE - ПОДРУГА ПОДРУГ
```

If nothing is playing:

```text
Not playing
```

## Notes

- `windows.py` works on Windows with the Spotify desktop app
- `linux.py` works on Linux with Spotify and `playerctl`
- Your Telegram bio is updated only when the text changes
- If the track title is too long, it will be shortened automatically

## Warning

Use this script responsibly. Updating your Telegram bio too often may look unusual, so avoid setting the polling interval too low.

## License

Use and modify this script freely for personal purposes.