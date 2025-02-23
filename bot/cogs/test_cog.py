from discord import Interaction, Message, app_commands
from discord.ext import commands
from discord.ext.commands import Cog

from bot.main import ActBot
from bot.ui import EmbedX


# ----------------------------------------------------------------------------------------------------
# * Test Cog
# ----------------------------------------------------------------------------------------------------
class Test(Cog, description="For test only."):
    def __init__(self, bot: ActBot):
        self.bot = bot

    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(description="Syncs app commands to Discord")
    async def sync(self, interaction: Interaction):
        count = await self.bot.sync_commands()
        await interaction.response.send_message(
            embed=EmbedX.success(
                "Commands Sync", f"{count[0]}/{count[1]} commands synced."
            )
        )

    @sync.error
    async def sync_error(
        self, interaction: Interaction, error: app_commands.AppCommandError
    ):
        await interaction.response.send_message(
            embed=EmbedX.error("Commands Sync", f"{error}.")
        )

    # ----------------------------------------------------------------------------------------------------
    # * App Commands (/ Slash Commands)
    # ----------------------------------------------------------------------------------------------------
    @app_commands.command(name="test", description="App command test")
    async def app_cmd_test(self, interaction: Interaction):
        await interaction.response.send_message(f"/ App command")

    # ----------------------------------------------------------------------------------------------------
    # * Commands (* Prefix Commands)
    # ----------------------------------------------------------------------------------------------------
    @commands.command(name="test", description="Command test")
    async def cmd_test(self, ctx: commands.Context):
        await ctx.send(f"* Command")

    @commands.group(name="grp-test", description="Command group test")
    async def cmd_grp_test(self, ctx):
        if ctx.invoked_subcommand:
            await ctx.send("* Command Group\nInvoked Subcommand!")
        else:
            await ctx.send("* Command Group")

    @cmd_grp_test.command(name="sub-test0", description="Subcommand test 0")
    async def sbcmd_test0(self, ctx, a: str, b: str):
        await ctx.send(f"* Command Subcommand\narguments: a={a}, b={b} 😲")

    @cmd_grp_test.command(name="sub-test1", description="Subcommand test 1")
    async def sbcmd_test1(self, ctx, x: int):
        await ctx.send(f"* Command Subcommand\narguments: x*2 = {x}*2 = {x*2} 😃")

    # ----------------------------------------------------------------------------------------------------
    # * Event Listeners
    # ----------------------------------------------------------------------------------------------------
    @Cog.listener()
    async def on_message(self, message: Message):
        # if "info" in message.content:
        #     await message.channel.send(
        #         embed=EmbedX.info("Example", "This is a standard info message.")
        #     )
        # if "succ" in message.content:
        #     await message.channel.send(
        #         embed=EmbedX.success("Example", "This is a standard success message.")
        #     )
        # if "warn" in message.content:
        #     await message.channel.send(
        #         embed=EmbedX.warning("Example", "This is a standard warning message.")
        #     )
        # if "err" in message.content:
        #     await message.channel.send(
        #         embed=EmbedX.error("Example", "This is a standard error message.")
        #     )

        # msg = ""
        # if "db" in message.content:
        #     db = self.bot.get_database(message.guild)
        #     msg = f"This server's database:\n- {db.name}\n"
        #     msg += f"Databases currently loaded in memory:\n{"\n".join([f"- {db.name}" for id, db in self.bot.db_client.databases.items()])}"
        #     db_refs = DbRef.get_collection(self.bot.db_client.main_database).find()
        #     db_refs = "\n".join([f"- {dbref.get("name")}" for dbref in db_refs])
        #     msg += f"\nDatabases that were generated and indexed:\n{db_refs}"
        #     await message.channel.send(msg)
        # if "xp" in message.content:
        #     actor = Actor(None, id=0)
        #     numbers = [
        #         int(word) for word in message.content.split(" ") if word.isdigit()
        #     ]
        #     embed = Embed()
        #     embed.add_field(name=f"Level ➡ Experience", value="", inline=True)
        #     for level, xp in actor.level_xp_table(numbers[0], numbers[1]):
        #         embed.add_field(name=f"{level} ➡ {xp}", value="", inline=False)
        #     await message.channel.send(embed=embed)
        # if "rnk" in message.content:
        #     actor = Actor(None, id=0)
        #     numbers = [
        #         int(word) for word in message.content.split(" ") if word.isdigit()
        #     ]
        #     embed = Embed()
        #     embed.add_field(name=f"Rank ➡ Level", value="", inline=True)
        #     for rank, level in actor.rank_level_table(numbers[0], numbers[1]):
        #         embed.add_field(name=f"🎖 {rank} ➡ {level}", value="", inline=False)
        #     await message.channel.send(embed=embed)
        # if "wtf" in message.content:
        #     await message.channel.send("i'm sorry")
        # if "raise e":
        #     try:
        #         raise Exception("This exception was raised on purpose.")
        #     except:
        #         await message.channel.send("i handled ur e_r_r_o_r 💚")
        await self.bot.process_commands(message)
