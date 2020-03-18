import asyncio
import aiohttp
import discord
from discord.ext import commands
from bs4 import BeautifulSoup
import random
import string
import time

from classes import Config


class LightShotCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.allowed_servers = Config.Config.cog_lightshot_servers
        self.reaction_emojis = []
        self.reaction_emojis.append(discord.utils.get(self.bot.emojis, id=689849247914262768))  # entertainment emoji
        self.reaction_emojis.append(discord.utils.get(self.bot.emojis, id=689849247935496265))  # nsfw emoji
        self.reaction_emojis.append(discord.utils.get(self.bot.emojis, id=689849247821987872))  # money emoji
        self.reaction_emojis.append(discord.utils.get(self.bot.emojis, id=689849247851347984))  # account emoji
        self.reaction_emojis.append(discord.utils.get(self.bot.emojis, id=689849247847546911))  # address emoji
        self.reaction_emojis.append(discord.utils.get(self.bot.emojis, id=689849495617405049))  # trash emoji

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, context):
        if context.user_id != self.bot.config.bot_id:
            if context.channel_id == 689541755560787996:  # spam channel in EiS
                if context.event_type == "REACTION_ADD":
                    spam_channel = self.bot.get_channel(id=689541755560787996)
                    if spam_channel is not None:
                        original_message = await spam_channel.fetch_message(context.message_id)
                        if original_message is not None:
                            if context.emoji.name == "trash":
                                await original_message.delete()
                            else:
                                await original_message.clear_reactions()
                                target_channel = None
                                if context.emoji.name == "entertainment":
                                    target_channel = self.bot.get_channel(id=689584388044095545)
                                elif context.emoji.name == "nsfw":
                                    target_channel = self.bot.get_channel(id=689584357194858515)
                                elif context.emoji.name == "money":
                                    target_channel = self.bot.get_channel(id=689583106549743769)
                                elif context.emoji.name == "account":
                                    target_channel = self.bot.get_channel(id=689585329006444656)
                                elif context.emoji.name == "address":
                                    target_channel = self.bot.get_channel(id=689591788708560966)
                                if target_channel is not None:
                                    await target_channel.send(original_message.content)

    @commands.command()
    async def image(self, context, amount=1, delay_in_seconds=1):
        """Get random image from LightShot"""
        if isinstance(context.message.channel, discord.abc.GuildChannel) and context.message.channel.guild.id in self.allowed_servers:
            if amount <= 500 and delay_in_seconds >= 1:
                for i in range(amount):
                    botMessage = await context.channel.send("Getting a new image for you...")

                    validImageFound = False

                    while not validImageFound:

                        fileName = await self.generate_image_id(6)
                        url = await self.generate_image_link(fileName)

                        async with aiohttp.ClientSession(headers=Config.Config.client_headers) as cs:
                            async with cs.get(url) as response:
                                website = await response.read()

                        # parse the downloaded homepage
                        soup = BeautifulSoup(website.decode('utf-8'), "lxml")

                        imgElement = soup.find('img', id='screenshot-image')

                        if imgElement is not None:
                            imgUrl = soup.find('img', id='screenshot-image')['src']
                            if '0_173a7b_211be8ff' not in imgUrl and imgUrl is not None:
                                validImageFound = True
                                await botMessage.edit(content=imgUrl)
                                for emoji in self.reaction_emojis:
                                    await botMessage.add_reaction(emoji)
                            else:
                                await botMessage.edit(content="The image was invalid or got removed, getting other image...")
                        else:
                            await botMessage.edit(content="Got redirected, getting other image...")
                    time.sleep(delay_in_seconds)
            else:
                await context.channel.send("You can request maximum 500 pictures and set a minimum delay of one second!")
        else:
            await context.channel.send("This command is not whitelisted here.")

    # - Generates random string
    async def generate_image_id(self, size):
        return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(size))

    # - Generates lightshot link using generateId() function
    async def generate_image_link(self, file_name):
        return "https://prnt.sc/" + file_name