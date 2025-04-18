from re import findall

from discord import Attachment, Interaction, TextStyle
from discord.abc import Messageable
from discord.ui import Modal, TextInput

from bot.ui.embed import EmbedX


# ----------------------------------------------------------------------------------------------------
# * Text Paragraph Modal
# ----------------------------------------------------------------------------------------------------
class TextParagraphModal(Modal, title="Proxy Text Message"):
    replyable_message_input = TextInput(
        label="Message ID",
        style=TextStyle.short,
        placeholder="ID of message to reply to.",
        required=False,
        max_length=100,
    )

    paragraph_input = TextInput(
        label="Text",
        style=TextStyle.paragraph,
        placeholder="Text to send.",
        required=False,
        max_length=2000,  # Discord message limit is 2000
    )

    reaction_emojis_input = TextInput(
        label="Reactions",
        style=TextStyle.short,
        placeholder="Reaction emojis to toggle.\nIf no message to reply to, apply to self.",
        required=False,
        max_length=100,
    )

    def __init__(self, attachment: Attachment | None = None):
        super().__init__()
        self.attachment = attachment

    async def on_submit(self, interaction: Interaction):
        # Deny non-messageable channel
        if not isinstance(interaction.channel, Messageable):
            await interaction.response.send_message(
                embed=EmbedX.warning("This command cannot be used in this context."),
                ephemeral=True,
            )
            return

        # Check input
        replyable_message_id = self.replyable_message_input.value
        paragraph = self.paragraph_input.value
        reaction_emojis = self.reaction_emojis_input.value
        attachment = self.attachment
        if not (paragraph or attachment or (reaction_emojis and replyable_message_id)):
            await interaction.response.send_message(
                embed=EmbedX.warning(
                    "You must provide either text, attachment (in command), or reactions with replyable message ID."
                ),
                ephemeral=True,
            )
            return

        # Prepare Attachment (if any)
        await interaction.response.defer(ephemeral=True, thinking=True)
        file = await attachment.to_file(use_cached=True) if attachment else None

        # Handle reply functionality
        replyable_message = None
        if replyable_message_id:
            # Extract message ID from link or use directly if it's an ID
            if "/" in replyable_message_id:  # Assuming it's a message link
                message_id = int(replyable_message_id.split("/")[-1])
            else:  # Assuming it's a raw message ID
                message_id = int(replyable_message_id)
            replyable_message = await interaction.channel.fetch_message(message_id)

        # Send to the original channel where the command was invoked
        sent_message = await interaction.channel.send(content=paragraph, file=file, reference=replyable_message) if paragraph or file else None  # type: ignore

        # Handle reactions
        message = replyable_message or sent_message
        if message and reaction_emojis:
            # Parse emojis (custom and Unicode) with regex: Match :name: for custom emojis and single Unicode emojis
            matches = findall(
                r"(:[a-zA-Z0-9_]+:)|([\U0001F000-\U0001FFFF])", reaction_emojis.strip()
            )
            # Flatten matches (each match is a tuple with groups) & Deduplicate emojis using a set
            unique_reaction_emojis = set([match[0] or match[1] for match in matches])
            guild = interaction.guild
            for reaction_emoji in unique_reaction_emojis:
                emoji = None
                # Check if it's a custom emoji (e.g., :tom:)
                if reaction_emoji.startswith(":") and reaction_emoji.endswith(":"):
                    emoji_name = reaction_emoji[1:-1].strip()  # Strip colons
                    if guild:  # Search for the emoji in the guild
                        for guild_emoji in guild.emojis:
                            if guild_emoji.name.lower() == emoji_name.lower():
                                emoji = guild_emoji
                                break
                else:  # Assume it's a Unicode emoji
                    emoji = reaction_emoji.strip()
                # Check if the emoji is already reacted by the bot
                if emoji:
                    reacted = False
                    bot_user = interaction.client.user
                    for reaction in message.reactions:
                        if reaction.emoji == emoji:
                            async for user in reaction.users():
                                if user == bot_user:
                                    reacted = True
                                    break
                            break
                    if reacted and bot_user:
                        await message.remove_reaction(emoji, bot_user)
                    else:
                        await message.add_reaction(emoji)

        # Send final confirmation
        await interaction.followup.send(embed=EmbedX.success("Message proxied."))
