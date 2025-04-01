from enum import Enum

from humanize import intcomma
from odmantic import Field, Model, Reference
from pydantic import NonNegativeInt

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
    max_health_bonus: int = 0
    max_energy_bonus: int = 0
    attack_bonus: int = 0
    defense_bonus: int = 0
    speed_bonus: int = 0

    # Consumable
    health_bonus: int = 0
    energy_bonus: int = 0

    # ----------------------------------------------------------------------------------------------------

    def effective_stats(self, scale: int = 1) -> dict[str, int]:
        """Get {name, value} list of effective (non-zero) stat names with their corresponding scaled values."""
        stats: dict[str, int] = {}
        if self.health_bonus:
            stats["health"] = scale * self.health_bonus
        if self.energy_bonus:
            stats["energy"] = scale * self.energy_bonus
        if self.max_health_bonus:
            stats["max_health"] = scale * self.max_health_bonus
        if self.max_energy_bonus:
            stats["max_energy"] = scale * self.max_energy_bonus
        if self.attack_bonus:
            stats["attack"] = scale * self.attack_bonus
        if self.defense_bonus:
            stats["defense"] = scale * self.defense_bonus
        if self.speed_bonus:
            stats["speed"] = scale * self.speed_bonus
        return stats

    def get_item_stats_text(self, scale: int = 1) -> str:
        stat_texts = []
        stat_safe_emojis = {
            "health": "♥",
            "max_health": "♥",
            "energy": "⚡",
            "max_energy": "⚡",
            "attack": "⚔",
            "defense": "🛡",
            "speed": "🥾",
        }
        for stat_name, stat_value in self.effective_stats(scale=scale).items():
            stat_emoji = stat_safe_emojis.get(stat_name, "")
            stat_texts.append(f"{stat_emoji}{numsign(intcomma(stat_value))}")
        return " ".join(stat_texts)


# ----------------------------------------------------------------------------------------------------
# * Item Stack
# ----------------------------------------------------------------------------------------------------
class ItemStack(Model):
    id: str = Field(primary_field=True)
    item: Item = Reference()
    quantity: NonNegativeInt = 1
