import discord
import time
import datetime
import os
import asyncio
import asyncpg

from classes import DBConnect
from classes import Config

from discord.ext import commands

from auto_commands import cmd_on_member_join


class Bot:


    config = Config.Config()

    bot = commands.Bot(command_prefix=config.prefix)
    voice = None
    player = None
    db_connection = None

    current_week = None

    message4 = None
    message3 = None
    message2 = None
    message1 = None


    async def print_servers(self):
        print("Bot is ready. Running on Servers: \n")
        for server in self.bot.servers:
            print("  - %s (%s)" % (server.name, server.id))
        print("\n-----------------------------------------------")

    async def set_presence(self, string):
        await self.bot.change_presence(game=discord.Game(name=string))

    def is_admin(self, user_id: str):
        if user_id == self.config.admin_id:
            return True
        else:
            return False

    async def get_faulty_server(self):
        return discord.utils.get(self.bot.connection.servers, id=self.config.faulty_member_server_id)


    async def assign_role_safe(self, member_on_server, role_on_server):
        role_assigned = False
        while not role_assigned:
            print("processing assign_role_safe - while")
            await self.bot.add_roles(member_on_server, role_on_server)
            await asyncio.sleep(1)
            for role in member_on_server.roles:
                if role.id == role_on_server.id:
                    role_assigned = True
                    break

    async def remove_role_safe(self, member_on_server, role_on_server):
        role_removed = False
        while not role_removed:
            print("processing remove_role_safe - while")
            await self.bot.remove_roles(member_on_server, role_on_server)
            await asyncio.sleep(1)
            for role in member_on_server.roles:
                removed = True
                if role.id == role_on_server.id:
                    removed = False
                if removed:
                    role_removed = True


    async def get_faulty_members(self):
        faulty_server = await self.get_faulty_server()

        faulty_members = []
        for member in faulty_server.members:
            for role in member.roles:
                if role.id == self.config.faulty_member_role_id:
                    faulty_members.append(member)
        return faulty_members

    async def get_old_faulty_members(self):
        faulty_server = await self.get_faulty_server()

        old_faulty_members = []
        for member in faulty_server.members:
            for role in member.roles:
                if role.id == self.config.old_faulty_member_role_id:
                    old_faulty_members.append(member)
        return old_faulty_members

    async def get_faulty_embed(self, year, week, user_id):
        year = str(year)
        week = str(week)
        faulty_server = self.get_faulty_server()

        faulty_member_list_string = ""
        if user_id is not None:
            faulty_member_data = await self.db_connection.getAWeeksFaultyUsersFromUser(year, week, user_id)
        else:
            faulty_member_data = await self.db_connection.getAWeeksFaultyUsers(year, week)
        for index, row in enumerate(faulty_member_data):
            prefix = " "
            if row[3]:
                prefix = "+"
            user = discord.utils.get(faulty_server.members, id=row[1])

            faulty_member_list_string += "\n" + prefix + " " + user.name

            if user_id is None:
                owner = discord.utils.get(faulty_server.members, id=row[4])
                faulty_member_list_string += "  ⬅️" + owner.name

        faulty_reason_list_string = ""
        if user_id is not None:
            faulty_reason_data = await self.db_connection.getAWeeksFaultyReasonsFromUser(year, week, user_id)
        else:
            faulty_reason_data = await self.db_connection.getAWeeksFaultyReasons(year, week)
        for index, row in enumerate(faulty_reason_data):
            prefix = " "
            if row[3]:
                prefix = "+"

            faulty_reason_list_string += "\n" + prefix + " " + row[1]

            if user_id is None:
                owner = discord.utils.get(faulty_server.members, id=row[4])
                faulty_reason_list_string += "  ⬅️" + owner.name


        embed_description = "Einträge müssen von den Leadern bestätigt werden, danach werden sie grün."

        if user_id is None:
            field_reasons_title = "Gründe:"
        else:
            field_reasons_title = "Grund:"


        if faulty_member_list_string == "":
            faulty_member_list_string = "\nKEINE SCHULDIGEN EINGETRAGEN"
        if faulty_reason_list_string == "":
            faulty_reason_list_string = "\nKEINE SCHULDGRÜNDE EINGETRAGEN"

        embed = discord.Embed(title="Das Schuldspiel", description=embed_description, color=0xFFCC00)
        embed.add_field(name="Schuldige:", value="```diff" + faulty_member_list_string + "```", inline=True)
        embed.add_field(name=field_reasons_title, value="```diff" + faulty_reason_list_string + "```", inline=True)

        return embed


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
        next_weekday_date = datetime.datetime(now.year, now.month, now.day, 0, 0, 1, 0) + datetime.timedelta(days=offset_days)
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


    async def set_current_faulty_members_to_old_faulty_members(self):
        faulty_members = await self.get_faulty_members()
        faulty_server = await self.get_faulty_server()

        if faulty_server is not None:
            old_faulty_member_role = discord.utils.get(faulty_server.roles, id=self.config.old_faulty_member_role_id)
            faulty_member_role = discord.utils.get(faulty_server.roles, id=self.config.faulty_member_role_id)
            for faulty_member in faulty_members:
                await self.assign_role_safe(faulty_member, old_faulty_member_role)
                await self.remove_role_safe(faulty_member, faulty_member_role)

    async def send_fault_message_to_old_faulty_members(self):
        old_faulty_members = await self.get_old_faulty_members()

        for old_faulty_member in old_faulty_members:
            print(old_faulty_member.name)
            await self.bot.send_message(old_faulty_member, "**Hurra, deine Schuldwoche ist vorbei!**\n\nDu kannst ab jetzt mit `" + self.config.prefix + "schuld ist \"<Username>\" ` den nächsten Schuldigen auswählen und anschließend mit `" + self.config.prefix + "schuld grund \"<Deine Begründung>\"` eine Begründung für seine Schuld angeben.\nAber pass auf, wenn du keinen Schuldigen auswählst, bist du wieder Schuld!\n\n**Beispiel**:\n`" + self.config.prefix + "schuld ist \"" + old_faulty_member.name + "\"`\n`" + self.config.prefix + "schuld grund \"" + old_faulty_member.name + " ist schuld, weil er/sie einfach zu langsam ist.\"`")  # TODO: add multiple random reasons

    async def monday_fault_event(self):
        await self.wait_until_next_week()

        await self.set_current_faulty_members_to_old_faulty_members()
        await self.send_fault_message_to_old_faulty_members()

        asyncio.ensure_future(await self.monday_fault_event())

    async def wednesday_fault_event(self):
        if not datetime.datetime.now().weekday == 2:
            await self.wait_until_weekday(2)
        else:
            await self.wait_until_hour(20)


    def __init__(self):

        @self.bot.event
        async def on_ready():
            await self.print_servers()
            await self.set_presence("nichts. I'm serious.")

            self.db_connection = DBConnect.DBConnect()
            await self.db_connection.setUp()
            await self.wait_until_next_minute()
            # await asyncio.ensure_future(self.wait_until_full_hour())
            # await self.send_fault_message_to_old_faulty_members()

        @self.bot.event
        async def on_member_join(member):
            pass
            # await cmd_on_member_join.ex(self.bot, member)

        @self.bot.event
        async def on_message(message):

            # in order to process the other command events
            await self.bot.process_commands(message)

            # custom ping/pong command, because bot checks if the message comes from a bot if used with a normal command
            if message.content == "!ping":
                if self.config.ping_pong_loop == 1:
                    await self.bot.send_message(message.channel, "!pong")
                else:
                    await self.bot.send_message(message.channel, "pong!")
            if message.content == "!pong":
                if self.config.ping_pong_loop == 1:
                    await self.bot.send_message(message.channel, "!ping")
                else:
                    await self.bot.send_message(message.channel, "ping!")

            # custom function to repeat a message if it was sent 4 times TODO: check if each message is of an individual person
            self.message4 = self.message3
            self.message3 = self.message2
            self.message2 = self.message1
            self.message1 = message
            if self.message4 is not None:
                if self.message1.author.id != self.config.bot_id and self.message2.author.id != self.config.bot_id and self.message3.author.id != self.config.bot_id and self.message4.author.id != self.config.bot_id:
                    if self.message1.content == self.message4.content:
                        if self.message1.content == self.message3.content:
                            if self.message1.content == self.message2.content:
                                await self.bot.send_message(message.channel, self.message1.content)

            # custom function to react to any user why writes " owo " anywhere
            if message.content.lower().__contains__("owo"):
                if message.author.id != self.config.bot_id:
                    await self.bot.send_message(message.channel, "***triggered***")

        @self.bot.command(pass_context=True)
        async def join(context):
            """Bot will join your voice channel."""
            self.voice = await self.bot.join_voice_channel(context.message.author.voice_channel)

        @self.bot.command()
        async def leave():
            """Bot will leave your voice channel."""
            await self.voice.disconnect()
            self.voice = None

        @self.bot.command(pass_context=True)
        async def airhorn(context):
            """Bot will play an airhorn sound in your channel. Just like good old !airhorn did."""
            self.voice = await self.bot.join_voice_channel(context.message.author.voice_channel)
            self.player = self.voice.create_ffmpeg_player('./sounds/airhorns/airhorn.m4a')
            self.player.start()
            if self.config.airhorn_stay_afterwards == 0:
                time.sleep(2)
                await self.voice.disconnect()

        @self.bot.group(pass_context=True)
        async def admin(context):
            """Admin commands, you need to be the owner to execute any of these."""
            admin_user = await self.bot.get_user_info(self.config.admin_id)
            if not self.is_admin(context.message.author.id):
                await self.bot.send_message(context.message.channel, embed=discord.Embed(color=discord.Color.red(), description="You are not " + admin_user.name + ", sorry!"))
            else:
                if context.invoked_subcommand is None:
                    await self.bot.say('admin: no currect subcommand: ' + context.message.content)

        @admin.command(pass_context=True)
        async def toggle(context, variable: str):
            """Toggle any of the on/off attributes of this bot."""
            if self.is_admin(context.message.author.id):
                if hasattr(self.config, variable):
                    if getattr(self.config, variable) == 0:
                        setattr(self.config, variable, 1)
                        await self.bot.say(embed=discord.Embed(color=discord.Color.green(), description="**`" + variable + "`** set to **`" + str(getattr(self.config, variable)) + "`**."))
                    elif getattr(self.config, variable) == 1:
                        setattr(self.config, variable, 0)
                        await self.bot.say(embed=discord.Embed(color=discord.Color.green(), description="**`" + variable + "`** set to **`" + str(getattr(self.config, variable)) + "`**."))
                    else:
                        await self.bot.say(embed=discord.Embed(color=discord.Color.red(), description="**`" + variable + "`** is not toggleable, as it is not `0` or `1`!"))
                else:
                    await self.bot.say(embed=discord.Embed(color=discord.Color.red(), description="There is no variable called **`" + variable + "`**!"))

        @admin.command(pass_context=True)
        async def say(context, channel, text: str):
            """Bot repeats what you write in any other channel on this server."""
            if self.is_admin(context.message.author.id):
                channel = discord.utils.get(context.message.server.channels, name=channel)
                await self.bot.send_message(channel, text)

        @self.bot.group()
        async def schuld():
            """Contains all commands to show or select who's responsible for this weeks fails."""
            pass

        @schuld.command()
        async def liste():
            """Used to show the list of proposed and confirmed members that are responsible for this weeks fails."""
            now = datetime.datetime.now()
            iso_date = datetime.date(now.year, now.month, now.day).isocalendar()
            await self.bot.say(embed=await self.get_faulty_embed(iso_date[0], iso_date[1], None))

        @schuld.command(pass_context=True)
        async def ist(context, new_faulty_user_name: str):
            """Used to select the next [iQ] Member, which is responsible for this weeks fails."""
            faulty_server = self.get_faulty_server()
            old_faulty_user_on_server = discord.utils.get(faulty_server.members, id=context.message.author.id)

            if len(context.message.mentions) > 0:
                new_faulty_users_on_server = context.message.mentions
            else:
                new_faulty_users_on_server = discord.utils.get(faulty_server.members, name=new_faulty_user_name)


            is_faulty_user = False
            for role in old_faulty_user_on_server.roles:
                if role.id == self.config.old_faulty_member_role_id:
                    is_faulty_user = True
                    break
            if is_faulty_user:
                if new_faulty_users_on_server is not None:
                    contains_self = False
                    for new_faulty_user in new_faulty_users_on_server:
                        if new_faulty_user.id == old_faulty_user_on_server.id:
                            await self.bot.say("Ey, Du kannst dir nicht selber die Schuld geben!")
                            contains_self = True
                            break
                    if not contains_self:
                        now = datetime.datetime.now()
                        iso_date = datetime.date(now.year, now.month, now.day).isocalendar()
                        for new_faulty_user in new_faulty_users_on_server:
                            if not await self.db_connection.isUserEnteredFromUserInWeek(str(iso_date[0]), str(iso_date[1]), old_faulty_user_on_server.id, new_faulty_user.id):
                                await self.db_connection.insertFaultyUser(str(iso_date[0]), str(iso_date[1]), old_faulty_user_on_server.id, new_faulty_user.id)
                            else:
                                await self.bot.say("Du hast **" + new_faulty_users_on_server.name + "** schon eingetragen!")
                        faulty_embed = await self.get_faulty_embed(str(iso_date[0]), str(iso_date[1]), old_faulty_user_on_server.id)
                        await self.bot.say("Du hast **" + str(len(new_faulty_users_on_server)) + "** Member in die Schuldnerliste eingetragen.\n", embed=faulty_embed)
                else:
                    await self.bot.say("Die ausgewählten Schuldigen sind nicht auf unserem Server oder du hast sie falsch angegeben :(")
            else:
                await self.bot.say("Ey, Ich höre nur auf den Schuldigen von letzter Woche!")

        @schuld.command(pass_context=True)
        async def grund(context, faulty_reason: str):
            """Used to give the reason for why the selected [iQ] Member is responsible for this weeks fails"""
            faulty_server = discord.utils.get(self.bot.servers, id=self.config.faulty_member_server_id)

            old_faulty_user_on_server = discord.utils.get(faulty_server.members, id=context.message.author.id)

            is_faulty_user = False
            for role in old_faulty_user_on_server.roles:
                if role.id == self.config.old_faulty_member_role_id:
                    is_faulty_user = True
                    break
            if is_faulty_user:
                now = datetime.datetime.now()
                iso_date = datetime.date(now.year, now.month, now.day).isocalendar()
                if not await self.db_connection.userEnteredReasonInWeek(str(iso_date[0]), str(iso_date[1]), old_faulty_user_on_server.id):
                    await self.db_connection.insertFaultyReason(str(iso_date[0]), str(iso_date[1]), old_faulty_user_on_server.id, faulty_reason)

                    faulty_embed = await self.get_faulty_embed(str(iso_date[0]), str(iso_date[1]), old_faulty_user_on_server.id)
                    await self.bot.say("Du hast folgendes als Schuldgrund für diese Woche eingetragen:\n```" + faulty_reason + "```", embed=faulty_embed)
                else:
                    await self.db_connection.alterReasonFromUserInWeek(str(iso_date[0]), str(iso_date[1]), old_faulty_user_on_server.id, faulty_reason)

                    faulty_embed = await self.get_faulty_embed(str(iso_date[0]), str(iso_date[1]), old_faulty_user_on_server.id)
                    await self.bot.say("Dein eingetragener Schuldgrund wurde aktualisiert:\n```" + faulty_reason + "```", embed=faulty_embed)
            else:
                await self.bot.say("Ey, Ich höre nur auf den Schuldigen von letzter Woche!")

        @schuld.group()
        async def confirm():
            """Used by [iQ]'s Leaders to confirm proposed responsible members of the current week."""
            pass

        @confirm.command(pass_context=True)
        async def user(context, new_faulty_user_name: str):
            """Confirm the proposed responsible member of a specific user for the current week."""
            faulty_server = discord.utils.get(self.bot.servers, id=self.config.faulty_member_server_id)

            iq_admin = discord.utils.get(faulty_server.members, id=context.message.author.id)
            new_faulty_user_on_server = discord.utils.get(faulty_server.members, name=new_faulty_user_name)

            if self.config.iq_leaders_id.__contains__(iq_admin.id):
                now = datetime.datetime.now()
                iso_date = datetime.date(now.year, now.month, now.day).isocalendar()
                if await self.db_connection.isUserEnteredInWeek(str(iso_date[0]), str(iso_date[1]), new_faulty_user_on_server.id):
                    data = await self.db_connection.alterConfirmationForUserInWeek(str(iso_date[0]), str(iso_date[1]), new_faulty_user_on_server.id)
                    await self.bot.say(data, embed=await self.get_faulty_embed(iso_date[0], iso_date[1], None))
                else:
                    await self.bot.say("**" + new_faulty_user_on_server.name + "** wurde von niemandem eingetragen!")
            else:
                await self.bot.say("Nur die [iQ]-Leader können diesen Befehl benutzen!")

        @confirm.command(pass_context=True)
        async def grund(context, owner_user_name: str):
            """Confirm the proposed reason of a specific user for the current week."""
            faulty_server = discord.utils.get(self.bot.servers, id=self.config.faulty_member_server_id)

            iq_admin = discord.utils.get(faulty_server.members, id=context.message.author.id)
            owner_user_on_server = discord.utils.get(faulty_server.members, name=owner_user_name)

            if self.config.iq_leaders_id.__contains__(iq_admin.id):
                now = datetime.datetime.now()
                iso_date = datetime.date(now.year, now.month, now.day).isocalendar()
                if await self.db_connection.userEnteredReasonInWeek(str(iso_date[0]), str(iso_date[1]), owner_user_on_server.id):
                    data = await self.db_connection.alterConfirmationForReasonFromUserInWeek(str(iso_date[0]), str(iso_date[1]), owner_user_on_server.id)
                    await self.bot.say(data, embed=await self.get_faulty_embed(iso_date[0], iso_date[1], None))
                else:
                    await self.bot.say("**" + owner_user_on_server.name + "** hat in dieser Woche keine Begründung eingetragen!")
            else:
                await self.bot.say("Nur die [iQ]-Leader können diesen Befehl benutzen!")

        self.bot.run(self.config.token)
