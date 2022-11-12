from telebot import TeleBot
from telebot.storage import StateMemoryStorage
from config_data.config import my_config


storage = StateMemoryStorage()
bot = TeleBot(token=my_config.bot_token, state_storage=storage)
