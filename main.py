from classes import Bot, Config, DBConnect


# bot = Bot.Bot(


async def setup():
    self.db_connection = await DBConnect.DBConnect()