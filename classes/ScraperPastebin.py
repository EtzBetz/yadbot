from classes import WebsiteScraper
import discord


class ScraperPastebin(WebsiteScraper.WebsiteScraper):

    def __init__(self, bot):
        super().__init__(bot)
        self.timer_enabled = True
        self.bot = bot
        self.url = self.bot.config.scraper_pastebin_url
        self.user_agent = self.bot.config.default_scraper_user_agent
        self.scraping_interval_seconds = self.bot.config.scraper_pastebin_check_interval
        self.direct_message_user_ids = self.bot.config.scraper_pastebin_dm_users
        self.servers = self.bot.config.scraper_pastebin_servers
        self.website_data = {
            "previous_pastes": [],
            "current_pastes": []
        }

    async def parse_website_content(self, website_soup):
        table = website_soup.find("table", class_='maintable')
        table_rows = table.findChildren("tr")

        # for row in table_rows:
        #     print("debug1: " + row.name)
        #     if row.find("th") is not None:
        #         print("debug2: found the first row, skipping")

        self.website_data['previous_pastes'] = self.website_data['current_pastes']
        self.website_data['current_pastes'] = []
        print("--------------")
        for row in reversed(table_rows):
            if row.find("th") is not None:
                pass
            else:
                element = row.td.a
                data = {
                    'title': element.decode_contents(),
                    'link': element['href']
                }
                self.website_data['current_pastes'].append(data)

        if len(self.website_data['previous_pastes']) != 0:
            newest_previous_paste = self.website_data['previous_pastes'][len(self.website_data['previous_pastes'])-1]
            newest_previous_paste_appearance_index = None
            try:
                newest_previous_paste_appearance_index = self.website_data['current_pastes'].index(newest_previous_paste)  # index of the newest paste in previous pastes in current pastes
            except ValueError:
                pass

            if newest_previous_paste_appearance_index is not None:
                while newest_previous_paste_appearance_index != -1:
                    self.website_data['current_pastes'].pop(0)
                    newest_previous_paste_appearance_index -= 1

        for row in self.website_data['current_pastes']:
            print(row['title'] + ": " + row['link'])
        await self.send_embed_messages()

    async def get_embed(self):

        embed = discord.Embed(
            title="New Pastes",
            url=self.url
        )

        for row in self.website_data['current_pastes']:

            paste_text = await self.get_paste_text("https://pastebin.com" + row['link'])
            embed.add_field(name="https://pastebin.com" + row['link'] + " (" + row['title'] + ")", value="```text\n" + paste_text[0:50] + "...\n```", inline=False)

        # embed.set_footer(text="Bug gefunden? Melde dich bei @EtzBetz#0001.")

        return embed

    async def get_paste_text(self, link):
        soup = await self.request_website(link)

        return soup.find(id="paste_code").get_text()

