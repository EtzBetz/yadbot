class Config:

    version_number = "1.4"  # version number of the bot you just see, don't update on your own

    token = ""  # token of the bot user
    prefix = "!"  # prefix for the bot to react to
    db_credentials = {  # credentials for the database
        "user": "",
        "password": "",
        "database": "",
        "host": "",
        "port": ""
    }

    new_user_guild_id = 133333333333333337  # the server id on which it will assign new users a specific role
    new_user_role_id = 133333333333333337  # the role id which will be assigned to new users on the specified server

    guilty_member_guild_id = 133333333333333337  # the server id of iQ, to get the latest bad member
    guilty_commands_channel_id = 133333333333333337  # channel id of the channel to write commands into
    guilty_news_channel_id = 133333333333333337  # channel id of the channel where guilty news are announced to
    guilty_member_role_id = 133333333333333337  # the role id for the current weeks faulty member
    old_guilty_member_role_id = 133333333333333337  # the role id for the last weeks faulty member

    bot_id = 133333333333333337  # userId of the bot
    admin_id = 133333333333333337  # userId of the bot admin
    iq_leaders_id = {  # userId of the iq leaders (usage in !schuld confirm)
        133333333333333337,  # person1
        # 133333333333333337,  # person2
        # admin_id,
    }

    ping_pong_loop = 0  # if set true, the bot will trigger itself with ping and pong commands
    airhorn_stay_afterwards = 0  # if set true, the bot will stay in voice after the airhorn was played

    support_skip_all = 0  # if set true, the bot will not send any support messages to bot-admin
    support_skip_player_missing_in_db = 0  # if set true, the bot will not send support messages regarding missing players in db