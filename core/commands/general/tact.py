from discord import app_commands, Interaction, Embed, Color
from discord.ext import commands
from services.gemini import generate_content
from services.paginator import Paginator
import re
import time
import random
from datetime import datetime, timedelta
from math import ceil
from collections import Counter, defaultdict

chat_history = [] # this should be imported from a module that manges chat history

class TACT(commands.Cog):
    def __init__(self, bot, ):
        self.bot = bot

    @app_commands.command(name="tact", description="Interact with the AI for questions or assistance!")
    async def tact(self, interaction:Interaction,  *, query: str):
        await interaction.response.defer(thinking=True)  # Show a typing indicator

        # Get the chat history for the current channel
        channel_id = interaction.channel.id
        relevant_history = chat_history.get(channel_id, [])

        # Construct the prompt with chat history
        prompt = f"The following is a conversation from a Discord server:\n"
        prompt += "\n".join(relevant_history) + "\n"  # Add the chat history
        prompt += f"Based on this, answer the following question:\n{query}"

        try:
            response = '''Lorem Ipsum is simply dummy text of the printing and typesetting industry. \n\nLorem Ipsum has been the industry's standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book. It has survived not only five centuries, but also the leap into electronic typesetting, remaining essentially unchanged. It was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages, and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum. Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book. It has survived not only five centuries, but also the leap into electronic typesetting, remaining essentially unchanged. It was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages, and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum.''' 
            # response = 'very long text :D'
            # response = generate_content(prompt)

            # Split response into pages if it's too long
            max_chars = 1024  # Discord embed character limit per field
            pages = [response[i:i + max_chars] for i in range(0, len(response), max_chars)]

            # define page content
            def page_content():
                embed = Embed(
                    color=Color.purple()
                )
                embed.add_field(name=f'👤 {interaction.user.display_name}', value=f'{query}', inline=False)
                embed.add_field(name='', value="\n\n", inline=False)
                embed.add_field(name="🤖 TACT AI", value=pages[paginator.current_page], inline=False)
                embed.set_footer(text=f"Page {paginator.current_page + 1}/{len(pages)}")
                embed.set_thumbnail(url=interaction.user.display_avatar.url)
                return embed

            # define paginator
            paginator = Paginator(pages, interaction.user, page_content)

            # send first page
            await paginator.create_page(interaction)
        except Exception as e:
            await interaction.followup.send(
                content="⚠️ Something went wrong while processing your request. Please try again later.",
                ephemeral=True
            )
            print(f"Error: {e}")

