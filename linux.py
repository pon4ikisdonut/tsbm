import asyncio
from telethon import TelegramClient
from telethon.tl.functions.account import UpdateProfileRequest


API_ID = put-your-app-id-here
API_HASH = "put-your-api-hash-here"
SESSION_NAME = "tg_spotify_bio"


BIO_LIMIT = 70
POLL_SECONDS = 13
PREFIX = "Сейчас слушаю:"
NOT_PLAYING = "Пока ничего не слушаю..."


def trim_bio(text: str, limit: int = BIO_LIMIT) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


async def run_playerctl(*args):
    try:
        process = await asyncio.create_subprocess_exec(
            "playerctl",
            "--player=spotify",
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    except FileNotFoundError:
        return None

    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        return None

    return stdout.decode("utf-8", errors="ignore").strip()


async def get_spotify_bio():
    status = await run_playerctl("status", "--format", "{{ uc(status) }}")
    if status != "PLAYING":
        return trim_bio(NOT_PLAYING)

    metadata = await run_playerctl("metadata", "--format", "{{ artist }}|||{{ title }}")
    if not metadata or "|||" not in metadata:
        return trim_bio(NOT_PLAYING)

    artist, title = metadata.split("|||", 1)
    artist = artist.strip()
    title = title.strip()

    if not title:
        return trim_bio(NOT_PLAYING)

    if artist:
        return trim_bio(f"{PREFIX} {artist} - {title}")
    return trim_bio(f"{PREFIX} {title}")


async def main():
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    await client.start()

    last_bio = None

    while True:
        try:
            bio = await get_spotify_bio()

            if bio != last_bio:
                await client(UpdateProfileRequest(about=bio))
                last_bio = bio
                print("Updated:", bio)

        except Exception as e:
            print("Error:", e)

        await asyncio.sleep(POLL_SECONDS)


if __name__ == "__main__":
    asyncio.run(main())