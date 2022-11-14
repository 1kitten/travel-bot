from datetime import date, timedelta, datetime

from telebot.types import Message, CallbackQuery
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP

from config_data.config import KeyboardStatus
from hotel_api.api_request import parse_destinations, find_hotels
from keyboards.inline.calendar import arrival_keyboard, departure_keyboard
from keyboards.inline.clarify_destination import keyboard_with_destinations
from keyboards.reply.hotels_photos import show_photos_or_not
from loader import bot
from states.user import UserInfoHighPriceState


@bot.message_handler(commands=['highprice'])
def highprice(message: Message) -> None:
    """
    Хендлер отлавливающий команду "/highprice"
    :param message: (Message) сообщение пользователя с командой "/highprice".
    """
    bot.set_state(message.from_user.id, UserInfoHighPriceState.cityHigh, message.chat.id)
    bot.send_message(message.from_user.id, '🏘️ Введите город:')


@bot.message_handler(state=UserInfoHighPriceState.cityHigh)
def get_city(message: Message) -> None:
    """
    Хендлер отлавливает сообщение пользователя по состоянию "cityHigh"
    (город, который он ввёл до этого).
    Тут же записывается информация с наименованием города, а так же вызывается клавиатура
    для уточнения введённого города.
    :param message: (Message) сообщение пользователя с наименованием города.
    """
    bot.set_state(message.from_user.id, UserInfoHighPriceState.destinationHigh, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['city'] = message.text
        data['user_id'] = message.from_user.id
        data['user_command'] = '/highprice'
        data['request_date'] = datetime.now()
        destinations_ids = parse_destinations(message.text)
        if destinations_ids:
            bot.send_message(message.from_user.id, '🤔 Уточните, пожалуйста:',
                             reply_markup=keyboard_with_destinations(destinations_ids, fltr='highprice'))
        else:
            bot.send_message(message.from_user.id, 'По вашему запросу ничего не найдено💀\n'
                                                   'Проверьте правильность написания города.')


@bot.callback_query_handler(func=lambda call: call.data.startswith('highprice'))
def get_destination(call: CallbackQuery) -> None:
    """
    Колбэк хендлер для отлавливания нажатия пользователя на кнопку клавиатуры.
    Далее мы записываем данные из call и просим пользователя ввести количество отелей.
    :param call: (CallbackQuery) само нажатие в котором лежит ".data" с destinationID.
    """
    bot.set_state(call.message.chat.id, UserInfoHighPriceState.hotels_to_showHigh)
    bot.send_message(call.message.chat.id, '🏨 Введите количество отелей: ')
    with bot.retrieve_data(call.message.chat.id) as data:
        data['destinationID'] = call.data.replace('highprice_', '')


@bot.message_handler(state=UserInfoHighPriceState.hotels_to_showHigh)
def get_hotels_to_show(message: Message) -> None:
    """
    Хендлер отлова сообщения пользователя по состоянию "hotels_to_showHigh".
    Проверяем валидность введённого значения, записываем его,
    после чего просим выбрать дату приезда и вызываем соответствующую клавиатуру.
    :param message: (Message) сообщение пользователя с количеством отелей.
    """
    if message.text.isdigit():
        if int(message.text) > 10:
            bot.send_message(message.from_user.id, '😢 Я могу вывести не более 10 отелей..')
        else:
            bot.set_state(message.from_user.id, UserInfoHighPriceState.arrival_dateHigh)
            with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
                data['hotels_to_show'] = int(message.text)
            bot.send_message(message.from_user.id, '📅 Выберите дату приезда', reply_markup=arrival_keyboard(
                keyboard_id=KeyboardStatus.highprice_arrival.value))
    else:
        bot.send_message(message.from_user.id, '😡 Цифрами, пожалуйста!')


@bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id=KeyboardStatus.highprice_arrival.value))
def get_arrival_date(call: CallbackQuery) -> None:
    """
    Хендлер, который отлавливает нажатие пользователя на кнопку клавиатуры под id=3.
    Далее записываем информацию о дате приезда, спрашиваем пользователя о дате выезда
    и вызываем клавиатуру.
    :param call: (CallbackQuery) колл пользователя с информацией о дате приезда.
    """
    bot.set_state(call.message.chat.id, UserInfoHighPriceState.departure_dateHigh)
    result, key, step = DetailedTelegramCalendar(calendar_id=KeyboardStatus.highprice_arrival.value,
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
        bot.send_message(call.message.chat.id, '📅 Выберите дату выезда',
                         reply_markup=departure_keyboard(call, keyboard_id=KeyboardStatus.highprice_departure.value))


@bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id=KeyboardStatus.highprice_departure.value))
def get_departure_date(call: CallbackQuery) -> None:
    """
    Хендлер, который отлавливает нажатие пользователя на кнопку клавиатуры с id=4.
    Записываем информацию о дате выезда из отеля и спрашиваем пользователя, показать
    фотографии или нет.
    :param call: (CallbackQuery) колл пользователя, содержащий информацию о дате выезда.
    """
    bot.set_state(call.message.chat.id, UserInfoHighPriceState.show_photoHigh)
    with bot.retrieve_data(call.message.chat.id) as data:
        user_arrival_date = data['arrival_date']
    result, key, step = DetailedTelegramCalendar(calendar_id=KeyboardStatus.highprice_departure.value,
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


@bot.message_handler(state=UserInfoHighPriceState.show_photoHigh)
def get_or_not_photos(message: Message) -> None:
    """
    Хендлер, отлавливающий состояние пользователя по "show_photoHigh".
    Если пользователь ответил "👍 Да", то спрашиваем его о количество фотографий.
    Если пользователь ответил "👎 Нет", то вызывается функция поиска отелей по заданным раннее критериям.
    :param message: (Message) сообщение пользователя содержащее ответ на вопрос.
    """
    if message.text == '👍 Да':
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['show_photo'] = True
        bot.set_state(message.from_user.id, UserInfoHighPriceState.photos_to_showHigh, message.chat.id)
        bot.send_message(message.from_user.id, '❔ Введите количество фотографий')
    else:
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['show_photo'] = False
            data['photos_to_show'] = 0
        find_hotels(message, sort_type='PRICE_HIGHEST_FIRST')
        bot.delete_state(message.from_user.id, message.chat.id)


@bot.message_handler(state=UserInfoHighPriceState.photos_to_showHigh)
def get_photos(message: Message) -> None:
    """
    Хендлер, срабатывающий по состоянию пользователя "photos_to_showHigh".
    Вызывается в результате ответа на вопрос "👍 Да".
    Происходит проверка данных на валидность, а так же запись информации о количестве фотографий.
    Далее вызывается функция поиска отелей.
    :param message: (Message) сообщение с количеством фотографий отелей.
    """
    if message.text.isdigit():
        if int(message.text) > 5:
            bot.send_message(message.from_user.id, '😢 Я могу вывести не более 5 фотографий..')
        else:
            with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
                data['photos_to_show'] = int(message.text)
            find_hotels(message, sort_type='PRICE_HIGHEST_FIRST')
            bot.delete_state(message.from_user.id, message.chat.id)
    else:
        bot.send_message(message.from_user.id, '😡 Цифрами, пожалуйста!')
