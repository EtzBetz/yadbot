from classes import Bot, Config

print("Loading da bot...")

config = Config.Config()
bot = Bot.YadBot(config, config.prefix, "At least you can help yourself :/")
bot.run(config.token)
