import asyncio
import contextlib
import re
from pathlib import Path

from telethon import TelegramClient, functions, types
from winsdk.windows.media.control import (
    GlobalSystemMediaTransportControlsSessionManager as MediaManager,
    GlobalSystemMediaTransportControlsSessionPlaybackStatus as PlaybackStatus,
)
from mutagen.id3 import ID3, TIT2, TPE1, ID3NoHeaderError

API_ID = your_app_id
API_HASH = "your_api_hash"
SESSION_NAME = "tg_spotify_bio"

DOWNLOAD_DIR = Path(r"C:\status") 
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

POLL_SECONDS = 3
PREFIX = "🎵"

_file_cache: dict[str, Path] = {}


def sanitize_filename(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "_", name).strip()


def _first_frame_text(tags: ID3, key: str) -> str:
    frames = tags.getall(key)
    if not frames:
        return ""
    text = getattr(frames[0], "text", None)
    if isinstance(text, list):
        return str(text[0]).strip() if text else ""
    return str(text).strip() if text is not None else ""


def write_fast_id3(file_path: Path, title: str, artist: str) -> None:
    try:
        try:
            tags = ID3(str(file_path))
        except ID3NoHeaderError:
            tags = ID3()

        current_title = _first_frame_text(tags, "TIT2")
        current_artist = _first_frame_text(tags, "TPE1")

        wanted_artist = artist.strip() if artist else title.strip()
        wanted_title = title.strip()

        if current_title == wanted_title and current_artist == wanted_artist:
            print(f"[meta skip] {wanted_artist} — {wanted_title}")
            return

        tags.delall("TIT2")
        tags.delall("TPE1")
        tags["TIT2"] = TIT2(encoding=3, text=wanted_title)
        tags["TPE1"] = TPE1(encoding=3, text=wanted_artist)
        tags.save(str(file_path), v2_version=3)

        print(f"[meta] {wanted_artist} — {wanted_title}")
    except Exception as e:
        print(f"[meta error] {e}")


async def get_current_track(manager) -> dict | None:
    for session in manager.get_sessions():
        try:
            source = session.source_app_user_model_id or ""
        except Exception:
            source = ""

        if "spotify" not in source.lower():
            continue

        playback = session.get_playback_info()
        if not playback or playback.playback_status != PlaybackStatus.PLAYING:
            continue

        info = await session.try_get_media_properties_async()
        if not info:
            continue

        title = (info.title or "").strip()
        artist = (info.artist or "").strip()

        if not title:
            continue

        return {"title": title, "artist": artist}

    return None


async def download_track(title: str, artist: str) -> Path | None:
    cache_key = f"{artist} - {title}" if artist else title
    safe_name = sanitize_filename(cache_key)

    if cache_key in _file_cache and _file_cache[cache_key].exists():
        print(f"[cache hit] {cache_key}")
        return _file_cache[cache_key]

    exact_mp3 = DOWNLOAD_DIR / f"{safe_name}.mp3"
    if exact_mp3.exists():
        _file_cache[cache_key] = exact_mp3
        print(f"[disk cache] {cache_key}")
        return exact_mp3

    existing = next(DOWNLOAD_DIR.glob(f"{safe_name}.*"), None)
    if existing:
        _file_cache[cache_key] = existing
        print(f"[disk cache] {cache_key}")
        return existing

    query = f"ytsearch1:{cache_key} lyrics"
    out_template = str(DOWNLOAD_DIR / f"{safe_name}.%(ext)s")

    cmd = [
        "yt-dlp",
        "--no-playlist",
        "--extract-audio",
        "--audio-format", "mp3",
        "--audio-quality", "0",
        "--output", out_template,
        "--no-post-overwrites",
        "--retries", "3",
        "--format", "bestaudio/best",
        "--cookies-from-browser", "firefox", # If you want to use Google Chrome cookies, switch from Firefox to Chrome.
        "--remote-components", "ejs:github",
        query,
    ]

    proc = None
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=None,
            stderr=None,
        )
        await asyncio.wait_for(proc.wait(), timeout=90)

        if proc.returncode != 0:
            print(f"[yt-dlp] Процесс завершился с ошибкой, код: {proc.returncode}")
            return None
    except asyncio.CancelledError:
        if proc and proc.returncode is None:
            with contextlib.suppress(ProcessLookupError):
                proc.terminate()
            try:
                await asyncio.wait_for(proc.wait(), timeout=3)
            except asyncio.TimeoutError:
                with contextlib.suppress(ProcessLookupError):
                    proc.kill()
                with contextlib.suppress(Exception):
                    await proc.wait()
        raise
    except asyncio.TimeoutError:
        print("[yt-dlp] timeout")
        if proc and proc.returncode is None:
            with contextlib.suppress(ProcessLookupError):
                proc.kill()
            with contextlib.suppress(Exception):
                await proc.wait()
        return None
    except FileNotFoundError:
        print("[yt-dlp] not found — pip install yt-dlp")
        return None

    if exact_mp3.exists():
        _file_cache[cache_key] = exact_mp3
        return exact_mp3

    result = next(DOWNLOAD_DIR.glob(f"{safe_name}.*"), None)
    if result:
        _file_cache[cache_key] = result
        return result

    return None


