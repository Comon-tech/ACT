from enum import Enum
from typing import ClassVar, Self

from humanize import intcomma
from odmantic import Field, Model, Reference
from pydantic import NonNegativeInt

from db.main import ActToml, TextUnit
from db.stat import Stat
from utils.misc import numsign


# ----------------------------------------------------------------------------------------------------
# * Item Type
# ----------------------------------------------------------------------------------------------------
class ItemType(str, Enum):
    EQUIPPABLE = "equippable"
    CONSUMABLE = "consumable"
    SPECIAL = "special"


# ----------------------------------------------------------------------------------------------------
# * Item
# ----------------------------------------------------------------------------------------------------
class Item(Model):
    model_config = {"collection": "items"}

    id: str = Field(primary_field=True)
    name: str
    description: str = ""
    emoji: str = ""
    alt_emoji: str = "❔"
    icon_url: str = ""
    is_buyable: bool = True
    price: NonNegativeInt = 0
    type: ItemType

    # Equippable
    health_max_bonus: int = 0
    energy_max_bonus: int = 0
    attack_bonus: int = 0
    defense_bonus: int = 0
    speed_bonus: int = 0

    # Consumable
    health_bonus: int = 0
    energy_bonus: int = 0

    # Display
    STATS: ClassVar[dict[str, Stat]] = ActToml.load_dict(Stat)

    # ----------------------------------------------------------------------------------------------------

    def effective_stats(self, scale: int = 1) -> dict[str, int]:
        """Get {name, value} list of effective (non-zero) stat names with their corresponding scaled values."""
        stats: dict[str, int] = {}
        if self.health_bonus:
            stats["health"] = scale * self.health_bonus
        if self.energy_bonus:
            stats["energy"] = scale * self.energy_bonus
        if self.health_max_bonus:
            stats["health_max"] = scale * self.health_max_bonus
        if self.energy_max_bonus:
            stats["energy_max"] = scale * self.energy_max_bonus
        if self.attack_bonus:
            stats["attack"] = scale * self.attack_bonus
        if self.defense_bonus:
            stats["defense"] = scale * self.defense_bonus
        if self.speed_bonus:
            stats["speed"] = scale * self.speed_bonus
        return stats

    def item_stats_text(self, scale: int = 1) -> str:
        stat_texts = []
        for id, value in self.effective_stats(scale=scale).items():
            stat = self.STATS.get(id)
            if stat:
                stat_texts.append(f"{stat.alt_emoji}{numsign(intcomma(value))}")
        return " ".join(stat_texts)


# ----------------------------------------------------------------------------------------------------
# * Item Stack
# ----------------------------------------------------------------------------------------------------
class ItemStack(Model):
    id: str = Field(primary_field=True)
    item: Item = Reference()
    quantity: NonNegativeInt = 1
