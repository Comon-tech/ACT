from discord import Embed, Interaction, app_commands
from discord.ext.commands import GroupCog
from humanize import intcomma
from tabulate import tabulate

from bot.main import ActBot
from bot.ui.embed import EmbedX
from db.actor import Actor
from db.item import Item
from db.main import ActToml
from utils.misc import numsign


# ----------------------------------------------------------------------------------------------------
# * Table Cog
# ----------------------------------------------------------------------------------------------------
class TableCog(
    GroupCog,
    group_name="table",
    description="Show data tables",
):
    def __init__(self, bot: ActBot):
        self.bot = bot

    @app_commands.guild_only()
    @app_commands.command(description="View table of items")
    async def items(
        self,
        interaction: Interaction,
    ):
        await interaction.response.defer()

        def format_stat_name(name: str):
            if "max_" in name:
                name = name.replace("max_", "")
                return f"M{name[0].upper()}"
            return name[0].upper()

        output = tabulate(
            [
                (
                    item.name,
                    " ".join(
                        f"{numsign(intcomma(value))}{format_stat_name(name)}"
                        for name, value in item.effective_stats().items()
                    ),
                    item.price,
                )
                for item in ActToml.load_dict(Item).values()
            ],
            headers=["Item", "Stats", "Price"],
            colalign=["right", "left", "left"],
            tablefmt="simple_outline",
        )
        await interaction.followup.send(
            embed=self.table_embed(emoji="📦", title="Items", desc=output)
        )

    @app_commands.guild_only()
    @app_commands.command(description="View table of levels")
    async def levels(
        self,
        interaction: Interaction,
        min: int = 0,
        max: int = 10,
    ):
        await interaction.response.defer()
        await interaction.followup.send(
            embed=self.table_embed(
                emoji="🏅",
                title="Levels",
                desc=tabulate(
                    Actor.level_xp_gold_table(min, max),
                    headers=["Level", "Experience", "Gold"],
                    colalign=["right", "left", "left"],
                    tablefmt="simple_outline",
                ),
            )
        )

    @app_commands.guild_only()
    @app_commands.command(description="View table of ranks")
    async def ranks(
        self,
        interaction: Interaction,
        min: int = 0,
        max: int = 10,
    ):
        await interaction.response.defer()
        await interaction.followup.send(
            embed=self.table_embed(
                emoji="🏆",
                title="Ranks",
                desc=tabulate(
                    [(rank.name, elo) for rank, elo in Actor.rank_elo_table(min, max)],
                    headers=["Rank", "Elo"],
                    colalign=["right", "left"],
                    tablefmt="simple_outline",
                ),
            )
        )

    @app_commands.guild_only()
    @app_commands.command(description="View table of roles")
    async def roles(
        self,
        interaction: Interaction,
        min: int = 0,
        max: int = 10,
    ):
        await interaction.response.defer()
        output = "_No roles found in this server._"
        guild = interaction.guild
        roles = (
            sorted(guild.roles, key=lambda role: role.position, reverse=True)
            if guild
            else []
        )
        if roles:
            output_list = []
            for role in roles:
                output_list.append((role.name, len(role.members)))
            output = tabulate(
                output_list,
                headers=["Role", "Members"],
                colalign=["right", "left"],
                tablefmt="simple_outline",
            )
        await interaction.followup.send(
            embed=self.table_embed(emoji="🎭", title="Roles", desc=output)
        )

    # ----------------------------------------------------------------------------------------------------

    def table_embed(self, emoji: str, title: str, desc: str) -> Embed:
        return EmbedX.info(emoji=emoji, title=title, description=f"```{desc}```")
