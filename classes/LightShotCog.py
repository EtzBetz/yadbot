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
        self.reaction_emojis.append(discord.utils.get(self.bot.emojis, id=self.bot.config.cog_lightshot_emojis["entertainment_emoji_id"]))  # entertainment emoji
        self.reaction_emojis.append(discord.utils.get(self.bot.emojis, id=self.bot.config.cog_lightshot_emojis["nsfw_emoji_id"]))           # nsfw emoji
        self.reaction_emojis.append(discord.utils.get(self.bot.emojis, id=self.bot.config.cog_lightshot_emojis["money_emoji_id"]))          # money emoji
        self.reaction_emojis.append(discord.utils.get(self.bot.emojis, id=self.bot.config.cog_lightshot_emojis["account_emoji_id"]))        # account emoji
        self.reaction_emojis.append(discord.utils.get(self.bot.emojis, id=self.bot.config.cog_lightshot_emojis["address_emoji_id"]))        # address emoji
        self.reaction_emojis.append(discord.utils.get(self.bot.emojis, id=self.bot.config.cog_lightshot_emojis["trash_emoji_id"]))          # trash emoji
        # self.reaction_emojis.append(discord.utils.get(self.bot.emojis, id=689849247914262768))  # entertainment emoji
        # self.reaction_emojis.append(discord.utils.get(self.bot.emojis, id=689849247935496265))  # nsfw emoji
        # self.reaction_emojis.append(discord.utils.get(self.bot.emojis, id=689849247821987872))  # money emoji
        # self.reaction_emojis.append(discord.utils.get(self.bot.emojis, id=689849247851347984))  # account emoji
        # self.reaction_emojis.append(discord.utils.get(self.bot.emojis, id=689849247847546911))  # address emoji
        # self.reaction_emojis.append(discord.utils.get(self.bot.emojis, id=689849495617405049))  # trash emoji
        self.ordered_links_history = []

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, context):
        if context.user_id != self.bot.config.bot_id:
            server_data = await self.get_data_for_server_if_allowed(context.guild_id)
            if server_data is not None:
                if context.event_type == "REACTION_ADD":
                    original_channel = self.bot.get_channel(id=context.channel_id)
                    if original_channel is not None:
                        original_message = None
                        try:
                            original_message = await original_channel.fetch_message(context.message_id)
                        except discord.NotFound:
                            pass
                        if original_message is not None:
                            if context.emoji.id == self.bot.config.cog_lightshot_emojis["trash_emoji_id"]:
                                try:
                                    await original_message.delete()
                                except discord.NotFound:
                                    pass
                            else:
                                await original_message.clear_reactions()
                                target_channel = None
                                if context.emoji.name == "entertainment":
                                    target_channel = self.bot.get_channel(id=server_data["entertainment_channel_id"])
                                elif context.emoji.name == "nsfw":
                                    target_channel = self.bot.get_channel(id=server_data["nsfw_channel_id"])
                                elif context.emoji.name == "money":
                                    target_channel = self.bot.get_channel(id=server_data["money_channel_id"])
                                elif context.emoji.name == "account":
                                    target_channel = self.bot.get_channel(id=server_data["account_channel_id"])
                                elif context.emoji.name == "address":
                                    target_channel = self.bot.get_channel(id=server_data["address_channel_id"])
                                if target_channel is not None:
                                    is_link_ordered_already = await self.history_handler(original_message.content)
                                    if not is_link_ordered_already:
                                        await target_channel.send(original_message.content)

    async def history_handler(self, link):
        if link in self.ordered_links_history:
            return True
        else:
            await self.add_link_to_history_remove_old(link)
            return False

    async def add_link_to_history_remove_old(self, link):
        self.ordered_links_history.append(link)
        while len(self.ordered_links_history) > 100:
            self.ordered_links_history.pop(0)

    async def get_data_for_server_if_allowed(self, server_id):
        for server_data in self.allowed_servers:
            if server_id == server_data['server_id']:
                return server_data
        return None

    @commands.command()
    async def image(self, context, amount=1, delay_in_seconds=1):
        """Get random image from LightShot"""
        if isinstance(context.message.channel, discord.abc.GuildChannel):
            is_allowed_server = False
            for server in self.allowed_servers:
                if context.message.channel.guild.id == server['server_id']:
                    is_allowed_server = True
                    break
            if is_allowed_server:
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