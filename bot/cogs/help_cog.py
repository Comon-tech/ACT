from collections import defaultdict

from discord import Interaction, Member, app_commands
from discord.ext.commands import GroupCog

from bot.main import ActBot
from bot.ui import EmbedX


# ----------------------------------------------------------------------------------------------------
# * Help Cog
# ----------------------------------------------------------------------------------------------------
class HelpCog(
    GroupCog, group_name="help", description="Provide help and information interface."
):
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
        # Initialize embed
        embed = EmbedX.info(emoji="🔷", title=f"Commands")

        # Group commands by category/module
        command_groups: dict[str, list[app_commands.Command]] = defaultdict(list)
        for cmd in self.bot.tree.get_commands():
            # Extract category (you might want to customize this based on your bot's structure)
            category = getattr(cmd, "category", "Root")
            if isinstance(cmd, app_commands.Group):
                category = f"📂 {cmd.name.capitalize()}"
            command_groups[category].append(cmd)

        # Check if user is admin for permission filtering
        is_admin = (
            isinstance(interaction.user, Member)
            and interaction.user.guild_permissions.administrator
        )

        # Build command list for each category
        for category, commands in sorted(command_groups.items()):
            command_lines = []
            for cmd in sorted(commands, key=lambda x: x.name):
                # Skip admin commands for non-admins
                admin_required = (
                    getattr(cmd, "default_permissions", None)
                    and cmd.default_permissions.administrator
                )
                if admin_required and not is_admin:
                    continue

                # Format command description
                cmd_line = ""
                if isinstance(cmd, app_commands.Group):  # Handle command groups
                    cmd_line = "\n".join(
                        [
                            f"- `/{cmd.name} {subcmd.name}`:  {subcmd.description}"
                            for subcmd in cmd.commands
                        ]
                    )
                else:
                    cmd_line = f"- `/{cmd.name}`: {(
                        cmd.description
                        if not isinstance(cmd, app_commands.ContextMenu)
                        else "Context Menu"
                    )}"

                command_lines.append(cmd_line)

            if command_lines:  # Only add field if there are visible commands
                embed.add_field(
                    name=category, value="\n".join(command_lines), inline=False
                )

        # Send
        if self.bot.user:
            embed.set_thumbnail(url=self.bot.user.display_avatar)
        await interaction.response.send_message(embed=embed, ephemeral=True)
