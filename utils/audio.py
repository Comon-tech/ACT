import asyncio
import functools
from typing import Any

import yt_dlp

from utils.log import logger

log = logger(__name__)


# ----------------------------------------------------------------------------------------------------
# * Media Source
# ----------------------------------------------------------------------------------------------------
class MediaSource:
    """Base class for media sources from various platforms."""

    def __init__(self, title: str, url: str, duration: int | None = None):
        self.title: str = title
        self.url: str = url
        self.duration: int | None = duration

    @classmethod
    async def from_url(cls, url: str, *, loop=None) -> list["MediaSource"]:
        """Extract audio sources from a URL."""
        raise NotImplementedError


# ----------------------------------------------------------------------------------------------------
# * YouTube Source
# ----------------------------------------------------------------------------------------------------
class YouTubeSource(MediaSource):
    """Audio source for YouTube videos and playlists."""

    YTDL = yt_dlp.YoutubeDL(
        {
            "format": "bestaudio[acodec=opus]/bestaudio[acodec=aac]/bestaudio/best",  # Prefer opus or aac for Discord
            "noplaylist": False,  # Allow playlists
            "quiet": True,  # Suppress console output
            "default_search": "auto",  # Enable search queries
            "extract_flat": True,  # Faster playlist processing
            "retries": 3,  # Retry failed requests
            "fragment_retries": 3,  # Retry failed fragments
            "http_chunk_size": 1048576,  # 1MB chunks for streaming
            "ignoreerrors": True,  # Skip invalid playlist entries
            "socket_timeout": 10,  # Timeout for slow connections
            "no_cache_dir": True,  # Avoid disk I/O
            "outtmpl": "%(title)s.%(ext)s",  # Consistent output naming (if downloading)
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",  # Bypass some restrictions
            "force_generic_extractor": True,  # Support non-YouTube platforms
            "max_downloads": 50,  # Limit playlist size to avoid overload
        }
    )

    @classmethod
    async def from_url(cls, url: str, *, loop=None) -> list["MediaSource"]:
        loop = loop or asyncio.get_event_loop()
        try:
            # Wrap ytdl.extract_info in executor to prevent blocking
            data: dict[str, Any] | None = await loop.run_in_executor(
                None, functools.partial(cls.YTDL.extract_info, url, download=False)
            )

            # Explicitly check for None
            if data is None:
                log.error(f"No data returned for URL: {url}")
                return []

            sources = []
            if "entries" in data:
                # Playlist
                for entry in data["entries"]:
                    if entry:
                        sources.append(
                            cls(
                                title=entry.get("title", "Unknown"),
                                url=entry.get("url", entry.get("webpage_url", "")),
                                duration=entry.get("duration"),
                            )
                        )
            else:
                # Single video
                sources.append(
                    cls(
                        title=data.get("title", "Unknown"),
                        url=data.get("url", data.get("webpage_url", "")),
                        duration=data.get("duration"),
                    )
                )

            return sources
        except Exception as e:
            log.error(f"Error extracting YouTube source: {e}")
            return []
