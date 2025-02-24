from datetime import datetime
from typing import ClassVar, Optional

from odmantic import Field, Model
from pydantic import NonNegativeInt

from utils.misc import text_progress_bar


# ----------------------------------------------------------------------------------------------------
# * Actor
# ----------------------------------------------------------------------------------------------------
class Actor(Model):
    model_config = {"collection": "actors"}

    id: int = Field(primary_field=True)
    name: str = ""
    display_name: str = ""

    ai_interacted_at: Optional[datetime] = None  # Last time actor interacted with AI

    xp: NonNegativeInt = 0
    level: NonNegativeInt = 0
    rank: NonNegativeInt = 0
    gold: NonNegativeInt = 0
    items: list[str] = []

    LEVEL_BASE_XP: ClassVar[int] = 100
    LEVEL_EXPONENT: ClassVar[float] = 2.5
    MAX_LEVEL: ClassVar[int] = 99

    RANK_BASE_LEVEL: ClassVar[int] = 30
    RANK_EXPONENT: ClassVar[float] = 1
    RANK_NAMES: ClassVar[list[str]] = [
        "Unranked",
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
    def rank_name(self) -> str:
        """Get name of current rank."""
        return self.RANK_NAMES[self.rank - 1]

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

    def try_level_up(self) -> bool:
        """Check if player has enough xp to level up and increment level if so."""
        initial_level = self.level
        while self.xp >= self.next_level_xp and self.level < self.MAX_LEVEL:
            self.level += 1
        return self.level > initial_level

    def try_rank_up(self) -> bool:
        """Check if player has enough level to rank up and increment rank if so."""
        initial_rank = self.rank
        if self.level >= self.next_rank_level and self.rank < self.MAX_RANKS:
            self.rank += 1
        return self.rank > initial_rank

    # ----------------------------------------------------------------------------------------------------

    @property
    def level_bar(self) -> str:
        return text_progress_bar(self.level, self.MAX_LEVEL, 5, "⭐", "☆")

    @property
    def xp_bar(self) -> str:
        return text_progress_bar(self.xp, self.next_level_xp, 10, "■", "□")

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
