from discord import utils
from discord.ext import commands
from services.bad_words import offensive_words
from services.db import get_user_data, save_user_data, chat_collection
from collections import defaultdict
import random
import asyncio

# ----------------------------
# /!\ this should be refactored into appropriate modules
# ----------------------------
class OnMessage(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.chat_history = {}  # Chat History Storage: Dictionary to store chat history for each channel
        self.PENALTY_THRESHOLD = 5 # Penalty system (e.g., lose 50 coins or XP after 5 offenses)
        self.PENALTY_AMOUNT = 500  # Amount of coins or XP to be deducted
        self.user_offenses = defaultdict(int)# Store user offenses count

    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignore bot messages
        if message.author.bot:
            return
        member = message.author
        guild = message.guild
        user_data = get_user_data(str(member.id))

        # implement the chat history feature
        channel_id = message.channel.id

        print(f"Channel ID: {channel_id}")

        if channel_id not in self.chat_history:
            # chat_history[channel_id] = []
            # save more information about the message
            self.chat_history[channel_id] = [{"author_id":message.author.id, "author_name": message.author.display_name, "content": message.content, "timestamp": message.created_at}]
            # save the chat history to the database
            self.save_chat_history(channel_id, self.chat_history[channel_id])

        # Store the last 10 messages (adjust as needed)
        self.chat_history[channel_id].append(f"{message.author.display_name}: {message.content}")

        if len(self.chat_history[channel_id]) > 10:
            self.chat_history[channel_id].pop(0)  # Remove the oldest message
        # implement the chat history feature end

        if user_data["level"] in range(1, 3):
            role = utils.get(guild.roles, name="Intermediate")
            #only assign role if the user doesn't have it
            if role not in member.roles:
                await member.add_roles(role)

                #award XP to the user
                xp_earned = random.randint(5, 1000)
                self.award_xp(str(member.id), xp_earned)

                #send this message to the channel
                await message.channel.send(f"🎉🎉🎉 **Role UP** \n{member.mention} has been awarded the **{role.name}** role and has been awarded **{xp_earned}**XPs!")

        elif user_data["level"] in range(4, 9):
            role = utils.get(guild.roles, name="Novice")
            #only assign role if the user doesn't have it
            if role not in member.roles:
                await member.add_roles(role)

                #award XP to the user
                xp_earned = random.randint(5, 1000)
                self.award_xp(str(member.id), xp_earned)

                #send this message to the channel
                await message.channel.send(f"🎉🎉🎉 **Role UP** \n{member.mention} has been awarded the **{role.name}** role and has been awarded **{xp_earned}**XPs!")

        elif user_data["level"] in range(11, 16):
            role = utils.get(guild.roles, name="Techie")
            #only assign role if the user doesn't have it
            if role not in member.roles:
                await member.add_roles(role)

                #award XP to the user
                xp_earned = random.randint(5, 1000)
                self.award_xp(str(member.id), xp_earned)

                #send this message to the channel
                await message.channel.send(f"🎉🎉🎉 **Role UP** \n{member.mention} has been awarded the **{role.name}** role and has been awarded **{xp_earned}**XPs!")

        elif user_data["level"] in range(17, 23):
            role = utils.get(guild.roles, name="Geek")
            print(f"User {member.name} is at level {user_data['level']}")
            #only assign role if the user doesn't have it
            if role not in member.roles:
                await member.add_roles(role)

                #award XP to the user
                xp_earned = random.randint(5, 1000)
                self.award_xp(str(member.id), xp_earned)

                #send this message to the channel
                await message.channel.send(f"🎉🎉🎉 **Role UP** \n{member.mention} has been awarded the **{role.name}** role and has been awarded **{xp_earned}**XPs!")

        elif user_data["level"] in range(24, 30):
            role = utils.get(guild.roles, name="Hacker")
            #only assign role if the user doesn't have it
            if role not in member.roles:
                await member.add_roles(role)

                #award XP to the user
                xp_earned = random.randint(5, 1000)
                self.award_xp(str(member.id), xp_earned)

                #send this message to the channel
                await message.channel.send(f"🎉🎉🎉 **Role UP** \n{member.mention} has been awarded the **{role.name}** role and has been awarded **{xp_earned}**XPs !")

        elif user_data["level"] in range(31, 37):
            role = utils.get(guild.roles, name="Guru")
            
            #only assign role if the user doesn't have it
            if role not in member.roles:
                await member.add_roles(role)
                
                #award XP to the user
                xp_earned = random.randint(5, 1000)
                self.award_xp(str(member.id), xp_earned)

                #send this message to the channel
                await message.channel.send(f"🎉🎉🎉 **Role UP** \n{member.mention} has been awarded the **{role.name}** role and has been awarded **{xp_earned}**XPs!")

        elif user_data["level"] in range(43, 49):
            role = utils.get(guild.roles, name="Godlike")
            #only assign role if the user doesn't have it
            if role not in member.roles:
                await member.add_roles(role)

                #award XP to the user
                xp_earned = random.randint(5, 1000)
                self.award_xp(str(member.id), xp_earned)

                #send this message to the channel
                await message.channel.send(f"🎉🎉🎉 **Role UP** \n{member.mention} has been awarded the **{role.name}** role and has been awarded **{xp_earned}**XPs!")

        elif user_data["level"] in range(55, 61):
            role = utils.get(guild.roles, name="Wizard")
            #only assign role if the user doesn't have it
            if role not in member.roles:
                await member.add_roles(role)
                
                #award XP to the user
                xp_earned = random.randint(5, 1000)
                self.award_xp(str(member.id), xp_earned)

                #send this message to the channel
                await message.channel.send(f"🎉🎉🎉 **Role UP** \n{member.mention} has been awarded the **{role.name}** role and has been awarded **{xp_earned}**XPs!")

            #rename the user's name to include the special badge 

        for word in offensive_words:
            if word in [message for message in message.content.split(" ")]:
                await message.delete()
                await message.channel.send(
                    f"🛑 {message.author.mention}: ||{message.content}||"
                )
                # Increase the offense count
                self.user_offenses[message.author.id] += 1
                
                if self.user_offenses[message.author.id] >= self.PENALTY_THRESHOLD:
                    await self.apply_penalty(message.author)
                    await message.channel.send(f"🚨 {message.author.mention}  ***has been penalized `{self.PENALTY_AMOUNT}` XPs for using offensive words too many times!!.***")
                    # Reset the offense count after penalty
                    self.user_offenses[message.author.id] = 0

        user_id = str(message.author.id)
        user_data = get_user_data(user_id)

        xp_needed = self.get_xp_needed(user_data["level"])
        # Award random XP between 5 and 10
        xp_earned = random.randint(5, 100)
        print(f"User {message.author.name} earned {xp_earned} XP!\n\n")
        self.award_xp(user_id, xp_earned)

        await self.bot.process_commands(message)  # Ensure other commands can still run

    def save_chat_history(self, channel_id, chat_data):
        chat_collection.update_one(
            {"channel_id": channel_id},
            {"$set": {"chat_data": chat_data}},
            upsert=True
        )
        print(f"Chat history for channel {channel_id} saved: {chat_data}\n\n")

    def award_xp(self, user_id, xp):
        user_data = get_user_data(user_id)
        user_data["xp"] += xp

        # Level up if XP exceeds the threshold
        while user_data["xp"] >= self.get_xp_needed(user_data["level"]):
            user_data["level"] += 1
        
        print(f"User {user_id} leveled up to {user_data['level']}!, with {user_data['xp']} XPs. \n\n")

        save_user_data(user_id, user_data)
        return user_data
    

    async def random_xp_drop(self):
        while True:
            await asyncio.sleep(random.randint(3600, 7200))  # 1-2 hours
            channel = self.bot.get_channel("998348764282634242") 
            reward = random.randint(50, 1500)
            lucky_user = random.choice(channel.members)
            user_data = get_user_data(str(lucky_user.id))
            user_data["xp"] += reward
            save_user_data(str(lucky_user.id), user_data)
            await channel.send(f"🎉 Surprise! {lucky_user.mention} just earned {reward} XP!")

    # Function to deduct XP
    async def apply_penalty(self, user):
        user_id = str(user.id)
        user_data = get_user_data(user_id)  # Fetch user data from database

        if not user_data:
            return

        # Deduct the penalty amount
        user_data["xp"] -= self.PENALTY_AMOUNT # Deduct XP
        save_user_data(user_id, user_data)  # Save the updated user data

        # Notify the user about the penalty
        await user.send(f"🚨 ***You have used offensive words too many times. You have been penalized `{self.PENALTY_AMOUNT}` XP!***")