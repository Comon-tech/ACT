from abc import ABC
from typing import ClassVar, Self

from pydantic import BaseModel, Field, PrivateAttr, ValidationError
from pymongo import ReturnDocument
from pymongo.database import Collection, Database
from pymongo.results import UpdateResult

from utils.log import logger

log = logger(__name__)


# ----------------------------------------------------------------------------------------------------
# * Database Model
# ----------------------------------------------------------------------------------------------------
class DbModel(BaseModel):
    """Model that supports working with a database."""

    id: int | str = Field(alias="_id")
    _database: Database = PrivateAttr()

    def __init__(self, database: Database, **kwargs):
        try:
            super().__init__(**kwargs)
            self._database = database
        except ValidationError as e:
            log.exception(e)

    @classmethod
    def __init_subclass__(cls, collection_name: str, **kwargs):
        cls.collection_name = collection_name
        return super().__init_subclass__(**kwargs)

    # @property
    # def database(self):
    #     return self._database

    @classmethod
    def get_collection(cls, database: Database) -> Collection:
        """Retrieve associated native collection from given database."""
        return database.get_collection(cls.collection_name)

    # @classmethod
    # def instantiate(cls, database: Database, document: dict) -> Self | None:
    #     """Create new model instance for given database using given document. Return None if error."""
    #     try:
    #         return cls(database, **document)
    #     except ValidationError as e:
    #         log.exception(e)

    @classmethod
    def load(cls, database: Database, id: int | str) -> Self | None:
        """Load model instance from given database using given id. Create if nonexistent. Return None if error."""
        try:
            document = cls.get_collection(database).find_one(
                {"_id": id},
            )
            return cls(database, **document) if document else None
        except Exception as e:
            log.exception(e)

    @property
    def collection(self) -> Collection:
        """Retrieve associated native collection from associated database."""
        if not self._database:
            raise Exception("No associated database.")
        return self._database.get_collection(self.collection_name)

    def save(self) -> UpdateResult | None:
        """Save this instance to associated database. Return None if error."""
        try:
            return self.collection.update_one(
                {"_id": self.id}, {"$set": self.model_dump(by_alias=True)}, upsert=True
            )
        except Exception as e:
            log.exception(e)
