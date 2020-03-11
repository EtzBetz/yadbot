import discord
import time
import datetime
import os
import asyncio
import aiohttp
from pprint import pprint
from random import randint
from bs4 import BeautifulSoup

from discord.ext import commands

from classes import Config


class YadBot(discord.ext.commands.Bot):

    def __init__(self,
                 config: Config,
                 command_prefix,
                 description: str):
        super().__init__(command_prefix,
                         description=description)
        self.config = config
        self.token = self.config.token
        self.uptime = datetime.datetime.utcnow()

        self.website_text = ""

    async def on_command(self, ctx):
        pass
        # bot.commands_used[ctx.command.name] += 1
        # ctx.logger.info(f"<{ctx.command}> {ctx.message.clean_content}")

    async def on_ready(self):
        print("I'm online! Setting presence...")
        game = discord.Game(name=f"Version {self.config.version_number}")
        await self.change_presence(status=discord.Status.online, activity=game)

        print(f"I see {len(self.guilds)} guilds and {len(self.users)} members:")
        for guild in self.guilds:
            print(f"  - {guild.name} ({guild.id})")
        print("---------------------------------------------------------")

        await self.enable_timers()

    async def on_command_error(self, context, exception):
        if (context.invoked_with == "ping") | (context.invoked_with == "pong"):
            return  # !ping and !pong are handled in on_message, as they have some special behaviour
        else:
            await super(YadBot, self).on_command_error(context, exception)

    async def check_website_timer(self):
        await self.check_website()
        await asyncio.sleep(self.config.website_check_interval_seconds)
        asyncio.create_task(self.check_website())

    async def check_website(self):

        # download the website
        async with aiohttp.ClientSession() as cs:
            async with cs.get(self.config.website_check_url) as response:
                text = await response.read()

        # parse the downloaded homepage
        soup = BeautifulSoup(text.decode('utf-8'), "lxml")

        posting_text = soup.find(id='content')
        if self.website_text != posting_text.get_text():
            if not self.website_text == "":
                self.website_text = posting_text.get_text()
                await self.send_website_changes_message(self.website_text)
            else:
                self.website_text = posting_text.get_text()


    async def enable_timers(self):
        if self.config.disable_timers == 0:
            print("(enable_timers) create timers")
            asyncio.create_task(self.check_website_timer())
            print("(enable_timers) timers created")
        else:
            print("(enable_timers) not running timers, disabled in config file.")

    async def send_website_changes_message(self, message_text):
        admin_id = self.config.admin_id

        print("(send_website_changes_message)")

        admin_user = discord.utils.get(self.users, id=admin_id)

        await admin_user.send(embed=await self.get_message_change_embed(message_text))

    async def get_message_change_embed(self, message_text):

        embed = discord.Embed(
            title="Änderungen auf dem schwarzen Brett!",
            description=message_text,
            color=0xFFFF00
        )
        embed.set_footer(text="Alle Angaben ohne Gewähr!")

        return embed
