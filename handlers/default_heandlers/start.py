from telebot.types import Message

from loader import bot


@bot.message_handler(commands=['start'])
def bot_start(message: Message) -> None:
    """
    Хендлер, обрабатывает команду "/start"
    :param message: (Message) сообщение пользователя с командой "/start"
    """
    bot.reply_to(message, f"Спасибо, что запустил меня 🥳, {message.from_user.full_name}!")

