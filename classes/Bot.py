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
from classes import Config, LightShotCog, ScraperBlackBoard, ScraperPastebin


class YadBot(discord.ext.commands.Bot):

    def __init__(
            self,
            config: Config,
            command_prefix,
            description: str
    ):
        super().__init__(command_prefix,
                         description=description)
        self.config = config
        self.token = self.config.token
        self.uptime = datetime.datetime.utcnow()

        self.scraper_black_board = None
        self.scraper_pastebin = None

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

        self.add_cog(LightShotCog.LightShotCog(self))

        self.scraper_black_board = ScraperBlackBoard.ScraperBlackBoard(self)
        self.scraper_pastebin = ScraperPastebin.ScraperPastebin(self)
        asyncio.create_task(self.scraper_black_board.timer())
        asyncio.create_task(self.scraper_pastebin.timer())

        # await self.enable_timers()

    async def on_command_error(self, context, exception):
        if (context.invoked_with == "ping") | (context.invoked_with == "pong"):
            return  # !ping and !pong are handled in on_message, as they have some special behaviour
        else:
            await super(YadBot, self).on_command_error(context, exception)

    async def enable_timers(self):
        if self.config.disable_timers == 0:
            print("(enable_timers) create timers")
            # asyncio.create_task(self.timer_website_check())
            print("(enable_timers) timers created")
        else:
            print("(enable_timers) not running timers, disabled in config file.")