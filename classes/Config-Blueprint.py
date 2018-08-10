class Config:

    token = ""  # token of the bot user
    prefix = "!"  # prefix for the bot to react to

    new_user_server_id = ""  # the server id on which it will assign new users a specific role
    new_user_role_id = ""  # the role id which will be assigned to new users on the specified server

    faulty_member_server_id = ""  # the server id of iQ, to get the latest bad member
    faulty_member_role_id = ""  # the role id for the current weeks faulty member
    old_faulty_member_role_id = ""  # the role id for the last weeks faulty member

    bot_id = ""  # userId of the bot
    admin_id = ""  # userId of the bot admin
    iq_leaders_id = {  # userId of the iq leaders (usage in !schuld confirm)
        "",
        # admin_id,
    }

    ping_pong_loop = 0  # if set true, the bot will trigger itself with ping and pong commands
    airhorn_stay_afterwards = 0  # if set true, the bot will stay in voice after the airhorn was played