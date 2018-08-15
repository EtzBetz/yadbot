import asyncpg
from classes import Config


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
        self.connection = await asyncpg.create_pool(**Config.Config.db_credentials)


    async def insertFaultyUser(self, year: str, week: str, owner_user_id: int, faulty_user_id: int):
        query = "INSERT INTO public.faulty_user(year, week, owner_user_id, faulty_user_id) VALUES (" + year + ", " + week + ", " + str(owner_user_id) + ", " + str(faulty_user_id) + ")"
        row = await self.connection.execute(query)
        return str(row)

    async def insertFaultyReason(self, year: str, week: str, owner_user_id: int, reason: str):
        query = "INSERT INTO public.faulty_reason(year, week, owner_user_id, reason) VALUES (" + year + ", " + week + ", " + str(owner_user_id) + ", '" + reason + "')"
        row = await self.connection.execute(query)
        return str(row)

    async def insertFinalizedWeek(self, year: str, week: str):
        query = "INSERT INTO public.week_finalized(year, week, finalized) VALUES (" + year + ", " + week + ", TRUE)"
        row = await self.connection.execute(query)
        return str(row)


    async def getAWeeksFaultyUsersFromUser(self, year: str, week: str, owner_user_id: int):
        query = "SELECT faulty_user.id, faulty_user.faulty_user_id, faulty_user.rejected, faulty_user.accepted FROM public.faulty_user WHERE faulty_user.owner_user_id = " + str(owner_user_id) + " AND faulty_user.year = " + year + " AND faulty_user.week = " + week + " ORDER BY faulty_user.id ASC"
        data = await self.connection.fetch(query)
        return data

    async def getAWeeksFaultyReasonsFromUser(self, year: str, week: str, owner_user_id: int):
        query = "SELECT faulty_reason.id, faulty_reason.reason, faulty_reason.rejected, faulty_reason.accepted FROM public.faulty_reason WHERE faulty_reason.owner_user_id = " + str(owner_user_id) + " AND faulty_reason.year = " + year + " AND faulty_reason.week = " + week + " ORDER BY faulty_reason.id ASC"
        data = await self.connection.fetch(query)
        return data

    async def getAWeeksFaultyUsers(self, year: str, week: str):
        query = "SELECT faulty_user.id, faulty_user.faulty_user_id, faulty_user.rejected, faulty_user.accepted, faulty_user.owner_user_id FROM public.faulty_user WHERE faulty_user.year = " + year + " AND faulty_user.week = " + week + " ORDER BY faulty_user.id ASC"
        data = await self.connection.fetch(query)
        return data

    async def getAWeeksFaultyReasons(self, year: str, week: str):
        query = "SELECT faulty_reason.id, faulty_reason.reason, faulty_reason.rejected, faulty_reason.accepted, faulty_reason.owner_user_id FROM public.faulty_reason WHERE faulty_reason.year = " + year + " AND faulty_reason.week = " + week + " ORDER BY faulty_reason.id ASC"
        data = await self.connection.fetch(query)
        return data


    async def alterConfirmationForUserInWeek(self, year: str, week: str, faulty_user_id: int):
        query = "UPDATE public.faulty_user SET accepted = TRUE WHERE faulty_user.faulty_user_id = " + str(faulty_user_id) + " AND faulty_user.year = '" + year + "' AND faulty_user.week = '" + week + "'"
        data = await self.connection.execute(query)
        return data

    async def alterConfirmationToTrueForReasonFromUserInWeek(self, year: str, week: str, owner_user_id: int):
        await self.alterConfirmationToFalseForReasonInWeek(year, week)
        query = "UPDATE public.faulty_reason SET accepted = TRUE WHERE faulty_reason.owner_user_id = " + str(owner_user_id) + " AND faulty_reason.year = '" + year + "' AND faulty_reason.week = '" + week + "'"
        data = await self.connection.execute(query)
        return data

    async def alterConfirmationToFalseForReasonFromUserInWeek(self, year: str, week: str, owner_user_id: int):
        query = "UPDATE public.faulty_reason SET accepted = FALSE WHERE faulty_reason.owner_user_id = " + str(owner_user_id) + " AND faulty_reason.year = '" + year + "' AND faulty_reason.week = '" + week + "'"
        data = await self.connection.execute(query)
        return data

    async def alterConfirmationToFalseForReasonInWeek(self, year: str, week: str):
        query = "UPDATE public.faulty_reason SET accepted = FALSE WHERE faulty_reason.year = '" + year + "' AND faulty_reason.week = '" + week + "'"
        data = await self.connection.execute(query)
        return data

    async def alterReasonFromUserInWeek(self, year: str, week: str, owner_user_id: int, reason: str):
        await self.alterConfirmationToFalseForReasonFromUserInWeek(year, week, owner_user_id)
        query = "UPDATE public.faulty_reason SET reason = '" + reason + "' WHERE faulty_reason.owner_user_id = " + str(owner_user_id) + " AND faulty_reason.year = '" + year + "' AND faulty_reason.week = '" + week + "'"
        data = await self.connection.execute(query)
        return data


    async def isUserEnteredFromUserInWeek(self, year: str, week: str, owner_user_id: int, faulty_user_id: int):
        query = "SELECT faulty_user.id, faulty_user.faulty_user_id, faulty_user.owner_user_id FROM public.faulty_user WHERE faulty_user.faulty_user_id = " + str(faulty_user_id) + " AND faulty_user.owner_user_id = " + str(owner_user_id) + " AND faulty_user.year = " + year + " AND faulty_user.week = " + week + " ORDER BY faulty_user.id ASC"
        data = await self.connection.fetch(query)
        return len(data) >= 1

    async def isUserEnteredInWeek(self, year: str, week: str, faulty_user_id: int):
        query = "SELECT faulty_user.id, faulty_user.faulty_user_id FROM public.faulty_user WHERE faulty_user.faulty_user_id = " + str(faulty_user_id) + " AND faulty_user.year = " + year + " AND faulty_user.week = " + week + " ORDER BY faulty_user.id ASC"
        data = await self.connection.fetch(query)
        return len(data) > 0

    async def hasUserEnteredReasonInWeek(self, year: str, week: str, owner_user_id: int):
        query = "SELECT faulty_reason.id, faulty_reason.owner_user_id FROM public.faulty_reason WHERE faulty_reason.owner_user_id = " + str(owner_user_id) + " AND faulty_reason.year = " + year + " AND faulty_reason.week = " + week + " ORDER BY faulty_reason.id ASC"
        data = await self.connection.fetch(query)
        return len(data) > 0

    async def isOneUserAcceptedInWeek(self, year: str, week: str):
        query = "SELECT faulty_user.id, faulty_user.faulty_user_id, faulty_user.owner_user_id, faulty_user.accepted FROM public.faulty_user WHERE faulty_user.year = " + year + " AND faulty_user.week = " + week + " AND faulty_user.accepted is TRUE ORDER BY faulty_user.id ASC"
        data = await self.connection.fetch(query)
        return len(data) >= 1

    async def isOneReasonAcceptedInWeek(self, year: str, week: str):
        query = "SELECT faulty_reason.id, faulty_reason.reason, faulty_reason.owner_user_id, faulty_reason.accepted FROM public.faulty_reason WHERE faulty_reason.year = " + year + " AND faulty_reason.week = " + week + " AND faulty_reason.accepted is TRUE ORDER BY faulty_reason.id ASC"
        data = await self.connection.fetch(query)
        return len(data) >= 1
    
    async def isWeekFinalized(self, year: str, week: str):
        query = "SELECT week_finalized.id, week_finalized.year, week_finalized.week, week_finalized.finalized FROM public.week_finalized WHERE week_finalized.year = " + year + " AND week_finalized.week = " + week + " AND week_finalized.finalized is TRUE ORDER BY week_finalized.id ASC"
        data = await self.connection.fetch(query)
        return len(data) >= 1
