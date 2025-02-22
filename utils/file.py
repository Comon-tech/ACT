import os
from io import BytesIO
from mimetypes import guess_file_type
from typing import Self
from urllib.parse import urlparse

from filetype import guess_mime
from pydantic import BaseModel, StringConstraints
from requests import get
from typing_extensions import Annotated

from utils.log import logger

NonEmptyStr = Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]
log = logger(__name__)


class ActFile(BaseModel):
    """General-purpose simple file interface."""

    data: bytes
    mime_type: str | None = None
    name: str | None = None

    _default_name = "__unnamed__.bin"
    _type_category = ""

    def model_post_init(self, __context):
        if not self.mime_type:
            self.mime_type = (
                guess_mime(self.data) or guess_file_type(self.name or "")[0]
            )
        if not self.name:
            self.name = self._default_name
        return super().model_post_init(__context)

    def __str__(self):
        return f"{self.name}, {self.major_type} ({self.mime_type or "unknown"}), {self.size} bytes"

    # ----------------------------------------------------------------------------------------------------

    @property
    def size(self) -> int:
        return len(self.data) if self.data else 0

    @property
    def major_type(self) -> str | None:
        """Primary file type deduced from mime type or by text decoding attempt. E.g. text, image, audio, video, ...etc"""
        return (
            self.mime_type.strip().split("/")[0].lower()
            if self.mime_type
            else ("text" if self.get_text(self.data) else None)
        )

    @property
    def text(self) -> str | None:
        """Get text content if major file type is text, or None otherwise."""
        if self.major_type != "text":
            return
        try:
            return self.data.decode("utf-8")
        except UnicodeDecodeError:
            return self.data.decode("latin-1", errors="replace")  # Fallback

    @staticmethod
    def get_text(data: bytes):
        """Get decoded UTF-8 string, or None if decoding fails."""
        try:
            return data.decode()
        except:
            return None

    # ----------------------------------------------------------------------------------------------------

    def save(self, dirpath: str = "./"):
        """Save file to given directory path. Create non-existent directory."""
        filepath = os.path.join(dirpath, self.name or self._default_name)
        os.makedirs(dirpath, exist_ok=True)
        with open(filepath, "wb") as f:
            f.write(self.data)
        log.info(f"File saved: {filepath}")

    @classmethod
    def load(cls, file_path_or_url: str) -> Self:
        """Load file from given file path or url."""
        parsed_url = urlparse(file_path_or_url)
        if parsed_url.scheme:
            response = get(file_path_or_url, stream=True)
            response.raise_for_status()
            data = BytesIO()
            for chunk in response.iter_content(chunk_size=8192):
                data.write(chunk)
            data.seek(0)
            name = os.path.basename(parsed_url.path)
            if "?" in name:
                name = name.split("?")[0]
            return cls(data=data.getvalue(), name=name)
        else:
            with open(file_path_or_url, "rb") as f:
                data = f.read()
                name = os.path.basename(file_path_or_url)
                return cls(data=data, name=name)
