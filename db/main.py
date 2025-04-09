import hashlib
import re
import tomllib
from pathlib import Path
from typing import Any, Self, Type, TypeVar

from colorama import Fore
from odmantic import Field, Model, SyncEngine
from pydantic import BaseModel
from pymongo import MongoClient
from pymongo.database import Database

from utils.log import logger
from utils.misc import text_block

log = logger(__name__)
T = TypeVar("T", bound=Model)


# ----------------------------------------------------------------------------------------------------
# * Display
# ----------------------------------------------------------------------------------------------------
class TextUnit(BaseModel):
    title: str
    emoji: str
    alt_emoji: str


# ----------------------------------------------------------------------------------------------------
# * Act Toml
# ----------------------------------------------------------------------------------------------------
class ActToml:
    """Static interface for loading models from TOML files."""

    DATA_DIR = Path(__file__).parent / "data"

    @classmethod
    def _load(cls, name: str) -> dict[str, Any]:
        with open(cls.DATA_DIR / f"{name}.toml", "rb") as file:
            data = tomllib.load(file)
        return data

    @staticmethod
    def _get_name(model_cls: type[T]) -> str | None:
        return model_cls.model_config.get("collection")

    # ----------------------------------------------------------------------------------------------------

    @classmethod
    def load_dict(
        cls,
        model_cls: type[T],
    ) -> dict[str, T]:
        """Load dict from toml file."""
        name = cls._get_name(model_cls)
        records = cls._load(name).items() if name else {}
        return {key: model_cls(**value) for key, value in records}

    @classmethod
    def load_list(
        cls,
        model_cls: type[T],
    ) -> list[T]:
        """Load list from toml file."""
        name = cls._get_name(model_cls)
        records = cls._load(name).get(name, []) if name else []
        return [model_cls(**value) for value in records]


# ----------------------------------------------------------------------------------------------------
# * Database Reference
# ----------------------------------------------------------------------------------------------------
class DbRef(Model):
    """Database model for storage of reference and relevant data about a database."""

    model_config = {"collection": "db_refs"}

    id: int = Field(primary_field=True)
    name: str
    ai_chat_history: list[dict[str, Any]] = []


# ----------------------------------------------------------------------------------------------------
# * Act Database
# ----------------------------------------------------------------------------------------------------
class ActDb:
    """Database interface for access and management of multiple related databases."""

    # ----------------------------------------------------------------------------------------------------

    def __init__(self, name: str, *args, **kwargs):
        """
        :param str name: Name of main database and prefix for all names of related databases.
        :param *args: Any MongoClient constructor positional arguments.
        :param **kwargs: Any MongoClient constructor keyword arguments.
        """
        self.name = name or ActDb.__name__
        self.db_refs: dict[int, DbRef] = {}
        log.loading(f"Database client opening...")
        self._engine = SyncEngine(MongoClient(*args, **kwargs), self.name)
        self._main_database = self._engine.database
        host, port = self._engine.client.address or ("?", "?")
        log.success(f"🍃 Database client connected to {host}:{port}.")
        # log.info("\n" + self.info_text)

    @property
    def info_text(self):
        output = "Databases:"
        for db_name in self._engine.client.list_database_names():
            if db_name == self.name:
                db_name = f"{Fore.CYAN}{db_name}{Fore.RESET}"
            elif db_name == "admin" or "config" or "local":
                db_name = f"{Fore.LIGHTBLACK_EX}{db_name}{Fore.RESET}"
            output += f"\n• {db_name}"
        return text_block(output)

    # ----------------------------------------------------------------------------------------------------

    def _get_engine(self, database: Database | str | None = None) -> SyncEngine:
        """Get engine with database of given instance or name. If none, get engine with main database."""
        if isinstance(database, Database):
            self._engine.database = database
        elif database and isinstance(database, str):
            self._engine.database = self._engine.client.get_database(database)
        else:
            self._engine.database = self._main_database
        return self._engine

    # ----------------------------------------------------------------------------------------------------

    def get_engine(
        self, id: int | None = None, name: str | None = None
    ) -> SyncEngine | None:
        """Get engine with database of given id. If no id, get engine with main database.
        If nonexistent, create database with given name, if no name, return None."""
        if id is None:
            return self._get_engine()
        db_ref = self.db_refs.get(id) or self._get_engine().find_one(
            DbRef, DbRef.id == id
        )  # Get reference from memory cache or main database
        if not db_ref and name:
            # Generate valid unique database name
            name = re.sub(r"[^a-zA-Z0-9_-]", "_", name).lower()
            if self._get_engine().find_one(DbRef, DbRef.name == name):
                # Name has duplicate: Append id-based hash to ensure name is different and unique
                name = f"{name}_{hashlib.sha256(str(id).encode()).hexdigest()[:8]}"
            name = f"{self.name}_{name}"
            db_ref = self._get_engine().save(DbRef(id=id, name=name))
        if db_ref:
            self.db_refs[id] = db_ref  # Add to memory cache
            return self._get_engine(db_ref.name)
        return None

    def close(self):
        log.loading(f"Database client closing...")
        self._engine.client.close()
        log.success(f"Database client closed.")
