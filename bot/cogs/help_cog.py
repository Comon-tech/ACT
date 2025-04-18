from collections import defaultdict

from discord import Color, Embed, Interaction, Member, app_commands
from discord.ext.commands import GroupCog

from bot.main import ActBot
from bot.ui.embed import EmbedX
from bot.ui.view import PaginationView


# ----------------------------------------------------------------------------------------------------
# * Help Cog
# ----------------------------------------------------------------------------------------------------
class HelpCog(
    GroupCog, group_name="help", description="Provide help and information interface."
):
    MAX_EMBED_FIELDS = 10  # Must be <= 25 (Discord limit)
    MAX_EMBED_CHARS = 1000  # Must be <= 6000 (Discord limit)

    def __init__(self, bot: ActBot):
        self.bot = bot

    # ----------------------------------------------------------------------------------------------------

    @app_commands.command(description="Learn about the bot")
    async def about(self, interaction: Interaction):
        embed = EmbedX.info(
            emoji="🤖",
            title=f"{self.bot.title} v{self.bot.version}",
            description=self.bot.description,
        )
        if self.bot.user:
            embed.set_thumbnail(url=self.bot.user.display_avatar)
        await interaction.response.send_message(
            embed=embed,
            ephemeral=True,
        )

    @app_commands.command(
        description="View a comprehensive list of all available commands"
    )
    async def commands(self, interaction: Interaction):
        # Group commands by category
        await interaction.response.defer(ephemeral=True)
        command_groups: dict[str, list[app_commands.Command]] = defaultdict(list)
        for cmd in self.bot.tree.get_commands():
            # category = getattr(cmd, "category", "")
            category: str = cmd.extras.get("category", "")
            if category:
                category = f"#️⃣ {category.capitalize()}"
            if isinstance(cmd, app_commands.Group):
                category = f"📂 {cmd.name.capitalize()}"
            command_groups[category].append(cmd)

        # Check if user is admin
        is_admin = (
            isinstance(interaction.user, Member)
            and interaction.user.guild_permissions.administrator
        )

        # Build command string
        pages: list[Embed] = []
        current_content = []
        current_char_count = 0
        embed_emoji = "🔷"
        embed_title = "Commands"

        for category, commands in sorted(command_groups.items()):
            command_lines = []
            for cmd in sorted(commands, key=lambda x: x.name):
                admin_required = (
                    getattr(cmd, "default_permissions", None)
                    and cmd.default_permissions.administrator
                )
                cmd_emoji = "🔹"
                if admin_required:
                    if is_admin:
                        cmd_emoji = "🔸"
                    else:
                        continue

                if isinstance(cmd, app_commands.Group):
                    cmd_lines = [
                        f"> {cmd_emoji} `/{cmd.name} {subcmd.name}`: {subcmd.description}"
                        for subcmd in cmd.commands
                    ]
                    command_lines.extend(cmd_lines)
                else:
                    cmd_line = f"> {cmd_emoji} `/{cmd.name}`: {cmd.description if not isinstance(cmd, app_commands.ContextMenu) else 'Context Menu'}"
                    command_lines.append(cmd_line)

            if not command_lines:
                continue

            # Add category header and commands
            category_block = (
                f"{f"**{category}**\n" if category else ""}{"\n".join(command_lines)}"
            )
            block_length = len(category_block) + 1  # +1 for newline

            # Check if adding this block exceeds character limit
            if (
                current_char_count + block_length > self.MAX_EMBED_CHARS - 200
            ):  # Buffer for title/description
                # Create new embed for current page
                embed = EmbedX.info(emoji=embed_emoji, title=embed_title)
                if self.bot.user:
                    embed.set_thumbnail(url=self.bot.user.display_avatar)
                embed.add_field(name="", value="\n".join(current_content))
                pages.append(embed)
                current_content = [category_block]
                current_char_count = block_length
            else:
                current_content.append(category_block)
                current_char_count += block_length

        # Add final page if there's content
        if current_content:
            embed = EmbedX.info(emoji=embed_emoji, title=embed_title)
            if self.bot.user:
                embed.set_thumbnail(url=self.bot.user.display_avatar)
            embed.add_field(name="", value="\n".join(current_content))
            pages.append(embed)

        # Add page numbers
        for i, embed in enumerate(pages, 1):
            embed.description = f"📄 Page **{i}** / {len(pages)}"

        # Send response
        if not pages:
            return await interaction.followup.send(
                embed=EmbedX.warning("No commands available.")
            )
        view = PaginationView(pages, interaction.user)
        view.message = await interaction.followup.send(embed=pages[0], view=view)
