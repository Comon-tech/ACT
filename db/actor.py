from datetime import datetime
from typing import Any, ClassVar, Optional, cast

from odmantic import Field, Model
from pydantic import NonNegativeFloat, NonNegativeInt

from db.item import Item, ItemStack, ItemType
from db.rank import RANKS, Rank
from utils.misc import clamp, scaled_linear, scaled_power, text_progress_bar


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

    # Member
    id: int = Field(primary_field=True)
    name: str = ""
    display_name: str = ""
    is_member: bool = True  # Still member in the server

    # Time
    ai_interacted_at: Optional[datetime] = None  # Last time actor interacted with AI
    attacked_at: Optional[datetime] = None  # Last time actor attacked another actor

    # Health & Energy
    health: NonNegativeInt = 10
    base_max_health: NonNegativeInt = 10
    extra_max_health: int = 0
    energy: NonNegativeInt = 3
    base_max_energy: NonNegativeInt = 3
    extra_max_energy: int = 0

    # Attack, Defense, & Speed
    base_attack: NonNegativeInt = 1
    extra_attack: int = 0
    base_defense: NonNegativeInt = 1
    extra_defense: int = 0
    base_speed: NonNegativeInt = 1
    extra_speed: int = 0

    # Gold, Items, & Equipment
    gold: NonNegativeInt = 0
    item_stacks: dict[str, ItemStack] = {}
    equipped_items: dict[str, Item] = {}
    MAX_ITEMS: ClassVar[NonNegativeInt] = 20
    MAX_EQUIPMENT: ClassVar[NonNegativeInt] = 3

    # Leveling
    level: NonNegativeInt = 0
    xp: NonNegativeInt = 0
    LEVEL_BASE_XP: ClassVar[NonNegativeInt] = 100
    LEVEL_EXPONENT: ClassVar[NonNegativeFloat] = 2.5
    MAX_LEVEL: ClassVar[NonNegativeInt] = 99

    # Ranking
    wins: NonNegativeInt = 0
    losses: NonNegativeInt = 0
    elo: int = 1500  # Starting Elo rating
    placement_duels: NonNegativeInt = 0
    BASE_ELO: ClassVar[NonNegativeInt] = 1200  # Starting point for Iron (Wood is 0)
    ELO_GROWTH_RATE: ClassVar[NonNegativeInt] = 100  # Linear increase per rank
    MAX_PLACEMENT_DUELS: ClassVar[NonNegativeInt] = 10
    K_FACTOR: ClassVar[NonNegativeInt] = 32  # Rating change per match
    RANKS: ClassVar[list[Rank]] = RANKS
    MAX_RANK: ClassVar[NonNegativeInt] = len(RANKS) - 1

    # ----------------------------------------------------------------------------------------------------

    @property
    def duels(self) -> NonNegativeInt:
        """Get total number of duels fought (wins + losses)."""
        return self.wins + self.losses

    @property
    def rank(self) -> Rank | None:
        """Get current rank or None if unranked."""
        if self.duels < self.MAX_PLACEMENT_DUELS:
            return None
        for i in range(len(self.RANKS) - 1, -1, -1):  # Reverse to check highest first
            if self.elo >= self.rank_elo(i):
                return self.RANKS[i]
        return self.RANKS[0]

    def expected_score(self, opponent_elo: int) -> float:
        """Calculate expected score against an opponent"""
        return 1 / (1 + pow(10, (opponent_elo - self.elo) / 400))

    # ----------------------------------------------------------------------------------------------------

    @property
    def max_health(self):
        return max(0, self.base_max_health + self.extra_max_health)

    @property
    def max_energy(self):
        return max(0, self.base_max_energy + self.extra_max_energy)

    @property
    def attack(self):
        return max(0, self.base_attack + self.extra_attack)

    @property
    def defense(self):
        return max(0, self.base_defense + self.extra_defense)

    @property
    def speed(self):
        return max(0, self.base_speed + self.extra_speed)

    # ----------------------------------------------------------------------------------------------------

    @property
    def next_level_xp(self) -> int:
        """Calculate xp required to reach next level."""
        return self.level_xp(self.level + 1)

    @classmethod
    def level_xp(cls, level: int):
        """Calculate xp required to reach given level."""
        return int(scaled_power(level, cls.LEVEL_BASE_XP, cls.LEVEL_EXPONENT))

    @staticmethod
    def rank_elo(rank_index: int) -> int:
        """Calculate elo rating of given rank index."""
        return (
            Actor.BASE_ELO + (rank_index - 1) * Actor.ELO_GROWTH_RATE
            if rank_index != 0
            else 0
        )

    # ----------------------------------------------------------------------------------------------------

    @property
    def health_bar(self) -> str:
        return text_progress_bar(self.health, self.base_max_health, 6, "▰", "▱")

    @property
    def energy_bar(self) -> str:
        return text_progress_bar(self.energy, self.max_energy, 6, "▰", "▱")

    @property
    def rank_bar(self) -> str:
        return text_progress_bar(
            self.rank.id if self.rank else -1, self.MAX_RANK, 5, "⭐", "☆"
        )

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

    def record_duel(self, opponent_elo: int, won: bool) -> None:
        """Record duel result and update elo rating accordingly."""
        expected = self.expected_score(opponent_elo)
        actual = 1 if won else 0
        elo_change = int(self.K_FACTOR * (actual - expected))
        self.elo += elo_change
        if won:
            self.wins += 1
        else:
            self.losses += 1
        self.placement_duels = min(self.wins + self.losses, self.MAX_PLACEMENT_DUELS)

    # ----------------------------------------------------------------------------------------------------

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

    def clear_extra_stats(self):
        self.extra_max_health = 0
        self.extra_max_energy = 0
        self.extra_attack = 0
        self.extra_defense = 0
        self.extra_speed = 0

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
            xp = cls.level_xp(level)
            lines.append((level, xp))
        return lines

    @classmethod
    def rank_elo_table(
        cls, min_rank_index: int = 0, max_rank_index: int = 2500
    ) -> list[tuple[Rank, int]]:
        """Get (rank, elo) tuple list of levels with corresponding minimum xp required."""
        min_rank_index = max(0, min_rank_index)
        max_rank_index = max(min_rank_index, max_rank_index)
        lines = []
        for rank_index in range(min_rank_index, max_rank_index + 1):
            elo = cls.rank_elo(rank_index)
            rank = (
                cls.RANKS[rank_index]
                if rank_index <= cls.MAX_RANK
                else Rank(id=rank_index, name=f"Untitled Rank {rank_index}")
            )
            lines.append((rank, elo))
        return lines
