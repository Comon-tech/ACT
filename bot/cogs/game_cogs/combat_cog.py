from datetime import datetime, timedelta, timezone

from discord import Interaction, Member, User, app_commands
from discord.abc import Messageable
from discord.ext.commands import Cog
from humanize import intcomma, naturaldelta, precisedelta
from odmantic import ObjectId

from bot.main import ActBot
from bot.ui import EmbedX
from db.actor import Actor
from db.attack import Attack
from utils.misc import numsign


# ----------------------------------------------------------------------------------------------------
# * Combat Cog
# ----------------------------------------------------------------------------------------------------
class CombatCog(Cog, description="Allow players to engage in battles"):
    def __init__(self, bot: ActBot):
        self.bot = bot

    @app_commands.guild_only()
    @app_commands.command(description="Attack a member")
    async def attack(self, interaction: Interaction, member: Member):
        # Check guild & member
        if not interaction.guild or not isinstance(interaction.user, Member):
            await interaction.response.send_message(
                embed=EmbedX.warning("This command cannot be used in this context."),
                ephemeral=True,
            )
            return

        # Check members
        await interaction.response.defer(ephemeral=True)
        attacker_member = interaction.user
        defender_member = member
        if attacker_member == defender_member:
            await interaction.followup.send(
                embed=EmbedX.warning(f"You can't attack yourself.")
            )
            return

        # Retrieve attacker actor
        db = self.bot.get_db(interaction.guild)
        attacker_actor = db.find_one(
            Actor, Actor.id == attacker_member.id
        ) or self.bot.create_actor(attacker_member)
        if not attacker_actor:
            await interaction.followup.send(
                embed=EmbedX.error(f"There seems to be a problem from your side."),
            )
            return

        # Retrieve defender actor
        defender_actor = db.find_one(
            Actor, Actor.id == defender_member.id
        ) or self.bot.create_actor(defender_member)
        if not defender_actor:
            await interaction.followup.send(
                embed=EmbedX.error(
                    f"There seems to be a problem from the side of {defender_member.mention}."
                )
            )
            return

        # Chek healths
        if attacker_actor.health <= 0:
            await interaction.followup.send(
                embed=EmbedX.warning(f"You are defeated and cannot attack!.")
            )
            return
        if defender_actor.health <= 0:
            await interaction.followup.send(
                embed=EmbedX.warning(f"{defender_member.mention} is already defeated.")
            )
            return

        # Check cooldown
        if not attacker_actor.has_cooled_down_since_last_attack:
            await interaction.followup.send(
                embed=EmbedX.warning(
                    "Your speed grants a cooldown of "
                    f"**{naturaldelta(attacker_actor.attack_cooldown_timedelta)}**.\n"
                    "You need to wait "
                    f"**{precisedelta(attacker_actor.remaining_attack_cooldown_timedelta, minimum_unit='seconds', format='%0.1f')}** more."
                )
            )
            return

        # Check energy
        if attacker_actor.energy < Attack.ENERGY_COST:
            await interaction.followup.send(
                embed=EmbedX.warning(f"You don't have enough energy to attack!.")
            )
            return

        # Perform attack
        # TODO?: Save attack in database ?
        attack = Attack(
            id=ObjectId(),
            attacker=attacker_actor,
            defender=defender_actor,
            winner=None,
            loser=None,
        )

        # Save user data
        db.save_all([attacker_actor, defender_actor])

        # Send private response
        await interaction.followup.send(
            embed=EmbedX.success(f"You attacked {defender_member.mention}.")
        )

        # Create combat embed
        combat_embed = EmbedX.info(
            emoji="💔",
            title="Combat",
            description=(
                f"{attacker_member.mention} has attacked {defender_member.mention}."
            ),
        )

        # Add health & energy fields
        combat_embed.add_field(
            name=f"{attacker_actor.display_name}",
            value=f"**Health{" 🔻" if attack.recoil_damage  > 0 else ""}**"
            f"{f"\n**💥 {numsign(-attack.recoil_damage )}**" if attack.recoil_damage  > 0 else ""}\n"
            f"**:heart: {intcomma(attacker_actor.health)}** / {intcomma(attacker_actor.health_max_base)} "
            f"_`({numsign(intcomma(attacker_actor.health_max_extra))})`_\n`{attacker_actor.health_bar}`\n"
            f"**Energy 🔻**\n"
            f"**🎆 {numsign(intcomma(-Actor.ATTACK_ENERGY_COST))}**\n"
            f"**⚡ {intcomma(attacker_actor.energy)}** / {intcomma(attacker_actor.energy_max_base)} "
            f"_`({numsign(intcomma(attacker_actor.energy_max_extra))})`_\n`{attacker_actor.energy_bar}`",
        )
        combat_embed.add_field(
            name=f"{defender_actor.display_name}",
            value=f"**Health{" 🔻" if attack.effective_damage  > 0 else ""}**"
            f"{f"\n**💥 {numsign(-attack.effective_damage )}**" if attack.effective_damage  > 0 else ""}\n"
            f"**:heart: {intcomma(defender_actor.health)}** / {intcomma(defender_actor.health_max_base)} "
            f"_`({numsign(intcomma(defender_actor.health_max_extra))})`_\n`{defender_actor.health_bar}`\n"
            f"**Energy**\n"
            f"**⚡ {intcomma(defender_actor.energy)}** / {intcomma(defender_actor.energy_max_base)} "
            f"_`({numsign(intcomma(defender_actor.energy_max_extra))})`_\n`{defender_actor.energy_bar}`",
        )

        # Add damage feedback fields
        if attack.recoil_damage > 0:
            combat_embed.add_field(
                name="🤺 Repellence",
                value=f"{attacker_member.mention} attack has been repelled by {defender_member.mention}!\n"
                f"{attacker_member.mention} has taken recoil damage.",
                inline=False,
            )
        elif attack.effective_damage > 0:
            combat_embed.add_field(
                name=":crossed_swords: Damage",
                value=f"{attacker_member.mention} has dealt damage to {defender_member.mention}.",
                inline=False,
            )
        else:
            combat_embed.add_field(
                name=":shield: Block",
                value=f"{attacker_member.mention} has dealt no damage to {defender_member.mention}.",
                inline=False,
            )

        # Add media fields
        combat_embed.set_author(
            name=attacker_member.display_name, icon_url=attacker_member.display_avatar
        )
        combat_embed.set_thumbnail(url=defender_member.display_avatar)

        # Send combat response
        if isinstance(interaction.channel, Messageable):
            await interaction.channel.send(
                content=f"{attacker_member.mention} 🆚 {defender_member.mention} 😱",
                embed=combat_embed,
            )

        # Create post-combat embed
        if not (attack.is_fatal):
            return
        post_combat_embed = EmbedX.info(emoji="🚩", title="Combat Over")

        # Add victory feedback field
        if attack.attacker_is_winner:
            post_combat_embed.add_field(
                name="🏴 Takedown",
                value=f"{attacker_member.mention} has defeated {defender_member.mention}.",
                inline=False,
            )
        if attack.defender_is_winner:
            post_combat_embed.add_field(
                name="🔥 Backfire",
                value=f"{defender_member.mention} has defeated {attacker_member.mention}.",
                inline=False,
            )

        # Add promotion/demotion fields
        if attacker_actor.rank:
            if attack.attacker_is_promoted:
                post_combat_embed.add_field(
                    name="👍 Promotion",
                    value=f"{attacker_member.mention} has been promoted to **{attacker_actor.rank.name}**",
                )
            elif attack.attacker_is_demoted:
                post_combat_embed.add_field(
                    name="👎 Demotion",
                    value=f"{attacker_member.mention} has been demoted to **{attacker_actor.rank.name}**",
                )
        if defender_actor.rank:
            if attack.defender_is_promoted:
                post_combat_embed.add_field(
                    name="👍 Promotion",
                    value=f"{defender_member.mention} has been promoted to **{defender_actor.rank.name}**",
                )
            elif attack.defender_is_demoted:
                post_combat_embed.add_field(
                    name="👎 Demotion",
                    value=f"{defender_member.mention} has been demoted to **{defender_actor.rank.name}**",
                )

        # Send post-combat response
        if isinstance(interaction.channel, Messageable):
            await interaction.channel.send(embed=post_combat_embed)

    @app_commands.guild_only()
    @app_commands.command(description="Recover your or a member's health and energy")
    async def revive(
        self,
        interaction: Interaction,
        member: Member | User | None = None,
    ):
        # Check guild & member
        member = member or interaction.user
        if not interaction.guild or not isinstance(member, Member):
            await interaction.response.send_message(
                embed=EmbedX.warning("This command cannot be used in this context."),
                ephemeral=True,
            )
            return

        # Get actor
        await interaction.response.defer(ephemeral=True)
        db = self.bot.get_db(interaction.guild)
        actor = db.find_one(Actor, Actor.id == member.id) or self.bot.create_actor(
            member
        )

        # Recover health & energy
        actor.health = actor.health_max
        actor.energy = actor.energy_max
        db.save(actor)

        # Send response
        await interaction.followup.send(
            embed=EmbedX.success(f"{member.mention} is revived.")
        )

    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(
        description="Initialize stats and unequip items for all actors"
    )
    async def reset_stats(self, interaction: Interaction):
        # Check guild
        guild = interaction.guild
        if not guild:
            await interaction.response.send_message(
                embed=EmbedX.warning("This command cannot be used in this context."),
                ephemeral=True,
            )
            return

        # Update actors
        await interaction.response.defer(ephemeral=True)
        db = self.bot.get_db(guild)
        actors = list(db.find(Actor))
        for actor in actors:
            actor.items_equipped.clear()
            actor.clear_extra_stats()
            actor.health = actor.health_max
            actor.energy = actor.energy_max
        db.save_all(actors)
        await interaction.followup.send(
            embed=EmbedX.success(f"Stats reset for **{len(actors)}** actors.")
        )
