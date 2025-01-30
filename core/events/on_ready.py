from discord.ext import commands  # type: ignore

class OnReady(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        # load_data()
        print(f"TACT Bot is ready! Logged in as {self.bot.user}")
        try:
            synced = await self.bot.tree.sync()
            print(f"synced {len(synced)} command(s)")
        except Exception as e:
            print(e)