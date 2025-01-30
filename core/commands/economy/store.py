from discord.ext import commands
from discord import app_commands, Interaction, Embed, Color, ButtonStyle
from discord.ui import View, Button
from math import ceil
from services.db import store_collection

class Store(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="store", description="Checkout the store")
    async def store(self, interaction: Interaction):
        interaction.response.defer()
        items = list(store_collection.find())
        if not items:
            await interaction.response.send_message("The store is currently empty!")
            return

        view = self.StoreView(items=items, user=interaction.user)
        await interaction.response.send_message(embed=view.embed, view=view)

     # Function to provide autocomplete options
    @staticmethod
    def item_autocomplete_fn():
        async def item_autocomplete(interaction: Interaction, current: str): 
            # Fetch item names from the database and filter based on the user's input
            all_items = [item["item_name"] for item in store_collection.find()]
            matching_items = [app_commands.Choice(name=item, value=item) for item in all_items if current.lower() in item.lower()]
            return matching_items[:25]  # Return up to 25 matches (Discord's limit)
        return item_autocomplete

    class StoreView(View):
        def __init__(self, items, user, per_page=10):
            super().__init__()
            self.items = items
            self.user = user
            self.per_page = per_page
            self.page = 0
            self.max_pages = ceil(len(items) / per_page)
            self.embed = None
            self.update_embed()

            # Add buttons
            self.previous_button = Button(label="Previous", style=ButtonStyle.primary, disabled=True)
            self.previous_button.callback = self.previous_callback
            self.add_item(self.previous_button)

            self.next_button = Button(label="Next", style=ButtonStyle.primary, disabled=(self.max_pages <= 1))
            self.next_button.callback = self.next_callback
            self.add_item(self.next_button)

        def update_embed(self):
            start = self.page * self.per_page
            end = start + self.per_page
            items_on_page = self.items[start:end]

            store_list = "\n".join([f"** {item['item_name']}: {item['item_price']} XP ** \n {item['description']}" for item in items_on_page])

            self.embed = Embed(
                title=f"**Welcome to the 🛒 Store! (Page {self.page + 1}/{self.max_pages})**",
                description=store_list,
                color=Color.blue()
            )
            self.embed.set_thumbnail(url=self.user.display_avatar.url)

        async def update_message(self, interaction):
            self.update_embed()
            await interaction.response.edit_message(embed=self.embed, view=self)

        async def previous_callback(self, interaction: Interaction):
            self.page -= 1
            self.previous_button.disabled = (self.page == 0)
            self.next_button.disabled = False
            await self.update_message(interaction)

        async def next_callback(self, interaction: Interaction):
            self.page += 1
            self.next_button.disabled = (self.page == self.max_pages - 1)
            self.previous_button.disabled = False
            await self.update_message(interaction)