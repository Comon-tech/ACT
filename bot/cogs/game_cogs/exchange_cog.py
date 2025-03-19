from random import randint

from discord import Interaction, Member, app_commands
from discord.abc import Messageable
from discord.ext.commands import Cog

from bot.main import ActBot
from bot.ui import EmbedX
from db.actor import Actor
from utils.misc import numsign


# ----------------------------------------------------------------------------------------------------
# * Exchange Cog
# ----------------------------------------------------------------------------------------------------
class ExchangeCog(Cog, description="Allow players to exchange gold and goods"):
    def __init__(self, bot: ActBot):
        self.bot = bot

    # ----------------------------------------------------------------------------------------------------
    # * Donate
    # ----------------------------------------------------------------------------------------------------
    @app_commands.guild_only()
    @app_commands.command(description="Give your gold to another member")
    @app_commands.describe(
        member="Recipient member to send gold to", gold="Amount of gold to donate"
    )
    async def donate(self, interaction: Interaction, member: Member, gold: int):
        # Validate input
        if gold <= 0:
            await interaction.response.send_message(
                embed=EmbedX.error(
                    f"Your gold input value of `{gold}` is invalid.\nDid you mean **{-gold if gold else randint(1, 1000)}** ?"
                ),
                ephemeral=True,
            )
            return

        # Retrieve donor user
        await interaction.response.defer(ephemeral=True)
        db = self.bot.get_db(interaction.guild)
        donor_member = interaction.user
        donor_actor = db.find_one(
            Actor, Actor.id == donor_member.id
        ) or self.bot.create_actor(donor_member)
        if not donor_actor:
            await interaction.followup.send(
                embed=EmbedX.error(f"There seems to be a problem from your side."),
            )
            return

        # Retrieve recipient user
        recipient_member = member
        recipient_actor = db.find_one(
            Actor, Actor.id == recipient_member.id
        ) or self.bot.create_actor(recipient_member)
        if not recipient_actor:
            await interaction.followup.send(
                embed=EmbedX.error(
                    f"There seems to be a problem from the side of {recipient_member.mention}."
                )
            )
            return

        # Check if user is trying to donate to themselves
        if donor_member == recipient_member:
            await interaction.followup.send(
                embed=EmbedX.warning(f"You can't donate to yourself.")
            )
            return

        # Chek if donor has the gold
        if donor_actor.gold < gold:
            await interaction.followup.send(
                embed=EmbedX.warning(
                    f"You don't have enough to donate **💰 {gold}** gold.\nYou only have **💰 {donor_actor.gold}** gold."
                )
            )
            return

        # Add gold and update user data
        donor_actor.gold = max(0, donor_actor.gold - gold)
        recipient_actor.gold += gold
        db.save_all([donor_actor, recipient_actor])

        # Send private response
        await interaction.followup.send(
            embed=EmbedX.success(
                f"You transferred **💰 {gold}** gold to {recipient_member.mention}."
            )
        )

        # Create public response embed
        embed = EmbedX.success(
            emoji="💛",
            title="Donation",
            description=(
                f"{donor_member.mention} has given gold to {recipient_member.mention}."
            ),
        )
        embed.add_field(
            name=f"{donor_actor.display_name}\nGold 🔻",
            value=f"**💰 -{gold}**",
        )
        embed.add_field(
            name=f"{recipient_member.display_name}\nGold 🔼",
            value=f"**💰 +{gold}**",
        )
        embed.set_author(
            name=donor_member.display_name, icon_url=donor_member.display_avatar
        )
        embed.set_thumbnail(url=recipient_member.display_avatar)

        # Send public response
        if isinstance(interaction.channel, Messageable):
            await interaction.channel.send(
                content=f"Congratulations, {recipient_member.mention}! 🎉", embed=embed
            )
