from datetime import datetime
from typing import Any, ClassVar, Optional, cast

from odmantic import Field, Model
from pydantic import NonNegativeInt

from db.item import Item, ItemStack, ItemType
from utils.misc import clamp, text_progress_bar


# ----------------------------------------------------------------------------------------------------
# * DM Actor
# ----------------------------------------------------------------------------------------------------
class DmActor(Model):
    model_config = {"collection": "dm_actors"}

    id: int = Field(primary_field=True)
    name: str = ""
    display_name: str = ""

    # AI
    ai_interacted_at: Optional[datetime] = None
    ai_chat_history: list[dict[str, Any]] = []


# ----------------------------------------------------------------------------------------------------
# * Actor
# ----------------------------------------------------------------------------------------------------
class Actor(Model):
    model_config = {"collection": "actors"}

    id: int = Field(primary_field=True)
    name: str = ""
    display_name: str = ""
    is_member: bool = True  # Still member in the server

    # AI
    ai_interacted_at: Optional[datetime] = None  # Last time actor interacted with AI

    # Combat stats
    health: NonNegativeInt = 1
    base_max_health: NonNegativeInt = 1
    extra_max_health: NonNegativeInt = 0
    energy: NonNegativeInt = 1
    base_max_energy: NonNegativeInt = 1
    extra_max_energy: NonNegativeInt = 0
    base_attack: NonNegativeInt = 1
    extra_attack: NonNegativeInt = 0
    base_defense: NonNegativeInt = 1
    extra_defense: NonNegativeInt = 0
    base_speed: NonNegativeInt = 1
    extra_speed: NonNegativeInt = 0

    # Gold, Items, & Equipment
    gold: NonNegativeInt = 0
    item_stacks: dict[str, ItemStack] = {}
    equipped_items: dict[str, Item] = {}
    MAX_ITEMS: ClassVar[int] = 20
    MAX_EQUIPMENT: ClassVar[int] = 3

    # Progress
    xp: NonNegativeInt = 0
    level: NonNegativeInt = 0
    rank: NonNegativeInt = 0
    LEVEL_BASE_XP: ClassVar[int] = 100
    LEVEL_EXPONENT: ClassVar[float] = 2.5
    MAX_LEVEL: ClassVar[int] = 99
    RANK_BASE_LEVEL: ClassVar[int] = 30
    RANK_EXPONENT: ClassVar[float] = 1
    RANK_NAMES: ClassVar[list[str]] = [
        "?",
        "Iron",
        "Bronze",
        "Silver",
        "Gold",
        "Platinum",
        "Emerald",
        "Diamond",
        "Master",
        "Grandmaster",
        "Challenger",
    ]
    MAX_RANKS: ClassVar[int] = len(RANK_NAMES)

    # ----------------------------------------------------------------------------------------------------

    @property
    def max_health(self):
        return self.base_max_health + self.extra_max_health

    @property
    def max_energy(self):
        return self.base_max_energy + self.extra_max_energy

    @property
    def attack(self):
        return self.base_attack + self.extra_attack

    @property
    def defense(self):
        return self.base_defense + self.extra_defense

    @property
    def speed(self):
        return self.base_speed + self.extra_speed

    @property
    def rank_name(self) -> str:
        """Get name of current rank."""
        return self.RANK_NAMES[self.rank]

    # ----------------------------------------------------------------------------------------------------

    @property
    def next_level_xp(self) -> int:
        """Calculate xp required to reach next level."""
        return self._tier_points(
            self.level + 1, self.LEVEL_BASE_XP, self.LEVEL_EXPONENT
        )

    @property
    def next_rank_level(self) -> int:
        """Calculate level required to reach next rank."""
        return self._tier_points(
            self.rank + 1, self.RANK_BASE_LEVEL, self.RANK_EXPONENT
        )

    @staticmethod
    def _tier_points(tier: int, base_points: int, exponent: float) -> int:
        """Calculate points of given tier based on exponential growth."""
        return int(base_points * (tier**exponent))

    # ----------------------------------------------------------------------------------------------------

    @property
    def health_bar(self) -> str:
        return text_progress_bar(self.health, self.base_max_health, 6, "▰", "▱")

    @property
    def energy_bar(self) -> str:
        return text_progress_bar(self.energy, self.max_energy, 6, "▰", "▱")

    @property
    def rank_bar(self) -> str:
        return text_progress_bar(self.rank, self.MAX_RANKS, 5, "⭐", "☆")

    @property
    def level_bar(self) -> str:
        return text_progress_bar(self.level, self.next_rank_level, 5, "⬥", "⬦")

    @property
    def xp_bar(self) -> str:
        return text_progress_bar(self.xp, self.next_level_xp, 10, "■", "□")

    # ----------------------------------------------------------------------------------------------------

    def try_level_up(self) -> bool:
        """Check if player has enough xp to level up and increment level if so."""
        initial_level = self.level
        while self.xp >= self.next_level_xp and self.level < self.MAX_LEVEL:
            self.level += 1
        return self.level > initial_level

    def try_rank_up(self) -> bool:
        """Check if player has enough level to rank up and increment rank if so."""
        initial_rank = self.rank
        while self.level >= self.next_rank_level and self.rank < self.MAX_RANKS:
            self.rank += 1
        return self.rank > initial_rank

    def add_item_stats(self, item: Item, scale: int = 1):
        """Apply scaled item stat bonuses to actor stats."""
        self.health = cast(
            int,
            clamp(self.health + (scale * item.health_bonus), 0, self.max_health),
        )
        self.energy = cast(
            int,
            clamp(self.energy + (scale * item.energy_bonus), 0, self.max_energy),
        )
        self.extra_max_health += scale * item.max_health_bonus
        self.extra_max_energy += scale * item.max_energy_bonus
        self.extra_attack += scale * item.attack_bonus
        self.extra_defense += scale * item.defense_bonus
        self.extra_speed += scale * item.speed_bonus

    # ----------------------------------------------------------------------------------------------------

    @classmethod
    def level_xp_table(
        cls, min_level: int = 0, max_level: int = 10
    ) -> list[tuple[int, int]]:
        """Get (level, xp) tuple list of levels with corresponding minimum xp required."""
        min_level = max(0, min_level)
        max_level = max(min_level, max_level)
        lines = []
        for level in range(min_level, max_level + 1):
            xp = cls._tier_points(level, cls.LEVEL_BASE_XP, cls.LEVEL_EXPONENT)
            lines.append((level, xp))
        return lines

    @classmethod
    def rank_level_table(
        cls, min_rank: int = 0, max_rank: int = 10
    ) -> list[tuple[str, int]]:
        """Get (rank_name, level) tuple list of ranks with corresponding minimum level required."""
        min_rank = max(0, min_rank)
        max_rank = max(min_rank, max_rank)
        lines = []
        for rank in range(min_rank, max_rank + 1):
            level = cls._tier_points(rank, cls.RANK_BASE_LEVEL, cls.RANK_EXPONENT)
            rank_name = cls.RANK_NAMES[rank] if rank < cls.MAX_RANKS - 1 else str(rank)
            lines.append((rank_name, level))
        return lines
