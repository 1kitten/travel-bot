from loader import bot
from database.travel_database import show_history, check_data
from telebot.types import Message


@bot.message_handler(commands=['history'])
def show_users_history(message: Message) -> None:
    if check_data(message.from_user.id):
        search_history = show_history(message.from_user.id)
        for i_result in search_history:
            bot.send_message(message.from_user.id,
                             f"✍ Команда: {i_result[0]}\n"
                             f"👀 Дата выполнения команды: {i_result[1][:19]}\n"
                             f"👉 Результат выполнения команды: {i_result[2]}\n",
                             disable_web_page_preview=True)
    else:
        bot.send_message(message.from_user.id, 'Сначала воспользуйтесь другими командами :)')
