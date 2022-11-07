from telebot import TeleBot
from telebot.storage import StateMemoryStorage
from config_data import config
from config_data.config import RAPID_API_KEY

storage = StateMemoryStorage()
bot = TeleBot(token=config.BOT_TOKEN, state_storage=storage)
headers = {
        "X-RapidAPI-Key": RAPID_API_KEY,
        "X-RapidAPI-Host": "hotels4.p.rapidapi.com"
    }
