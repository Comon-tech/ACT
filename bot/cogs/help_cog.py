from discord import Color, Embed, Interaction, app_commands
from discord.ext.commands import Cog

from bot.main import ActBot


class Help(Cog, description="Provides help and informations."):
    def __init__(self, bot: ActBot):
        self.bot = bot

    @app_commands.command(description="Get help with the commands")
    async def help(self, interaction: Interaction):
        all_cmds = self.bot.tree.get_commands()
        embed = Embed(
            title=f"🤖 {self.bot.title} v{self.bot.version}",
            description=(f"{self.bot.description}\n\n"),
            color=Color.blue(),
        )
        for cmd in all_cmds:
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
