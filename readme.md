# Telegram Spotify Bio Monitor

This script updates your Telegram profile bio with the track you are currently listening to on Spotify.

It checks the current media session on Windows and automatically changes your Telegram bio to show the current song. If nothing is playing, it can display a custom fallback text instead.

## Features

- Shows your current Spotify track in your Telegram bio
- Updates automatically every few seconds
- Supports a custom text when nothing is playing
- Lets you customize the bio prefix
- Keeps the bio within Telegram's length limit

## Requirements

- Python 3.10+
- Windows
- A Telegram account
- Spotify desktop app

## Installation

First, install the required dependencies:

```bash
pip install telethon winsdk
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

You can customize several variables in the script:

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
POLL_SECONDS = 5
```

### `BIO_LIMIT`
Maximum allowed bio length.

Example:

```python
BIO_LIMIT = 70
```

## Usage

Run the script with:

```bash
python main.py
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

- This script works with the Spotify desktop app on Windows
- Your Telegram bio is updated only when the text changes
- If the track title is too long, it will be shortened automatically

## Warning

Use this script responsibly. Updating your Telegram bio too often may look unusual, so avoid setting the polling interval too low.

## License

Use and modify this script freely for personal purposes.