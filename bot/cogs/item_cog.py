from discord import Embed, Interaction, app_commands
from discord.ext.commands import Cog

from bot.main import ActBot
from bot.ui import EmbedX

ALPHA_PREVIEW_NOTICE = {"title": "", "content": "**: "}


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
# * Item Cog
# ----------------------------------------------------------------------------------------------------
class ItemCog(Cog, description="Allows players to use items."):
    def __init__(self, bot: ActBot):
        self.bot = bot

    @app_commands.guild_only()
    @app_commands.command(description="View purchasable items")
    async def shop(self, interaction: Interaction):
        await interaction.response.send_message(
            embed=add_preview_notice(
                EmbedX.info(
                    icon="🏬",
                    title="Shop",
                    description="\n⚔ Sword\n🛡 Shield\n🥾 Boot\n🍎 Apple\n🍌 Banana\n🍔 Burger\n🔫 Gun\n👕 T-Shirt",
                )
            )
        )

    @app_commands.guild_only()
    @app_commands.command(description="Purchase an item")
    async def buy(self, interaction: Interaction, item: str):
        await interaction.response.send_message(
            embed=add_preview_notice(
                EmbedX.info(
                    icon="🛒",
                    title="Purchase",
                    description=f"{interaction.user.mention} purchased **{item}**.",
                )
            ),
        )

    @app_commands.guild_only()
    @app_commands.command(description="View your item inventory")
    async def inventory(self, interaction: Interaction):
        await interaction.response.send_message(
            embed=add_preview_notice(
                EmbedX.info(
                    icon="🎒",
                    title="Inventory",
                    description="🐵 Abducted Monkey **x 3**",
                ),
            )
        )

    @app_commands.guild_only()
    @app_commands.command(description="Equip an equippable item")
    async def equip(self, interaction: Interaction, item: str):
        command_name = interaction.command.name if interaction.command else "?"
        await interaction.response.send_message(
            embed=add_preview_notice(
                EmbedX.info(
                    icon="🎒",
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
                    icon="🎒",
                    title="Item Consumption",
                    description=f"{interaction.user.mention} used **{item}**.",
                )
            ),
        )
