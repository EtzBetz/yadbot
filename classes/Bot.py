import discord
import time
import datetime
import os
import asyncio
import asyncpg
from pprint import pprint
from random import randint

from classes import DBConnect, Config, Player

from discord.ext import commands

from auto_commands import cmd_on_member_join


class Bot:

    # Here will the instance be stored.
    __instance = None
    connection = None

    config = Config.Config()

    bot = commands.Bot(command_prefix=config.prefix)
    voice = None
    player = None
    db_connection = None

    current_week = None

    last_messages = [None] * 4


    async def print_guilds(self):
        print("Bot is ready. Running on Guilds: \n")
        for guild in self.bot.guilds:
            print("  - %s (%s)" % (guild.name, guild.id))
        print("\n-----------------------------------------------")

    async def set_presence(self, string):
        # noinspection PyArgumentList
        await self.bot.change_presence(status=discord.Status.online, activity=discord.Game(name=string))

    def is_admin(self, user_id: str):
        return user_id == self.config.admin_id

    async def assign_role_safe(self, member_in_guild, role_in_guild):
        role_assigned = False
        while not role_assigned:
            print("processing assign_role_safe - while")
            await member_in_guild.add_roles(role_in_guild)
            await asyncio.sleep(1)
            for role in member_in_guild.roles:
                if role.id == role_in_guild.id:
                    role_assigned = True
                    break

    async def remove_role_safe(self, member_in_guild, role_in_guild):
        role_removed = False
        while not role_removed:
            print("processing remove_role_safe - while")
            await member_in_guild.remove_roles(role_in_guild)
            await asyncio.sleep(1)
            for role in member_in_guild.roles:
                removed = True
                if role.id == role_in_guild.id:
                    removed = False
                if removed:
                    role_removed = True

    async def get_guild_from_id(self, guild_id):
        return discord.utils.get(self.bot.guilds, id=guild_id)

    async def get_channel_from_id(self, guild_id, channel_id):
        return discord.utils.get((await self.get_guild_from_id(guild_id)).channels, id=channel_id)

    async def get_guilty_players(self):
        guilty_guild = await self.get_guild_from_id(self.config.guilty_member_guild_id)

        guilty_players = []
        for member in guilty_guild.members:
            for role in member.roles:
                if role.id == self.config.guilty_member_role_id:
                    player = Player.Player(discord_user_id=member.id)
                    await player.fill_object_from_db()
                    guilty_players.append(player)
        return guilty_players

    async def get_old_guilty_players(self):
        guilty_guild = await self.get_guild_from_id(self.config.guilty_member_guild_id)

        old_guilty_players = []
        for member in guilty_guild.members:
            for role in member.roles:
                if role.id == self.config.old_guilty_member_role_id:
                    player = Player.Player(discord_user_id=member.id)
                    await player.fill_object_from_db()
                    old_guilty_players.append(player)
        return old_guilty_players

    async def get_guilty_embed(self, year, week, user_id=None, description=""):
        year = str(year)
        week = str(week)

        pre_string = "```diff\n"
        post_string = "```"

        guilty_member_list_string = ""
        if user_id is not None:
            guilty_member_data = await self.db_connection.getAWeeksGuiltyUsersFromUser(year, week, user_id)
        else:
            guilty_member_data = await self.db_connection.getAWeeksGuiltyUsers(year, week)
        for row in guilty_member_data:
            prefix = " "
            if row[3]:
                prefix = "+"
            elif row[2]:
                prefix = "-"
            user = await self.db_connection.getPlayerData(id=row[1])
            guilty_member_list_string += "\n" + prefix + user[0][1]

            if user_id is None:
                owner = await self.db_connection.getPlayerData(id=row[4])
                guilty_member_list_string += "  ⬅️" + owner[0][1]

        guilty_reason_list_string = ""
        if user_id is not None:
            guilty_reason_data = await self.db_connection.getAWeeksGuiltyReasonsFromUser(year, week, user_id)
        else:
            guilty_reason_data = await self.db_connection.getAWeeksGuiltyReasons(year, week)
        for row in guilty_reason_data:
            prefix = " "
            if row[3]:
                prefix = "+"
            elif row[2]:
                prefix = "-"

            guilty_reason_list_string += "\n" + prefix + row[1]

            if user_id is None:
                owner = await self.db_connection.getPlayerData(id=row[4])
                guilty_reason_list_string += "  ⬅️" + owner[0][1]

        embed_description = description

        if user_id is None:
            field_reasons_title = "Gründe:"
        else:
            field_reasons_title = "Grund:"


        if guilty_member_list_string == "":
            guilty_member_list_string = "\n KEINE SCHULDIGEN EINGETRAGEN"
        if guilty_reason_list_string == "":
            guilty_reason_list_string = "\n KEINE SCHULDGRÜNDE EINGETRAGEN"

        guilty_reason_list_array = []
        for i in range((len(guilty_reason_list_string) // (1024 - (len(pre_string)+len(post_string)))) + 1):
            guilty_reason_list_array.append(guilty_reason_list_string[(1024 - (len(pre_string)+len(post_string))) * i:(1024 - (len(pre_string)+len(post_string))) * (i + 1)])

        embed = discord.Embed(title="Das Schuldspiel " + year + ", Woche " + week, description=embed_description, color=0xFFCC00)
        embed.add_field(name="Schuldige:", value=pre_string + guilty_member_list_string + post_string, inline=False)
        for guilty_reason_string in guilty_reason_list_array:
            embed.add_field(name=field_reasons_title, value=pre_string + guilty_reason_string + post_string, inline=False)
        if await self.db_connection.isWeekFinalized(year, week):
            embed.set_footer(text="Die Schuldigen wurden für diese Woche festgelegt.")

        return embed

    async def get_player_missing_in_db_embed(self, context, member):
        embed_string = ""
        embed_string += "**Support:** *YAD__PLAYER_MISSING_IN_DB*\n\n"
        embed_string += "From: " + context.message.author.mention + "\n"
        embed_string += "User: " + member.mention + ", ID: ``" + str(member.id) + "``\n"
        embed_string += "Channel: "
        if context.message.guild is None:  # If message was sent not in a guild
            embed_string += "DM\n"
        else:
            embed_string += context.message.channel.mention + "\n"
        embed_string += "Time: " + context.message.created_at.strftime("%H:%M:%S %d.%m.%Y") + "\n"
        embed_string += "Link: " + context.message.jump_url + "\n"  # TODO: Use link markdown when it is fixed: https://trello.com/c/WD5FyVBu/2124-jump-urls-dont-work-if-masked
        embed_string += "Message: \"" + context.message.content + "\""
        return discord.Embed(color=discord.Color.gold(), description=embed_string)


    async def emoji_mention(self, guild_id: int, id=None, name=None):
        guild = await self.get_guild_from_id(guild_id)
        if id is not None:
            emoji = discord.utils.get(guild.emojis, id=id)
        elif id is None and name is not None:
            emoji = discord.utils.get(guild.emojis, name=name)
        else:
            raise TypeError("Either of parameters \"id\" or \"name\" need to be given.")
        if emoji is not None:
            return "<:" + emoji.name + ":" + str(emoji.id) + ">"


    async def wait_until_minute(self, target_minute: int):
        while datetime.datetime.now().minute != target_minute:
            await self.wait_until_next_minute()

    async def wait_until_hour(self, target_hour: int):
        while datetime.datetime.now().hour != target_hour:
            await self.wait_until_next_hour()

    async def wait_until_weekday(self, target_weekday: int):
        while datetime.datetime.now().weekday != target_weekday:
            await self.wait_until_next_day()

    async def wait_until_day_of_month(self, target_day_of_month: int):
        while datetime.datetime.now().day != target_day_of_month:
            await self.wait_until_next_day()

    async def wait_until_week(self, target_week: int):
        while datetime.datetime.now().isocalendar()[1] != target_week:
            await self.wait_until_next_week()

    async def wait_until_month(self, target_month: int):
        while datetime.datetime.now().month != target_month:
            await self.wait_until_next_month()

    async def wait_until_year(self, target_year: int):
        while datetime.datetime.now().year != target_year:
            await self.wait_until_next_year()


    async def wait_until_next_minute(self):
        now = datetime.datetime.now()
        next_minute_date = datetime.datetime(now.year, now.month, now.day, now.hour, now.minute, 1, 0) + datetime.timedelta(minutes=1)
        difference = next_minute_date - now
        await asyncio.sleep((difference.days * 24 * 60 * 60) + difference.seconds)

    async def wait_until_next_hour(self):
        now = datetime.datetime.now()
        next_hour_date = datetime.datetime(now.year, now.month, now.day, now.hour, 0, 1, 0) + datetime.timedelta(hours=1)
        difference = next_hour_date - now
        await asyncio.sleep((difference.days * 24 * 60 * 60) + difference.seconds)

    async def wait_until_next_day(self):
        now = datetime.datetime.now()
        next_weekday_date = datetime.datetime(now.year, now.month, now.day, 0, 0, 1, 0)
        difference = next_weekday_date - now
        await asyncio.sleep((difference.days * 24 * 60 * 60) + difference.seconds)

    async def wait_until_next_week(self):
        now = datetime.datetime.now()
        offset_days = 7 - now.weekday()
        next_week_date = datetime.datetime(now.year, now.month, now.day, 0, 0, 1, 0) + datetime.timedelta(days=offset_days)
        difference = next_week_date - now
        await asyncio.sleep((difference.days * 24 * 60 * 60) + difference.seconds)

    async def wait_until_next_month(self):
        now = datetime.datetime.now()
        if now.month == 12:
            next_month_date = datetime.datetime(now.year + 1, 1, 1, 0, 0, 1, 0)
        else:
            next_month_date = datetime.datetime(now.year, now.month + 1, 1, 0, 0, 1, 0)
        difference = next_month_date - now
        await asyncio.sleep((difference.days * 24 * 60 * 60) + difference.seconds)

    async def wait_until_next_year(self):
        now = datetime.datetime.now()
        next_year_date = datetime.datetime(now.year + 1, 1, 1, 0, 0, 1, 0)
        difference = next_year_date - now
        await asyncio.sleep((difference.days*24*60*60)+difference.seconds)

    async def remove_old_guilty_members(self):
        old_guilty_players = await self.get_old_guilty_players()
        guilty_guild = await self.get_guild_from_id(self.config.guilty_member_guild_id)
        if guilty_guild is not None:
            old_guilty_member_role = discord.utils.get(guilty_guild.roles, id=self.config.old_guilty_member_role_id)
            for old_guilty_player in old_guilty_players:
                old_guilty_member = discord.utils.get(guilty_guild.members, id=old_guilty_player.discord_user_id)
                await self.remove_role_safe(old_guilty_member, old_guilty_member_role)

    async def refresh_guilty_members(self):
        guilty_guild = await self.get_guild_from_id(self.config.guilty_member_guild_id)
        guilty_member_role = discord.utils.get(guilty_guild.roles, id=self.config.guilty_member_role_id)
        now = datetime.datetime.now()
        iso_date = datetime.date(now.year, now.month, now.day).isocalendar()

        data = await self.db_connection.getAWeeksConfirmedGuiltyUsers(str(iso_date[0]), str(iso_date[1]))
        new_guilty_players = []
        for player_data in data:
            player = Player.Player(id=player_data['guilty_user_id'])
            await player.fill_object_from_db()
            new_guilty_players.append(player)
            player_member = discord.utils.get(guilty_guild.members, id=player.discord_user_id)
            await self.assign_role_safe(player_member, guilty_member_role)

        if guilty_guild is not None:
            old_guilty_member_role = discord.utils.get(guilty_guild.roles, id=self.config.old_guilty_member_role_id)
            old_guilty_players = await self.get_old_guilty_players()
            for old_guilty_player in old_guilty_players:
                old_guilty_member = discord.utils.get(guilty_guild.members, id=old_guilty_player.discord_user_id)
                await self.remove_role_safe(old_guilty_member, old_guilty_member_role)

    async def set_current_guilty_members_to_old_guilty_members(self):
        guilty_players = await self.get_guilty_players()
        guilty_guild = await self.get_guild_from_id(self.config.guilty_member_guild_id)

        if guilty_guild is not None:
            old_guilty_member_role = discord.utils.get(guilty_guild.roles, id=self.config.old_guilty_member_role_id)
            guilty_member_role = discord.utils.get(guilty_guild.roles, id=self.config.guilty_member_role_id)
            for guilty_player in guilty_players:
                guilty_member = discord.utils.get(guilty_guild.members, id=guilty_player.discord_user_id)
                await self.assign_role_safe(guilty_member, old_guilty_member_role)
                await self.remove_role_safe(guilty_member, guilty_member_role)

    async def send_guilty_message_to_old_guilty_members(self):
        old_guilty_players = await self.get_old_guilty_players()
        admin_player = Player.Player(discord_user_id=self.config.admin_id)
        await admin_player.fill_object_from_db()

        for old_guilty_player in old_guilty_players:
            print("send_guilty_message_to_old_guilty_members(): " + old_guilty_player.name + ": " + old_guilty_player.discord_user_object.name)
            await old_guilty_player.discord_user_object.send("**Hurra, deine Schuldwoche ist vorbei!**\n"
                                                             "\n"
                                                             "Du kannst ab jetzt mit `" + self.config.prefix + "schuld ist ...` ein oder mehrere Schuldige für diese Woche festlegen.\n"
                                                             "Ich akzeptiere die Personen auf zwei Arten:\n"
                                                             "Entweder du schreibst nacheinander die Namen, wie sie mit `" + self.config.prefix + "schuld member` angezeigt werden, oder du @pingst sie.\n"
                                                             "**Pingen kannst du aber nur in " + (await self.get_channel_from_id(self.config.guilty_member_guild_id, self.config.guilty_news_channel_id)).mention + " bzw. dem [iQ]-Server.**\n"
                                                             "Anschließend musst du noch mit `" + self.config.prefix + "schuld grund \"Deine Begründung\"` einen Schuldgrund angeben.\n"
                                                             "Später werden dann die Zuständigen entscheiden, ob dein Vorschlag angenommen oder abgelehnt wird.\n"
                                                             "\n"
                                                             "**Beispiele**:\n"
                                                             "`" + self.config.prefix + "schuld ist " + old_guilty_player.name + "` **(überall)**\n"
                                                             "`" + self.config.prefix + "schuld ist " + old_guilty_player.name + " " + admin_player.name + "` **(überall)**\n"
                                                             "`" + self.config.prefix + "schuld ist` " + old_guilty_player.discord_user_object.mention + "  **(nur in " + (await self.get_channel_from_id(self.config.guilty_member_guild_id, self.config.guilty_news_channel_id)).mention + ")**\n"
                                                             "`" + self.config.prefix + "schuld ist` " + old_guilty_player.discord_user_object.mention + " `" + admin_player.name + "`  **(nur in " + (await self.get_channel_from_id(self.config.guilty_member_guild_id, self.config.guilty_news_channel_id)).mention + ")**\n"
                                                             "`" + self.config.prefix + "schuld grund \"" + old_guilty_player.name + " ist schuld, weil ...\"`")

    async def send_reminder_message_to_old_guilty_members(self):
        old_guilty_players = await self.get_old_guilty_players()

        for old_guilty_player in old_guilty_players:
            print("send_reminder_message_to_old_guilty_members(): " + old_guilty_player.name + ": " + old_guilty_player.discord_user_object.name)
            await old_guilty_player.discord_user_object.send("Hier ist eine freundliche Erinnerung, dass du noch einen/die Schuldigen festlegen musst. " + await self.emoji_mention(self.config.guilty_member_guild_id, name="quagganthinking"))

    async def send_guilty_message_to_guilty_channel(self):
        now = datetime.datetime.now()
        iso_date = datetime.date(now.year, now.month, now.day).isocalendar()
        news_channel = await self.get_channel_from_id(self.config.guilty_member_guild_id, self.config.guilty_news_channel_id)
        await news_channel.send("@here Der/die Schuldige(n) für diese Woche stehen fest!", embed=await self.get_guilty_embed(str(iso_date[0]), str(iso_date[1])))

    async def new_week_guilty_event(self):
        await self.wait_until_next_week()

        await self.remove_old_guilty_members()
        await self.set_current_guilty_members_to_old_guilty_members()
        await self.send_guilty_message_to_old_guilty_members()

        asyncio.create_task(await self.new_week_guilty_event())

    async def monday_reminder(self):
        if not datetime.datetime.now().weekday == 0:
            await self.wait_until_weekday(0)
        if not datetime.datetime.now().hour == 19:
            await self.wait_until_hour(19)
        if datetime.datetime.now().minute <= 5:
            now = datetime.datetime.now()
            iso_date = datetime.date(now.year, now.month, now.day).isocalendar()
            if not await self.db_connection.isWeekFinalized(iso_date[0], iso_date[1]):
                await self.send_reminder_message_to_old_guilty_members()

        asyncio.create_task(await self.monday_reminder())

    async def tuesday_reminder(self):
        if not datetime.datetime.now().weekday == 1:
            await self.wait_until_weekday(1)
        if not datetime.datetime.now().hour == 19:
            await self.wait_until_hour(19)
        if datetime.datetime.now().minute <= 5:
            now = datetime.datetime.now()
            iso_date = datetime.date(now.year, now.month, now.day).isocalendar()
            if not await self.db_connection.isWeekFinalized(iso_date[0], iso_date[1]):
                await self.send_reminder_message_to_old_guilty_members()

        asyncio.create_task(await self.tuesday_reminder())

    async def wednesday_reminder(self):
        if not datetime.datetime.now().weekday == 2:
            await self.wait_until_weekday(2)
        if not datetime.datetime.now().hour == 19:
            await self.wait_until_hour(19)
        if datetime.datetime.now().minute <= 5:
            now = datetime.datetime.now()
            iso_date = datetime.date(now.year, now.month, now.day).isocalendar()
            if not await self.db_connection.isWeekFinalized(iso_date[0], iso_date[1]):
                await self.send_reminder_message_to_old_guilty_members()

        asyncio.create_task(await self.wednesday_reminder())

    async def thursday_guilty_event(self):
        if not datetime.datetime.now().weekday == 3:
            await self.wait_until_weekday(3)
        if not datetime.datetime.now().hour == 20:
            await self.wait_until_hour(20)
        if datetime.datetime.now().minute <= 5:
            now = datetime.datetime.now()
            iso_date = datetime.date(now.year, now.month, now.day).isocalendar()

            if not await self.db_connection.isWeekFinalized(str(iso_date[0]), str(iso_date[1])):
                print("debug: not finalized")
                if not await self.db_connection.isOneUserAcceptedInWeek(str(iso_date[0]), str(iso_date[1])):
                    print("debug: no user got accepted")
                    proposed_players = await self.db_connection.getAWeeksGuiltyUsers(str(iso_date[0]), str(iso_date[1]))
                    if len(proposed_players) == 0:
                        print("debug: no user proposed")
                        player_ids = await self.db_connection.getAllPlayersIds(only_active=True)
                        pprint(player_ids)
                        random_player_id = player_ids[randint(1, len(player_ids))]['id']

                        pprint(random_player_id)
                        random_player = Player.Player(random_player_id)
                        await random_player.fill_object_from_db()
                        await self.db_connection.insertGuiltyUser(str(iso_date[0]), str(iso_date[1]), random_player.id, random_player.id)
                        await self.db_connection.insertGuiltyReason(str(iso_date[0]), str(iso_date[1]), random_player.id, "Der Schuldige von letzter Woche hat leider geschlafen, jetzt ist " + random_player.name + " schuld.")
                        await self.db_connection.alterConfirmationToTrueForUserInWeek(str(iso_date[0]), str(iso_date[1]), random_player.id)
                        await self.db_connection.alterConfirmationToTrueForReasonFromUserInWeek(str(iso_date[0]), str(iso_date[1]), random_player.id)
                    else:
                        print("debug: user proposed, not accepted")
                        for proposed_player in proposed_players:
                            await self.db_connection.alterConfirmationToTrueForUserInWeek(str(iso_date[0]), str(iso_date[1]), proposed_player['guilty_user_id'])
                            if await self.db_connection.hasUserEnteredReasonInWeek(str(iso_date[0]), str(iso_date[1]), proposed_player['owner_user_id']):
                                print("debug: user has entered reason, confirming now")
                            await self.db_connection.alterConfirmationToTrueForReasonFromUserInWeek(str(iso_date[0]), str(iso_date[1]), proposed_player['owner_user_id'])
                elif not await self.db_connection.isOneReasonAcceptedInWeek(str(iso_date[0]), str(iso_date[1])):
                    print("debug: user accepted, reason not")
                    guilty_users_data = await self.db_connection.getAWeeksConfirmedGuiltyUsers(str(iso_date[0]), str(iso_date[1]))
                    for data in guilty_users_data:
                        if await self.db_connection.hasUserEnteredReasonInWeek(str(iso_date[0]), str(iso_date[1]), data['owner_user_id']):
                            print("debug: user entered reason, didnt get confirmed, confirming now")
                            await self.db_connection.alterConfirmationToTrueForReasonFromUserInWeek(str(iso_date[0]), str(iso_date[1]), data['owner_user_id'])
                            break
                        else:
                            print("debug: no reason entered, creating and confirming it now")
                            if await self.db_connection.hasUserEnteredRejectedReasonInWeek(str(iso_date[0]), str(iso_date[1]), data['owner_user_id']):
                                await self.db_connection.alterReasonFromUserInWeek(str(iso_date[0]), str(iso_date[1]), data['owner_user_id'], "Ich habe vergessen, einen neuen Grund anzugeben :(")
                            else:
                                await self.db_connection.insertGuiltyReason(str(iso_date[0]), str(iso_date[1]), data['owner_user_id'], "Ich habe vergessen, einen Grund anzugeben :(")
                            await self.db_connection.alterConfirmationToTrueForReasonFromUserInWeek(str(iso_date[0]), str(iso_date[1]), data['owner_user_id'])
                print("debug: finalizing week")
                await self.db_connection.insertFinalizedWeek(str(iso_date[0]), str(iso_date[1]))
                await self.refresh_guilty_members()
                await self.send_guilty_message_to_guilty_channel()

        asyncio.create_task(await self.thursday_guilty_event())


    async def enable_timers(self):
        print("debug: create timers")
        asyncio.create_task(self.new_week_guilty_event())
        asyncio.create_task(self.monday_reminder())
        asyncio.create_task(self.tuesday_reminder())
        asyncio.create_task(self.wednesday_reminder())
        asyncio.create_task(self.thursday_guilty_event())
        print("debug: timers created")

    async def is_discord_id_in_db(self, discord_user_id):
        return await self.db_connection.getPlayerData(discord_user_id=discord_user_id)

    async def reply_equal_messages(self, message):
        self.last_messages[3] = self.last_messages[2]
        self.last_messages[2] = self.last_messages[1]
        self.last_messages[1] = self.last_messages[0]
        self.last_messages[0] = message

        if not message.author.id == self.config.bot_id:
            if self.last_messages[3] is not None:
                if self.last_messages[0].content == self.last_messages[1].content and self.last_messages[1].content == self.last_messages[2].content and self.last_messages[2].content == self.last_messages[3].content:
                    message_author_ids = [self.last_messages[0].author.id]
                    if not message_author_ids.__contains__(self.last_messages[1].author.id):
                        message_author_ids.append(self.last_messages[1].author.id)
                        if not message_author_ids.__contains__(self.last_messages[2].author.id):
                            message_author_ids.append(self.last_messages[2].author.id)
                            if not message_author_ids.__contains__(self.last_messages[3].author.id):
                                if len(message.content) > 0:
                                    await message.channel.send(message.content)

    @staticmethod
    async def getInstance():
        """Static access method."""
        if Bot.__instance is None:
            Bot()
        return Bot.__instance


    def __init__(self):

        if Bot.__instance is not None:
            raise Exception("This class is a singleton!")
        else:
            Bot.__instance = self

        @self.bot.event
        async def on_ready():
            await self.print_guilds()
            await self.set_presence("Version " + self.config.version_number)

            self.db_connection = DBConnect.DBConnect()
            await self.db_connection.setUp()

            asyncio.create_task(self.enable_timers())

        @self.bot.event
        async def on_member_join(member):
            pass
            # await cmd_on_member_join.ex(self.bot, member)

        @self.bot.event
        async def on_message(message):

            # in order to process the other command events
            await self.bot.process_commands(message)

            # custom ping/pong command, because bot checks if the message comes from a bot if used with a normal command
            if message.content == self.config.prefix + "ping":
                if self.config.ping_pong_loop == 1:
                    await message.channel.send(self.config.prefix + "pong")
                else:
                    await message.channel.send("pong" + self.config.prefix)
            if message.content == self.config.prefix + "pong":
                if self.config.ping_pong_loop == 1:
                    await message.channel.send(self.config.prefix + "ping")
                else:
                    await message.channel.send("ping" + self.config.prefix)

            # custom function to repeat a message if it was sent 4 times
            await self.reply_equal_messages(message)  # TODO: check if this works properly

            # custom function to react to any user why writes " owo " anywhere
            if message.content.lower().__contains__("owo"):
                if message.author.id != self.config.bot_id:
                    await message.channel.send("***triggered***")

        @self.bot.command()
        async def join(context):
            """Bot will join your voice channel."""
            self.voice = await context.message.author.voice.channel.connect()

        @self.bot.command()
        async def leave(context):
            """Bot will leave your voice channel."""
            await self.voice.disconnect()
            self.voice = None

        @self.bot.command()
        async def airhorn(context):
            """Bot will play an airhorn sound in your channel. Just like good old !airhorn did."""
            self.voice = await context.message.author.voice.channel.connect()
            self.voice.play(discord.FFmpegPCMAudio('./sounds/airhorns/airhorn.m4a'))
            if self.config.airhorn_stay_afterwards == 0:
                time.sleep(2)
                await self.voice.disconnect()

        @self.bot.group()
        @commands.is_owner()
        async def admin(context):
            """Admin commands, you need to be the owner to execute any of these."""
            admin_user = await self.bot.get_user_info(self.config.admin_id)
            if not self.is_admin(context.message.author.id):
                await context.message.channel.send(embed=discord.Embed(color=discord.Color.red(), description="You are not " + admin_user.name + ", sorry!"))
            else:
                if context.invoked_subcommand is None:
                    await context.message.channel.send(embed=discord.Embed(color=discord.Color.red(), description="admin: no currect subcommand: `" + context.message.content + "`"))

        @admin.command()
        async def toggle(context, variable: str):
            """Toggle any of the on/off attributes of this bot."""
            if self.is_admin(context.message.author.id):
                if hasattr(self.config, variable):
                    if getattr(self.config, variable) == 0:
                        setattr(self.config, variable, 1)
                        await context.message.channel.send(embed=discord.Embed(color=discord.Color.green(), description="**`" + variable + "`** set to **`" + str(getattr(self.config, variable)) + "`**."))
                    elif getattr(self.config, variable) == 1:
                        setattr(self.config, variable, 0)
                        await context.message.channel.send(embed=discord.Embed(color=discord.Color.green(), description="**`" + variable + "`** set to **`" + str(getattr(self.config, variable)) + "`**."))
                    else:
                        await context.message.channel.send(embed=discord.Embed(color=discord.Color.red(), description="**`" + variable + "`** is not toggleable, as it is not `0` or `1`!"))
                else:
                    await context.message.channel.send(embed=discord.Embed(color=discord.Color.red(), description="There is no variable called **`" + variable + "`**!"))

        @admin.command()
        async def say(context, channel, text: str):
            """Bot repeats what you write in any other channel on this server."""
            if self.is_admin(context.message.author.id):
                channel = discord.utils.get(context.message.guild.channels, mention=channel)
                await channel.send(text)

        @admin.command()
        async def schuldtimeline(context):  # KEEP UNTIL BOT IS SETUP AND ALL MESSAGES WERE SEND IN GUILTY CHANNEL ONCE
            """Command for guilty usage."""
            if self.is_admin(context.message.author.id):
                for x in range(52):
                    await context.message.channel.send(embed=await self.get_guilty_embed(2017, x+1, None))
                for x in range(42):
                    await context.message.channel.send(embed=await self.get_guilty_embed(2018, x+1, None))

        @admin.command()
        async def schuldnews(context):
            if self.is_admin(context.message.author.id):
                await self.send_guilty_message_to_guilty_channel()

        @admin.command()
        async def schuldpm(context):
            if self.is_admin(context.message.author.id):
                await self.send_guilty_message_to_old_guilty_members()

        @admin.command()
        async def schuldexecute(context):
            if self.is_admin(context.message.author.id):
                now = datetime.datetime.now()
                iso_date = datetime.date(now.year, now.month, now.day).isocalendar()

                if not await self.db_connection.isWeekFinalized(str(iso_date[0]), str(iso_date[1])):
                    print("debug: not finalized")
                    if not await self.db_connection.isOneUserAcceptedInWeek(str(iso_date[0]), str(iso_date[1])):
                        print("debug: no user got accepted")
                        proposed_players = await self.db_connection.getAWeeksGuiltyUsers(str(iso_date[0]), str(iso_date[1]))
                        if len(proposed_players) == 0:
                            print("debug: no user proposed")
                            player_ids = await self.db_connection.getAllPlayersIds(only_active=True)
                            pprint(player_ids)
                            random_player_id = player_ids[randint(1, len(player_ids))]['id']

                            pprint(random_player_id)
                            random_player = Player.Player(random_player_id)
                            await random_player.fill_object_from_db()
                            await self.db_connection.insertGuiltyUser(str(iso_date[0]), str(iso_date[1]), random_player.id, random_player.id)
                            await self.db_connection.insertGuiltyReason(str(iso_date[0]), str(iso_date[1]), random_player.id, "Der Schuldige von letzter Woche hat leider geschlafen, jetzt ist " + random_player.name + " schuld.")
                            await self.db_connection.alterConfirmationToTrueForUserInWeek(str(iso_date[0]), str(iso_date[1]), random_player.id)
                            await self.db_connection.alterConfirmationToTrueForReasonFromUserInWeek(str(iso_date[0]), str(iso_date[1]), random_player.id)
                        else:
                            print("debug: user proposed, not accepted")
                            for proposed_player in proposed_players:
                                await self.db_connection.alterConfirmationToTrueForUserInWeek(str(iso_date[0]), str(iso_date[1]), proposed_player['guilty_user_id'])
                                if await self.db_connection.hasUserEnteredReasonInWeek(str(iso_date[0]), str(iso_date[1]), proposed_player['owner_user_id']):
                                    print("debug: user has entered reason, confirming now")
                                await self.db_connection.alterConfirmationToTrueForReasonFromUserInWeek(str(iso_date[0]), str(iso_date[1]), proposed_player['owner_user_id'])
                    elif not await self.db_connection.isOneReasonAcceptedInWeek(str(iso_date[0]), str(iso_date[1])):
                        print("debug: user accepted, reason not")
                        guilty_users_data = await self.db_connection.getAWeeksConfirmedGuiltyUsers(str(iso_date[0]), str(iso_date[1]))
                        for data in guilty_users_data:
                            if await self.db_connection.hasUserEnteredReasonInWeek(str(iso_date[0]), str(iso_date[1]), data['owner_user_id']):
                                print("debug: user entered reason, didnt get confirmed, confirming now")
                                await self.db_connection.alterConfirmationToTrueForReasonFromUserInWeek(str(iso_date[0]), str(iso_date[1]), data['owner_user_id'])
                                break
                            else:
                                print("debug: no reason entered, creating and confirming it now")
                                if await self.db_connection.hasUserEnteredRejectedReasonInWeek(str(iso_date[0]), str(iso_date[1]), data['owner_user_id']):
                                    await self.db_connection.alterReasonFromUserInWeek(str(iso_date[0]), str(iso_date[1]), data['owner_user_id'], "Ich habe vergessen, einen neuen Grund anzugeben :(")
                                else:
                                    await self.db_connection.insertGuiltyReason(str(iso_date[0]), str(iso_date[1]), data['owner_user_id'], "Ich habe vergessen, einen Grund anzugeben :(")
                                await self.db_connection.alterConfirmationToTrueForReasonFromUserInWeek(str(iso_date[0]), str(iso_date[1]), data['owner_user_id'])
                    print("debug: finalizing week")
                    await self.db_connection.insertFinalizedWeek(str(iso_date[0]), str(iso_date[1]))
                    await self.refresh_guilty_members()
                    await self.send_guilty_message_to_guilty_channel()

        @admin.command()
        async def refreshguilty(context):
            if self.is_admin(context.message.author.id):
                await self.refresh_guilty_members()

        @admin.command()
        async def code(context, code):
            """Execute the given string as python code."""
            if self.is_admin(context.message.author.id):
                exec(code)

        @admin.command()
        async def test(context):
            """Command to test some new functionality."""
            if self.is_admin(context.message.author.id):
                pass

        @self.bot.group()
        async def schuld(context):
            """Commands belonging to the guilty game."""
            if context.invoked_subcommand is None:
                await context.message.channel.send(embed=discord.Embed(color=discord.Color.red(), description="schuld: no currect subcommand: `" + context.message.content + "`"))

        @schuld.command()
        async def liste(context):
            """Show the guilty list."""
            now = datetime.datetime.now()
            iso_date = datetime.date(now.year, now.month, now.day).isocalendar()
            await context.message.channel.send(embed=await self.get_guilty_embed(iso_date[0], iso_date[1], None))

        @schuld.command()
        async def ist(context, *guilty_members):  # guilty_members is being used, despite IDE highlighting it not being used (context.args)
            """Select this weeks guilty member(s)."""
            now = datetime.datetime.now()
            iso_date = datetime.date(now.year, now.month, now.day).isocalendar()

            author_player = Player.Player(discord_user_id=context.message.author.id)
            await author_player.fill_object_from_db()

            old_guilty_players = await self.get_old_guilty_players()
            not_recognized_written_names = []
            not_added_members = []
            proposed_guilty_players = []
            already_added_guilty_players = []
            new_guilty_players = []

            authorized_player = False
            for old_guilty_player in old_guilty_players:
                if old_guilty_player.discord_user_object.id == author_player.discord_user_object.id:
                    authorized_player = True

            if authorized_player:
                if not await self.db_connection.isWeekFinalized(str(iso_date[0]), str(iso_date[1])):
                    for mentioned_member in context.message.mentions:
                        if await self.is_discord_id_in_db(mentioned_member.id) is False:
                            not_added_members.append(mentioned_member)
                        else:
                            player = Player.Player(discord_user_id=mentioned_member.id)
                            await player.fill_object_from_db()
                            proposed_guilty_players.append(player)

                    context_skipped = False
                    for written_member in context.args:
                        if context_skipped is False:  # First element in context.args is context, so just skip over first element of for loop
                            context_skipped = True
                        else:
                            if written_member[0:2] == "<@" and written_member[-1:] == ">":
                                pass
                            else:
                                player_data = await self.db_connection.getPlayerData(name=written_member)
                                if player_data is not False:
                                    player = Player.Player(name=player_data[0][1])
                                    await player.fill_object_from_db()
                                    proposed_guilty_players.append(player)
                                else:
                                    not_recognized_written_names.append(written_member)


                    admin_user = self.bot.get_user(self.config.admin_id)
                    for member in not_added_members:
                        if self.config.support_skip_all == 0:
                            if self.config.support_skip_player_missing_in_db == 0:
                                await admin_user.send(embed=(await self.get_player_missing_in_db_embed(context, member)))
                            else:
                                pass
                        else:
                            pass

                    contains_self = False
                    for proposed_player in proposed_guilty_players:
                        if proposed_player.discord_user_object.id == author_player.discord_user_object.id:
                            contains_self = True
                        elif await self.db_connection.isUserEnteredFromUserInWeek(str(iso_date[0]), str(iso_date[1]), author_player.id, proposed_player.id):
                            already_added_guilty_players.append(proposed_player)
                        else:
                            await self.db_connection.insertGuiltyUser(str(iso_date[0]), str(iso_date[1]), author_player.id, proposed_player.id)
                            new_guilty_players.append(proposed_player)

                    message_string = ""
                    if contains_self is True:
                        message_string += "Du hast versucht, dich selber einzutragen, das ist nicht möglich.\n\n"
                    if len(not_recognized_written_names) > 0:
                        message_string += "Folgende Namen wurden nicht erkannt oder existieren nicht:\n```diff\n"
                        for written_name in not_recognized_written_names:
                            message_string += "-" + written_name + "\n"
                        message_string += "```\n"
                    if len(not_added_members) > 0:
                        message_string += "Folgende Personen wurden noch nicht von den Admins eingetragen, sie wurden benachrichtigt und kümmern sich darum.\n```diff\n"
                        for member in not_added_members:
                            message_string += "-" + member.name + "\n"
                        message_string += "```\n"
                    if len(already_added_guilty_players) > 0:
                        message_string += "Folgende Personen wurden schon von dir vorgeschlagen. Du kannst sie nicht ein zweites mal vorschlagen.\n```diff\n"
                        for player in already_added_guilty_players:
                            message_string += " " + player.name + "\n"
                        message_string += "```\n"
                    if len(new_guilty_players) > 0:
                        message_string += "Folgende Personen wurden erfolgreich von dir für das Schuldspiel vorgeschlagen:\n```diff\n"
                        for proposed_player in new_guilty_players:
                            message_string += "+" + proposed_player.name
                        message_string += "```\n"

                    guilty_embed = await self.get_guilty_embed(str(iso_date[0]), str(iso_date[1]), author_player.id, message_string)
                    await context.message.channel.send(embed=guilty_embed)
                else:
                    await context.message.channel.send(embed=discord.Embed(color=discord.Color.red(), description="Diese Woche wurde schon abgeschlossen!"))
            else:
                await context.message.channel.send(embed=discord.Embed(color=discord.Color.red(), description="Ey, dieser Befehl ist nur für Schuldigen von letzter Woche zugelassen!"))

        @schuld.command()
        async def grund(context, guilty_reason: str):
            """Enter the reasons why the selected members are guilty this week."""
            old_guilty_players = await self.get_old_guilty_players()
            author_player = Player.Player(discord_user_id=context.message.author.id)
            await author_player.fill_object_from_db()

            authorized_player = False
            for old_guilty_player in old_guilty_players:
                if old_guilty_player.discord_user_object.id == author_player.discord_user_object.id:
                    authorized_player = True

            if authorized_player:
                now = datetime.datetime.now()
                iso_date = datetime.date(now.year, now.month, now.day).isocalendar()
                if not await self.db_connection.isWeekFinalized(str(iso_date[0]), str(iso_date[1])):
                    if not await self.db_connection.hasUserEnteredReasonInWeek(str(iso_date[0]), str(iso_date[1]), author_player.id):
                        await self.db_connection.insertGuiltyReason(str(iso_date[0]), str(iso_date[1]), author_player.id, guilty_reason)

                        guilty_embed = await self.get_guilty_embed(str(iso_date[0]), str(iso_date[1]), author_player.id, "Du hast folgendes als Schuldgrund für diese Woche eingetragen:\n```" + guilty_reason + "```")
                        await context.message.channel.send(embed=guilty_embed)
                    else:
                        await self.db_connection.alterReasonFromUserInWeek(str(iso_date[0]), str(iso_date[1]), author_player.id, guilty_reason)

                        guilty_embed = await self.get_guilty_embed(str(iso_date[0]), str(iso_date[1]), author_player.id, "Dein eingetragener Schuldgrund wurde aktualisiert:\n```" + guilty_reason + "```")
                        await context.message.channel.send(embed=guilty_embed)
                else:
                    await context.message.channel.send(embed=discord.Embed(color=discord.Color.red(), description="Diese Woche wurde schon abgeschlossen!"))
            else:
                await context.message.channel.send("Ey, Ich höre nur auf den Schuldigen von letzter Woche!")

        @schuld.command()
        async def memberliste(context):
            """Shows a list of all members that can be guilty or were guilty once."""
            active_players = []
            inactive_players = []
            players_data = await self.db_connection.getAllPlayersIds()
            for player_data in players_data:
                player = Player.Player(id=player_data['id'])
                await player.fill_object_from_db()
                if player.active:
                    active_players.append(player)
                else:
                    inactive_players.append(player)

            active_players_list = "```\n"
            for active_player in active_players:
                active_players_list += active_player.name + "\n"
            active_players_list += "```"
            inactive_players_list = "```\n"
            for inactive_player in inactive_players:
                inactive_players_list += inactive_player.name + "\n"
            inactive_players_list += "```"

            member_embed = discord.Embed(title="Member des Schuldspiels", description="Folgende Member sind für das Schuldspiel eingetragen:", color=0xFFCC00)
            member_embed.add_field(name="Aktive Member:", value=active_players_list, inline=False)
            member_embed.add_field(name="Inaktive Member:", value=inactive_players_list, inline=False)
            member_embed.set_footer(text="Nur aktive Member können schuldig gemacht werden.")
            await context.message.channel.send(embed=member_embed)

        @schuld.command()
        async def farbe(context, red_value, green_value, blue_value):
            """Change the color of the guilty role. (Can only be used by the current guilty member(s).)"""
            guilty_guild = await self.get_guild_from_id(self.config.guilty_member_guild_id)
            guilty_member_role = discord.utils.get(guilty_guild.roles, id=self.config.guilty_member_role_id)
            guilty_players = await self.get_guilty_players()
            authorized = False

            for guilty_player in guilty_players:
                if guilty_player.discord_user_id == context.message.author.id:
                    authorized = True
                    break

            if authorized:
                try:
                    if 0 <= int(red_value) <= 255 and 0 <= int(green_value) <= 255 and 0 <= int(blue_value) <= 255:
                        color_hex = "{:02x}{:02x}{:02x}".format(int(red_value), int(green_value), int(blue_value))
                        await guilty_member_role.edit(color=discord.Color(int(color_hex, 16)))
                        await context.message.channel.send(embed=discord.Embed(color=discord.Color(int(color_hex, 16)), description="Die Farbe wurde erfolgreich geändert."))
                    else:
                        raise ValueError("Values not between or equal to 0 and 255")
                except ValueError:
                        await context.message.channel.send(embed=discord.Embed(color=discord.Color.red(), description="**Deine Farbeingabe war falsch!**\n"
                                                                                                                      "Gebe jeweils einen Wert von 0 bis 255 für **Rot**, **Grün** und **Blau** ein.\n"
                                                                                                                      "\n"
                                                                                                                      "Hilfe: https://www.google.de/search?&q=color+picker\n"
                                                                                                                      "\n"
                                                                                                                      "Syntax:\n"
                                                                                                                      "```!schuld farbe 0-255 0-255 0-255```\n"
                                                                                                                      "\n"
                                                                                                                      "Beispiel:\n"
                                                                                                                      "```!schuld farbe 233 31 98```"))
            else:
                await context.message.channel.send(embed=discord.Embed(color=discord.Color.red(), description="Dieser Befehl kann nur vom aktuell Schuldigen benutzt werden!"))

        @schuld.group()
        async def edit(context):
            """Edit your name or description for the guilty game. ([iQ]-Leaders can edit everyone.)"""
            pass

        @edit.command()
        async def name(context, new_username, user_to_edit_mention=None):
            """Edit your name for the guilty game. ([iQ]-Leaders can edit everyone's name.) """
            player_data = None
            if user_to_edit_mention is not None:
                if self.config.iq_leaders_id.__contains__(context.message.author.id):
                    player_data = await self.is_discord_id_in_db(context.message.mentions[0].id)
                else:
                    await context.message.channel.send(embed=discord.Embed(color=discord.Color.red(), description="Nur die [iQ]-Leader dürfen den Namen von anderen editieren."))
            else:
                player_data = await self.is_discord_id_in_db(context.message.author.id)

            if player_data is not None:
                if player_data is False:
                    admin_user = self.bot.get_user(self.config.admin_id)
                    await context.message.channel.send(embed=discord.Embed(color=discord.Color.red(), description="Du/der angegebene Member ist nicht in der Memberliste eingetragen.\n"
                                                                                                                  "Wende dich an " + admin_user.mention + "."))
                else:
                    player = Player.Player(id=player_data[0]['id'])
                    await player.fill_object_from_db()
                    name_used = await self.db_connection.isNameUsed(new_username)
                    if name_used is False:
                        query = await self.db_connection.alterNameOfPlayer(player.id, new_username)
                        if query:
                            await context.message.channel.send(embed=discord.Embed(color=discord.Color.green(), description="Der Name von " + player.discord_user_object.mention + " wurde erfolgreich zu `" + new_username + "` geändert."))
                        else:
                            admin_user = self.bot.get_user(self.config.admin_id)
                            await context.message.channel.send(embed=discord.Embed(color=discord.Color.red(), description="Ein Fehler ist aufgetreten. Wende dich eventuell an " + admin_user.mention + "."))
                    else:
                        await context.message.channel.send(embed=discord.Embed(color=discord.Color.red(), description="Es ist bereits ein Member mit dem Namen `" + new_username + "` in der Memberliste eingetragen!\n"
                                                                                                                      "Versuche es mit einem anderen Namen."))

        @edit.command()
        async def description(context, new_description, user_mention=None):
            """Edit your description for the guilty game. ([iQ]-Leaders can edit everyone's description.) """
            player_data = None
            if user_mention is not None and len(context.message.mentions) > 0:
                if self.config.iq_leaders_id.__contains__(context.message.author.id):
                    player_data = await self.is_discord_id_in_db(context.message.mentions[0].id)
                else:
                    await context.message.channel.send(embed=discord.Embed(color=discord.Color.red(), description="Nur die [iQ]-Leader dürfen die Beschreibung von anderen editieren."))
            else:
                player_data = await self.is_discord_id_in_db(context.message.author.id)

            if player_data is not None:
                if player_data is False:
                    admin_user = self.bot.get_user(self.config.admin_id)
                    await context.message.channel.send(embed=discord.Embed(color=discord.Color.red(), description="Du/der angegebene Member ist nicht in der Memberliste eingetragen.\n"
                                                                                                                  "Wende dich an " + admin_user.mention + "."))
                else:
                    player = Player.Player(id=player_data[0]['id'])
                    await player.fill_object_from_db()
                    query = await self.db_connection.alterDescriptionOfPlayer(player.id, new_description)
                    if query:
                        await context.message.channel.send(embed=discord.Embed(color=discord.Color.green(), description="Die Beschreibung von **" + player.discord_user_object.mention + "** wurde geändert:\n"
                                                                                                                        "```" + new_description + "```"))
                    else:
                        admin_user = self.bot.get_user(self.config.admin_id)
                        await context.message.channel.send(embed=discord.Embed(color=discord.Color.red(), description="Ein Fehler ist aufgetreten. Wende dich eventuell an " + admin_user.mention + "."))

        @edit.command()
        async def active(context, user_mention):
            """Toggle the active/inactive state of an [iQ]-Member. (Can only be used by Leaders of [iQ].)"""
            player_data = None
            if self.config.iq_leaders_id.__contains__(context.message.author.id):
                player_data = await self.is_discord_id_in_db(context.message.mentions[0].id)
            else:
                await context.message.channel.send(embed=discord.Embed(color=discord.Color.red(), description="Nur die [iQ]-Leader dürfen den Aktivitätsstatus ändern."))

            if player_data is not None:
                if player_data is False:
                    await context.message.channel.send(embed=discord.Embed(color=discord.Color.red(), description="Der angegebene Member ist nicht in der Memberliste eingetragen."))
                else:
                    player = Player.Player(id=player_data[0]['id'])
                    await player.fill_object_from_db()
                    query = await self.db_connection.alterActivityOfPlayer(player.id, not player.active)
                    if query:
                        await context.message.channel.send(embed=discord.Embed(color=discord.Color.green(), description="Der Aktivitätsstatus von " + player.discord_user_object.mention + " wurde erfolgreich auf `" + str(not player.active) + "` geändert."))
                    else:
                        admin_user = self.bot.get_user(self.config.admin_id)
                        await context.message.channel.send(embed=discord.Embed(color=discord.Color.red(), description="Ein Fehler ist aufgetreten. Wende dich eventuell an " + admin_user.mention + "."))

        @schuld.group()
        async def confirm(context):
            """Confirm proposed guilty member(s) and guilty reasons. (Can only be used by Leaders of [iQ].)"""
            pass

        @confirm.command()
        async def user(context, *guilty_members):
            """Confirm proposed guilty member(s)."""
            if self.config.iq_leaders_id.__contains__(context.message.author.id):
                now = datetime.datetime.now()
                iso_date = datetime.date(now.year, now.month, now.day).isocalendar()
                if not await self.db_connection.isWeekFinalized(str(iso_date[0]), str(iso_date[1])):
                    new_guilty_players = []

                    for mentioned_member in context.message.mentions:
                        player = Player.Player(discord_user_id=mentioned_member.id)
                        await player.fill_object_from_db()
                        new_guilty_players.append(player)

                    context_skipped = False
                    for written_member in context.args:
                        if context_skipped is False:  # First element in context.args is context, so just skip over first element of for loop
                            context_skipped = True
                        else:
                            if written_member[0:2] == "<@" and written_member[-1:] == ">":
                                pass
                            else:
                                player_data = await self.db_connection.getPlayerData(name=written_member)
                                if player_data is not False:
                                    player = Player.Player(name=player_data[0]['name'])
                                    await player.fill_object_from_db()
                                    new_guilty_players.append(player)
                                else:
                                    await context.message.channel.send(embed=discord.Embed(color=discord.Color.red(), description="Es wurde kein Member mit dem Namen `" + written_member + "` in der Memberliste gefunden."))


                    for new_guilty_player in new_guilty_players:
                        if await self.db_connection.isUserEnteredInWeek(str(iso_date[0]), str(iso_date[1]), new_guilty_player.id):
                            data = await self.db_connection.alterConfirmationToTrueForUserInWeek(str(iso_date[0]), str(iso_date[1]), new_guilty_player.id)
                            await context.message.channel.send("`" + data + "`", embed=await self.get_guilty_embed(iso_date[0], iso_date[1], None))
                        else:
                            await context.message.channel.send(embed=discord.Embed(color=discord.Color.red(), description="**" + new_guilty_player.name + "** wurde von niemandem eingetragen!"))
                else:
                    await context.message.channel.send(embed=discord.Embed(color=discord.Color.red(), description="Diese Woche wurde schon abgeschlossen!"))
            else:
                await context.message.channel.send(embed=discord.Embed(color=discord.Color.red(), description="Nur die [iQ]-Leader dürfen diesen Befehl benutzen!"))

        @confirm.command()
        async def grund(context, reason_owner_member: str):
            """Confirm proposed guilty reason."""
            if self.config.iq_leaders_id.__contains__(context.message.author.id):
                now = datetime.datetime.now()
                iso_date = datetime.date(now.year, now.month, now.day).isocalendar()
                if not await self.db_connection.isWeekFinalized(str(iso_date[0]), str(iso_date[1])):
                    owner_player = None
                    get_written_player = True

                    if len(context.message.mentions) > 1:
                        await context.message.channel.send(embed=discord.Embed(color=discord.Color.red(), description="Es kann nur ein Grund eingetragen werden!"))
                        get_written_player = False
                    elif len(context.message.mentions) == 1:
                        get_written_player = False
                        for mentioned_member in context.message.mentions:
                            player = Player.Player(discord_user_id=mentioned_member.id)
                            await player.fill_object_from_db()
                            owner_player = player

                    if get_written_player:
                        player_data = await self.db_connection.getPlayerData(name=reason_owner_member)
                        if player_data is not False:
                            player = Player.Player(name=player_data[0]['name'])
                            await player.fill_object_from_db()
                            owner_player = player
                        else:
                            await context.message.channel.send(embed=discord.Embed(color=discord.Color.red(), description="Es wurde kein Member mit dem Namen `" + written_member + "` in der Memberliste gefunden."))

                    if owner_player is not None:
                        if await self.db_connection.hasUserEnteredReasonInWeek(str(iso_date[0]), str(iso_date[1]), owner_player.id):
                            data = await self.db_connection.alterConfirmationToTrueForReasonFromUserInWeek(str(iso_date[0]), str(iso_date[1]), owner_player.id)
                            await context.message.channel.send("`" + data + "`", embed=await self.get_guilty_embed(iso_date[0], iso_date[1], None))
                        else:
                            await context.message.channel.send(embed=discord.Embed(color=discord.Color.red(), description="**" + owner_player.name + "** hat in dieser Woche keine Begründung eingetragen!"))
                else:
                    await context.message.channel.send(embed=discord.Embed(color=discord.Color.red(), description="Diese Woche wurde schon abgeschlossen!"))
            else:
                await context.message.channel.send(embed=discord.Embed(color=discord.Color.red(), description="Nur die [iQ]-Leader dürfen diesen Befehl benutzen!"))

        @schuld.group()
        async def reject(context):
            """Reject proposed guilty member(s) and guilty reasons. (Can only be used by Leaders of [iQ].)"""
            pass

        @reject.command()
        async def user(context, *guilty_member):
            """Reject proposed guilty member(s)."""
            if self.config.iq_leaders_id.__contains__(context.message.author.id):
                now = datetime.datetime.now()
                iso_date = datetime.date(now.year, now.month, now.day).isocalendar()
                if not await self.db_connection.isWeekFinalized(str(iso_date[0]), str(iso_date[1])):
                    rejected_guilty_players = []

                    for mentioned_member in context.message.mentions:
                        player = Player.Player(discord_user_id=mentioned_member.id)
                        await player.fill_object_from_db()
                        rejected_guilty_players.append(player)

                    context_skipped = False
                    for written_member in context.args:
                        if context_skipped is False:  # First element in context.args is context, so just skip over first element of for loop
                            context_skipped = True
                        else:
                            if written_member[0:2] == "<@" and written_member[-1:] == ">":
                                pass
                            else:
                                player_data = await self.db_connection.getPlayerData(name=written_member)
                                if player_data is not False:
                                    player = Player.Player(name=player_data[0]['name'])
                                    await player.fill_object_from_db()
                                    rejected_guilty_players.append(player)
                                else:
                                    await context.message.channel.send(embed=discord.Embed(color=discord.Color.red(), description="Es wurde kein Member mit dem Namen `" + written_member + "` in der Memberliste gefunden."))


                    for rejected_guilty_player in rejected_guilty_players:
                        if await self.db_connection.isUserEnteredInWeek(str(iso_date[0]), str(iso_date[1]), rejected_guilty_player.id):
                            data = await self.db_connection.alterRejectionToTrueForUserInWeek(str(iso_date[0]), str(iso_date[1]), rejected_guilty_player.id)
                            await context.message.channel.send("`" + data + "`", embed=await self.get_guilty_embed(iso_date[0], iso_date[1], None))
                        else:
                            await context.message.channel.send(embed=discord.Embed(color=discord.Color.red(), description="**" + rejected_guilty_player.name + "** wurde von niemandem eingetragen!"))
                else:
                    await context.message.channel.send(embed=discord.Embed(color=discord.Color.red(), description="Diese Woche wurde schon abgeschlossen!"))
            else:
                await context.message.channel.send(embed=discord.Embed(color=discord.Color.red(), description="Nur die [iQ]-Leader dürfen diesen Befehl benutzen!"))

        @reject.command()
        async def grund(context, reason_owner_member: str):
            """Reject proposed guilty reason."""
            if self.config.iq_leaders_id.__contains__(context.message.author.id):
                now = datetime.datetime.now()
                iso_date = datetime.date(now.year, now.month, now.day).isocalendar()
                if not await self.db_connection.isWeekFinalized(str(iso_date[0]), str(iso_date[1])):
                    owner_players = []
                    get_written_player = True

                    if len(context.message.mentions) >= 1:
                        get_written_player = False
                        for mentioned_member in context.message.mentions:
                            player = Player.Player(discord_user_id=mentioned_member.id)
                            await player.fill_object_from_db()
                            owner_players.append(player)

                    if get_written_player:
                        player_data = await self.db_connection.getPlayerData(name=reason_owner_member)
                        if player_data is not False:
                            player = Player.Player(name=player_data[0]['name'])
                            await player.fill_object_from_db()
                            owner_players.append(player)
                        else:
                            await context.message.channel.send(embed=discord.Embed(color=discord.Color.red(), description="Es wurde kein Member mit dem Namen `" + written_member + "` in der Memberliste gefunden."))

                    if len(owner_players) >= 1:
                        for owner_player in owner_players:
                            if await self.db_connection.hasUserEnteredReasonInWeek(str(iso_date[0]), str(iso_date[1]), owner_player.id):
                                data = await self.db_connection.alterRejectionToTrueForReasonFromUserInWeek(str(iso_date[0]), str(iso_date[1]), owner_player.id)
                                await context.message.channel.send("`" + data + "`", embed=await self.get_guilty_embed(iso_date[0], iso_date[1], None))
                            else:
                                await context.message.channel.send(embed=discord.Embed(color=discord.Color.red(), description="**" + owner_player.name + "** hat in dieser Woche keine Begründung eingetragen!"))
                else:
                    await context.message.channel.send(embed=discord.Embed(color=discord.Color.red(), description="Diese Woche wurde schon abgeschlossen!"))
            else:
                await context.message.channel.send(embed=discord.Embed(color=discord.Color.red(), description="Nur die [iQ]-Leader dürfen diesen Befehl benutzen!"))

        @confirm.command()
        async def final(context):
            """Finalize the current week. Guilty members and reasons will be locked."""
            if self.config.iq_leaders_id.__contains__(context.message.author.id):
                now = datetime.datetime.now()
                iso_date = datetime.date(now.year, now.month, now.day).isocalendar()
                if await self.db_connection.isOneUserAcceptedInWeek(str(iso_date[0]), str(iso_date[1])) and await self.db_connection.isOneReasonAcceptedInWeek(str(iso_date[0]), str(iso_date[1])):
                    if not await self.db_connection.isWeekFinalized(str(iso_date[0]), str(iso_date[1])):
                        data = await self.db_connection.insertFinalizedWeek(str(iso_date[0]), str(iso_date[1]))
                        await context.message.channel.send("`" + data + "`", embed=await self.get_guilty_embed(iso_date[0], iso_date[1], None))
                        await self.refresh_guilty_members()
                        await self.send_guilty_message_to_guilty_channel()
                    else:
                        await context.message.channel.send(embed=discord.Embed(color=discord.Color.red(), description="Diese Woche wurde schon abgeschlossen!"))
                else:
                    await context.message.channel.send(embed=discord.Embed(color=discord.Color.red(), description="Es wurden in dieser Woche noch keine Benutzer oder Begründungen akzeptiert!"))
            else:
                await context.message.channel.send(embed=discord.Embed(color=discord.Color.red(), description="Nur die [iQ]-Leader können diesen Befehl benutzen!"))

        # TODO: Add logout and/or closing of connections to discord, db and other stuff. Somehow end coroutines?
        self.bot.run(self.config.token)