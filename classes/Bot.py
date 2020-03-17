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
from classes import Config, LightShotCog


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

        self.add_cog(LightShotCog.LightShotCog(self))

        await self.enable_timers()

    async def on_command_error(self, context, exception):
        if (context.invoked_with == "ping") | (context.invoked_with == "pong"):
            return  # !ping and !pong are handled in on_message, as they have some special behaviour
        else:
            await super(YadBot, self).on_command_error(context, exception)

    async def timer_website_check(self):
        await self.website_check()
        await asyncio.sleep(self.config.website_check_interval_seconds)
        asyncio.create_task(self.timer_website_check())

    async def website_check(self):
        print("running website check task")
        # download the website
        async with aiohttp.ClientSession() as cs:
            async with cs.get(self.config.website_check_url) as response:
                text = await response.read()

        # parse the downloaded homepage
        soup = BeautifulSoup(text.decode('utf-8'), "lxml")

        posting_container = soup.find(id='content')
        posting_text = posting_container.div.div
        if self.website_text != posting_text.get_text():
            if not self.website_text == "":
                await self.send_website_changes_message(self.website_text)
            self.website_text = posting_text.get_text()


    async def enable_timers(self):
        if self.config.disable_timers == 0:
            print("(enable_timers) create timers")
            asyncio.create_task(self.timer_website_check())
            print("(enable_timers) timers created")
        else:
            print("(enable_timers) not running timers, disabled in config file.")

    async def send_website_changes_message(self, message_text):
        admin_id = self.config.admin_id

        print("(send_website_changes_message)")

        admin_user = discord.utils.get(self.users, id=admin_id)

        await admin_user.send(embed=await self.get_message_change_embed(message_text))

    async def parse_message_text(self, message_text):
        parsed_texts = []
        message_text = message_text[1:]
        is_text_fully_parsed = False
        while not is_text_fully_parsed:
            divider_start_index = message_text.find("====")
            if divider_start_index == -1:
                if not len(message_text) == 0:
                    parsed_texts.append(message_text)
                is_text_fully_parsed = True
            else:
                if not divider_start_index == 0:
                    parsed_texts.append(message_text[:divider_start_index-1])  # TODO: probably -2 to also cut linebreak, test
                    # print("message: \n" + message_text[:divider_start_index-1])
                divider_end_index = divider_start_index + 3
                divider_end_index_found = False
                while not divider_end_index_found:
                    if message_text[divider_end_index + 1] == "=":
                        divider_end_index += 1
                    else:
                        divider_end_index_found = True
                message_text = message_text[divider_end_index+2:]  # TODO: probably +2 to also cut last character and linebreak, test
        return parsed_texts



    async def get_message_change_embed(self, message_text):
        parsed_texts = await self.parse_message_text(message_text)

        embed = discord.Embed(
            title="Änderungen auf dem Schwarzen Brett!",
            color=0x0096d1,
            url=self.config.website_check_url
        )
        embed.set_footer(text="Alle Angaben ohne Gewähr!  |  Bug gefunden? Melde dich bei @EtzBetz#0001.")

        for i, parsed_text in enumerate(parsed_texts):
            embed.add_field(name=str(i+1) + ". Eintrag", value=parsed_text, inline=False)

        return embed
