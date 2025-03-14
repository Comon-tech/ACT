from discord import Embed, Interaction, app_commands
from discord.ext.commands import GroupCog
from humanize import intcomma
from tabulate import WIDE_CHARS_MODE, tabulate

from bot.main import ActBot
from bot.ui import EmbedX
from db.item import Item


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
    ITEMS: list[Item]
    BUYABLE_ITEMS: list[Item]

    def __init__(self, bot: ActBot):
        self.bot = bot
        self.ITEMS = list(bot.get_db().find(Item))
        self.BUYABLE_ITEMS = [item for item in self.ITEMS if item.is_buyable == True]
        self.buy.autocomplete("item_id")(self.item_autocomplete)
        self.view.autocomplete("item_id")(self.item_autocomplete)

    # ----------------------------------------------------------------------------------------------------

    @app_commands.guild_only()
    @app_commands.command(description="View your items or another member's items")
    async def bag(self, interaction: Interaction):
        await interaction.response.send_message(
            embed=EmbedX.info(
                emoji="🎒",
                title="Inventory",
                description="🐵 Abducted Monkey **x 3**",
            )
        )

    @app_commands.guild_only()
    @app_commands.command(description="View purchasable items")
    async def store(self, interaction: Interaction):
        # store_items = [
        #     f"{item.emoji} **{item.name}** : 💰 **{item.price}** Gold"
        #     for item in self.BUYABLE_ITEMS
        # ]
        embed = EmbedX.info(emoji="🏬", title="Store")
        items_column = []
        prices_column = []

        for item in self.BUYABLE_ITEMS:
            items_column.append(f"{item.emoji} **{item.name}**")
            prices_column.append(f"**`💰{intcomma(item.price)}`**")
        embed.add_field(name="Item", value="\n".join(items_column))
        embed.add_field(name="Price", value="\n".join(prices_column))
        url = "https://cdn.discordapp.com/attachments/1349262615431483473/1349272946555748372/store.png?ex=67d27fda&is=67d12e5a&hm=29365e671148a9996341f92b1d34a1f7004e642478e1b6249f0d13b5d7a8c051&"
        # embed.set_image(url=url)
        embed.set_thumbnail(url=url)
        embed.add_field(
            name="Command",
            value=f"👁 `/{self.view.qualified_name}`\n"
            f"💳 `/{self.buy.qualified_name}`",
            inline=False,
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.guild_only()
    @app_commands.command(description="View an item information")
    @app_commands.rename(item_id="item")
    @app_commands.describe(item_id="Choose item you wish to view")
    async def view(self, interaction: Interaction, item_id: str):
        item = next((item for item in self.BUYABLE_ITEMS if item.id == item_id), None)
        if not item:
            await interaction.response.send_message(
                embed=EmbedX.error(f"Invalid **item** input: `{item_id}`\n"),
                ephemeral=True,
            )
            return
        embed = EmbedX.info(
            emoji=item.emoji,
            title=item.name,
            description=item.description,
        )
        embed.add_field(name="Price", value=f"💰 **{intcomma(item.price)}**")
        if item.health_bonus:
            embed.add_field(
                name="Health",
                value=f":heart: +**{intcomma(item.health_bonus)}**",
            )
        if item.energy_bonus:
            embed.add_field(
                name="Energy",
                value=f"⚡ +**{intcomma(item.energy_bonus)}**",
            )
        if item.max_health_bonus:
            embed.add_field(
                name="Max Health",
                value=f":heart: +**{intcomma(item.max_health_bonus)}**",
            )
        if item.max_energy_bonus:
            embed.add_field(
                name="Max Energy",
                value=f"⚡ +**{intcomma(item.max_energy_bonus)}**",
            )
        if item.attack_bonus:
            embed.add_field(
                name="Attack",
                value=f":crossed_swords: +**{intcomma(item.attack_bonus)}**",
            )
        if item.defense_bonus:
            embed.add_field(
                name="Defense", value=f"🛡 +**{intcomma(item.defense_bonus)}**"
            )
        if item.speed_bonus:
            embed.add_field(name="Speed", value=f"🥾 +**{intcomma(item.speed_bonus)}**")
        embed.set_thumbnail(url=item.icon_url)
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
            description=f"{member.mention} purchased **{quantity}** x {item.emoji} **{item.name}** for 💰 **{total_price}**.",
        )
        embed.set_author(name=member.display_name, icon_url=member.display_avatar)
        embed.set_thumbnail(url=item.icon_url)
        await interaction.response.send_message(embed=embed)

    @app_commands.guild_only()
    @app_commands.command(description="Equip an equippable item")
    async def equip(self, interaction: Interaction, item: str):
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

    async def item_autocomplete(
        self, interaction: Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        return [
            app_commands.Choice(
                name=f"{item.emoji} {item.name} ― 💰{intcomma(item.price)}",
                value=item.id,
            )
            for item in [
                item
                for item in self.BUYABLE_ITEMS
                if current.lower() in item.name.lower()
            ][:25]
        ]
