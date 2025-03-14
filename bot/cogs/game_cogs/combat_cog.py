from discord import Color, Embed, Guild, Interaction, Member, User, app_commands
from discord.ext.commands import Cog
from humanize import intcomma, naturalsize, naturaltime
from odmantic import query

from bot.main import ActBot
from bot.ui import EmbedX
from db.actor import Actor


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
# * Combat Cog
# ----------------------------------------------------------------------------------------------------
class CombatCog(Cog, description="Allows players to engage in battles."):
    def __init__(self, bot: ActBot):
        self.bot = bot

    @app_commands.guild_only()
    @app_commands.command(description="Attack a member")
    async def attack(self, interaction: Interaction, member: Member):
        command_name = interaction.command.name if interaction.command else "?"
        await interaction.response.send_message(
            content=f"{member.mention} 😱",
            embed=add_preview_notice(
                EmbedX.info(
                    emoji=":crossed_swords:",
                    title="Combat",
                    description=f"{interaction.user.mention} attacked {member.mention}.",
                )
            ),
        )
