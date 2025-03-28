import tomllib
from enum import Enum
from pathlib import Path
from typing import Callable, Literal, Self

from humanize import intcomma
from odmantic import Field, Model, Reference
from pydantic import NonNegativeInt

from utils.misc import numsign


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
    name: str = ""
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


# ----------------------------------------------------------------------------------------------------
# * Items
# ----------------------------------------------------------------------------------------------------
ITEMS = [
    # ----------------------------------------------------------------------------------------------------
    # * Weapon Equippables
    # ----------------------------------------------------------------------------------------------------
    Item(
        id="dagger",
        name="Dagger",
        description="A lightweight, curved dagger for quick strikes.",
        emoji="<:dagger:1350710430519267359>",
        alt_emoji="🗡",
        icon_url="https://cdn.discordapp.com/attachments/1348859490203734057/1350655923160354907/dagger.png?ex=67d787da&is=67d6365a&hm=582b04b4d8dce9de72c15630cd3f4e83ca35db88aa01dc688876c510fdddb7f7&",
        type=ItemType.EQUIPPABLE,
        attack_bonus=1,
        speed_bonus=2,
        price=1000,
    ),
    Item(
        id="short_sword",
        name="Short Sword",
        description="A versatile one-handed sword for balanced combat.",
        emoji="<:short_sword:1350710454271344640>",
        alt_emoji="⚔️",
        icon_url="https://cdn.discordapp.com/attachments/1348859490203734057/1350655933486862439/short_sword.png?ex=67d787dc&is=67d6365c&hm=8b88ef796761eb5a0a5756d37250c1b26418942e4b4f1edf10e8f1b52ea6f1b9&",
        type=ItemType.EQUIPPABLE,
        attack_bonus=2,
        speed_bonus=1,
        price=2500,
    ),
    Item(
        id="sword",
        name="Sword",
        description="A standard long sword for reliable combat.",
        emoji="<:sword:1350710458302201979>",
        alt_emoji="⚔️",
        icon_url="https://cdn.discordapp.com/attachments/1348859490203734057/1350655934141038616/sword.png?ex=67d787dc&is=67d6365c&hm=ca9e16a8374db65f3d4b940a8ae7c883eda4c1891fca47fc33c46dd0abec9b2a&",
        type=ItemType.EQUIPPABLE,
        attack_bonus=3,
        speed_bonus=0,
        price=3500,
    ),
    Item(
        id="scimitar",
        name="Scimitar",
        description="A curved sword designed for powerful slashing attacks.",
        emoji="<:scimitar:1350710445610242070>",
        alt_emoji="⚔️",
        icon_url="https://cdn.discordapp.com/attachments/1348859490203734057/1350655932568309760/scimitar.png?ex=67d787dc&is=67d6365c&hm=4159155d521e71c48f9248a36137f3898b449b61bcb4e27fb5cd7b586e3dbd73&",
        type=ItemType.EQUIPPABLE,
        attack_bonus=3,
        speed_bonus=-1,
        price=4000,
    ),
    Item(
        id="spear",
        name="Spear",
        description="A long-reaching weapon that allows for defensive maneuvers.",
        emoji="<:spear:1350710456335073350>",
        alt_emoji="🔱",
        icon_url="https://cdn.discordapp.com/attachments/1348859490203734057/1350655933830664202/spear.png?ex=67d787dc&is=67d6365c&hm=372e40a86edff2f172ee9e0c8942bc8d75ccbf78200c003d0aa38b2df4df1126&",
        type=ItemType.EQUIPPABLE,
        attack_bonus=2,
        defense_bonus=1,
        price=3000,
    ),
    Item(
        id="axe",
        name="Axe",
        description="A brutal weapon for raw damage but harder to wield defensively.",
        emoji="<:axe:1350710418615697508>",
        alt_emoji="🪓",
        icon_url="https://cdn.discordapp.com/attachments/1348859490203734057/1350655921411461210/axe.png?ex=67d787d9&is=67d63659&hm=fef92de5958e86ddc6e314e6aa1fe33e54322eb6a012a93de139ca7f73dd1a1b&",
        type=ItemType.EQUIPPABLE,
        attack_bonus=3,
        defense_bonus=-1,
        price=3500,
    ),
    Item(
        id="mace",
        name="Mace",
        description="A blunt weapon effective against armored foes.",
        emoji="<:mace:1350710438530256927>",
        alt_emoji="🔨",
        icon_url="https://cdn.discordapp.com/attachments/1348859490203734057/1350655931540836353/mace.png?ex=67d787dc&is=67d6365c&hm=a332201cb819a928698d991a833f7565ed76458178fd517ce212884514b425d4&",
        type=ItemType.EQUIPPABLE,
        attack_bonus=2,
        defense_bonus=1,
        price=3000,
    ),
    Item(
        id="bow",
        name="Bow",
        description="A lightweight bow designed for quick shots.",
        emoji="<:bow:1350710424076550164>",
        alt_emoji="🏹",
        icon_url="https://cdn.discordapp.com/attachments/1348859490203734057/1350655922132877375/bow.png?ex=67d787d9&is=67d63659&hm=bcc0f9b37ed26e7a980f49b86b7deff461245ff37faa7a9604ae419c1b1ef997&",
        type=ItemType.EQUIPPABLE,
        attack_bonus=2,
        speed_bonus=1,
        price=3500,
    ),
    # ----------------------------------------------------------------------------------------------------
    # * Armor Equippables
    # ----------------------------------------------------------------------------------------------------
    Item(
        id="shield",
        name="Shield",
        description="A sturdy shield for blocking attacks.",
        emoji="<:shield:1350710449494036610>",
        alt_emoji="🛡️",
        icon_url="https://cdn.discordapp.com/attachments/1348859490203734057/1350655932866232360/shield.png?ex=67d787dc&is=67d6365c&hm=2c6ca7a3edd62fdbe9006320ea435f4c0d50714d1c8776565726a82d09a94b4e&",
        type=ItemType.EQUIPPABLE,
        defense_bonus=2,
        speed_bonus=-1,
        price=2500,
    ),
    Item(
        id="helmet",
        name="Helmet",
        description="Protects the head from critical blows.",
        emoji="<:helmet:1350710433551618058>",
        alt_emoji="⛑️",
        icon_url="https://cdn.discordapp.com/attachments/1348859490203734057/1350655920371404911/helmet.png?ex=67d787d9&is=67d63659&hm=ccebe366e9ec93bfcc9679dc9f2bfc3e75b7e4a9a4ffa22393afcc5d5f055c8d&",
        type=ItemType.EQUIPPABLE,
        defense_bonus=1,
        price=1500,
    ),
    Item(
        id="armor",
        name="Armor",
        description="Standard armor for balanced protection.",
        emoji="<:armor:1350705245625253888>",
        alt_emoji="🦺",
        icon_url="https://cdn.discordapp.com/attachments/1348859490203734057/1350655920962666580/armor.png?ex=67d787d9&is=67d63659&hm=80ab8ea8e8c2fc9f096a6374839d409aeccde039cff87da7f8615ac51a3c8ccf&",
        type=ItemType.EQUIPPABLE,
        max_health_bonus=1,
        defense_bonus=2,
        speed_bonus=0,
        price=3000,
    ),
    Item(
        id="chainmail",
        name="Chainmail",
        description="Medium armor offering better protection but slightly heavier.",
        emoji="<:chainmail:1350710428501803100>",
        alt_emoji="🧥",
        icon_url="https://cdn.discordapp.com/attachments/1348859490203734057/1350655922808164352/chainmail.png?ex=67d787d9&is=67d63659&hm=106ea326b53e1ad5d59d5b661239415ab852603489c0461fd35ec5e373648000&",
        type=ItemType.EQUIPPABLE,
        defense_bonus=3,
        speed_bonus=-1,
        price=4500,
    ),
    # ----------------------------------------------------------------------------------------------------
    # * Footwear Equippables
    # ----------------------------------------------------------------------------------------------------
    Item(
        id="sandals",
        name="Sandals",
        description="Lightweight sandals for basic mobility.",
        emoji="<:sandals:1350710443643109457>",
        alt_emoji="👡",
        icon_url="https://cdn.discordapp.com/attachments/1348859490203734057/1350655932253868114/sandals.png?ex=67d787dc&is=67d6365c&hm=2a86819852e1e282b35e62d142a40947e34f84db1e0960c274b9220aef7b312c&",
        type=ItemType.EQUIPPABLE,
        speed_bonus=1,
        price=1000,
    ),
    Item(
        id="shoes",
        name="Shoes",
        description="Sturdy shoes for comfortable travel.",
        emoji="<:shoes:1350710452228984852>",
        alt_emoji="👞",
        icon_url="https://cdn.discordapp.com/attachments/1348859490203734057/1350655933205839964/shoes.png?ex=67d787dc&is=67d6365c&hm=22eb643751b16521a77c1a0c3b3bb8b8805ca0bff36e4af09c2b0e341c4d629a&",
        type=ItemType.EQUIPPABLE,
        speed_bonus=2,
        price=2000,
    ),
    Item(
        id="boots",
        name="Boots",
        description="Heavy boots for long journeys and rough terrain.",
        emoji="<:boots:1350710421572681838>",
        alt_emoji="🥾",
        icon_url="https://cdn.discordapp.com/attachments/1348859490203734057/1350655921793269853/boots.png?ex=67d787d9&is=67d63659&hm=0b72f2267e232100531686bc6321bd47245cdada5498a2233f4161f6574a1601&",
        type=ItemType.EQUIPPABLE,
        speed_bonus=1,
        defense_bonus=1,
        price=3000,
    ),
    # ----------------------------------------------------------------------------------------------------
    # * Consumables
    # ----------------------------------------------------------------------------------------------------
    Item(
        id="potion",
        name="Potion",
        description="A basic potion that restores health.",
        emoji="<:potion:1350710440950366218>",
        alt_emoji="🧪",
        icon_url="https://cdn.discordapp.com/attachments/1348859490203734057/1350655931947417672/potion.png?ex=67d787dc&is=67d6365c&hm=87bec8eb5769212f444e990d27a245f014dc865eb4fb23b97fa718f2212fe214&",
        type=ItemType.CONSUMABLE,
        health_bonus=3,
        price=20,
    ),
    Item(
        id="honeypot",
        name="Honeypot",
        description="A sweet treat that restores energy.",
        emoji="<:honeypot:1350710436273590294>",
        alt_emoji="🍯",
        icon_url="https://cdn.discordapp.com/attachments/1348859490203734057/1350655931137921036/honeypot.png?ex=67d787db&is=67d6365b&hm=853f6cc0a38c04f416c2eaab15e062009318c4a4a44221b10ee65c2e1c11652d&",
        type=ItemType.CONSUMABLE,
        energy_bonus=3,
        price=20,
    ),
    Item(
        id="cookie",
        name="Cookie",
        description="A delicious cookie that restores a small amount of health and energy.",
        emoji="<:cookie:1351081122267660349>",
        alt_emoji="🍪",
        icon_url="https://cdn.discordapp.com/attachments/1348859490203734057/1351081403634417695/cookie.png?ex=67d9141c&is=67d7c29c&hm=4ae302921dc66a87b29814141acb8ab666386ac15d9167be43926efc8d5d053d&",
        type=ItemType.CONSUMABLE,
        health_bonus=1,
        energy_bonus=1,
        price=4,
    ),
]
