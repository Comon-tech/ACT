from odmantic import Model
from pydantic import StringConstraints
from typing_extensions import Annotated

from utils.log import logger

log = logger(__name__)
NonEmptyStr = Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]


# ----------------------------------------------------------------------------------------------------
# * Persona
# ----------------------------------------------------------------------------------------------------
class Persona(Model):
    """Persona data that can be used to store AI personality instrutions."""

    model_config = {"collection": "personas"}

    name: str = ""
    description: list[str]
    messages: dict[str, list[str]] = {}
