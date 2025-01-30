from discord import Interaction, User, Embed, ButtonStyle
from discord.ui import View, Button, button
from typing import Callable

class Paginator(View):
    def __init__(self, pages: list, user: User, page_content: Callable[[], Embed]):
        super().__init__(timeout=120)  # Timeout after 2 minutes
        self.page_content = page_content
        self.pages = pages
        self.current_page = 0
        self.user = user  # Restrict button usage to the original user

    def update_buttons(self):
        # Enable/disable buttons based on the current page
        for child in self.children:
            if isinstance(child, Button):
                if child.label == "⏮️ First":
                    child.disabled = self.current_page == 0
                elif child.label == "⬅️ Previous":
                    child.disabled = self.current_page == 0
                elif child.label == "➡️ Next":
                    child.disabled = self.current_page == len(self.pages) - 1
                elif child.label == "⏭️ Last":
                    child.disabled = self.current_page == len(self.pages) - 1

    async def create_page(self, interaction: Interaction):
        self.update_buttons()
        await interaction.followup.send(embed=(self.page_content()), view=self)

    async def send_page(self, interaction: Interaction):
        self.update_buttons()
        await interaction.response.edit_message(embed=(self.page_content()), view=self)

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user != self.user:
            await interaction.response.send_message(
                "❌ You cannot interact with this menu.", ephemeral=True
            )
            return False
        return True

    @button(label="⏮️ First", style=ButtonStyle.primary)
    async def first_page(self, interaction: Interaction, button: Button):
        self.current_page = 0
        await self.send_page(interaction)

    @button(label="⬅️ Previous", style=ButtonStyle.primary)
    async def previous_page(self, interaction: Interaction, button: Button):
        self.current_page -= 1
        await self.send_page(interaction)

    @button(label="➡️ Next", style=ButtonStyle.primary)
    async def next_page(self, interaction: Interaction, button: Button):
        self.current_page += 1
        await self.send_page(interaction)

    @button(label="⏭️ Last", style=ButtonStyle.primary)
    async def last_page(self, interaction: Interaction, button: Button):
        self.current_page = len(self.pages) - 1
        await self.send_page(interaction)