#  _______          ______             _______                  _
# |__   __|        |  ____|           |__   __|                | |
#    | | ___   ___ | |__   __ _ ___ _   _| |_ __ __ ___   _____| |
#    | |/ _ \ / _ \|  __| / _` / __| | | | | '__/ _` \ \ / / _ \ |
#    | | (_) | (_) | |___| (_| \__ \ |_| | | | | (_| |\ V /  __/ |
#    |_|\___/ \___/|______\__,_|___/\__, |_|_|  \__,_| \_/ \___|_|
#                                    __/ |
#                                   |___/
#     Telegram bot made by Maxim S.

from loader import bot
import handlers
from telebot.custom_filters import StateFilter
from utils.set_bot_commands import set_default_commands

if __name__ == '__main__':
    bot.add_custom_filter(StateFilter(bot))
    set_default_commands(bot)
    bot.infinity_polling()
