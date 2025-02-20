import hashlib
import re

from colorama import Fore
from odmantic import Field, Model, SyncEngine
from pymongo import MongoClient
from pymongo.database import Database

from utils.log import logger
from utils.misc import text_block

log = logger(__name__)


# ----------------------------------------------------------------------------------------------------
# * Act Database
# ----------------------------------------------------------------------------------------------------
class ActDb:
    """Database interface allowing access and management of multiple related databases."""

    class DbRef(Model):
        """Database reference."""

        model_config = {"collection": "db_refs"}

        id: int = Field(primary_field=True)
        name: str

    # ----------------------------------------------------------------------------------------------------

    def __init__(self, name: str, *args, **kwargs):
        """
        :param str name: Name of main database and prefix for all names of related databases.
        :param *args: Any MongoClient constructor positional arguments.
        :param **kwargs: Any MongoClient constructor keyword arguments.
        """
        self.name = name or ActDb.__name__
        self.db_refs: dict[int, ActDb.DbRef] = {}
        log.loading(f"Database client opening...")
        self._engine = SyncEngine(MongoClient(*args, **kwargs), self.name)
        self._main_database = self._engine.database
        log.success(
            f"🍃 Database client connected to {self._engine.client.address[0]}:{self._engine.client.address[1]}."
        )
        log.info("\n" + self.info_text)

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

    def _get_engine(self, database: Database | str = None) -> SyncEngine:
        """Retrieve engine configured for specified database instance or name. Defaults to main database (using `self.name`)."""
        if isinstance(database, Database):
            self._engine.database = database
        elif database and isinstance(database, str):
            self._engine.database = self._engine.client.get_database(database)
        else:
            self._engine.database = self._main_database
        return self._engine

    # ----------------------------------------------------------------------------------------------------

    def get_engine(self, id: int, name: str = None) -> SyncEngine | None:
        """Retrieve engine by id. If nonexistent, create database using given name, if no name given return None."""
        db_ref = self.db_refs.get(id) or self._get_engine().find_one(
            ActDb.DbRef, ActDb.DbRef.id == id
        )  # Get reference from memory cache or main database
        if not db_ref and name:
            # Generate valid unique database name
            name = re.sub(r"[^a-zA-Z0-9_-]", "_", name).lower()
            if self._get_engine().find_one(ActDb.DbRef, ActDb.DbRef.name == name):
                # Name has duplicate: Append id-based hash to ensure name is different and unique
                name = f"{name}_{hashlib.sha256(str(id).encode()).hexdigest()[:8]}"
            name = f"{self.name}_{name}"
            db_ref = self._get_engine().save(ActDb.DbRef(id=id, name=name))
        if db_ref:
            self.db_refs[id] = db_ref  # Add to memory cache
            return self._get_engine(db_ref.name)
        return None

    def close(self):
        log.loading(f"Database client closing...")
        self._engine.client.close()
        log.success(f"Database client closed.")
