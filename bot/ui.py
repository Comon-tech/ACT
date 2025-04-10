from discord import (
    Attachment,
    Color,
    Embed,
    Forbidden,
    HTTPException,
    Interaction,
    TextStyle,
    errors,
)
from discord.abc import Messageable
from discord.ui import Modal, TextInput


# ----------------------------------------------------------------------------------------------------
# * Embed Extension
# ----------------------------------------------------------------------------------------------------
class EmbedX:
    STYLES = {
        "info": {"color": Color.blue(), "icon": ":information_source:"},
        "success": {"color": Color.green(), "icon": "✅"},
        "warning": {"color": Color.yellow(), "icon": "⚠️"},
        "error": {"color": Color.red(), "icon": "⛔"},
    }

    @classmethod
    def _create(
        cls,
        style_name: str,
        description: str,
        title: str | None = None,
        emoji: str | None = None,
    ) -> Embed:
        """Create a styled embed."""
        if style_name not in cls.STYLES:
            raise ValueError(f"Invalid embed style: {style_name}")
        style = cls.STYLES[style_name]
        if emoji == None:
            emoji = style["icon"]
        if title == None:
            title = style_name.capitalize()
        return Embed(
            title=f"{emoji.strip()} {title.strip()}",  # type: ignore
            description=description.strip(),
            color=style["color"],
        )

    @classmethod
    def info(
        cls, description="", title: str | None = None, emoji: str | None = None
    ) -> Embed:
        return cls._create("info", description, title, emoji)

    @classmethod
    def success(
        cls, description="", title: str | None = None, emoji: str | None = None
    ) -> Embed:
        return cls._create("success", description, title, emoji)

    @classmethod
    def warning(
        cls, description="", title: str | None = None, emoji: str | None = None
    ) -> Embed:
        return cls._create("warning", description, title, emoji)

    @classmethod
    def error(
        cls, description="", title: str | None = None, emoji: str | None = None
    ) -> Embed:
        return cls._create("error", description, title, emoji)


# ----------------------------------------------------------------------------------------------------
# * Text Paragraph Modal
# ----------------------------------------------------------------------------------------------------
class TextParagraphModal(Modal, title="Proxy Text Message"):
    text_paragraph = TextInput(
        label="Text",
        style=TextStyle.paragraph,  # Use paragraph style for multi-line input
        placeholder="Enter the text you want the bot to send...\nLeave blank if only sending the attachment.",
        required=False,  # Make it optional if they only attached a file
        max_length=1900,  # Discord message limit is 2000, leave some buffer
    )

    def __init__(self, attachment: Attachment | None = None):
        super().__init__()
        self.attachment = attachment  # Store the attachment passed from the command
        self.text_paragraph.required = not bool(attachment)

    async def on_submit(self, interaction: Interaction):
        # Deny non-messageable channel
        if not isinstance(interaction.channel, Messageable):
            await interaction.response.send_message(
                embed=EmbedX.warning("This command cannot be used in this context."),
                ephemeral=True,
            )
            return

        # Get the text entered by the user
        text = self.text_paragraph.value or None  # Use None if empty
        if not text and not self.attachment:
            await interaction.response.send_message(
                embed=EmbedX.warning(
                    "You must provide either text in the modal or an attachment in the command."
                ),
                ephemeral=True,
            )
            return

        # Prepare Attachment (if any)
        await interaction.response.defer(ephemeral=True, thinking=True)
        file = (
            await self.attachment.to_file(use_cached=True) if self.attachment else None
        )

        # Send to the original channel where the command was invoked
        await interaction.channel.send(content=text, file=file)  # type: ignore

        # Send final confirmation
        await interaction.followup.send(embed=EmbedX.success("Message proxied"))
