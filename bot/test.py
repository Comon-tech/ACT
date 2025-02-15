from discord import Embed, Interaction, Message, app_commands
from discord.ext import commands
from discord.ext.commands import Cog

from bot.main import ActBot
from bot.ui import EmbedX
from db.actor import Actor
from db.main import ActDbClient


# ----------------------------------------------------------------------------------------------------
# * Test Cog
# ----------------------------------------------------------------------------------------------------
class Test(Cog, description="For test only."):
    def __init__(self, bot: ActBot):
        self.bot = bot

    # ----------------------------------------------------------------------------------------------------
    # * New Syle Commands (/)
    # ----------------------------------------------------------------------------------------------------
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="admin", description="Checks if you are administrator")
    async def admin_new_style_cmd(self, interaction: Interaction):
        await interaction.response.send_message(
            f"[New / Command]\n✅ YOU ({interaction.user}) ARE ADMIN !"
        )

    @admin_new_style_cmd.error
    async def sadmin_error(
        self, interaction: Interaction, error: app_commands.AppCommandError
    ):
        await interaction.response.send_message(
            f"[New / Command]\n❌ you ({interaction.user}) are NOT admin."
        )

    # ----------------------------------------------------------------------------------------------------
    # * Old Style Commands (*)
    # ----------------------------------------------------------------------------------------------------
    @commands.has_guild_permissions(administrator=True)
    @commands.command(name="admin")
    async def admin_old_style_cmd(self, ctx: commands.Context):
        """Checks if you are administrator"""
        await ctx.send(f"[Old ! Command]\n✔ YOU ({ctx.author}) ARE ADMIN !")

    @admin_old_style_cmd.error
    async def admin_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(f"[Old ! Command]\n❌ you ({ctx.author}) are NOT admin.")

    # ----------------------------------------------------------------------------------------------------
    # * Event Listeners
    # ----------------------------------------------------------------------------------------------------
    @Cog.listener()
    async def on_message(self, message: Message):
        if "info" in message.content:
            await message.channel.send(
                embed=EmbedX.info("Example", "This is a standard info message.")
            )
        if "succ" in message.content:
            await message.channel.send(
                embed=EmbedX.success("Example", "This is a standard success message.")
            )
        if "warn" in message.content:
            await message.channel.send(
                embed=EmbedX.warning("Example", "This is a standard warning message.")
            )
        if "err" in message.content:
            await message.channel.send(
                embed=EmbedX.error("Example", "This is a standard error message.")
            )

        msg = ""
        if "db" in message.content:
            db = self.bot.get_database(message.guild)
            msg = f"Database for this server is:\n{db}"
            await message.channel.send(msg)
        if "xp" in message.content:
            actor = Actor(None, id=0)
            numbers = [
                int(word) for word in message.content.split(" ") if word.isdigit()
            ]
            embed = Embed()
            embed.add_field(name=f"Level ➡ Experience", value="", inline=True)
            for level, xp in actor.level_xp_table(numbers[0], numbers[1]):
                embed.add_field(name=f"{level} ➡ {xp}", value="", inline=False)
            await message.channel.send(embed=embed)
        if "rnk" in message.content:
            actor = Actor(None, id=0)
            numbers = [
                int(word) for word in message.content.split(" ") if word.isdigit()
            ]
            embed = Embed()
            embed.add_field(name=f"Rank ➡ Level", value="", inline=True)
            for rank, level in actor.rank_level_table(numbers[0], numbers[1]):
                embed.add_field(name=f"🎖 {rank} ➡ {level}", value="", inline=False)
            await message.channel.send(embed=embed)
        if "wtf" in message.content:
            await message.channel.send("i'm sorry")
