import asyncio
from telethon import TelegramClient
from telethon.tl.functions.account import UpdateProfileRequest
from winsdk.windows.media.control import (
    GlobalSystemMediaTransportControlsSessionManager as MediaManager,
    GlobalSystemMediaTransportControlsSessionPlaybackStatus as PlaybackStatus,
)

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


async def get_spotify_bio():
    manager = await MediaManager.request_async()
    session = manager.get_current_session()

    if not session:
        return trim_bio(NOT_PLAYING)

    app_id = (session.source_app_user_model_id or "").lower()
    if "spotify" not in app_id:
        return trim_bio(NOT_PLAYING)

    playback_info = session.get_playback_info()
    if not playback_info or playback_info.playback_status != PlaybackStatus.PLAYING:
        return trim_bio(NOT_PLAYING)

    info = await session.try_get_media_properties_async()
    title = (info.title or "").strip()
    artist = (info.artist or "").strip()

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