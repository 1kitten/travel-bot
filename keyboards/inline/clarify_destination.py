from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Dict


def keyboard_with_destinations(destinations: Dict[str, str]) -> InlineKeyboardMarkup:
    """
    Клавиатура для уточнения местоположения отеля.
    :param destinations: список из местоположений.
    :return keyboard: (InlineKeyboardMarkup) клавиатура с местоположениями.
    """
    keyboard = InlineKeyboardMarkup()
    for i_elem in destinations:
        keyboard.add(InlineKeyboardButton(text=i_elem, callback_data=f'dist_{destinations[i_elem]}'))
    return keyboard
