from datetime import date, timedelta

from telebot.types import CallbackQuery
from telegram_bot_calendar import DetailedTelegramCalendar

from loader import bot


def arrival_keyboard(keyboard_id: int) -> DetailedTelegramCalendar:
    """
    Клавиатура для выбора даты приезда с ID=1.
    :param keyboard_id: (int) Номер клавиатуры.
    :return calendar: (DetailedTelegramCalendar) клавиатура.
    """
    calendar, step = DetailedTelegramCalendar(calendar_id=keyboard_id,
                                              current_date=date.today(),
                                              min_date=date.today(),
                                              max_date=date.today() + timedelta(days=365),
                                              locale="ru").build()
    return calendar


def departure_keyboard(call: CallbackQuery, keyboard_id: int) -> DetailedTelegramCalendar:
    """
    Клавиатура для выбора даты выезда с ID=2.
    :param keyboard_id: (id). Номер клавиатуры
    :param call: (CallbackQuery) из него мы берём id пользователя, чтобы оттуда
    взять дату приезда и по ней уже создать клавиатуру с датой выезда.
    :return calendar: (DetailedTelegramCalendar) клавиатура.
    """
    with bot.retrieve_data(call.message.chat.id) as data:
        user_arrival_date = data['arrival_date']

    calendar, step = DetailedTelegramCalendar(calendar_id=keyboard_id,
                                              min_date=user_arrival_date + timedelta(days=1),
                                              max_date=user_arrival_date + timedelta(days=365),
                                              locale="ru").build()
    return calendar
