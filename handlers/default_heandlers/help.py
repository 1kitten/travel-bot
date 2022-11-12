from telebot.types import Message

from config_data.config import my_config
from loader import bot


@bot.message_handler(commands=['help'])
def bot_help(message: Message) -> None:
    """
    Хендлер, который обрабатывает команду "/help".
    :param message: сообщение пользователя с командой "/help"
    """
    text = [f'/{command} - {desk}' for command, desk in my_config.default_commands]
    bot.reply_to(message, '\n'.join(text))
