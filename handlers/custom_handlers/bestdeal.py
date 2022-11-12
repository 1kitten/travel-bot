from datetime import date, timedelta

from telebot.types import Message, CallbackQuery
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP

from hotel_api.api_request import parse_destinations, find_bestdeal
from keyboards.inline.calendar import arrival_keyboard, departure_keyboard
from keyboards.inline.clarify_destination import keyboard_with_destinations
from keyboards.reply.hotels_photos import show_photos_or_not
from loader import bot
from states.user import UserInfoBestDealsState


@bot.message_handler(commands=['bestdeal'])
def get_city(message: Message) -> None:
    """
    Хендлер обрабатывает команду "/bestdeal"
    :param message:
    :return:
    """
    bot.set_state(message.from_user.id, UserInfoBestDealsState.cityBest, message.chat.id)
    bot.send_message(message.from_user.id, '🏘️ Введите город:')


@bot.message_handler(state=UserInfoBestDealsState.cityBest)
def get_destination(message: Message) -> None:
    """
    Хендлер, отлавливает сообщение пользователя по состоянию "cityBest".
    :param message: (Message) сообщение пользователя.
    """
    bot.set_state(message.from_user.id, UserInfoBestDealsState.destinationBest, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['city'] = message.text
        destinations = parse_destinations(message.text)
        if destinations:
            bot.send_message(message.from_user.id, '🤔 Уточните, пожалуйста:',
                             reply_markup=keyboard_with_destinations(destinations, fltr='bestdeal'))
        else:
            bot.send_message(message.from_user.id, 'По вашему запросу ничего не найдено💀\n'
                                                   'Проверьте правильность написания города.')


@bot.callback_query_handler(func=lambda call: call.data.startswith('bestdeal'))
def get_destination(call: CallbackQuery) -> None:
    """
    Хендлер, отлавливает колбек от клавиатуры с пунктами назначения.
    :param call: (CallbackQuery) кол, нажатие на кнопку.
    """
    bot.set_state(call.message.chat.id, UserInfoBestDealsState.price_range)
    bot.send_message(call.message.chat.id, '💰 Укажите диапазон цен USD$ (например XXX-XXX): ')
    with bot.retrieve_data(call.message.chat.id) as data:
        data['destinationID'] = call.data.replace('bestdeal_', '')


@bot.message_handler(state=UserInfoBestDealsState.price_range)
def get_price_range(message: Message) -> None:
    """
    Хендлер, отлавливает сообщения пользователя по состоянию 'price_range'.
    :param message: (Message) сообщение пользователя с диапазоном цен.
    """
    price_range = message.text.split('-')
    if len(price_range) != 2:
        bot.send_message(message.from_user.id, '😡 Пожалуйста укажите диапазон цен в соответствии с форматом.')
    else:
        try:
            int(price_range[0]), int(price_range[1])
        except ValueError:
            bot.send_message(message.from_user.id, '😡 Пожалуйста вводите числа.')
        else:
            with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
                if int(price_range[0]) > int(price_range[1]):
                    data['max_price'], data['min_price'] = int(price_range[0]), int(price_range[1])
                else:
                    data['max_price'], data['min_price'] = int(price_range[1]), int(price_range[0])
            bot.send_message(message.from_user.id, '🏃 Введите расстояние от цента города (miles):')
            bot.set_state(message.from_user.id, UserInfoBestDealsState.center_distance, message.chat.id)


@bot.message_handler(state=UserInfoBestDealsState.center_distance)
def get_center_distance(message: Message) -> None:
    """
    Хендлер, отлавливает сообщение пользователя по состоянию "center_distance".
    :param message: (Message) сообщение пользователя с расстоянием до цента.
    """
    try:
        int(message.text)
    except ValueError:
        bot.send_message(message.from_user.id, '😡 Пожалуйста введите целое число.')
    else:
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['distance_from_center'] = int(message.text)
        bot.set_state(message.from_user.id, UserInfoBestDealsState.hotels_to_showBest)
        bot.send_message(message.from_user.id, '🏨 Введите количество отелей:')


@bot.message_handler(state=UserInfoBestDealsState.hotels_to_showBest)
def get_hotels_to_show(message: Message) -> None:
    """
    Хендлер, отлавливает сообщение пользователя по состоянию "hotels_to_showBest".
    :param message: (Message) сообщение пользователя с кол-вом отелей.
    """
    if message.text.isdigit():
        if int(message.text) > 10:
            bot.send_message(message.from_user.id, '😢 Я могу вывести не более 10 отелей..')
        else:
            bot.set_state(message.from_user.id, UserInfoBestDealsState.arrival_dateBest)
            with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
                data['hotels_to_show'] = int(message.text)
            bot.send_message(message.from_user.id, '📅 Выберите дату приезда', reply_markup=arrival_keyboard(
                keyboard_id=5))
    else:
        bot.send_message(message.from_user.id, '😡 Цифрами, пожалуйста!')


@bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id=5))
def get_arrival_date(call: CallbackQuery) -> None:
    """
    Хендлер, который отлавливает нажатие пользователя на кнопку клавиатуры.
    :param call: (CallbackQuery) нажатие пользователя на кнопку клавиатуры с датой приезда.
    """
    bot.set_state(call.message.chat.id, UserInfoBestDealsState.departure_dateBest)
    result, key, step = DetailedTelegramCalendar(calendar_id=5,
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
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, '📅 Выберите дату выезда', reply_markup=departure_keyboard(call,
                                                                                                         keyboard_id=6))


@bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id=6))
def get_departure_date(call: CallbackQuery) -> None:
    """
    Хендлер, который отлавливает нажатие пользователя на кнопку клавиатуры.
    :param call: (CallbackQuery) нажатие пользователя на кнопку клавиатуры с датой отъезда.
    """
    bot.set_state(call.message.chat.id, UserInfoBestDealsState.show_photoBest)
    with bot.retrieve_data(call.message.chat.id) as data:
        user_arrival_date = data['arrival_date']
    result, key, step = DetailedTelegramCalendar(calendar_id=6,
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


@bot.message_handler(state=UserInfoBestDealsState.show_photoBest)
def get_or_not_photos(message: Message) -> None:
    """
    Хендлер, отлавливает сообщение пользователя по состоянию "show_photoBest".
    :param message: (Message) ответ пользователя.
    """
    if message.text == '👍 Да':
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['show_photo'] = True
        bot.set_state(message.from_user.id, UserInfoBestDealsState.photos_to_showBest)
        bot.send_message(message.from_user.id, '❔ Введите количество фотографий')
    else:
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['show_photo'] = False
            data['photos_to_show'] = 0
        find_bestdeal(message)


@bot.message_handler(state=UserInfoBestDealsState.photos_to_showBest)
def get_photos(message: Message) -> None:
    """
    Хендлер, отлавливает сообщение пользователя по состоянию "photos_to_showBest".
    :param message: (Message) сообщение пользователя с количеством фотографий.
    :return:
    """
    if message.text.isdigit():
        if int(message.text) > 5:
            bot.send_message(message.from_user.id, '😢 Я могу вывести не более 5 фотографий..')
        else:
            with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
                data['photos_to_show'] = int(message.text)
            find_bestdeal(message)
    else:
        bot.send_message(message.from_user.id, '😡 Цифрами, пожалуйста!')
