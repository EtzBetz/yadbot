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


    async def print_guilds(self):
        print("Bot is ready. Running on Guilds: \n")
        for guild in self.bot.guilds:
            print("  - %s (%s)" % (guild.name, guild.id))
        print("\n-----------------------------------------------")

    async def set_presence(self, string):
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


    async def get_faulty_guild(self):
        return discord.utils.get(self.bot.guilds, id=self.config.faulty_member_guild_id)

    async def get_commands_channel(self):
        return discord.utils.get((await self.get_faulty_guild()).channels, id=self.config.faulty_commands_channel_id)

    async def get_faulty_members(self):
        faulty_guild = await self.get_faulty_guild()

        faulty_members = []
        for member in faulty_guild.members:
            for role in member.roles:
                if role.id == self.config.faulty_member_role_id:
                    faulty_members.append(member)
        return faulty_members

    async def get_old_faulty_members(self):
        faulty_guild = await self.get_faulty_guild()

        old_faulty_members = []
        for member in faulty_guild.members:
            for role in member.roles:
                if role.id == self.config.old_faulty_member_role_id:
                    old_faulty_members.append(member)
        return old_faulty_members

    async def get_faulty_embed(self, year, week, user_id):
        year = str(year)
        week = str(week)
        faulty_guild = await self.get_faulty_guild()

        faulty_member_list_string = ""
        if user_id is not None:
            faulty_member_data = await self.db_connection.getAWeeksFaultyUsersFromUser(year, week, user_id)
        else:
            faulty_member_data = await self.db_connection.getAWeeksFaultyUsers(year, week)
        for index, row in enumerate(faulty_member_data):
            prefix = " "
            if row[3]:
                prefix = "+"
            user = discord.utils.get(faulty_guild.members, id=row[1])

            faulty_member_list_string += "\n" + prefix + user.name

            if user_id is None:
                owner = discord.utils.get(faulty_guild.members, id=row[4])
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

            faulty_reason_list_string += "\n" + prefix + row[1]

            if user_id is None:
                owner = discord.utils.get(faulty_guild.members, id=row[4])
                faulty_reason_list_string += "  ⬅️" + owner.name


        embed_description = "Einträge müssen von den Leadern bestätigt werden, danach werden sie grün."

        if user_id is None:
            field_reasons_title = "Gründe:"
        else:
            field_reasons_title = "Grund:"


        if faulty_member_list_string == "":
            faulty_member_list_string = "\n KEINE SCHULDIGEN EINGETRAGEN"
        if faulty_reason_list_string == "":
            faulty_reason_list_string = "\n KEINE SCHULDGRÜNDE EINGETRAGEN"

        embed = discord.Embed(title="Das Schuldspiel, Woche " + week, description=embed_description, color=0xFFCC00)
        embed.add_field(name="Schuldige:", value="```diff" + faulty_member_list_string + "```", inline=False)
        embed.add_field(name=field_reasons_title, value="```diff" + faulty_reason_list_string + "```", inline=False)
        if await self.db_connection.isWeekFinalized(year, week):
            embed.set_footer(text="Die Schuldigen wurden für diese Woche festgelegt.")

        return embed


    async def emoji_mention(self, guild_id: int, emoji, reference_type="id"):
        guild = await self.get_faulty_guild()
        if reference_type == "id":
            emoji = discord.utils.get(guild.emojis, id=emoji)
        elif reference_type == "name":
            emoji = discord.utils.get(guild.emojis, name=emoji)
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


    async def remove_old_faulty_members(self):
        old_faulty_members = await self.get_old_faulty_members()
        faulty_guild = await self.get_faulty_guild()

        if faulty_guild is not None:
            old_faulty_member_role = discord.utils.get(faulty_guild.roles, id=self.config.old_faulty_member_role_id)
            for old_faulty_member in old_faulty_members:
                await self.remove_role_safe(old_faulty_member, old_faulty_member_role)

    async def set_current_faulty_members_to_old_faulty_members(self):
        faulty_members = await self.get_faulty_members()
        faulty_guild = await self.get_faulty_guild()

        if faulty_guild is not None:
            old_faulty_member_role = discord.utils.get(faulty_guild.roles, id=self.config.old_faulty_member_role_id)
            faulty_member_role = discord.utils.get(faulty_guild.roles, id=self.config.faulty_member_role_id)
            for faulty_member in faulty_members:
                await self.assign_role_safe(faulty_member, old_faulty_member_role)
                await self.remove_role_safe(faulty_member, faulty_member_role)

    async def send_fault_message_to_old_faulty_members(self):
        old_faulty_members = await self.get_old_faulty_members()

        for old_faulty_member in old_faulty_members:
            print(old_faulty_member.name)
            await old_faulty_member.send("**Hurra, deine Schuldwoche ist vorbei!**\n"
                                            "\n"
                                            "Du kannst ab jetzt mit `" + self.config.prefix + "schuld ist \"Nutzername\" ` oder in " + (await self.get_commands_channel()).mention + " mit `" + self.config.prefix + "schuld ist @Nutzername` den nächsten Schuldigen auswählen.\n"
                                            "Anschließend musst du noch mit `" + self.config.prefix + "schuld grund \"Deine Begründung\"` eine Begründung für seine Schuld angeben.\n"
                                            "Aber pass auf, wenn du nicht rechtzeitig einen Schuldigen auswählst, bist du wieder Schuld!\n"
                                            "\n"
                                            "**Beispiel**:\n"
                                            "`" + self.config.prefix + "schuld ist \"" + old_faulty_member.name + "\"` **(hier)**\n"
                                            "`" + self.config.prefix + "schuld ist ` " + old_faulty_member.mention + "  **(in " + (await self.get_commands_channel()).mention + ")**\n"
                                            "`" + self.config.prefix + "schuld grund \"" + old_faulty_member.name + " ist schuld, weil er/sie einfach zu langsam ist.\"`")  # TODO: add multiple random reasons

    async def send_reminder_message_to_old_faulty_members(self):
        old_faulty_members = await self.get_old_faulty_members()

        for old_faulty_member in old_faulty_members:
            print(old_faulty_member.name)
            await old_faulty_member.send("Hier ist eine freundliche Erinnerung, dass du noch einen Schuldigen festlegen musst. " + await self.emoji_mention(self.config.faulty_member_guild_id, "quagganthinking", "name"))


    async def new_week_fault_event(self):
        await self.wait_until_next_week()

        await self.remove_old_faulty_members()
        await self.set_current_faulty_members_to_old_faulty_members()
        await self.send_fault_message_to_old_faulty_members()

        asyncio.create_task(await self.new_week_fault_event())

    async def monday_reminder(self):
        now = datetime.datetime.now()
        iso_date = datetime.date(now.year, now.month, now.day).isocalendar()

        if not datetime.datetime.now().weekday == 0:
            await self.wait_until_weekday(0)
        await self.wait_until_hour(19)

        if not self.db_connection.isWeekFinalized(iso_date[0], iso_date[1]):
            await self.send_reminder_message_to_old_faulty_members()

    async def tuesday_reminder(self):
        now = datetime.datetime.now()
        iso_date = datetime.date(now.year, now.month, now.day).isocalendar()

        if not datetime.datetime.now().weekday == 1:
            await self.wait_until_weekday(1)
        await self.wait_until_hour(19)

        if not self.db_connection.isWeekFinalized(iso_date[0], iso_date[1]):
            await self.send_reminder_message_to_old_faulty_members()

    async def wednesday_fault_event(self):
        if not datetime.datetime.now().weekday == 2:
            await self.wait_until_weekday(2)
        await self.wait_until_hour(20)


    async def enable_timers(self):
        print("debug: enable timers")
        asyncio.create_task(await self.new_week_fault_event())
        asyncio.create_task(await self.monday_reminder())
        asyncio.create_task(await self.tuesday_reminder())
        asyncio.create_task(await self.wednesday_fault_event())


    def __init__(self):

        @self.bot.event
        async def on_ready():
            await self.print_guilds()
            await self.set_presence("nichts. I'm serious.")

            self.db_connection = DBConnect.DBConnect()
            await self.db_connection.setUp()

            await asyncio.create_task(await self.enable_timers())

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
                    await message.channel.send("!pong")
                else:
                    await message.channel.send("pong!")
            if message.content == "!pong":
                if self.config.ping_pong_loop == 1:
                    await message.channel.send("!ping")
                else:
                    await message.channel.send("ping!")

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
                                await message.channel.send(self.message1.content)

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

        @self.bot.group()
        async def schuld(context):
            """Contains all commands to show or select who's responsible for this weeks fails."""
            pass

        @schuld.command()
        async def liste(context):
            """Used to show the list of proposed and confirmed members that are responsible for this weeks fails."""
            now = datetime.datetime.now()
            iso_date = datetime.date(now.year, now.month, now.day).isocalendar()
            await context.message.channel.send(embed=await self.get_faulty_embed(iso_date[0], iso_date[1], None))

        @schuld.command()
        async def ist(context, new_faulty_user_name: str):
            """Used to select the next [iQ] Member, which is responsible for this weeks fails."""
            faulty_guild = await self.get_faulty_guild()
            old_faulty_user_in_guild = discord.utils.get(faulty_guild.members, id=context.message.author.id)

            if len(context.message.mentions) > 0:
                new_faulty_user_s_in_guild = context.message.mentions
            else:
                new_faulty_user_s_in_guild = discord.utils.get(faulty_guild.members, name=new_faulty_user_name)

            is_faulty_user = False
            for role in old_faulty_user_in_guild.roles:
                if role.id == self.config.old_faulty_member_role_id:
                    is_faulty_user = True
                    break
            if is_faulty_user:
                if new_faulty_user_s_in_guild is not None:
                    contains_self = False
                    if len(context.message.mentions) > 0:
                        for new_faulty_user in new_faulty_user_s_in_guild:
                            if new_faulty_user.id == old_faulty_user_in_guild.id:
                                await context.message.channel.send("Ey, Du kannst dir nicht selber die Schuld geben!")
                                contains_self = True
                                break
                    else:
                        if new_faulty_user_s_in_guild.id == old_faulty_user_in_guild.id:
                            await context.message.channel.send("Ey, Du kannst dir nicht selber die Schuld geben!")
                            contains_self = True
                    if not contains_self:
                        now = datetime.datetime.now()
                        iso_date = datetime.date(now.year, now.month, now.day).isocalendar()
                        inserted_users = 0
                        if len(context.message.mentions) > 0:
                            for new_faulty_user in new_faulty_user_s_in_guild:
                                if not await self.db_connection.isUserEnteredFromUserInWeek(str(iso_date[0]), str(iso_date[1]), old_faulty_user_in_guild.id, new_faulty_user.id):
                                    await self.db_connection.insertFaultyUser(str(iso_date[0]), str(iso_date[1]), old_faulty_user_in_guild.id, new_faulty_user.id)
                                    inserted_users += 1
                                else:
                                    await context.message.channel.send("Du hast **" + new_faulty_user.name + "** schon eingetragen!")
                        else:
                            if not await self.db_connection.isUserEnteredFromUserInWeek(str(iso_date[0]), str(iso_date[1]), old_faulty_user_in_guild.id, new_faulty_user_s_in_guild.id):
                                await self.db_connection.insertFaultyUser(str(iso_date[0]), str(iso_date[1]), old_faulty_user_in_guild.id, new_faulty_user_s_in_guild.id)
                                inserted_users += 1
                            else:
                                await context.message.channel.send("Du hast **" + new_faulty_user_s_in_guild.name + "** schon eingetragen!")
                        faulty_embed = await self.get_faulty_embed(str(iso_date[0]), str(iso_date[1]), old_faulty_user_in_guild.id)
                        await context.message.channel.send("Du hast **" + str(inserted_users) + "** Leute in die Schuldnerliste eingetragen.\n", embed=faulty_embed)
                else:
                    await context.message.channel.send("Die ausgewählten Schuldigen sind nicht auf unserem Server oder du hast sie falsch angegeben :(")
            else:
                await context.message.channel.send("Ey, Ich höre nur auf den Schuldigen von letzter Woche!")

        @schuld.command()
        async def grund(context, faulty_reason: str):
            """Used to give the reason for why the selected [iQ] Member is responsible for this weeks fails"""
            faulty_guild = discord.utils.get(self.bot.guilds, id=self.config.faulty_member_guild_id)

            old_faulty_user_in_guild = discord.utils.get(faulty_guild.members, id=context.message.author.id)

            is_faulty_user = False
            for role in old_faulty_user_in_guild.roles:
                if role.id == self.config.old_faulty_member_role_id:
                    is_faulty_user = True
                    break
            if is_faulty_user:
                now = datetime.datetime.now()
                iso_date = datetime.date(now.year, now.month, now.day).isocalendar()
                if not await self.db_connection.hasUserEnteredReasonInWeek(str(iso_date[0]), str(iso_date[1]), old_faulty_user_in_guild.id):
                    await self.db_connection.insertFaultyReason(str(iso_date[0]), str(iso_date[1]), old_faulty_user_in_guild.id, faulty_reason)

                    faulty_embed = await self.get_faulty_embed(str(iso_date[0]), str(iso_date[1]), old_faulty_user_in_guild.id)
                    await context.message.channel.send("Du hast folgendes als Schuldgrund für diese Woche eingetragen:\n```" + faulty_reason + "```", embed=faulty_embed)
                else:
                    await self.db_connection.alterReasonFromUserInWeek(str(iso_date[0]), str(iso_date[1]), old_faulty_user_in_guild.id, faulty_reason)

                    faulty_embed = await self.get_faulty_embed(str(iso_date[0]), str(iso_date[1]), old_faulty_user_in_guild.id)
                    await context.message.channel.send("Dein eingetragener Schuldgrund wurde aktualisiert:\n```" + faulty_reason + "```", embed=faulty_embed)
            else:
                await context.message.channel.send("Ey, Ich höre nur auf den Schuldigen von letzter Woche!")

        @schuld.command()
        async def farbe(context, red, green, blue):
            """Used to change the color of the responsible role, only used from current responsible member."""
            faulty_guild = await self.get_faulty_guild()
            faulty_member_role = discord.utils.get(faulty_guild.roles, id=self.config.faulty_member_role_id)

            try:
                if 0 <= int(red) <= 255 and 0 <= int(green) <= 255 and 0 <= int(blue) <= 255:
                    if (await self.get_faulty_members()).__contains__(context.message.author):  # or context.message.author.id == self.config.admin_id:
                        color_hex = "{:02x}{:02x}{:02x}".format(int(red), int(green), int(blue))
                        await faulty_member_role.edit(color=discord.Color(int(color_hex, 16)))
                        await context.message.channel.send(embed=discord.Embed(color=discord.Color(int(color_hex, 16)), description="Die Farbe wurde erfolgreich geändert."))
                    else:
                        await context.message.channel.send(embed=discord.Embed(color=discord.Color.red(), description="Dieser Befehl kann nur von Schuldigen benutzt werden!"))
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

        @schuld.group()
        async def confirm(context):
            """Used by [iQ]'s Leaders to confirm proposed responsible members of the current week."""
            pass

        @confirm.command()
        async def user(context, new_faulty_user_name: str):
            """Confirm the proposed responsible member of a specific user for the current week."""
            faulty_guild = discord.utils.get(self.bot.guilds, id=self.config.faulty_member_guild_id)
            command_user = discord.utils.get(faulty_guild.members, id=context.message.author.id)

            if len(context.message.mentions) > 0:
                new_faulty_user_s_in_guild = context.message.mentions
            else:
                new_faulty_user_s_in_guild = discord.utils.get(faulty_guild.members, name=new_faulty_user_name)

            if self.config.iq_leaders_id.__contains__(command_user.id):
                now = datetime.datetime.now()
                iso_date = datetime.date(now.year, now.month, now.day).isocalendar()
                for new_faulty_user in new_faulty_user_s_in_guild:
                    if await self.db_connection.isUserEnteredInWeek(str(iso_date[0]), str(iso_date[1]), new_faulty_user.id):
                        data = await self.db_connection.alterConfirmationForUserInWeek(str(iso_date[0]), str(iso_date[1]), new_faulty_user.id)
                        await context.message.channel.send("`" + data + "`", embed=await self.get_faulty_embed(iso_date[0], iso_date[1], None))
                    else:
                        await context.message.channel.send("**" + new_faulty_user.name + "** wurde von niemandem eingetragen!")
            else:
                await context.message.channel.send("Nur die [iQ]-Leader können diesen Befehl benutzen!")

        @confirm.command()
        async def grund(context, owner_user_name: str):
            """Confirm the proposed reason of a specific user for the current week."""
            faulty_guild = discord.utils.get(self.bot.guilds, id=self.config.faulty_member_guild_id)

            command_user = discord.utils.get(faulty_guild.members, id=context.message.author.id)

            if len(context.message.mentions) > 0:
                if len(context.message.mentions) > 1:
                    await context.message.channel.send(embed=discord.Embed(color=discord.Color.red(), description="Es kann nur ein Grund angegeben werden!"))
                owner_user_in_guild = context.message.mentions[0]

            else:
                owner_user_in_guild = discord.utils.get(faulty_guild.members, name=owner_user_name)

            if self.config.iq_leaders_id.__contains__(command_user.id):
                now = datetime.datetime.now()
                iso_date = datetime.date(now.year, now.month, now.day).isocalendar()
                if await self.db_connection.hasUserEnteredReasonInWeek(str(iso_date[0]), str(iso_date[1]), owner_user_in_guild.id):
                    data = await self.db_connection.alterConfirmationToTrueForReasonFromUserInWeek(str(iso_date[0]), str(iso_date[1]), owner_user_in_guild.id)
                    await context.message.channel.send("`" + data + "`", embed=await self.get_faulty_embed(iso_date[0], iso_date[1], None))
                else:
                    await context.message.channel.send("**" + owner_user_in_guild.name + "** hat in dieser Woche keine Begründung eingetragen!")
            else:
                await context.message.channel.send("Nur die [iQ]-Leader können diesen Befehl benutzen!")

        @confirm.command()
        async def final(context):
            """Used by [iQ]'s Leaders to finalize proposed responsible members of the current week."""
            faulty_guild = discord.utils.get(self.bot.guilds, id=self.config.faulty_member_guild_id)

            command_user = discord.utils.get(faulty_guild.members, id=context.message.author.id)


            if self.config.iq_leaders_id.__contains__(command_user.id):
                now = datetime.datetime.now()
                iso_date = datetime.date(now.year, now.month, now.day).isocalendar()
                if await self.db_connection.isOneUserAcceptedInWeek(str(iso_date[0]), str(iso_date[1])) and await self.db_connection.isOneUserAcceptedInWeek(str(iso_date[0]), str(iso_date[1])):
                    if not await self.db_connection.isWeekFinalized(str(iso_date[0]), str(iso_date[1])):
                        data = await self.db_connection.insertFinalizedWeek(str(iso_date[0]), str(iso_date[1]))
                        await context.message.channel.send("`" + data + "`", embed=await self.get_faulty_embed(iso_date[0], iso_date[1], None))
                    else:
                        await context.message.channel.send("Diese Woche wurde schon finalisiert.")
                else:
                    await context.message.channel.send("Es wurden in dieser Woche noch keine Benutzer oder Begründungen akzeptiert!")
            else:
                await context.message.channel.send("Nur die [iQ]-Leader können diesen Befehl benutzen!")


        self.bot.run(self.config.token)
