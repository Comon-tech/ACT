# import re
# from datetime import datetime, timedelta

# import discord
# from discord import Member, app_commands
# from discord.abc import Messageable, PrivateChannel
# from discord.ext import commands

# from bot.ui import EmbedX


# # ----------------------------------------------------------------------------------------------------
# # * Purge Cog
# # ----------------------------------------------------------------------------------------------------
# class PurgeCog(commands.Cog):
#     def __init__(self, bot):
#         self.bot = bot

#     @app_commands.command(
#         name="purge",
#         description="Delete messages based on count, time, or message range",
#     )
#     @app_commands.describe(
#         value="Count (e.g., 10), time (e.g., 5m/2h/1d), or message URL/ID",
#         second_value="Second message URL/ID for range deletion (optional)",
#         user="Only delete messages from this user (optional)",
#     )
#     @app_commands.checks.has_permissions(manage_messages=True)
#     async def purge(
#         self,
#         interaction: discord.Interaction,
#         value: str,
#         second_value: str | None = None,
#         user: Member | None = None,
#     ):
#         """ """
#         if (
#             not interaction.guild
#             or not interaction.channel
#             or not isinstance(interaction.channel, Messageable)
#             or isinstance(interaction.channel, PrivateChannel)
#         ):
#             await interaction.followup.send(
#                 embed=EmbedX.warning("This command cannot be used in this context."),
#                 ephemeral=True,
#             )
#             return

#         await interaction.response.defer(ephemeral=True)
#         channel = interaction.channel

#         # Check bot permissions
#         if not channel.permissions_for(interaction.guild.me).manage_messages:
#             await interaction.followup.send(
#                 embed=EmbedX.warning("You don't have permission to manage messages."),
#                 ephemeral=True,
#             )
#             return

#         try:
#             # Case 1: Purge by count
#             if value.isdigit():
#                 count = min(
#                     int(value), 100
#                 )  # Discord limit is 100 messages per bulk delete
#                 messages = [
#                     msg
#                     async for msg in channel.history(limit=count + 1)
#                     if not user or msg.author == user
#                 ]
#                 await channel.delete_messages(messages)
#                 await interaction.followup.send(
#                     embed=EmbedX.success(f"Deleted **{len(messages)}** messages."),
#                     ephemeral=True,
#                 )
#                 return

#             # Case 2: Purge by time
#             time_units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
#             if value[-1] in time_units and value[:-1].isdigit():
#                 time_amount = int(value[:-1])
#                 time_unit = time_units[value[-1]]
#                 time_delta = timedelta(seconds=time_amount * time_unit)
#                 cutoff_time = datetime.utcnow() - time_delta

#                 messages = [
#                     msg
#                     async for msg in channel.history(limit=100)
#                     if msg.created_at > cutoff_time and (not user or msg.author == user)
#                 ]
#                 await channel.delete_messages(messages)
#                 await interaction.followup.send(
#                     embed=EmbedX.warning(
#                         f"Deleted **{len(messages)}** messages from last {value}."
#                     ),
#                     ephemeral=True,
#                 )
#                 return

#             # Case 3 & 4: Purge by message or between messages
#             start_msg = await self.get_message_from_input(channel, value)
#             if not start_msg:
#                 await interaction.followup.send(
#                     embed=EmbedX.error("Invalid message ID or URL."), ephemeral=True
#                 )
#                 return

#             if second_value:  # Between two messages
#                 end_msg = await self.get_message_from_input(channel, second_value)
#                 if not end_msg:
#                     await interaction.followup.send(
#                         embed=EmbedX.error("Invalid second message ID or URL."),
#                         ephemeral=True,
#                     )
#                     return

#                 # Ensure start_msg is older than end_msg
#                 if start_msg.created_at > end_msg.created_at:
#                     start_msg, end_msg = end_msg, start_msg

#                 messages = [
#                     msg
#                     async for msg in channel.history(limit=100, before=end_msg)
#                     if msg.created_at >= start_msg.created_at
#                     and (not user or msg.author == user)
#                 ]
#             else:  # Until one message
#                 messages = [
#                     msg
#                     async for msg in channel.history(limit=100, before=start_msg)
#                     if not user or msg.author == user
#                 ]

#             await channel.delete_messages(messages)
#             await interaction.followup.send(
#                 embed=EmbedX.success(f"Deleted **{len(messages)}** messages"),
#                 ephemeral=True,
#             )

#         except discord.Forbidden:
#             await interaction.followup.send(
#                 embed=EmbedX.error("You don't have permission to delete messages!"),
#                 ephemeral=True,
#             )
#         except Exception as e:
#             await interaction.followup.send(embed=EmbedX.error(str(e)), ephemeral=True)

#     @purge.error
#     async def purge_error(self, interaction: discord.Interaction, error):
#         if isinstance(error, app_commands.MissingPermissions):
#             await interaction.response.send_message(
#                 embed=EmbedX.warning(
#                     "You need Manage Messages permission to use this command!"
#                 ),
#                 ephemeral=True,
#             )

#     # ----------------------------------------------------------------------------------------------------

#     async def get_message_from_input(self, channel, input_str):
#         """Extract message ID from URL or plain ID."""
#         url_pattern = r"https://discord\.com/channels/\d+/\d+/(\d+)"
#         match = re.match(url_pattern, input_str)
#         if match:
#             message_id = int(match.group(1))
#         else:
#             try:
#                 message_id = int(input_str)
#             except ValueError:
#                 return None
#         try:
#             return await channel.fetch_message(message_id)
#         except discord.NotFound:
#             return None
