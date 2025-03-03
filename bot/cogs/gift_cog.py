from random import randint

from discord import Interaction, Member, app_commands
from discord.ext.commands import Cog

from bot.main import ActBot
from bot.ui import EmbedX
from db.actor import Actor


# ----------------------------------------------------------------------------------------------------
# * Gift Cog
# ----------------------------------------------------------------------------------------------------
class GiftCog(Cog, description="Allows players to gift eachother."):
    def __init__(self, bot: ActBot):
        self.bot = bot

    # ----------------------------------------------------------------------------------------------------
    # * Donate
    # ----------------------------------------------------------------------------------------------------
    @app_commands.guild_only()
    @app_commands.command(description="Give your gold to another member")
    @app_commands.describe(
        member="Member to donate gold to", gold="Amount of gold to donate"
    )
    async def donate(self, interaction: Interaction, member: Member, gold: int):
        # Validate input
        if gold <= 0:
            await interaction.response.send_message(
                embed=EmbedX.error(
                    f"Your gold input value of **{gold}** is invalid.\nDid you mean **{-gold if gold else randint(1, 1000)}** ?"
                ),
                ephemeral=True,
            )
            return

        # Retrieve donor user
        await interaction.response.defer()
        db = self.bot.get_db(interaction.guild)
        donor_member = interaction.user
        donor_actor = db.find_one(Actor, Actor.id == donor_member.id)
        if not donor_actor:
            await interaction.followup.send(
                embed=EmbedX.error(f"There seems to be a problem from your side."),
            )
            return

        # Retrieve recipient user
        recipient_member = member
        recipient_actor = db.find_one(Actor, Actor.id == recipient_member.id)
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
                    f"You don't have enough to donate **💰 {gold} Gold**.\nYou have **💰 {donor_actor.gold} Gold**."
                )
            )
            return

        # Add gold and update user data
        donor_actor.gold = max(0, donor_actor.gold - gold)
        recipient_actor.gold += gold
        db.save_all([donor_actor, recipient_actor])

        # Create the response embed
        embed = EmbedX.success(
            icon="💛",
            title="Gold Donation",
            description=(
                f"{recipient_member.mention} has received **💰 {gold} Gold** from {donor_member.mention}."
            ),
        )
        embed.set_author(
            name=donor_member.display_name, icon_url=donor_member.display_avatar
        )
        embed.set_thumbnail(url=recipient_member.display_avatar)

        # Respond
        await interaction.followup.send(
            content=f"Congratulations, {recipient_member.mention}! 🎉", embed=embed
        )
