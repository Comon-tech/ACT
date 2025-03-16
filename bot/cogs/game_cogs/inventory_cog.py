from typing import Callable

from discord import Embed, Interaction, app_commands
from discord.ext.commands import GroupCog
from humanize import intcomma
from tabulate import WIDE_CHARS_MODE, tabulate

from bot.main import ActBot
from bot.ui import EmbedX
from db.actor import Actor
from db.item import ITEMS, Item, ItemStack, ItemType
from utils.misc import numsign


def add_preview_notice(embed: Embed):
    embed.set_author(name="FEATURE PREVIEW")
    embed.add_field(name="", value="", inline=False)
    embed.add_field(name="", value="")
    embed.add_field(
        name=":warning: Important Notice",
        value="This feature is not yet functional. "
        "It's a work-in-progress and will be released in a future update. "
        "Thank you for your patience. 🙏",
    )
    return embed


# ----------------------------------------------------------------------------------------------------
# * Inventory Cog
# ----------------------------------------------------------------------------------------------------
class InventoryCog(
    GroupCog, group_name="items", description="Allows players to use items."
):
    BUYABLE_ITEMS: list[Item]

    def __init__(self, bot: ActBot):
        self.bot = bot
        self.BUYABLE_ITEMS = [item for item in ITEMS if item.is_buyable == True]
        self.buy.autocomplete("item_id")(self.buyable_items_autocomplete)
        self.store.autocomplete("item_id")(self.buyable_items_autocomplete)
        self.equip.autocomplete("item_id")(self.actor_equippable_items_autocomplete)

    # ----------------------------------------------------------------------------------------------------

    @app_commands.guild_only()
    @app_commands.command(description="View your items or another member's items")
    async def bag(self, interaction: Interaction):
        embed = EmbedX.info(emoji="🎒", title="Inventory")
        actor = self.bot.get_db(interaction.guild).find_one(
            Actor, Actor.id == interaction.user.id
        ) or self.bot.create_actor(interaction.user)

        item_stacks = actor.item_stacks
        if item_stacks:
            midpoint = len(item_stacks) // 2
            item_stack_row: Callable[[ItemStack], str] = lambda item_stack: (
                f"{item_stack.item.emoji} **{item_stack.item.name} `{item_stack.quantity}`**"
            )
            first_column = [
                item_stack_row(item_stack) for item_stack in item_stacks[:midpoint]
            ]
            second_column = [
                item_stack_row(item_stack) for item_stack in item_stacks[midpoint:]
            ]
            embed.add_field(name="", value="\n".join(first_column), inline=True)
            embed.add_field(name="", value="\n".join(second_column), inline=True)
        else:
            embed.add_field(name="", value="_No items_")

        equipped_items = actor.equipped_items
        embed.add_field(name="Equipment", value="", inline=False)
        if equipped_items:
            midpoint = len(item_stacks) // 2
            equipped_item_row: Callable[[Item], str] = lambda item: (
                f"{item.alt_emoji} **{item.name}**"
            )
            first_column = [
                equipped_item_row(item) for item in equipped_items[:midpoint]
            ]
            second_column = [
                equipped_item_row(item) for item in equipped_items[midpoint:]
            ]
            embed.add_field(name="", value="\n".join(first_column), inline=True)
            embed.add_field(name="", value="\n".join(second_column), inline=True)
        else:
            embed.add_field(name="", value="_No items_")

        await interaction.response.send_message(embed=embed)

    @app_commands.guild_only()
    @app_commands.command(description="View purchasable items")
    @app_commands.rename(item_id="item")
    @app_commands.describe(item_id="Choose item you wish to view")
    async def store(self, interaction: Interaction, item_id: str = ""):
        if item_id:
            item = next(
                (item for item in self.BUYABLE_ITEMS if item.id == item_id), None
            )
            if not item:
                await interaction.response.send_message(
                    embed=EmbedX.error(f"Invalid **item** input: `{item_id}`\n"),
                    ephemeral=True,
                )
                return
            embed = EmbedX.info(
                emoji=item.alt_emoji,
                title=item.name,
                description=item.description,
            )
            embed.add_field(name="Price", value=f"💰 **{intcomma(item.price)}**")
            if item.health_bonus:
                embed.add_field(
                    name="Health",
                    value=f":heart: **{numsign(intcomma(item.health_bonus))}**",
                )
            if item.energy_bonus:
                embed.add_field(
                    name="Energy",
                    value=f"⚡ **{numsign(intcomma(item.energy_bonus))}**",
                )
            if item.max_health_bonus:
                embed.add_field(
                    name="Max Health",
                    value=f":heart: **{numsign(intcomma(item.max_health_bonus))}**",
                )
            if item.max_energy_bonus:
                embed.add_field(
                    name="Max Energy",
                    value=f"⚡ **{numsign(intcomma(item.max_energy_bonus))}**",
                )
            if item.attack_bonus:
                embed.add_field(
                    name="Attack",
                    value=f":crossed_swords: **{numsign(intcomma(item.attack_bonus))}**",
                )
            if item.defense_bonus:
                embed.add_field(
                    name="Defense",
                    value=f"🛡 **{numsign(intcomma(item.defense_bonus))}**",
                )
            if item.speed_bonus:
                embed.add_field(
                    name="Speed", value=f"🥾 **{numsign(intcomma(item.speed_bonus))}**"
                )
            embed.set_thumbnail(url=item.icon_url)
            await interaction.response.send_message(embed=embed)
        else:
            embed = EmbedX.info(emoji="🏬", title="Store")
            items = self.BUYABLE_ITEMS
            if items:
                midpoint = len(items) // 2
                row: Callable[[Item], str] = (
                    lambda item: f"{item.emoji or item.alt_emoji} **{item.name} `💰{intcomma(item.price)}`**"
                )
                first_column = [row(item) for item in items[:midpoint]]
                second_column = [row(item) for item in items[midpoint:]]
                embed.add_field(name="", value="\n".join(first_column))
                embed.add_field(name="", value="\n".join(second_column))
            else:
                embed.add_field(name="", value="_No items_")
            embed.add_field(
                name="Buy",
                value=f"🛒 `/{self.buy.qualified_name}`",
                inline=False,
            )
            await interaction.response.send_message(embed=embed)

    @app_commands.guild_only()
    @app_commands.guild_only()
    @app_commands.command(description="Purchase an item")
    @app_commands.rename(item_id="item")
    @app_commands.describe(
        item_id="Choose item you wish to buy", quantity="Amount of items to buy"
    )
    async def buy(self, interaction: Interaction, item_id: str, quantity: int = 1):
        item = next((item for item in self.BUYABLE_ITEMS if item.id == item_id), None)
        if not item:
            await interaction.response.send_message(
                embed=EmbedX.error(f"Invalid **item** input: `{item_id}`\n"),
                ephemeral=True,
            )
            return

        member = interaction.user
        total_price = item.price * quantity
        embed = EmbedX.success(
            emoji="🛒",
            title="Purchase",
            description=f"{member.mention} purchased **{quantity}** x {item.alt_emoji} **{item.name}** for 💰 **{total_price}**.",
        )
        embed.set_author(name=member.display_name, icon_url=member.display_avatar)
        embed.set_thumbnail(url=item.icon_url)
        await interaction.response.send_message(embed=add_preview_notice(embed))

    @app_commands.guild_only()
    @app_commands.command(description="Equip an equippable item")
    @app_commands.rename(item_id="item")
    async def equip(self, interaction: Interaction, item_id: str):
        item = next((item for item in self.BUYABLE_ITEMS if item.id == item_id), None)
        await interaction.response.send_message(
            embed=add_preview_notice(
                EmbedX.info(
                    emoji="🎒",
                    title="Item Equipage",
                    description=f"{interaction.user.mention} equipped **{item}**.",
                )
            ),
        )

    @app_commands.guild_only()
    @app_commands.command(description="Use a consumable item")
    async def use(self, interaction: Interaction, item: str):
        await interaction.response.send_message(
            embed=add_preview_notice(
                EmbedX.info(
                    emoji="🎒",
                    title="Item Consumption",
                    description=f"{interaction.user.mention} used **{item}**.",
                )
            ),
        )

    # ----------------------------------------------------------------------------------------------------

    async def buyable_items_autocomplete(
        self, interaction: Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        return [
            app_commands.Choice(
                name=f"{item.alt_emoji} {item.name} ― 💰{intcomma(item.price)}",
                value=item.id,
            )
            for item in [
                item
                for item in self.BUYABLE_ITEMS
                if current.lower() in item.name.lower()
            ][:25]
        ]

    async def actor_equippable_items_autocomplete(
        self, interaction: Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        actor = self.bot.get_db(interaction.guild).find_one(
            Actor, Actor.id == interaction.user.id
        ) or self.bot.create_actor(interaction.user)
        return [
            app_commands.Choice(
                name=f"{item.alt_emoji} {item.name}",
                value=item.id,
            )
            for item in [
                item_stack.item
                for item_stack in actor.item_stacks
                if item_stack.item.type == ItemType.EQUIPPABLE
                and current.lower() in item_stack.item.name.lower()
            ][:25]
        ]
