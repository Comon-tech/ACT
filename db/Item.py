from datetime import datetime
from typing import Any, ClassVar, Literal, Optional

from odmantic import Field, Model
from pydantic import NonNegativeInt

from utils.misc import text_progress_bar

# ----------------------------------------------------------------------------------------------------
# * Item
# ----------------------------------------------------------------------------------------------------
class Item(Model):
    model_config = {"collection": "items"}

    id: str = Field(primary_field=True)
    name: str = ""
    description: str = ""
    price: NonNegativeInt = 0
    type: Literal["equippable", "consumable", "special"]
    # rarity: Literal["common", "uncommon", "rare", "epic", "legendary"]

    # Effects when used/equipped
    max_health_bonus: NonNegativeInt = 0
    max_energy_bonus: NonNegativeInt = 0
    attack_bonus: NonNegativeInt = 0
    defense_bonus: NonNegativeInt = 0
    speed_bonus: NonNegativeInt = 0
    effects: dict[str, Any] = {}