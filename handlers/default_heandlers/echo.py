from telebot.types import Message

from loader import bot


@bot.message_handler(commands=['hello'])
def bot_echo(message: Message) -> None:
    """
    Хендлер, обрабатывает команду "/hello".
    :param message: (Message) сообщение пользователя с командой "/hello".
    """
    bot.reply_to(message, "Привет👋")
