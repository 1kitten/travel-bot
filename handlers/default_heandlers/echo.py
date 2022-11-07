from telebot.types import Message

from loader import bot


@bot.message_handler(commands=['hello'])
def bot_echo(message: Message):
    bot.reply_to(message, "Привет👋")
