class Config:

    version_number = "2.1.1"  # version number of the bot you just see, don't update on your own

    token = ""  # token of the bot user
    prefix = "!"  # prefix for the bot to react to

    bot_id = 133333333333333337  # userId of the bot
    admin_id = 133333333333333337  # userId of the bot admin

    ping_pong_loop = 0  # if set true, the bot will trigger itself with ping and pong commands

    disable_timers = 1  # if set true, the bot will not run

    website_check_interval_seconds = 300  # number of seconds the bot should wait for re-fetching content of the fetched website
    website_check_url = "https://www.google.de"  # the website to check
    client_headers = {  # header that the bot will be using
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
    }

    cog_lightshot_servers = [  # servers in this list can use the lightshot cog commands
        133333333333333337
    ]