def make_input_doc(doc) -> types.InputDocument:
    return types.InputDocument(
        id=doc.id,
        access_hash=doc.access_hash,
        file_reference=doc.file_reference,
    )


async def cleanup_old(client: TelegramClient, msg_id: int) -> None:
    try:
        await client.delete_messages("me", [msg_id])
        print(f"[cleanup] Удалено id={msg_id}")
    except Exception as e:
        print(f"[delete msg] {e}")


async def main():
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    await client.start()

    manager = await MediaManager.request_async()

    last_track: dict | None = None
    last_msg_id: int | None = None
    download_task: asyncio.Task | None = None
    idle_logged = False

    async def process_track(track: dict) -> None:
        nonlocal last_msg_id

        caption = (
            f"{PREFIX} {track['artist']} — {track['title']}"
            if track["artist"] else f"{PREFIX} {track['title']}"
        )
        print(f"[download] {caption}")

        try:
            file_path = await download_track(track["title"], track["artist"])
            if not file_path:
                return

            await asyncio.to_thread(
                write_fast_id3,
                file_path,
                track["title"],
                track["artist"],
            )

            msg = await client.send_file(
                "me",
                str(file_path),
                caption=caption,
                voice_note=False,
                attributes=[
                    types.DocumentAttributeAudio(
                        duration=0,
                        title=track["title"],
                        performer=track["artist"],
                    )
                ],
            )

            doc = msg.document
            if doc:
                try:
                    await client(functions.account.SaveMusicRequest(
                        id=make_input_doc(doc),
                        unsave=False,
                    ))
                    last_msg_id = msg.id
                    print(f"[music] Сохранено: {caption}")
                except Exception as e:
                    print(f"[music save] {e}")
            else:
                print("[music] document не найден")

        except asyncio.CancelledError:
            print(f"[cancel] {caption}")
            raise
        except Exception as e:
            print(f"[process error] {e}")

    while True:
        try:
            track = await get_current_track(manager)

            if track is None:
                if not idle_logged:
                    print("[status] Ничего не играет")
                    idle_logged = True

                if track != last_track:
                    if download_task and not download_task.done():
                        download_task.cancel()
                        with contextlib.suppress(asyncio.CancelledError):
                            await download_task

                    if last_msg_id is not None:
                        asyncio.create_task(cleanup_old(client, last_msg_id))
                        last_msg_id = None

                    last_track = track

                await asyncio.sleep(POLL_SECONDS)
                continue

            idle_logged = False

            if track != last_track:
                if download_task and not download_task.done():
                    download_task.cancel()
                    with contextlib.suppress(asyncio.CancelledError):
                        await download_task

                if last_msg_id is not None:
                    asyncio.create_task(cleanup_old(client, last_msg_id))
                    last_msg_id = None

                download_task = asyncio.create_task(process_track(track))
                last_track = track

        except Exception as e:
            print(f"[error] {e}")

        await asyncio.sleep(POLL_SECONDS)


if __name__ == "__main__":
    asyncio.run(main())
