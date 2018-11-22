import asyncpg
from classes import Config
from pprint import pprint


class DBConnect:

    # Here will the instance be stored.
    __instance = None
    connection = None

    @staticmethod
    async def getInstance():
        """ Static access method. """
        if DBConnect.__instance is None:
            DBConnect()
        return DBConnect.__instance

    def __init__(self):
        """ Virtually private constructor. """
        if DBConnect.__instance is not None:
            raise Exception("This class is a singleton!")
        else:
            DBConnect.__instance = self

    async def setUp(self):
        """ Connects to the PostgreSQL Database. """
        self.connection = await asyncpg.create_pool(**Config.Config.db_credentials)
        self.__instance = self

    async def insertPlayerData(self, name: str, discord_user_id: int = None, description: str = ""):
        """Inserts a new Member into the user table."""
        query = "INSERT INTO public.player(name, discord_user_id, description) VALUES ('" + name + "', " + str(discord_user_id) + ", '" + description + "') RETURNING id"
        row = await self.connection.fetchval(query)
        return str(row)

    async def insertGuiltyUser(self, year: str, week: str, owner_user_id: int, guilty_user_id: int):
        query = "INSERT INTO public.guilty_user(year, week, owner_user_id, guilty_user_id) VALUES (" + year + ", " + week + ", " + str(owner_user_id) + ", " + str(guilty_user_id) + ") RETURNING id"
        row = await self.connection.fetchval(query)
        return str(row)

    async def insertGuiltyReason(self, year: str, week: str, owner_user_id: int, reason: str):
        query = "INSERT INTO public.guilty_reason(year, week, owner_user_id, reason) VALUES (" + year + ", " + week + ", " + str(owner_user_id) + ", '" + reason + "') RETURNING id"
        row = (await self.connection.fetchval(query))
        return row

    async def insertFinalizedWeek(self, year: str, week: str):
        query = "INSERT INTO public.week_finalized(year, week, finalized) VALUES (" + year + ", " + week + ", TRUE) RETURNING id"
        row = await self.connection.fetchval(query)
        return str(row)


    async def getAWeeksGuiltyUsersFromUser(self, year: str, week: str, owner_user_id: int):
        query = "SELECT guilty_user.id, guilty_user.guilty_user_id, guilty_user.rejected, guilty_user.accepted FROM public.guilty_user WHERE guilty_user.owner_user_id = " + str(owner_user_id) + " AND guilty_user.year = " + year + " AND guilty_user.week = " + week + " ORDER BY guilty_user.id ASC"
        data = await self.connection.fetch(query)
        return data

    async def getAWeeksGuiltyReasonsFromUser(self, year: str, week: str, owner_user_id: int):
        query = "SELECT guilty_reason.id, guilty_reason.reason, guilty_reason.rejected, guilty_reason.accepted FROM public.guilty_reason WHERE guilty_reason.owner_user_id = " + str(owner_user_id) + " AND guilty_reason.year = " + year + " AND guilty_reason.week = " + week + " ORDER BY guilty_reason.id ASC"
        data = await self.connection.fetch(query)
        return data

    async def getAWeeksGuiltyUsers(self, year: str, week: str):
        query = "SELECT guilty_user.id, guilty_user.guilty_user_id, guilty_user.rejected, guilty_user.accepted, guilty_user.owner_user_id FROM public.guilty_user WHERE guilty_user.year = " + year + " AND guilty_user.week = " + week + " ORDER BY guilty_user.id ASC"
        data = await self.connection.fetch(query)
        return data

    async def getAWeeksGuiltyReasons(self, year: str, week: str):
        query = "SELECT guilty_reason.id, guilty_reason.reason, guilty_reason.rejected, guilty_reason.accepted, guilty_reason.owner_user_id FROM public.guilty_reason WHERE guilty_reason.year = " + year + " AND guilty_reason.week = " + week + " ORDER BY guilty_reason.id ASC"
        data = await self.connection.fetch(query)
        return data

    async def getAWeeksConfirmedGuiltyUsers(self, year: str, week: str):
        query = "SELECT guilty_user.id, guilty_user.guilty_user_id, guilty_user.rejected, guilty_user.accepted, guilty_user.owner_user_id FROM public.guilty_user WHERE guilty_user.year = " + year + " AND guilty_user.week = " + week + " AND guilty_user.accepted IS TRUE ORDER BY guilty_user.id ASC"
        data = await self.connection.fetch(query)
        return data

    async def getAWeeksConfirmedGuiltyReason(self, year: str, week: str):
        query = "SELECT guilty_reason.id, guilty_reason.reason, guilty_reason.rejected, guilty_reason.accepted, guilty_reason.owner_user_id FROM public.guilty_reason WHERE guilty_reason.year = " + year + " AND guilty_reason.week = " + week + " AND guilty_reason.accepted IS TRUE ORDER BY guilty_reason.id ASC"
        data = await self.connection.fetch(query)
        return data

    async def getAllPlayersIds(self, only_active=False):
        if only_active is True:
            query = "SELECT player.id FROM public.player WHERE player.active = TRUE ORDER BY player.id ASC"
        else:
            query = "SELECT player.id FROM public.player ORDER BY player.id ASC"
        if query is not None:
            data = await self.connection.fetch(query)
            if data is not None and len(data) > 0:
                return data
            else:
                return False

    async def getPlayerData(self, id=None, name: str = None, discord_user_id: int = None, description: str = None):
        query = None
        if id is not None:
            query = "SELECT player.id, player.name, player.discord_user_id, player.description, player.active FROM public.player WHERE player.id = " + str(id) + " ORDER BY player.id ASC"
        elif discord_user_id is not None:
            query = "SELECT player.id, player.name, player.discord_user_id, player.description, player.active FROM public.player WHERE player.discord_user_id = " + str(discord_user_id) + " ORDER BY player.id ASC"
        elif name is not None:
            query = "SELECT player.id, player.name, player.discord_user_id, player.description, player.active FROM public.player WHERE LOWER(player.name) LIKE LOWER('%" + name + "%') ORDER BY player.id ASC"
        elif description is not None:
            query = "SELECT player.id, player.name, player.discord_user_id, player.description, player.active FROM public.player WHERE LOWER(player.description) LIKE LOWER('%" + description + "%') ORDER BY player.id ASC"
        if query is not None:
            data = await self.connection.fetch(query)
            if data is not None and len(data) > 0:
                return data
            else:
                return False


    async def alterConfirmationToTrueForUserInWeek(self, year: str, week: str, guilty_user_id: int):
        await self.alterRejectionToFalseForUserInWeek(year, week, guilty_user_id)  # This is done to have the entered user either confirmed or rejected, but not both.
        query = "UPDATE public.guilty_user SET accepted = TRUE WHERE guilty_user.guilty_user_id = " + str(guilty_user_id) + " AND guilty_user.year = '" + year + "' AND guilty_user.week = '" + week + "'"
        data = await self.connection.execute(query)
        return data

    async def alterConfirmationToFalseForUserInWeek(self, year: str, week: str, guilty_user_id: int):
        query = "UPDATE public.guilty_user SET accepted = FALSE WHERE guilty_user.guilty_user_id = " + str(guilty_user_id) + " AND guilty_user.year = '" + year + "' AND guilty_user.week = '" + week + "'"
        data = await self.connection.execute(query)
        return data

    async def alterRejectionToTrueForUserInWeek(self, year: str, week: str, guilty_user_id: int):
        await self.alterConfirmationToFalseForUserInWeek(year, week, guilty_user_id)  # This is done to have the entered user either confirmed or rejected, but not both.
        query = "UPDATE public.guilty_user SET rejected = TRUE WHERE guilty_user.guilty_user_id = " + str(guilty_user_id) + " AND guilty_user.year = '" + year + "' AND guilty_user.week = '" + week + "'"
        data = await self.connection.execute(query)
        return data

    async def alterRejectionToFalseForUserInWeek(self, year: str, week: str, guilty_user_id: int):
        query = "UPDATE public.guilty_user SET rejected = FALSE WHERE guilty_user.guilty_user_id = " + str(guilty_user_id) + " AND guilty_user.year = '" + year + "' AND guilty_user.week = '" + week + "'"
        data = await self.connection.execute(query)
        return data



    async def alterConfirmationToTrueForReasonFromUserInWeek(self, year: str, week: str, owner_user_id: int):
        await self.alterAllConfirmationsToFalseForReasonInWeek(year, week)  # This is done to only have one confirmed reason in each week.
        query = "UPDATE public.guilty_reason SET accepted = TRUE WHERE guilty_reason.owner_user_id = " + str(owner_user_id) + " AND guilty_reason.year = '" + year + "' AND guilty_reason.week = '" + week + "'"
        data = await self.connection.execute(query)
        return data

    async def alterConfirmationToFalseForReasonFromUserInWeek(self, year: str, week: str, owner_user_id: int):
        query = "UPDATE public.guilty_reason SET accepted = FALSE WHERE guilty_reason.owner_user_id = " + str(owner_user_id) + " AND guilty_reason.year = '" + year + "' AND guilty_reason.week = '" + week + "'"
        data = await self.connection.execute(query)
        return data

    async def alterRejectionToTrueForReasonFromUserInWeek(self, year: str, week: str, owner_user_id: int):
        await self.alterConfirmationToFalseForReasonFromUserInWeek(year, week, owner_user_id)
        query = "UPDATE public.guilty_reason SET rejected = TRUE WHERE guilty_reason.owner_user_id = " + str(owner_user_id) + " AND guilty_reason.year = '" + year + "' AND guilty_reason.week = '" + week + "'"
        data = await self.connection.execute(query)
        return data

    async def alterRejectionToFalseForReasonFromUserInWeek(self, year: str, week: str, owner_user_id: int):
        query = "UPDATE public.guilty_reason SET rejected = FALSE WHERE guilty_reason.owner_user_id = " + str(owner_user_id) + " AND guilty_reason.year = '" + year + "' AND guilty_reason.week = '" + week + "'"
        data = await self.connection.execute(query)
        return data


    async def alterAllConfirmationsToFalseForReasonInWeek(self, year: str, week: str):
        query = "UPDATE public.guilty_reason SET accepted = FALSE WHERE guilty_reason.year = '" + year + "' AND guilty_reason.week = '" + week + "'"
        data = await self.connection.execute(query)
        return data

    async def alterReasonFromUserInWeek(self, year: str, week: str, owner_user_id: int, reason: str):
        await self.alterConfirmationToFalseForReasonFromUserInWeek(year, week, owner_user_id)  # This is done because otherwise players could change a reason after it was confirmed.
        query = "UPDATE public.guilty_reason SET reason = '" + reason + "' WHERE guilty_reason.owner_user_id = " + str(owner_user_id) + " AND guilty_reason.year = '" + year + "' AND guilty_reason.week = '" + week + "'"
        data = await self.connection.execute(query)
        return data

    async def alterNameOfPlayer(self, id: int, name: str):
        query = "UPDATE public.player SET name = '" + name + "' WHERE player.id = " + str(id)
        data = await self.connection.execute(query)
        return data

    async def alterDescriptionOfPlayer(self, id: int, description: str):
        query = "UPDATE public.player SET description = '" + description + "' WHERE player.id = " + str(id)
        data = await self.connection.execute(query)
        return data

    async def alterActivityOfPlayer(self, id: int, active_state: bool):
        query = "UPDATE public.player SET active = '" + str(active_state) + "' WHERE player.id = " + str(id)
        data = await self.connection.execute(query)
        return data

    async def isUserEnteredFromUserInWeek(self, year: str, week: str, owner_user_id: int, guilty_user_id: int):
        query = "SELECT guilty_user.id, guilty_user.guilty_user_id, guilty_user.owner_user_id FROM public.guilty_user WHERE guilty_user.guilty_user_id = " + str(guilty_user_id) + " AND guilty_user.owner_user_id = " + str(owner_user_id) + " AND guilty_user.year = " + year + " AND guilty_user.week = " + week + " ORDER BY guilty_user.id ASC"
        data = await self.connection.fetch(query)
        return len(data) > 0

    async def isUserEnteredInWeek(self, year: str, week: str, guilty_user_id: int):
        query = "SELECT guilty_user.id, guilty_user.guilty_user_id FROM public.guilty_user WHERE guilty_user.guilty_user_id = " + str(guilty_user_id) + " AND guilty_user.year = " + year + " AND guilty_user.week = " + week + " ORDER BY guilty_user.id ASC"
        data = await self.connection.fetch(query)
        return len(data) > 0

    async def hasUserEnteredReasonInWeek(self, year: str, week: str, owner_user_id: int):
        query = "SELECT guilty_reason.id, guilty_reason.owner_user_id FROM public.guilty_reason WHERE guilty_reason.owner_user_id = " + str(owner_user_id) + " AND guilty_reason.rejected != True AND guilty_reason.year = " + year + " AND guilty_reason.week = " + week + " ORDER BY guilty_reason.id ASC"
        data = await self.connection.fetch(query)
        return len(data) > 0

    async def hasUserEnteredRejectedReasonInWeek(self, year: str, week: str, owner_user_id: int):
        query = "SELECT guilty_reason.id, guilty_reason.owner_user_id FROM public.guilty_reason WHERE guilty_reason.owner_user_id = " + str(owner_user_id) + " AND guilty_reason.rejected = True AND guilty_reason.year = " + year + " AND guilty_reason.week = " + week + " ORDER BY guilty_reason.id ASC"
        data = await self.connection.fetch(query)
        return len(data) > 0

    async def isOneUserAcceptedInWeek(self, year: str, week: str):
        query = "SELECT guilty_user.id, guilty_user.guilty_user_id, guilty_user.owner_user_id, guilty_user.accepted FROM public.guilty_user WHERE guilty_user.year = " + year + " AND guilty_user.week = " + week + " AND guilty_user.accepted IS TRUE ORDER BY guilty_user.id ASC"
        data = await self.connection.fetch(query)
        return len(data) > 0

    async def isOneReasonAcceptedInWeek(self, year: str, week: str):
        query = "SELECT guilty_reason.id, guilty_reason.reason, guilty_reason.owner_user_id, guilty_reason.accepted FROM public.guilty_reason WHERE guilty_reason.year = " + year + " AND guilty_reason.week = " + week + " AND guilty_reason.accepted IS TRUE ORDER BY guilty_reason.id ASC"
        data = await self.connection.fetch(query)
        return len(data) > 0
    
    async def isWeekFinalized(self, year: str, week: str):
        query = "SELECT week_finalized.id, week_finalized.year, week_finalized.week, week_finalized.finalized FROM public.week_finalized WHERE week_finalized.year = " + year + " AND week_finalized.week = " + week + " AND week_finalized.finalized IS TRUE ORDER BY week_finalized.id ASC"
        data = await self.connection.fetch(query)
        return len(data) > 0

    async def isNameUsed(self, name: str):
        query = "SELECT player.name FROM public.player WHERE player.name = '" + name + "' ORDER BY player.id ASC"
        data = await self.connection.fetch(query)
        return len(data) > 0