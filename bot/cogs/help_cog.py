from colorama import Fore, Style
from discord import Color, Embed, Interaction, Status, app_commands
from discord.ext.commands import Bot, Cog

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
                value=cmd.description,
                inline=False,
            )
        embed.set_thumbnail(url=self.bot.user.display_avatar)
        await interaction.response.send_message(embed=embed)
