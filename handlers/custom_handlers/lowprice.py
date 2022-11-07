from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP
from loader import bot
from states.user import UserInfoState
from telebot.types import Message, CallbackQuery
from hotel_api.api_request import parse_destinations, find_hotels_lowprice
from keyboards.inline.clarify_destination import keyboard_with_destinations
from keyboards.inline.calendar import arrival_keyboard, departure_keyboard
from keyboards.reply.hotels_photos import show_photos_or_not
from datetime import date, timedelta


@bot.message_handler(commands=['lowprice'])
def lowprice(message: Message) -> None:
    bot.set_state(message.from_user.id, UserInfoState.city, message.chat.id)
    bot.send_message(message.from_user.id, '🏘️ Введите город:')


@bot.message_handler(state=UserInfoState.city)
def get_city(message: Message) -> None:
    bot.set_state(message.from_user.id, UserInfoState.destination, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['city'] = message.text
        destinations_ids = parse_destinations(message.text)
        if destinations_ids:
            bot.send_message(message.from_user.id, '🤔 Уточните, пожалуйста:',
                             reply_markup=keyboard_with_destinations(destinations_ids))
        else:
            bot.send_message(message.from_user.id, 'По вашему запросу ничего не найдено💀\n'
                                                   'Проверьте правильность написания города.')


@bot.callback_query_handler(state=UserInfoState.destination, func=lambda call: call.data.startswith('dist'))
def get_destination(call: CallbackQuery) -> None:
    bot.set_state(call.message.chat.id, UserInfoState.hotels_to_show)
    bot.send_message(call.message.chat.id, '🏨 Введите количество отелей: ')
    with bot.retrieve_data(call.message.chat.id) as data:
        data['destinationID'] = call.data.replace('dist_', '')


@bot.message_handler(state=UserInfoState.hotels_to_show)
def get_hotels_to_show(message: Message) -> None:
    if message.text.isdigit():
        if int(message.text) > 10:
            bot.send_message(message.from_user.id, '😢 Я могу вывести не более 10 отелей..')
        else:
            bot.set_state(message.from_user.id, UserInfoState.arrival_date)
            with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
                data['hotels_to_show'] = int(message.text)
            bot.send_message(message.from_user.id, '📅 Выберите дату приезда', reply_markup=arrival_keyboard())
    else:
        bot.send_message(message.from_user.id, '😡 Цифрами, пожалуйста!')


@bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id=1))
def get_arrival_date(call: CallbackQuery) -> None:
    bot.set_state(call.message.chat.id, UserInfoState.departure_date)
    result, key, step = DetailedTelegramCalendar(calendar_id=1,
                                                 current_date=date.today(),
                                                 min_date=date.today(),
                                                 max_date=date.today() + timedelta(days=365),
                                                 locale="ru").process(call.data)
    if not result and key:
        bot.edit_message_text(f"Выберите {LSTEP[step]}",
                              call.message.chat.id,
                              call.message.message_id,
                              reply_markup=key)
    else:
        with bot.retrieve_data(call.message.chat.id) as data:
            data['arrival_date'] = result
        bot.delete_message(call.message.chat.id, call.message.message_id) # # #
        bot.send_message(call.message.chat.id, '📅 Выберите дату выезда', reply_markup=departure_keyboard(call))


@bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id=2))
def get_departure_date(call: CallbackQuery) -> None:
    bot.set_state(call.message.chat.id, UserInfoState.show_photo)
    with bot.retrieve_data(call.message.chat.id) as data:
        user_arrival_date = data['arrival_date']
    result, key, step = DetailedTelegramCalendar(calendar_id=2,
                                                 min_date=user_arrival_date + timedelta(days=1),
                                                 max_date=user_arrival_date + timedelta(days=365),
                                                 locale="ru").process(call.data)
    if not result and key:
        bot.edit_message_text(f"Выберите {LSTEP[step]}",
                              call.message.chat.id,
                              call.message.message_id,
                              reply_markup=key)
    elif result:
        with bot.retrieve_data(call.message.chat.id) as data:
            data['departure_date'] = result
            arrival_date = data['arrival_date']
            departure_date = data['departure_date']
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, f'📈 Дата приезда: {arrival_date}\n📉 Дата выезда: {departure_date}')
        bot.send_message(call.message.chat.id, '📷 Показать фотографии отелей?', reply_markup=show_photos_or_not())


@bot.message_handler(state=UserInfoState.show_photo)
def get_or_not_photos(message: Message) -> None:
    if message.text == '👍 Да':
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['show_photo'] = True
        bot.set_state(message.from_user.id, UserInfoState.photos_to_show, message.chat.id)
        bot.send_message(message.chat.id, '❔ Введите количество фотографий')
    else:
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['show_photo'] = False
            data['photos_to_show'] = 0
        find_hotels_lowprice(message)


@bot.message_handler(state=UserInfoState.photos_to_show)
def get_photos(message: Message) -> None:
    if message.text.isdigit():
        if int(message.text) > 5:
            bot.send_message(message.from_user.id, '😢 Я могу вывести не более 5 фотографий..')
        else:
            with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
                data['photos_to_show'] = int(message.text)
            find_hotels_lowprice(message)
