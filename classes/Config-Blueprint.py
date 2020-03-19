class Config:

    version_number = "2.2.1"  # version number of the bot you just see, don't update on your own

    token = ""  # token of the bot user
    prefix = "!"  # prefix for the bot to react to

    bot_id = 133333333333333337  # userId of the bot
    admin_id = 133333333333333337  # userId of the bot admin

    ping_pong_loop = 0  # if set true, the bot will trigger itself with ping and pong commands

    disable_timers = 1  # if set true, the bot will not run

    client_headers = {  # header that the bot will be using
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
    }

    default_scraper_user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36"
    default_scraper_check_interval = 300  # number of seconds the bot should wait for re-fetching content of a fetched website

    scraper_black_board_url = "https://google.de"  # the website to check
    scraper_black_board_dm_users = [
        133333333333333337
    ]
    scraper_black_board_servers = [
        {
            "server_id": 133333333333333337,
            "channel_id": 133333333333333337
        }
    ]

    scraper_pastebin_check_interval = 10  # number of seconds the bot should wait for re-fetching content of a fetched website
    scraper_pastebin_url = "https://pastebin.com/archive"  # the website to check
    scraper_pastebin_dm_users = [
        133333333333333337
    ]
    scraper_pastebin_servers = [
        {
            "server_id": 133333333333333337,
            "channel_id": 133333333333333337
        }
    ]

    cog_lightshot_emojis = {
        "entertainment_emoji_id": 133333333333333337,    # which emoji to use to sort entertainment images
        "nsfw_emoji_id": 133333333333333337,             # which emoji to use to sort nsfw images
        "money_emoji_id": 133333333333333337,            # which emoji to use to sort money images
        "account_emoji_id": 133333333333333337,          # which emoji to use to sort account images
        "address_emoji_id": 133333333333333337,          # which emoji to use to sort address images

        "trash_emoji_id": 133333333333333337,            # which emoji to use for the delete reaction
    }

    cog_lightshot_servers = [  # servers in this list can use the lightshot cog commands
        {
            "server_id": 133333333333333337,                 # one individual server that the commands are allowed on

            "reaction_handler": True,                        # if true the bot adds reactions to images and moves the images to following channels on reaction

            "entertainment_channel_id": 133333333333333337,  # channel on this server to which to move the entertaining images to
            "nsfw_channel_id": 133333333333333337,           # channel on this server to which to move the nsfw images to
            "money_channel_id": 133333333333333337,          # channel on this server to which to move the money images to
            "account_channel_id": 133333333333333337,        # channel on this server to which to move the account images to
            "address_channel_id": 133333333333333337,        # channel on this server to which to move the address images to
        }
    ]