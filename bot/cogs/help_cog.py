from discord import Color, Embed, Interaction, Member, app_commands
from discord.ext.commands import Cog, GroupCog
from tabulate import tabulate

from bot.main import ActBot
from bot.ui import EmbedX
from db.actor import Actor


# ----------------------------------------------------------------------------------------------------
# * Help Cog
# ----------------------------------------------------------------------------------------------------
class HelpCog(Cog, description="Provides help and information interface."):
    def __init__(self, bot: ActBot):
        self.bot = bot

    # ----------------------------------------------------------------------------------------------------
    # * Commands
    # ----------------------------------------------------------------------------------------------------
    @app_commands.command(description="View all commands")
    async def help(self, interaction: Interaction):
        all_cmds = self.bot.tree.get_commands()
        embed = Embed(
            title=f"🤖 {self.bot.title} v{self.bot.version}",
            description=(f"{self.bot.description}\n\n"),
            color=Color.blue(),
        )
        for cmd in all_cmds:
            # Check if command has administrator requirement in default_permissions
            admin_required = False
            if hasattr(cmd, "default_permissions") and cmd.default_permissions:
                admin_required = cmd.default_permissions.administrator
            if not admin_required or (
                isinstance(interaction.user, Member)
                and interaction.user.guild_permissions.administrator
            ):
                embed.add_field(
                    name=f"/{cmd.name}",
                    value=(
                        cmd.description
                        if not isinstance(cmd, app_commands.commands.ContextMenu)
                        else ""
                    ),
                    inline=False,
                )
        if self.bot.user:
            embed.set_thumbnail(url=self.bot.user.display_avatar)
        await interaction.response.send_message(embed=embed)

    # ----------------------------------------------------------------------------------------------------
    # * Table
    # ----------------------------------------------------------------------------------------------------
    @app_commands.guild_only
    @app_commands.command(description="View table of data")
    @app_commands.choices(
        data=[
            app_commands.Choice(name="🏅 Levels", value="levels"),
            app_commands.Choice(name="🏆 Ranks", value="ranks"),
            app_commands.Choice(name="🎭 Roles", value="roles"),
        ]
    )
    async def table(
        self,
        interaction: Interaction,
        data: app_commands.Choice[str],
        min: int = 0,
        max: int = 10,
    ):
        await interaction.response.defer()
        output = " "
        match data.value:
            case "levels":
                output = tabulate(
                    Actor.level_xp_table(min, max),
                    headers=["Level", "Experience"],
                    colalign=["right", "left"],
                    tablefmt="simple_outline",
                )
            case "ranks":
                output = tabulate(
                    Actor.rank_level_table(min, max),
                    headers=["Rank", "Level"],
                    colalign=["right", "left"],
                    tablefmt="simple_outline",
                )
            case "roles":
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
                else:
                    output = "_No roles found in this server._"
        await interaction.followup.send(
            embed=EmbedX.info(icon="", title=data.name, description=f"```{output}```")
        )
