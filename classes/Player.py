import discord
from classes import Bot, DBConnect
from pprint import pprint


class Player:
    id = None
    name = None
    discord_user_id = None
    discord_user_object = None
    description = None
    active = None

    def __init__(self, id=None, name=None, discord_user_id=None, discord_user_object=None, description=None) -> None:
        super().__init__()
        if id is None and name is None and discord_user_id is None and discord_user_object is None:
            raise ValueError("One unique attribute needs to be given to create a player object.")
        self.id = id
        self.name = name
        self.discord_user_id = discord_user_id
        self.discord_user_object = discord_user_object
        self.description = description

        # await self.fill_object_from_db() # TODO: find a way to do this. async objects?

    async def fill_object_from_db(self):
        db_connection = await DBConnect.DBConnect.getInstance()
        data = None
        if self.id is not None:
            data = await db_connection.getPlayerData(id=self.id)
        elif self.name is not None:
            data = await db_connection.getPlayerData(name=self.name)
        elif self.discord_user_id is not None:
            data = await db_connection.getPlayerData(discord_user_id=self.discord_user_id)
        elif self.discord_user_object is not None:
            data = await db_connection.getPlayerData(discord_user_id=self.discord_user_object.id)

        self.id = data[0]['id']
        self.name = data[0]['name']
        self.discord_user_id = data[0]['discord_user_id']
        self.discord_user_object = Bot.Bot.bot.get_user(self.discord_user_id)
        self.active = data[0]['active']