import tomllib
from pathlib import Path
from typing import Literal, Self

from odmantic import Field, Model
from pydantic import NonNegativeInt


# ----------------------------------------------------------------------------------------------------
# * Item
# ----------------------------------------------------------------------------------------------------
class Item(Model):
    model_config = {"collection": "items"}

    id: str = Field(primary_field=True)
    name: str = ""
    description: str = ""
    emoji: str = "❔"
    icon_url: str = ""
    is_buyable: bool = True
    price: NonNegativeInt = 0
    type: Literal["equippable", "consumable", "special"]

    # Equippable
    max_health_bonus: int = 0
    max_energy_bonus: int = 0
    attack_bonus: int = 0
    defense_bonus: int = 0
    speed_bonus: int = 0

    # Consumable
    health_bonus: int = 0
    energy_bonus: int = 0
