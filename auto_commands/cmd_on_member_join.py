import discord
import os

import config


async def ex(bot, member):
    if member.server.id == config.new_user_server_id:
        role = discord.utils.get(member.server.roles, id=config.new_user_role_id)
        await bot.add_roles(member, role)
