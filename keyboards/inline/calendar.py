from datetime import date, timedelta

from telebot.types import CallbackQuery
from telegram_bot_calendar import DetailedTelegramCalendar

from loader import bot


def arrival_keyboard() -> DetailedTelegramCalendar:
    """
    Клавиатура для выбора даты приезда с ID=1.
    :return calendar: (DetailedTelegramCalendar) клавиатура.
    """
    calendar, step = DetailedTelegramCalendar(calendar_id=1,
                                              current_date=date.today(),
                                              min_date=date.today(),
                                              max_date=date.today() + timedelta(days=365),
                                              locale="ru").build()
    return calendar


def departure_keyboard(call: CallbackQuery) -> DetailedTelegramCalendar:
    """
    Клавиатура для выбора даты выезда с ID=2.
    :param call: (CallbackQuery) из него мы берём id пользователя, чтобы оттуда
    взять дату приезда и по ней уже создать клавиатуру с датой выезда.
    :return calendar: (DetailedTelegramCalendar) клавиатура.
    """
    with bot.retrieve_data(call.message.chat.id) as data:
        user_arrival_date = data['arrival_date']

    calendar, step = DetailedTelegramCalendar(calendar_id=2,
                                              min_date=user_arrival_date + timedelta(days=1),
                                              max_date=user_arrival_date + timedelta(days=365),
                                              locale="ru").build()
    return calendar


def arrival_keyboard_high() -> DetailedTelegramCalendar:
    """
    Клавиатура для выбора даты приезда с ID=3.
    :return calendar: (DetailedTelegramCalendar) клавиатура.
    """
    calendar, step = DetailedTelegramCalendar(calendar_id=3,
                                              current_date=date.today(),
                                              min_date=date.today(),
                                              max_date=date.today() + timedelta(days=365),
                                              locale="ru").build()
    return calendar


def departure_keyboard_high(call: CallbackQuery) -> DetailedTelegramCalendar:
    """
    Клавиатура для выбора даты выезда с ID=4.
    :param call: (CallbackQuery) из него мы берём id пользователя, чтобы оттуда
    взять дату приезда и по ней уже создать клавиатуру с датой выезда.
    :return calendar: (DetailedTelegramCalendar) клавиатура.
    """
    with bot.retrieve_data(call.message.chat.id) as data:
        user_arrival_date = data['arrival_date']

    calendar, step = DetailedTelegramCalendar(calendar_id=4,
                                              min_date=user_arrival_date + timedelta(days=1),
                                              max_date=user_arrival_date + timedelta(days=365),
                                              locale="ru").build()
    return calendar
