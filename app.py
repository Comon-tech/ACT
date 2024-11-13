import discord # type: ignore
import dotenv # type: ignore
import os # type: ignore

dotenv.load_dotenv()

class MyClient(discord.Client):
    async def on_ready(self):
        print('Logged on as', self.user)

    async def on_message(self, message):
        print('Message from {0.author}: {0.content}'.format(message))
    

intents = discord.Intents.default()
intents.message_content = True

client = MyClient(intents=intents)
client.run(os.getenv('DISCORD_TOKEN'))