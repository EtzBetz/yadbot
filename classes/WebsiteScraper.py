import aiohttp
import asyncio
from bs4 import BeautifulSoup
import discord


class WebsiteScraper:

    def __init__(self, bot):
        self.timer_enabled = False
        self.bot = bot
        self.url = "https://google.com"
        self.user_agent = self.bot.config.default_scraper_user_agent
        self.scraping_interval_seconds = self.bot.config.default_scraper_check_interval
        self.servers = [

        ]
        self.direct_message_user_ids = [

        ]
        self.website_data = {

        }

    async def set_is_enabled(self, state):
        self.timer_enabled = state
        if self.enabled:
            await self.timer()

    async def timer(self):
        if self.timer_enabled:
            await self.timer_occurrence_handler()
            await asyncio.sleep(self.scraping_interval_seconds)
            asyncio.create_task(self.timer())

    async def timer_occurrence_handler(self):
        website_soup = await self.request_website()
        await self.parse_website_content(website_soup)

    async def request_website(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(self.url) as response:
                website_content = await response.read()

        return BeautifulSoup(website_content.decode('utf-8'), "lxml")

    async def parse_website_content(self, website_soup):
        pass

    async def send_embed_messages(self):
        embed = await self.get_embed()
        for guild_data in self.bot.config.scraper_black_board_servers:
            guild = discord.utils.get(self.bot.guilds, id=guild_data["server_id"])
            channel = discord.utils.get(guild.channels, id=guild_data["channel_id"])
            await channel.send(embed=embed)
        for user_id in self.bot.config.scraper_black_board_dm_users:
            user = discord.utils.get(self.bot.users, id=user_id)
            await user.send(embed=embed)

    async def get_embed(self):
        return discord.Embed(
            title="Preview Embed",
            color=0xeb6734,
            url=self.url
        )