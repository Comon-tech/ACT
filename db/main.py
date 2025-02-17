import hashlib
import re

from colorama import Fore
from pymongo import MongoClient, monitoring
from pymongo.database import Database
from pymongo.monitoring import ConnectionPoolListener, register

from db.model import DbModel
from utils.log import logger
from utils.misc import text_block

log = logger(__name__)


class DbRef(DbModel, collection_name="db_refs"):
    name: str


# ----------------------------------------------------------------------------------------------------
# * Act Database Client
# ----------------------------------------------------------------------------------------------------
class ActDbClient(MongoClient):

    def __init__(self, *args, name: str = "", **kwargs):
        log.loading(f"Database client opening...")
        super().__init__(*args, **kwargs)
        self.name = name or ActDbClient.__name__
        self.title = self.name
        self.databases: dict[str, Database] = {}
        self.main_database = self.get_database(self.name)
        log.success(
            f"🍃 Database client connected to {self.address[0]}:{self.address[1]}."
        )
        log.info("\n" + self.info_text)

    @property
    def info_text(self):
        output = "Databases:"
        for db_name in self.list_database_names():
            if db_name == self.name:
                db_name = f"{Fore.CYAN}{db_name}{Fore.RESET}"
            elif db_name == "admin" or "config" or "local":
                db_name = f"{Fore.LIGHTBLACK_EX}{db_name}{Fore.RESET}"
            output += f"\n• {db_name}"
        return text_block(output)

    def get_database_by_id(self, id: int, name: str = None) -> Database | None:
        """Retrieve database by id. if nonexistent, create using given name, if no name given return None."""
        if id not in self.databases:
            db_ref = DbRef.load(self.main_database, id)
            if not db_ref and name:
                db_name = self._generate_database_name(name, id)
                db_ref = DbRef(self.main_database, {"id": id, "name": db_name})
                db_ref.save()
            self.databases[id] = self.get_database(db_ref.name)
        return self.databases.get(id)

    def _generate_database_name(self, name: str, id: int) -> str:
        """Generate a unique database name from given name. Guard against duplicate name using id if needed."""
        name = re.sub(r"[^a-zA-Z0-9_-]", "_", name).lower()
        if DbRef.get_collection(self.main_database).find_one({"name": name}):
            id_hash = hashlib.sha256(str(id).encode()).hexdigest()[:8]
            name = f"{name}_{id_hash}"
        return f"{self.name}_{name}"

    def close(self):
        log.loading(f"Database client closing...")
        super().close()
        log.success(f"Database client closed.")
