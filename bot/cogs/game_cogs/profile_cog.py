from enum import Enum

from discord import Color, Embed, Guild, Interaction, Member, User, app_commands
from discord.ext.commands import Cog
from humanize import intcomma, naturalsize, naturaltime
from odmantic import query

from bot.main import ActBot
from bot.ui import EmbedX
from db.actor import Actor
from utils.misc import numsign


# ----------------------------------------------------------------------------------------------------
# * Profile Cog
# ----------------------------------------------------------------------------------------------------
class ProfileCog(Cog, description="Allow players to view their profile data"):
    def __init__(self, bot: ActBot):
        self.bot = bot
        self.profile.autocomplete("section")(self.profile_section_autocomplete)

    # ----------------------------------------------------------------------------------------------------

    @app_commands.guild_only()
    @app_commands.command(
        description="View your or another member's profile information"
    )
    async def profile(
        self,
        interaction: Interaction,
        member: Member | User | None = None,
        section: str = "all",
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
        actor = self.bot.get_db(interaction.guild).find_one(
            Actor, Actor.id == member.id
        ) or self.bot.create_actor(member)

        # Create profile embed
        await interaction.response.defer()
        embed = EmbedX.info(title="", emoji="", description=member.mention)

        # Add roles field
        embed.add_field(
            name="",
            value=" ".join(
                [
                    f"`{role.name}`"
                    for role in member.roles
                    if role != member.guild.default_role
                ]
            ),
            inline=False,
        )

        # Add progress (leveling) stats fields
        if section in ("all", "progress"):
            embed.add_field(
                name="Rank", value=f"**🏆 {actor.rank_name}**\n`{actor.rank_bar}`"
            )
            embed.add_field(
                name="Level",
                value=f"**🏅 {actor.level}**\n`{actor.level_bar}`",
            )
            embed.add_field(
                name="Experience",
                value=f"**⏫ {intcomma(actor.xp)}** / {intcomma(actor.next_level_xp)}\n`{actor.xp_bar}`",
            )
            embed.add_field(name="", value="", inline=False)

        # Add property (economy) stats fields
        if section in ("all", "property"):
            embed.add_field(name="Gold", value=f"**💰 {intcomma(actor.gold)}**")
            embed.add_field(
                name="Items", value=f"**🎒 {intcomma(len(actor.item_stacks))}**"
            )
            embed.add_field(
                name="Equipment",
                value=f"**🧰 {intcomma(len(actor.equipped_items))}** / {actor.MAX_EQUIPMENT}",
            )
            embed.add_field(name="", value="", inline=False)

        # Add status (combat) stats fields
        if section in ("all", "status"):
            embed.add_field(
                name="Health",
                value=f"**:heart: {intcomma(actor.health)}** / {intcomma(actor.base_max_health)} "
                f"_`({numsign(intcomma(actor.extra_max_health))})`_\n`{actor.health_bar}`",
            )
            embed.add_field(
                name="Energy",
                value=f"**⚡ {intcomma(actor.energy)}** / {intcomma(actor.max_energy)} "
                f"_`({numsign(intcomma(actor.extra_max_energy))})`_\n`{actor.energy_bar}`",
            )
            embed.add_field(name="", value="", inline=False)
            embed.add_field(
                name="Attack",
                value=f"**:crossed_swords: {intcomma(actor.attack)}** _`({numsign(intcomma(actor.extra_attack))})`_",
            )
            embed.add_field(
                name="Defense",
                value=f"**🛡 {intcomma(actor.defense)}** _`({numsign(intcomma(actor.extra_defense))})`_",
            )
            embed.add_field(
                name="Speed",
                value=f"**🥾 {intcomma(actor.speed)}** _`({numsign(intcomma(actor.extra_speed))})`_",
            )
            embed.add_field(name="", value="", inline=False)

        # Add images & extra infos
        if section in ("picture"):
            embed.set_image(url=member.display_avatar.url)
        else:
            embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_author(name=member.display_name, icon_url=member.display_avatar.url)
        embed.set_footer(
            text=f"⌚ Joined {member.guild.name} {naturaltime(member.joined_at or 0)}\n"
            f"⌚ Joind Discord {naturaltime(member.created_at)}",
            icon_url=member.guild.icon.url if member.guild.icon else None,
        )

        # Send response
        await interaction.followup.send(embed=embed)

    async def profile_section_autocomplete(
        self,
        interaction: Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        return [
            choice
            for choice in [
                app_commands.Choice(name="「✳」 All", value="all"),
                app_commands.Choice(name="「🏆」 Progress", value="progress"),
                app_commands.Choice(name="「💰」 Property", value="property"),
                app_commands.Choice(name="「💗」 Status", value="status"),
                app_commands.Choice(name="「🌆」 Picture", value="picture"),
                app_commands.Choice(name="「 」 None", value="none"),
            ]
            if current.lower() in choice.value.lower()
        ]
