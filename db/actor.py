from datetime import datetime, timedelta, timezone
from typing import Any, ClassVar, Optional, cast

from humanize import precisedelta
from odmantic import Field, Model
from pydantic import NonNegativeFloat, NonNegativeInt

from db.item import Item, ItemStack, ItemType
from db.main import ActToml
from db.rank import Rank
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

    # Membership
    id: int = Field(primary_field=True)
    name: str = ""
    display_name: str = ""
    is_member: bool = True  # Still member in the server

    # AI
    attacked_at: Optional[datetime] = None  # Last time actor attacked another actor

    # Health & Energy
    health: NonNegativeInt = 10
    health_max_base: NonNegativeInt = 10
    health_max_extra: int = 0
    energy: NonNegativeInt = 5
    energy_max_base: NonNegativeInt = 5
    energy_max_extra: int = 0

    # Attack, Defense, & Speed
    attack_base: NonNegativeInt = 1
    attack_extra: int = 0
    defense_base: NonNegativeInt = 1
    defense_extra: int = 0
    speed_base: NonNegativeInt = 1
    speed_extra: int = 0

    # Combat
    ai_interacted_at: Optional[datetime] = None  # Last time actor interacted with AI
    ATTACK_ENERGY_COST: ClassVar[NonNegativeInt] = 1
    ATTACK_COOLDOWN_BASE: ClassVar[NonNegativeFloat] = 30.0  # seconds
    ATTACK_COOLDOWN_MIN: ClassVar[NonNegativeFloat] = 2.0  # seconds
    SPEED_COOLDOWN_FACTOR: ClassVar[NonNegativeFloat] = (
        0.5  # 0.1 => 10 speed <=> -1 sec cooldown
    )

    # Gold
    gold: int = 0  # Negative gold allowed
    GOLD_REWARD_BASE: ClassVar[NonNegativeInt] = 100
    GOLD_REWARD_PER_LEVEL: ClassVar[NonNegativeInt] = 100

    # Items
    item_stacks: dict[str, ItemStack] = {}
    items_equipped: dict[str, Item] = {}
    ITEMS_MAX: ClassVar[NonNegativeInt] = 20
    ITEMS_EQUIP_MAX: ClassVar[NonNegativeInt] = 3

    # Level & XP
    level: NonNegativeInt = 0
    xp: NonNegativeInt = 0
    LEVEL_XP_BASE: ClassVar[NonNegativeInt] = 100
    LEVEL_EXPONENT: ClassVar[NonNegativeFloat] = 2.5
    LEVEL_MAX: ClassVar[NonNegativeInt] = 99

    # Elo
    elo: int = 1500  # Starting Elo rating
    ELO_BASE: ClassVar[NonNegativeInt] = 1200  # Starting point for Iron (Wood is 0)
    ELO_GROWTH_RATE: ClassVar[NonNegativeInt] = 100  # Linear increase per rank
    ELO_K_FACTOR: ClassVar[NonNegativeInt] = 32  # Rating change per match

    # duels
    wins: NonNegativeInt = 0
    losses: NonNegativeInt = 0
    placement_duels: NonNegativeInt = 0
    PLACEMENT_DUELS_MAX: ClassVar[NonNegativeInt] = 10

    # Rank
    RANKS: ClassVar[list[Rank]] = ActToml.load_list(Rank)
    RANK_MAX: ClassVar[NonNegativeInt] = len(RANKS) - 1

    # ----------------------------------------------------------------------------------------------------

    @property
    def max_health(self):
        return max(0, self.health_max_base + self.health_max_extra)

    @property
    def max_energy(self):
        return max(0, self.energy_max_base + self.energy_max_extra)

    @property
    def attack(self):
        return max(0, self.attack_base + self.attack_extra)

    @property
    def defense(self):
        return max(0, self.defense_base + self.defense_extra)

    @property
    def speed(self):
        return max(0, self.speed_base + self.speed_extra)

    # ----------------------------------------------------------------------------------------------------

    @property
    def has_energy_to_attack(self) -> bool:
        """Check if player has enough energy to attack."""
        return self.energy >= self.ATTACK_ENERGY_COST

    @property
    def has_cooled_down_since_last_attack(self) -> bool:
        return self.remaining_attack_cooldown_timedelta.total_seconds() <= 0

    @property
    def remaining_attack_cooldown_timedelta(self) -> timedelta:
        if self.attacked_at:
            self.attacked_at = self.attacked_at.replace(
                tzinfo=timezone.utc
            )  # If naive datetime, Assign timezone info
            return self.attack_cooldown_timedelta - (
                datetime.now(timezone.utc) - self.attacked_at
            )
        return timedelta(seconds=0)

    @property
    def attack_cooldown_timedelta(self) -> timedelta:
        """Calculate minimum cooldown time (seconds) required between consecutive attacks."""
        return timedelta(
            seconds=max(
                self.ATTACK_COOLDOWN_MIN,
                self.ATTACK_COOLDOWN_BASE - (self.speed * self.SPEED_COOLDOWN_FACTOR),
            )
        )

    # ----------------------------------------------------------------------------------------------------

    def try_level_up(self) -> bool:
        """Check if player has enough xp to level up and increment level if so."""
        initial_level = self.level
        while self.xp >= self.next_level_xp and self.level < self.LEVEL_MAX:
            self.level += 1
        return self.level > initial_level

    @classmethod
    def level_xp(cls, level: int):
        """Calculate xp required to reach given level."""
        return int(scaled_power(level, cls.LEVEL_XP_BASE, cls.LEVEL_EXPONENT))

    @property
    def next_level_xp(self) -> int:
        """Calculate xp required to reach next level."""
        return self.level_xp(self.level + 1)

    # ----------------------------------------------------------------------------------------------------

    @property
    def duels(self) -> NonNegativeInt:
        """Get total number of duels fought (wins + losses)."""
        return self.wins + self.losses

    def record_duel(self, opponent_elo: int, won: bool) -> None:
        """Record duel result and update elo rating accordingly."""
        expected = self.expected_score(opponent_elo)
        actual = 1 if won else 0
        elo_change = int(self.ELO_K_FACTOR * (actual - expected))
        self.elo += elo_change
        if won:
            self.wins += 1
        else:
            self.losses += 1
        self.placement_duels = min(self.wins + self.losses, self.PLACEMENT_DUELS_MAX)

    # ----------------------------------------------------------------------------------------------------

    @property
    def rank(self) -> Rank | None:
        """Get current rank or None if unranked."""
        if self.duels < self.PLACEMENT_DUELS_MAX:
            return None
        for i in range(len(self.RANKS) - 1, -1, -1):  # Reverse to check highest first
            if self.elo >= self.rank_elo(i):
                return self.RANKS[i]
        return self.RANKS[0]

    def expected_score(self, opponent_elo: int) -> float:
        """Calculate expected score against an opponent."""
        return 1 / (1 + pow(10, (opponent_elo - self.elo) / 400))

    @staticmethod
    def rank_elo(rank_index: int) -> int:
        """Calculate elo rating of given rank index."""
        return (
            Actor.ELO_BASE + (rank_index - 1) * Actor.ELO_GROWTH_RATE
            if rank_index != 0
            else 0
        )

    # ----------------------------------------------------------------------------------------------------

    @classmethod
    def level_gold(cls, level: int) -> int:
        """Calculate gold reward for reaching given level."""
        return (
            cls.GOLD_REWARD_BASE + (cls.GOLD_REWARD_PER_LEVEL * level)
            if level > 0
            else 0
        )

    @property
    def current_level_gold(self) -> int:
        """Calculate gold reward for reaching current level."""
        return self.level_gold(self.level)

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
        self.health_max_extra += scale * item.max_health_bonus
        self.energy_max_extra += scale * item.max_energy_bonus
        self.attack_extra += scale * item.attack_bonus
        self.defense_extra += scale * item.defense_bonus
        self.speed_extra += scale * item.speed_bonus

    def clear_extra_stats(self):
        self.health_max_extra = 0
        self.energy_max_extra = 0
        self.attack_extra = 0
        self.defense_extra = 0
        self.speed_extra = 0

    # ----------------------------------------------------------------------------------------------------

    @property
    def health_bar(self) -> str:
        return text_progress_bar(self.health, self.health_max_base, 10, "▰", "▱")

    @property
    def energy_bar(self) -> str:
        return text_progress_bar(self.energy, self.max_energy, 10, "▰", "▱")

    @property
    def rank_bar(self) -> str:
        return text_progress_bar(
            self.rank.id if self.rank else -1, self.RANK_MAX, 10, "⭐", "☆"
        )

    @property
    def level_bar(self) -> str:
        return text_progress_bar(self.level, self.LEVEL_MAX, 10, "■", "□")

    @property
    def xp_bar(self) -> str:
        return text_progress_bar(self.xp, self.next_level_xp, 10, "■", "□")

    # ----------------------------------------------------------------------------------------------------

    @classmethod
    def level_xp_gold_table(
        cls, min_level: int = 0, max_level: int = 10
    ) -> list[tuple[int, int, int]]:
        """Get (level, xp, gold) tuple list of levels with corresponding minimum xp required and gold rewarded."""
        min_level = max(0, min_level)
        max_level = max(min_level, max_level)
        lines = []
        for level in range(min_level, max_level + 1):
            xp = cls.level_xp(level)
            gold = cls.level_gold(level)
            lines.append((level, xp, gold))
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
                if rank_index <= cls.RANK_MAX
                else Rank(id=rank_index, name=f"Untitled Rank {rank_index}")
            )
            lines.append((rank, elo))
        return lines
