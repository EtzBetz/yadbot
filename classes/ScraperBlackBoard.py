from classes import WebsiteScraper
import discord


class ScraperBlackBoard(WebsiteScraper.WebsiteScraper):

    def __init__(self, bot):
        super().__init__(bot)
        self.timer_enabled = True
        self.bot = bot
        self.url = self.bot.config.scraper_black_board_url
        self.user_agent = self.bot.config.default_scraper_user_agent
        self.scraping_interval_seconds = self.bot.config.default_scraper_check_interval
        self.direct_message_user_ids = self.bot.config.scraper_black_board_dm_users
        self.servers = self.bot.config.scraper_black_board_servers
        self.website_data = {
            "previous_text": "",
            "current_text": ""
        }

    async def parse_website_content(self, website_soup):
        posting_container = website_soup.find(id='content')
        posting_text = posting_container.div.div
        self.website_data['previous_text'] = self.website_data['current_text']
        self.website_data['current_text'] = posting_text.get_text()
        if self.website_data['previous_text'] != self.website_data['current_text'] and self.website_data['previous_text'] != "":
            await self.send_embed_messages()

    async def get_embed(self):
        parsed_texts = await self.parse_message_text(self.website_data['current_text'])

        embed = discord.Embed(
            title="Änderungen auf dem Schwarzen Brett!",
            color=0x0096d1,
            url=self.url
        )
        embed.set_footer(text="Alle Angaben ohne Gewähr!  |  Bug gefunden? Melde dich bei @EtzBetz#0001.")

        for i, parsed_text in enumerate(parsed_texts):
            embed.add_field(name=str(i + 1) + ". Eintrag", value=parsed_text, inline=False)

        return embed

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
                    parsed_texts.append(message_text[:divider_start_index-1])
                    # print("message: \n" + message_text[:divider_start_index-1])
                divider_end_index = divider_start_index + 3
                divider_end_index_found = False
                while not divider_end_index_found:
                    if message_text[divider_end_index + 1] == "=":
                        divider_end_index += 1
                    else:
                        divider_end_index_found = True
                message_text = message_text[divider_end_index+2:]
        return parsed_texts