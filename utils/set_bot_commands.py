from telebot.types import BotCommand
from config_data.config import my_config


def set_default_commands(bot):
    bot.set_my_commands(
        [BotCommand(*i) for i in my_config.default_commands]
    )
