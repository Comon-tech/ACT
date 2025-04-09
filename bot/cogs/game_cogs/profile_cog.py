from enum import Enum
from typing import Callable

from discord import Color, Embed, Guild, Interaction, Member, User, app_commands
from discord.ext.commands import Cog, GroupCog
from humanize import intcomma, naturalsize, naturaltime
from odmantic import query

from bot.main import ActBot
from bot.ui import EmbedX
from db.actor import Actor
from db.item import Item, ItemStack
from utils.misc import numsign


# ----------------------------------------------------------------------------------------------------
# * Profile Cog
# ----------------------------------------------------------------------------------------------------
class ProfileCog(
    GroupCog,
    group_name="profile",
    description="Allow players to view their profile data",
):
    def __init__(self, bot: ActBot):
        self.bot = bot

    # ----------------------------------------------------------------------------------------------------

    @app_commands.guild_only()
    @app_commands.command(
        description="View your or another member's profile overview information"
    )
    async def overview(self, interaction: Interaction, member: Member | None = None):
        profile_interface = await self.get_profile_interface(interaction, member)
        if not profile_interface:
            return
        embed, member, actor = profile_interface
        self.add_roles_field(embed, member)
        self.add_separator_field(embed)
        self.add_rank_field(embed, actor)
        self.add_duels_field(embed, actor)
        self.add_separator_field(embed)
        self.add_level_field(embed, actor)
        self.add_experience_field(embed, actor)
        self.add_separator_field(embed)
        self.add_health_field(embed, actor)
        self.add_energy_field(embed, actor)
        self.add_separator_field(embed)
        self.add_attack_field(embed, actor)
        self.add_defense_field(embed, actor)
        self.add_speed_field(embed, actor)
        self.add_separator_field(embed)
        self.add_gold_field(embed, actor)
        self.add_equipment_field(embed, actor)
        self.add_items_field(embed, actor)
        self.add_separator_field(embed)
        self.set_thumbnail(embed, member)
        self.set_footer(embed, member)
        await interaction.followup.send(embed=embed)

    @app_commands.guild_only()
    @app_commands.command(description="View your or another member's profile picture")
    async def picture(self, interaction: Interaction, member: Member | None = None):
        profile_interface = await self.get_profile_interface(interaction, member)
        if not profile_interface:
            return
        embed, member, _ = profile_interface
        embed.set_image(url=member.display_avatar.url)
        await interaction.followup.send(embed=embed)

    @app_commands.guild_only()
    @app_commands.command(
        description="View your or another member's membership (roles, dates) information"
    )
    async def membership(self, interaction: Interaction, member: Member | None = None):
        profile_interface = await self.get_profile_interface(interaction, member)
        if not profile_interface:
            return
        embed, member, _ = profile_interface
        self.add_roles_field(embed, member)
        self.add_separator_field(embed)
        embed.add_field(name="ID", value=f"🆔 {member.id}", inline=False)
        embed.add_field(name="Username", value=f"📧 {member.name}")
        embed.add_field(name="Name", value=f"👤 {member.display_name}")
        self.add_separator_field(embed)
        self.set_thumbnail(embed, member)
        self.set_footer(embed, member)
        await interaction.followup.send(embed=embed)

    @app_commands.guild_only()
    @app_commands.command(
        description="View your or another member's progress (rank, duels, level, experience) information"
    )
    async def progress(self, interaction: Interaction, member: Member | None = None):
        profile_interface = await self.get_profile_interface(interaction, member)
        if not profile_interface:
            return
        embed, member, actor = profile_interface
        self.add_separator_field(embed)
        self.add_rank_field(embed, actor)
        self.add_duels_field(embed, actor)
        self.add_separator_field(embed)
        self.add_level_field(embed, actor)
        self.add_experience_field(embed, actor)
        self.add_separator_field(embed)
        self.set_thumbnail(embed, member)
        await interaction.followup.send(embed=embed)

    @app_commands.guild_only()
    @app_commands.command(
        description="View your or another member's status (health, energy, attack, defense, speed) information"
    )
    async def status(self, interaction: Interaction, member: Member | None = None):
        profile_interface = await self.get_profile_interface(interaction, member)
        if not profile_interface:
            return
        embed, member, actor = profile_interface
        self.add_separator_field(embed)
        self.add_health_field(embed, actor)
        self.add_energy_field(embed, actor)
        self.add_separator_field(embed)
        self.add_attack_field(embed, actor)
        self.add_defense_field(embed, actor)
        self.add_speed_field(embed, actor)
        self.add_separator_field(embed)
        self.set_thumbnail(embed, member)
        await interaction.followup.send(embed=embed)

    @app_commands.guild_only()
    @app_commands.command(
        description="View your or another member's property (gold and items) information"
    )
    async def property(self, interaction: Interaction, member: Member | None = None):
        profile_interface = await self.get_profile_interface(interaction, member)
        if not profile_interface:
            return
        embed, member, actor = profile_interface
        self.add_separator_field(embed)
        self.add_gold_field(embed, actor)
        self.add_separator_field(embed)
        self.add_equipment_list_field(embed, actor)
        self.add_separator_field(embed)
        self.add_items_list_field(embed, actor)
        self.add_separator_field(embed)
        self.set_thumbnail(embed, member)
        await interaction.followup.send(embed=embed)

    # ----------------------------------------------------------------------------------------------------

    async def get_profile_interface(
        self, interaction: Interaction, member: Member | User | None
    ) -> tuple[Embed, Member, Actor] | None:
        # Check guild & member
        member = member or interaction.user
        if not interaction.guild or not isinstance(member, Member):
            await interaction.response.send_message(
                embed=EmbedX.warning("This command cannot be used in this context."),
                ephemeral=True,
            )
            return

        # Defer interaction
        await interaction.response.defer()

        # Get actor
        actor = self.bot.get_db(member.guild).find_one(
            Actor, Actor.id == member.id
        ) or self.bot.create_actor(member)

        # Create embed
        embed = EmbedX.info(title="", emoji="", description=member.mention)

        # Return interface
        return (embed, member, actor)

    # ----------------------------------------------------------------------------------------------------

    @staticmethod
    def add_separator_field(embed: Embed):
        embed.add_field(name="", value="", inline=False)

    @staticmethod
    def add_roles_field(embed: Embed, member: Member):
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

    @staticmethod
    def set_thumbnail(embed: Embed, member: Member):
        embed.set_thumbnail(url=member.display_avatar.url)

    @staticmethod
    def set_footer(embed: Embed, member: Member):
        embed.set_footer(
            text=f"⌚ Joined {member.guild.name} {naturaltime(member.joined_at or 0)}\n"
            f"⌚ Joind Discord {naturaltime(member.created_at)}",
            icon_url=member.guild.icon.url if member.guild.icon else None,
        )

    # ----------------------------------------------------------------------------------------------------

    @staticmethod
    def add_rank_field(embed: Embed, actor: Actor):
        embed.add_field(
            name="Rank",
            value=f"**🏆 {actor.rank.name if actor.rank else "?"}**\n`{actor.rank_bar}`",
        )

    @staticmethod
    def add_duels_field(embed: Embed, actor: Actor):
        embed.add_field(
            name=f"Duels `🚩{actor.duels}`",
            value=f"**:flag_white: {actor.wins}** _wins_\n**:flag_black: {actor.losses}** _losses_",
        )

    @staticmethod
    def add_level_field(embed: Embed, actor: Actor):
        embed.add_field(
            name="Level", value=f"**🏅 {actor.level}**\n`{actor.level_bar}`"
        )

    @staticmethod
    def add_experience_field(embed: Embed, actor: Actor):
        embed.add_field(
            name="Experience",
            value=f"**⏫ {intcomma(actor.xp)}** / {intcomma(actor.next_level_xp)}\n`{actor.xp_bar}`",
        )

    # ----------------------------------------------------------------------------------------------------

    @staticmethod
    def add_health_field(embed: Embed, actor: Actor):
        stat = Item.STATS.get("health")
        if stat:
            embed.add_field(
                name=f"{stat.name}{" `💀`" if actor.health <= 0 else ""}",
                value=f"**{(stat.emoji or stat.alt_emoji)} {intcomma(actor.health)}** / {intcomma(actor.health_max)} "
                f"_`({numsign(intcomma(actor.health_max_extra))})`_\n`{actor.health_bar}`",
            )

    @staticmethod
    def add_energy_field(embed: Embed, actor: Actor):
        stat = Item.STATS.get("energy")
        if stat:
            embed.add_field(
                name=f"Energy{" `⚠️`" if actor.energy <= 0 else ""}",
                value=f"**{stat.emoji or stat.alt_emoji} {intcomma(actor.energy)}** / {intcomma(actor.energy_max)} "
                f"_`({numsign(intcomma(actor.energy_max_extra))})`_\n`{actor.energy_bar}`",
            )

    @staticmethod
    def add_attack_field(embed: Embed, actor: Actor):
        stat = Item.STATS.get("attack")
        if stat:
            embed.add_field(
                name="Attack",
                value=f"**{stat.emoji or stat.alt_emoji} {intcomma(actor.attack)}** _`({numsign(intcomma(actor.attack_extra))})`_",
            )

    @staticmethod
    def add_defense_field(embed: Embed, actor: Actor):
        stat = Item.STATS.get("defense")
        if stat:
            embed.add_field(
                name="Defense",
                value=f"**{stat.emoji or stat.alt_emoji} {intcomma(actor.defense)}** _`({numsign(intcomma(actor.defense_extra))})`_",
            )

    @staticmethod
    def add_speed_field(embed: Embed, actor: Actor):
        stat = Item.STATS.get("speed")
        if stat:
            embed.add_field(
                name="Speed",
                value=f"**{stat.emoji or stat.alt_emoji} {intcomma(actor.speed)}** _`({numsign(intcomma(actor.speed_extra))})`_",
            )

    # ----------------------------------------------------------------------------------------------------

    @staticmethod
    def add_gold_field(embed: Embed, actor: Actor):
        embed.add_field(name="Gold", value=f"**💰 {intcomma(actor.gold)}**")

    @staticmethod
    def add_equipment_field(embed: Embed, actor: Actor):
        embed.add_field(
            name="Equipment",
            value=f"**🧰 {intcomma(len(actor.items_equipped))}/{actor.ITEMS_EQUIP_MAX}**",
        )

    @staticmethod
    def add_items_field(embed: Embed, actor: Actor):
        embed.add_field(
            name="Items", value=f"**🎒 {intcomma(len(actor.item_stacks))}**"
        )

    @staticmethod
    def add_equipment_list_field(embed: Embed, actor: Actor):
        equipped_items = list(actor.items_equipped.values())
        embed.add_field(
            name=f"Equipment **`🧰{intcomma(len(actor.items_equipped))}/{actor.ITEMS_EQUIP_MAX}`**",
            value="",
            inline=False,
        )
        if equipped_items:
            midpoint = (len(equipped_items) + 1) // 2
            equipped_item_row: Callable[[Item], str] = lambda item: (
                f"{item.emoji or item.alt_emoji} **{item.name} `{item.item_stats_text()}`**"
            )
            first_column = [
                equipped_item_row(item) for item in equipped_items[:midpoint]
            ]
            second_column = [
                equipped_item_row(item) for item in equipped_items[midpoint:]
            ]
            embed.add_field(name="", value="\n".join(first_column))
            embed.add_field(name="", value="\n".join(second_column))
        else:
            embed.add_field(name="", value="_No equipped items_")

    @staticmethod
    def add_items_list_field(embed: Embed, actor: Actor):
        item_stacks = list(actor.item_stacks.values())
        embed.add_field(
            name=f"Items **`🎒{intcomma(len(actor.item_stacks))}`**",
            value="",
            inline=False,
        )
        if item_stacks:
            midpoint = (len(item_stacks) + 1) // 2
            item_stack_row: Callable[[ItemStack], str] = lambda item_stack: (
                f"{item_stack.item.emoji or item_stack.item.alt_emoji} **{item_stack.item.name} `x{item_stack.quantity}`**"
            )
            first_column = [
                item_stack_row(item_stack) for item_stack in item_stacks[:midpoint]
            ]
            second_column = [
                item_stack_row(item_stack) for item_stack in item_stacks[midpoint:]
            ]
            embed.add_field(name="", value="\n".join(first_column))
            embed.add_field(name="", value="\n".join(second_column))
        else:
            embed.add_field(name="", value="_No items_")
