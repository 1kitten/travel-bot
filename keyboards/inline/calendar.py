from telegram_bot_calendar import DetailedTelegramCalendar
from datetime import date, timedelta
from loader import bot
from telebot.types import CallbackQuery


def arrival_keyboard() -> DetailedTelegramCalendar:
    calendar, step = DetailedTelegramCalendar(calendar_id=1,
                                              current_date=date.today(),
                                              min_date=date.today(),
                                              max_date=date.today() + timedelta(days=365),
                                              locale="ru").build()
    return calendar


def departure_keyboard(call: CallbackQuery) -> DetailedTelegramCalendar:
    with bot.retrieve_data(call.message.chat.id) as data:
        user_arrival_date = data['arrival_date']

    calendar, step = DetailedTelegramCalendar(calendar_id=2,
                                              min_date=user_arrival_date + timedelta(days=1),
                                              max_date=user_arrival_date + timedelta(days=365),
                                              locale="ru").build()
    return calendar
