import tomllib
from enum import Enum
from pathlib import Path
from typing import Callable, Literal, Self

from humanize import intcomma
from odmantic import Field, Model, Reference
from pydantic import NonNegativeInt

from utils.misc import numsign


# ----------------------------------------------------------------------------------------------------
# * Rank
# ----------------------------------------------------------------------------------------------------
class Rank(Model):
    model_config = {"collection": "ranks"}

    id: int = Field(primary_field=True)
    name: str
    description: str = ""
    emoji: str = ""
    alt_emoji: str = "🎖"
    icon_url: str = ""


# ----------------------------------------------------------------------------------------------------
# * Ranks
# ----------------------------------------------------------------------------------------------------
RANKS = [
    Rank(
        id=0,
        name="Wood",
        description="The humble beginning, carved from nature’s roots.",
        emoji="",
        alt_emoji="🌳",
        icon_url="",
    ),
    Rank(
        id=1,
        name="Iron",
        description="A sturdy start, forged in the fires of effort.",
        emoji="",
        alt_emoji="⚙️",
        icon_url="",
    ),
    Rank(
        id=2,
        name="Bronze",
        description="A step up, blending strength with a touch of shine.",
        emoji="",
        alt_emoji="🥉",
        icon_url="",
    ),
    Rank(
        id=3,
        name="Silver",
        description="A gleaming rank for those proving their worth.",
        emoji="",
        alt_emoji="🥈",
        icon_url="",
    ),
    Rank(
        id=4,
        name="Gold",
        description="A golden milestone of skill and prestige.",
        emoji="",
        alt_emoji="🥇",
        icon_url="",
    ),
    Rank(
        id=5,
        name="Platinum",
        description="A rare metal rank for the near-elite.",
        emoji="",
        alt_emoji="💿",
        icon_url="",
    ),
    Rank(
        id=6,
        name="Amethyst",
        description="A purple gem marking the rise to greatness.",
        emoji="",
        alt_emoji="💜",
        icon_url="",
    ),
    Rank(
        id=7,
        name="Emerald",
        description="A rich green jewel of advanced mastery.",
        emoji="",
        alt_emoji="💚",
        icon_url="",
    ),
    Rank(
        id=8,
        name="Sapphire",
        description="A deep blue shine of near-perfection.",
        emoji="",
        alt_emoji="💙",
        icon_url="",
    ),
    Rank(
        id=9,
        name="Ruby",
        description="A fiery red crown for the almost-unbeatable.",
        emoji="",
        alt_emoji="❤️",
        icon_url="",
    ),
    Rank(
        id=10,
        name="Diamond",
        description="The ultimate rank, sparkling at the top.",
        emoji="",
        alt_emoji="💎",
        icon_url="",
    ),
]
