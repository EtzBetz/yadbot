import asyncio
import aiohttp
import discord
from discord.ext import commands
from bs4 import BeautifulSoup
import random
import string

from classes import Config


class LightShotCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.allowed_servers = Config.Config.cog_lightshot_servers

    @commands.Cog.listener()
    async def on_member_join(self, member):
        pass

    @commands.command()
    async def image(self, context, amount=1):
        """Get random image from LightShot"""
        if isinstance(context.message.channel, discord.abc.GuildChannel) and context.message.channel.guild.id in self.allowed_servers:
            for i in range(amount):
                botMessage = await context.channel.send("Getting an image for you...")

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
                            await botMessage.edit(content="Got an invalid image.")
                    else:
                        validImageFound = True
                        await botMessage.edit(content="Probably User-Agent was wrong or image wasn't found.")

        else:
            await context.channel.send("Command is not whitelisted here.")

    # - Generates random string
    async def generate_image_id(self, size):
        return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(size))

    # - Generates lightshot link using generateId() function
    async def generate_image_link(self, file_name):
        return "https://prnt.sc/" + file_name