from typing import Callable

from discord import ButtonStyle, Embed, Interaction, Member, Message, User
from discord.ui import Button, View, button

from bot.ui.embed import EmbedX


# ----------------------------------------------------------------------------------------------------
# * Pagination View
# ----------------------------------------------------------------------------------------------------
class PaginationView(View):

    def __init__(self, pages: list[Embed], user: User | Member | None = None):
        super().__init__(timeout=600)  # 600s = 10min
        self.message: Message | None = None
        self.pages = pages
        self.current_page = 0
        self.user = user
        self.update_buttons()

    # ----------------------------------------------------------------------------------------------------

    def update_buttons(self):
        """Update button states based on current page"""
        self.first_button.disabled = self.previous_button.disabled = (
            self.current_page == 0
        )
        self.last_button.disabled = self.next_button.disabled = (
            self.current_page == len(self.pages) - 1
        )

    @button(label="First", emoji="⏮", style=ButtonStyle.primary, disabled=True)
    async def first_button(self, interaction: Interaction, button: Button):
        self.current_page = 0
        await self.send_page(interaction)

    @button(label="Previous", emoji="◀", style=ButtonStyle.primary, disabled=True)
    async def previous_button(self, interaction: Interaction, button: Button):
        self.current_page -= 1
        await self.send_page(interaction)

    @button(label="Next", emoji="▶", style=ButtonStyle.primary, disabled=True)
    async def next_button(self, interaction: Interaction, button: Button):
        self.current_page += 1
        await self.send_page(interaction)

    @button(label="Last", emoji="⏭", style=ButtonStyle.primary, disabled=True)
    async def last_button(self, interaction: Interaction, button: Button):
        self.current_page = len(self.pages) - 1
        await self.send_page(interaction)

    async def on_timeout(self):
        """Disable buttons on timeout"""
        for button in self.children:
            if isinstance(button, Button):
                button.disabled = True
        if self.message:
            await self.message.edit(view=self)

    # ----------------------------------------------------------------------------------------------------

    async def send_page(self, interaction: Interaction):
        if self.interaction_is_allowed(interaction):
            self.update_buttons()
            await interaction.response.edit_message(
                embed=self.pages[self.current_page], view=self
            )

    async def interaction_is_allowed(self, interaction: Interaction) -> bool:
        if self.user and interaction.user != self.user:
            """Restrict button usage to original user."""
            await interaction.response.send_message(
                embed=EmbedX.warning("Only the command issuer can navigate."),
                ephemeral=True,
            )
            return False
        return True
