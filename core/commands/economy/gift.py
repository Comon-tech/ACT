from discord.ext import commands
from discord import app_commands, Interaction, Embed, Member, Color
from services.db import get_user_data, save_user_data
from .store import Store



class Gift(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @app_commands.command(name="gift", description="Gift an item to another user.")
    @app_commands.describe(item="The item you want to purchase")
    @app_commands.autocomplete(item=Store.item_autocomplete_fn())
    async def gift(interaction: Interaction, recipient: Member, *, item: str):
        giver_id = str(interaction.user.id)
        recipient_id = str(recipient.id)

        # Prevent self-gifting
        if giver_id == recipient_id:
            embed = Embed(
                title=f"Gift {recipient.display_name}",
                description=f"**❌ You can't gift items to yourself.**",
                color=Color.gold()
            )
            embed.set_thumbnail(url=recipient.display_avatar.url)
            await interaction.response.send_message(embed=embed)
            return

        # Fetch giver and recipient data
        giver_data = get_user_data(giver_id)
        recipient_data = get_user_data(recipient_id)

        # Validate giver's inventory
        if not giver_data or "inventory" not in giver_data:
            embed = Embed(
                title=f"Gift {recipient.display_name}",
                description=f"**❌ You don't have an inventory to gift from.**",
                color=Color.gold()
            )
            embed.set_thumbnail(url=recipient.display_avatar.url)
            await interaction.response.send_message(embed=embed)
            return

        # Ensure recipient data exists
        if not recipient_data:
            recipient_data = {"user_id": recipient_id, "balance": 0, "xp": 0, "level": 1, "inventory": []}

        giver_inventory = giver_data.get("inventory", [])

        # Check if the giver owns the item
        if item not in giver_inventory:
            embed = Embed(
                title=f"Gift {recipient.display_name}",
                description=f"**❌ You don't own an item called {item}.**",
                color=Color.gold()
            )
            embed.set_thumbnail(url=recipient.display_avatar.url)
            await interaction.response.send_message(embed=embed)
            return

        # Update giver's inventory
        giver_inventory.remove(item)
        giver_data["inventory"] = giver_inventory

        # Update recipient's inventory
        recipient_inventory = recipient_data.get("inventory", [])
        recipient_inventory.append(item)
        recipient_data["inventory"] = recipient_inventory

        # Save data to database
        save_user_data(giver_id, giver_data)  # Update giver in the database
        save_user_data(recipient_id, recipient_data)  # Update recipient in the database

        # Confirm the gift
        embed = Embed(
            title="🎁 Gift Successful!",
            description=(
                f"{interaction.user.mention} has gifted **{item}** to {recipient.mention}!\n"
                f"Check your inventory to see the updated items."
            ),
            color=Color.green()
        )
        embed.set_thumbnail(url=recipient.display_avatar.url)
        await interaction.response.send_message(embed=embed)

    @gift.error
    async def gift_error(ctx, error):
        member: Member
        if isinstance(error, commands.BadArgument, ):
            embed = Embed(
            title=f"Gift error",
            description=f"**❌ Invalid arguments. Usage: `/gift @User item_name`**",
            color=Color.gold()
            )
            embed.set_thumbnail(url=ctx.author.display_avatar.url)
            await ctx.send(embed=embed)
        else:
            embed = Embed(
            title=f"Gift error",
            description=f"**❌ An error occurred while processing the gift.**",
            color=Color.gold()
            )
            embed.set_thumbnail(url=ctx.author.display_avatar.url)
            await ctx.send(embed=embed)

        user_id = str(member.id)
        user_data = get_user_data(user_id)

        if user_id in user_data:
            user_data[user_id] = {"xp": 0, "level": 1}
            await ctx.send(f"✅ {member.mention}'s XP has been reset.")
        else:
            await ctx.send(f"{member.mention} has no XP data to reset.")

        save_user_data(user_id, user_data)  # Save the data