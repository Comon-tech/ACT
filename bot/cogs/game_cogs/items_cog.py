from typing import Callable

from discord import Embed, Interaction, Member, User, app_commands
from discord.abc import Messageable
from discord.ext.commands import Cog
from humanize import intcomma, intword

from bot.main import ActBot
from bot.ui import EmbedX
from db.actor import Actor
from db.item import ITEMS, Item, ItemStack, ItemType
from utils.misc import numsign


# ----------------------------------------------------------------------------------------------------
# * Inventory Cog
# ----------------------------------------------------------------------------------------------------
class InventoryCog(Cog, description="Acquire and use items"):
    STORE_ICON_URL = "https://cdn.discordapp.com/attachments/1349262615431483473/1350655944706752663/store.png?ex=67dad39f&is=67d9821f&hm=df852700992931016996079be4a0cba5a0707db0572ef1d1dc55566aec61d6db&"
    BUYABLE_ITEMS: list[Item]

    def __init__(self, bot: ActBot):
        self.bot = bot
        self.BUYABLE_ITEMS = [item for item in ITEMS if item.is_buyable == True]
        self.buy.autocomplete("item_id")(self.buyable_items_autocomplete)
        self.store.autocomplete("item_id")(self.buyable_items_autocomplete)
        self.equip.autocomplete("item_id")(self.actor_equippable_items_autocomplete)
        self.unequip.autocomplete("item_id")(self.actor_equipped_items_autocomplete)
        self.use.autocomplete("item_id")(self.actor_consumable_items_autocomplete)

    # ----------------------------------------------------------------------------------------------------

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
                emoji=item.emoji or item.alt_emoji,
                title=item.name,
                description=item.description,
            )
            embed.add_field(name="Price", value=f"💰 **{intcomma(item.price)}**")
            embed.set_thumbnail(url=item.icon_url)
            await interaction.response.send_message(
                embed=self.add_item_stat_embed_fields(embed, item, show_mod_emoji=False)
            )
        else:
            embed = EmbedX.info(emoji="🏬", title="Store")
            items = self.BUYABLE_ITEMS
            if items:
                midpoint = len(items) // 2
                row: Callable[[Item], str] = (
                    lambda item: f"{item.emoji or item.alt_emoji} **{item.name} \n"
                    f"`💰{intcomma(item.price)}` `{item.get_item_stats_text()}`**"
                )
                first_column = [row(item) for item in items[:midpoint]]
                second_column = [row(item) for item in items[midpoint:]]
                embed.add_field(name="", value="\n\n".join(first_column))
                embed.add_field(name="", value="\n\n".join(second_column))
            else:
                embed.add_field(name="", value="_No items_")
            embed.set_thumbnail(url=self.STORE_ICON_URL)
            await interaction.response.send_message(embed=embed)

    @app_commands.guild_only()
    @app_commands.guild_only()
    @app_commands.command(description="Purchase an item")
    @app_commands.rename(item_id="item")
    @app_commands.describe(
        item_id="Choose item you wish to buy", quantity="Amount of items to buy"
    )
    async def buy(self, interaction: Interaction, item_id: str, quantity: int = 1):
        # Check guild & member
        member = interaction.user
        if not interaction.guild or not isinstance(member, Member):
            await interaction.response.send_message(
                embed=EmbedX.warning("This command cannot be used in this context."),
                ephemeral=True,
            )
            return

        # Get item
        await interaction.response.defer(ephemeral=True)
        item = next((item for item in self.BUYABLE_ITEMS if item.id == item_id), None)
        if not item:
            await interaction.followup.send(
                embed=EmbedX.error(f"Invalid **item** input: `{item_id}`\n")
            )
            return

        # Check quantity
        if quantity <= 0:
            await interaction.followup.send(
                embed=EmbedX.error(
                    f"Your quantity input value of `{quantity}` is invalid.\nDid you mean **{-quantity if quantity else 1}** ?"
                )
            )
            return

        # Get actor
        db = self.bot.get_db(interaction.guild)
        actor = db.find_one(Actor, Actor.id == member.id) or self.bot.create_actor(
            member
        )

        # Chek actor has enough gold to buy
        total_price = item.price * quantity
        if actor.gold < total_price:
            await interaction.followup.send(
                embed=EmbedX.warning(
                    f"You don't have enough to buy **{item.emoji or item.alt_emoji} {item.name} `x{quantity}`** "
                    f"for **💰 {total_price}** gold.\n"
                    f"You only have **💰 {actor.gold}** gold."
                )
            )
            return

        # Perform transaction
        actor.gold = max(0, actor.gold - total_price)
        item_stack = actor.item_stacks.get(item.id)
        if item_stack:
            item_stack.quantity += quantity
        else:
            item_stack = ItemStack(id=item.id, item=item, quantity=quantity)
        actor.item_stacks[item.id] = item_stack
        db.save(actor)

        # Send private response
        await interaction.followup.send(
            embed=EmbedX.success(
                f"You bought **{item.emoji or item.alt_emoji} {item.name} `x{quantity}`** for **💰 {total_price}** gold."
            )
        )

        # Create & send response embed
        embed = EmbedX.success(
            emoji="🛒",
            title="Purchase",
            description=f"{member.mention} has bought an item.",
        )
        embed.add_field(
            name="Item 🔼",
            value=f"{item.emoji or item.alt_emoji} **{item.name} `x{intword(quantity)}`**",
        )
        embed.add_field(
            name="Gold 🔻",
            value=f"**💰 -{intcomma(total_price)}**",
        )
        embed.set_author(name=member.display_name, icon_url=member.display_avatar)
        embed.set_thumbnail(url=item.icon_url)
        if isinstance(interaction.channel, Messageable):
            await interaction.channel.send(embed=embed)

    @app_commands.guild_only()
    @app_commands.command(description="Equip an equippable item")
    @app_commands.rename(item_id="item")
    async def equip(self, interaction: Interaction, item_id: str):
        # Check guild & member
        member = interaction.user
        if not interaction.guild or not isinstance(member, Member):
            await interaction.response.send_message(
                embed=EmbedX.warning("This command cannot be used in this context."),
                ephemeral=True,
            )
            return

        # Get actor
        db = self.bot.get_db(interaction.guild)
        actor = db.find_one(Actor, Actor.id == member.id) or self.bot.create_actor(
            member
        )

        # Check max
        if len(actor.equipped_items) >= actor.MAX_EQUIPMENT:
            await interaction.response.send_message(
                embed=EmbedX.warning(
                    f"You've reached your equipment limit of **{actor.MAX_EQUIPMENT}** items."
                ),
                ephemeral=True,
            )
            return

        # Get item
        await interaction.response.defer(ephemeral=True)
        item_stack = actor.item_stacks.get(item_id)
        item = item_stack.item if item_stack else None
        if not item or item.type != ItemType.EQUIPPABLE:
            await interaction.followup.send(
                embed=EmbedX.error(f"Invalid **item** input: `{item_id}`\n")
            )
            return

        # Equip item
        equipped_item = actor.equipped_items.get(item.id)
        if equipped_item:
            await interaction.followup.send(
                embed=EmbedX.info(
                    f"**{equipped_item.emoji or equipped_item.alt_emoji} {equipped_item.name}** is already equipped."
                )
            )
            return
        actor.equipped_items[item.id] = item
        actor.add_item_stats(item)
        db.save(actor)
        await interaction.followup.send(
            embed=EmbedX.success(
                f"You equipped **{item.emoji or item.alt_emoji} {item.name}**."
            )
        )

        # Send public response
        if isinstance(interaction.channel, Messageable):
            embed = EmbedX.info(
                emoji="🧰",
                title="Equipment",
                description=f"{member.mention} has equipped an item.",
            )
            embed.add_field(
                name="Item 🔼",
                value=f"{item.emoji or item.alt_emoji} **{item.name}**",
            )
            embed.set_author(name=member.display_name, icon_url=member.display_avatar)
            embed.set_thumbnail(url=item.icon_url)
            await interaction.channel.send(
                embed=self.add_item_stat_embed_fields(embed, item),
            )

    @app_commands.guild_only()
    @app_commands.command(description="Unequip an equipped item")
    @app_commands.rename(item_id="item")
    async def unequip(self, interaction: Interaction, item_id: str):
        # Check guild & member
        member = interaction.user
        if not interaction.guild or not isinstance(member, Member):
            await interaction.response.send_message(
                embed=EmbedX.warning("This command cannot be used in this context."),
                ephemeral=True,
            )
            return

        # Get actor
        db = self.bot.get_db(interaction.guild)
        actor = db.find_one(Actor, Actor.id == member.id) or self.bot.create_actor(
            member
        )

        # Get item
        await interaction.response.defer(ephemeral=True)
        item = actor.equipped_items.get(item_id)
        if not item or item.type != ItemType.EQUIPPABLE:
            await interaction.followup.send(
                embed=EmbedX.error(f"Invalid **item** input: `{item_id}`\n")
            )
            return

        # Unequip item
        equipped_item = actor.equipped_items.get(item.id)
        if not equipped_item:
            await interaction.followup.send(
                embed=EmbedX.info(
                    f"**{item.emoji or item.alt_emoji} {item.name}** is not equipped."
                )
            )
            return
        del actor.equipped_items[item.id]
        actor.add_item_stats(item, scale=-1)
        db.save(actor)
        await interaction.followup.send(
            embed=EmbedX.success(
                f"You unequipped **{item.emoji or item.alt_emoji} {item.name}**."
            )
        )

        # Send public response
        if isinstance(interaction.channel, Messageable):
            embed = EmbedX.info(
                emoji="🧰",
                title="Equipment",
                description=f"{member.mention} has unequipped an item.",
            )
            embed.add_field(
                name="Item 🔻",
                value=f"{item.emoji or item.alt_emoji} **{item.name}**",
            )
            embed.set_author(name=member.display_name, icon_url=member.display_avatar)
            embed.set_thumbnail(url=item.icon_url)
            await interaction.channel.send(
                embed=self.add_item_stat_embed_fields(embed, item, scale=-1),
            )

    @app_commands.guild_only()
    @app_commands.command(description="Use a consumable item")
    @app_commands.rename(item_id="item")
    async def use(self, interaction: Interaction, item_id: str):
        # Check guild & member
        member = interaction.user
        if not interaction.guild or not isinstance(member, Member):
            await interaction.response.send_message(
                embed=EmbedX.warning("This command cannot be used in this context."),
                ephemeral=True,
            )
            return

        # Get actor
        db = self.bot.get_db(interaction.guild)
        actor = db.find_one(Actor, Actor.id == member.id) or self.bot.create_actor(
            member
        )

        # Get item
        await interaction.response.defer(ephemeral=True)
        item_stack = actor.item_stacks.get(item_id)
        item = item_stack.item if item_stack else None
        if not item_stack or not item or item.type != ItemType.CONSUMABLE:
            await interaction.followup.send(
                embed=EmbedX.error(f"Invalid **item** input: `{item_id}`\n")
            )
            return

        # Consume item
        actor.add_item_stats(item)
        item_stack.quantity = max(0, item_stack.quantity - 1)
        if item_stack.quantity <= 0:
            del actor.item_stacks[item.id]
        db.save(actor)
        await interaction.followup.send(
            embed=EmbedX.success(
                f"You consumed **{item.emoji or item.alt_emoji} {item.name}**."
            )
        )

        # Send public response
        if isinstance(interaction.channel, Messageable):
            embed = EmbedX.info(
                emoji="🍴",
                title="Consumption",
                description=f"{member.mention} has consumed an item.",
            )
            embed.add_field(
                name="Item 🔻",
                value=f"{item.emoji or item.alt_emoji} **{item.name}**",
            )
            embed.set_author(name=member.display_name, icon_url=member.display_avatar)
            embed.set_thumbnail(url=item.icon_url)
            await interaction.channel.send(
                embed=self.add_item_stat_embed_fields(embed, item)
            )

    # ----------------------------------------------------------------------------------------------------

    def add_item_stat_embed_fields(
        self, embed: Embed, item: Item, scale: int = 1, show_mod_emoji: bool = True
    ) -> Embed:
        stat_emojis = {
            "health": ":heart:",
            "max_health": ":heart:",
            "energy": "⚡",
            "max_energy": "⚡",
            "attack": ":crossed_swords:",
            "defense": "🛡",
            "speed": "🥾",
        }
        stat_mod_emoji = (" 🔼" if scale >= 0 else " 🔻") if show_mod_emoji else ""
        for stat_name, stat_value in item.effective_stats(scale=scale).items():
            stat_emoji = stat_emojis.get(stat_name, "")
            embed.add_field(
                name=f"{stat_name.capitalize()}{stat_mod_emoji}",
                value=f"{stat_emoji} **{numsign(intcomma(stat_value))}**",
            )
        return embed

    # ----------------------------------------------------------------------------------------------------

    async def buyable_items_autocomplete(
        self, interaction: Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        return [
            app_commands.Choice(
                name=f"{item.alt_emoji} {item.name} ({item.get_item_stats_text()}) ― 💰{intcomma(item.price)}",
                value=item.id,
            )
            for item in [
                item
                for item in self.BUYABLE_ITEMS
                if current.lower() in item.name.lower()
            ][:25]
        ]

    async def actor_consumable_items_autocomplete(
        self, interaction: Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        member = interaction.user
        if not isinstance(member, Member):
            return []
        actor = self.bot.get_db(interaction.guild).find_one(
            Actor, Actor.id == interaction.user.id
        ) or self.bot.create_actor(member)
        return [
            app_commands.Choice(
                name=f"{item_stack.item.alt_emoji} {item_stack.item.name} "
                f"({item_stack.item.get_item_stats_text()}) ― x{item_stack.quantity}",
                value=item_stack.item.id,
            )
            for item_stack in [
                item_stack
                for item_stack in actor.item_stacks.values()
                if item_stack.item.type == ItemType.CONSUMABLE
                and current.lower() in item_stack.item.name.lower()
            ][:25]
        ]

    async def actor_equippable_items_autocomplete(
        self, interaction: Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        member = interaction.user
        if not isinstance(member, Member):
            return []
        actor = self.bot.get_db(interaction.guild).find_one(
            Actor, Actor.id == interaction.user.id
        ) or self.bot.create_actor(member)
        return [
            app_commands.Choice(
                name=f"{item.alt_emoji} {item.name} ({item.get_item_stats_text()})",
                value=item.id,
            )
            for item in [
                item_stack.item
                for item_stack in actor.item_stacks.values()
                if item_stack.item.type == ItemType.EQUIPPABLE
                and not actor.equipped_items.get(item_stack.id)
                and current.lower() in item_stack.item.name.lower()
            ][:25]
        ]

    async def actor_equipped_items_autocomplete(
        self, interaction: Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        member = interaction.user
        if not isinstance(member, Member):
            return []
        actor = self.bot.get_db(interaction.guild).find_one(
            Actor, Actor.id == interaction.user.id
        ) or self.bot.create_actor(member)
        return [
            app_commands.Choice(
                name=f"{item.alt_emoji} {item.name} ({item.get_item_stats_text()})",
                value=item.id,
            )
            for item in [
                equipped_item
                for equipped_item in actor.equipped_items.values()
                if current.lower() in equipped_item.name.lower()
            ][:25]
        ]
