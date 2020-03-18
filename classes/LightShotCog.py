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

    @commands.Cog.listener()
    async def on_member_join(self, member):
        pass

    @commands.command()
    async def image(self, context, amount=1, delay=0):
        """Get random image from LightShot"""
        if isinstance(context.message.channel, discord.abc.GuildChannel) and context.message.channel.guild.id in self.allowed_servers:
            if amount <= 500:
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
                            else:
                                await botMessage.edit(content="The image was invalid or got removed, getting other image...")
                        else:
                            await botMessage.edit(content="Got redirected, getting other image...")
                    time.sleep(delay)
            else:
                await context.channel.send("You can request max. 500 pictures!")
        else:
            await context.channel.send("This command is not whitelisted here.")

    # - Generates random string
    async def generate_image_id(self, size):
        return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(size))

    # - Generates lightshot link using generateId() function
    async def generate_image_link(self, file_name):
        return "https://prnt.sc/" + file_name