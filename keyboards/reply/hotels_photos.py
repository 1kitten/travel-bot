from telebot.types import ReplyKeyboardMarkup, KeyboardButton


def show_photos_or_not() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(True, True)
    keyboard.add(KeyboardButton('👍 Да'), KeyboardButton('👎 Нет'))
    return keyboard
