import json
import re
from typing import Dict, Optional

import requests
from telebot.types import InputMediaPhoto, Message

from config_data.config import headers, url_destinations, url_for_photos, url_for_hotels_id_list
from loader import bot
from database.travel_database import add_new_value


def request_to_api(url: str, headers: dict, querystring: dict) -> Optional[str]:
    """
    Функция, которая отправляет запрос к API.
    Проверяет ответ на статус кода, и возвращает ответ в виде текста.
    :param url: ссылка, по которой будет отправлен запрос.
    :param headers: параметры для доступа к отправке запроса.
    :param querystring: заданные пользователем критерии.
    :return: текст ответа от запроса, в случае не возникновения ошибки.
    """
    try:
        response = requests.request('GET', url=url, headers=headers, params=querystring, timeout=100)
        if response.status_code == requests.codes.ok:
            return response.text
    except Exception as exc:
        print('Произошла ошибка: {}'.format(exc))
        return


def parse_destinations(city_name: str) -> Dict[str, str]:
    """
    Функция, которая парсит айди назначений по городу, который ввёл пользователь.
    Добавляет все результаты в словарь destinations_ids.
    :param city_name: город, который ввёл пользователь боту.
    :return destinations_ids: словарь, где "Наименование места: Номер назначения".
    """
    query = {'query': city_name, 'locate': 'en_EN', 'currency': 'USD'}
    response = request_to_api(url_destinations, headers, query)

    if response:
        result = json.loads(response)['suggestions'][0]['entities']
        if result:
            destinations_ids = dict()
            for i_item in result:
                if '<' in i_item.get('caption'):
                    formed_loc = re.sub(r'<.*?>+', '', i_item.get('caption'))
                    if (city_name.title() in formed_loc) or (city_name.lower() in formed_loc):
                        destinations_ids[formed_loc] = i_item.get('destinationId')
            return destinations_ids


def get_photo(message: Message) -> None:
    """
    Функция, которая парсит фотографии отелей. Далее добавляет результаты в список
    с фотографиями отелей, который лежит внутри data['list_of_hotels']
    :param message: сообщение пользователя, оно нужно, чтобы взять его id
    и обратиться к data['list_of_hotels'].
    """
    with bot.retrieve_data(message.chat.id) as data:
        for hotel in data['list_of_hotels']:
            query = {'id': hotel}
            response_for_hotels_photo = request_to_api(url=url_for_photos, headers=headers, querystring=query)
            if response_for_hotels_photo:
                try:
                    length_of_photos = len(json.loads(response_for_hotels_photo)['roomImages'][0]['images'])
                    if length_of_photos > data['photos_to_show']:
                        result_of_photos = json.loads(response_for_hotels_photo)['roomImages'][0]['images'][0:data[
                            'photos_to_show']]
                    else:
                        result_of_photos = json.loads(response_for_hotels_photo)['roomImages'][0]['images'][
                                           0:length_of_photos]
                except Exception:
                    result_of_photos = [json.loads(response_for_hotels_photo)['hotelImages'][0]]
                for photo in result_of_photos:
                    photo_url = photo['baseUrl'].format(size="z")
                    data['list_of_hotels'][hotel]['photos'].append(photo_url)


def find_hotels(message: Message, sort_type: str = 'PRICE') -> None:
    """
    Функция нахождения отелей по низкой цене с параметрами пользователя.
    Собираем все критерии для поиска в отдельные переменные.
    Отправляем соответствующий запрос к API и получаем результат.
    Далее обрабатываем этот результат и записываем в data['list_of_hotels'].
    Если пользователь не желает просматривать фотографии отелей, то просто
    выводим информацию о каждом отеле.
    Если пользователь хочет посмотреть фотографии отелей, то вызывается функция get_photo.
    :param sort_type: (str) тип сортировки.
    :param message: (Message) сообщение пользователя, нужно для обращения к его id, чтобы взять
    оттуда параметры для запроса.
    """
    with bot.retrieve_data(message.chat.id) as data:
        user_destinationid = data['destinationID']
        user_show_photo = data['show_photo']
        user_total_hotels = data['hotels_to_show']
        user_arrival_date = data['arrival_date']
        user_departure_date = data['departure_date']
        user_id = data['user_id']
        request_date = data['request_date']
        user_command = data['user_command']

    query = {"destinationId": user_destinationid,
             "pageNumber": "1",
             "pageSize": user_total_hotels,
             "checkIn": user_arrival_date,
             "checkOut": user_departure_date,
             "adults1": "1",
             "sortOrder": sort_type,
             "locale": "en_EN",
             "currency": "USD",
             }

    response_hotels_id_list = request_to_api(url=url_for_hotels_id_list, headers=headers, querystring=query)
    if response_hotels_id_list:
        bot.send_message(message.from_user.id, '🔍 Ищу подходящие отели...')
        result_for_hotels_id = json.loads(response_hotels_id_list)['data']['body']['searchResults']['results']
        if result_for_hotels_id:
            with bot.retrieve_data(message.chat.id) as data:
                data['list_of_hotels'] = {i.get('id'):
                                              {'hotel_name': i.get('name'),
                                               'hotel_address': i['address'].get('streetAddress'),
                                               "distance_from_center": i["landmarks"][0].get("distance"),
                                               "hotel_website": f"https://hotels.com/ho{i.get('id')}",
                                               'price_for_certain_period': int(re.sub(r'[^0-9]+', '',
                                                                                      i['ratePlan']['price'].get(
                                                                                          'current'))),
                                               'full_bundle_price': re.findall(r'\$[0-9,]{0,}',
                                                                               i['ratePlan']['price'].get(
                                                                                   'fullyBundledPricePerStay',
                                                                                   'Not found')),
                                               "photos": []
                                               } for i in result_for_hotels_id
                                          }
                user_hotels_list = data['list_of_hotels']
            if not user_show_photo:
                for hotel in user_hotels_list:
                    bot.send_message(message.chat.id,
                                     f"🏨 Отель: {user_hotels_list[hotel]['hotel_name']}\n"
                                     f"🔗 Ссылка: {user_hotels_list[hotel]['hotel_website']}\n"
                                     f"🗺️ Адрес: {user_hotels_list[hotel]['hotel_address']}\n"
                                     f"📍 До центра: {user_hotels_list[hotel]['distance_from_center']}\n"
                                     f"📅 Период проживания: с {user_arrival_date} по {user_departure_date}\n"
                                     f"💵 Цена: ${user_hotels_list[hotel]['price_for_certain_period']}\n"
                                     f"💵 Цена за период проживания: "
                                     f"{''.join(user_hotels_list[hotel]['full_bundle_price'])}",
                                     disable_web_page_preview=True
                                     )
                    add_new_value(user_id, user_command, request_date, user_hotels_list[hotel]['hotel_website'])
                bot.send_message(message.from_user.id, '❤ По вашему запросу было найдено {} результата'.format(
                    len(user_hotels_list)
                ))
            else:
                get_photo(message)
                with bot.retrieve_data(message.chat.id) as data:
                    for hotel in data['list_of_hotels']:
                        text = f"🏨 Отель: {data['list_of_hotels'][hotel]['hotel_name']}\n" \
                               f"🔗 Ссылка: {data['list_of_hotels'][hotel]['hotel_website']}\n" \
                               f"🗺️ Адрес: {data['list_of_hotels'][hotel]['hotel_address']}\n" \
                               f"📍 До центра: {data['list_of_hotels'][hotel]['distance_from_center']}\n" \
                               f"📅 Период проживания: с {user_arrival_date} по {user_departure_date}\n" \
                               f"💵 Цена: ${data['list_of_hotels'][hotel]['price_for_certain_period']}\n" \
                               f"💵 Цена за период проживания: " \
                               f"{''.join(data['list_of_hotels'][hotel]['full_bundle_price'])}"

                        photos = [InputMediaPhoto(media=url, caption=text) if num == 0
                                  else InputMediaPhoto(media=url)
                                  for num, url in enumerate(data['list_of_hotels'][hotel]['photos'])]

                        bot.send_media_group(message.chat.id, photos)
                        add_new_value(user_id, user_command, request_date, user_hotels_list[hotel]['hotel_website'])
                bot.send_message(message.from_user.id, '❤ По вашему запросу было найдено {} результата'.format(
                    len(user_hotels_list)
                ))
        else:
            bot.send_message(message.chat.id, '😭 По вашему запросу ничего не найдено.')


def find_bestdeal(message: Message) -> None:
    """
    Функция нахождения отелей по параметрам, заданным пользователем.
    Собираем все критерии для поиска в отдельные переменные.
    Отправляем соответствующий запрос к API и получаем результат.
    Далее обрабатываем этот результат и записываем в data['list_of_hotels'].
    Если пользователь не желает просматривать фотографии отелей, то просто
    выводим информацию о каждом отеле.
    Если пользователь хочет посмотреть фотографии отелей, то вызывается функция get_photo.
    :param message: (Message) сообщение пользователя, нужно для обращения к его id.
    """
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        user_destination = data['destinationID']
        user_max_price = data['max_price']
        user_min_price = data['min_price']
        user_center_distance = data['distance_from_center']
        user_total_hotels = data['hotels_to_show']
        user_arrival_date = data['arrival_date']
        user_departure_date = data['departure_date']
        user_show_photo = data['show_photo']
        user_id = data['user_id']
        request_date = data['request_date']
        user_command = data['user_command']

    query = {"destinationId": user_destination,
             "pageNumber": "1",
             "pageSize": user_total_hotels,
             "checkIn": user_arrival_date,
             "checkOut": user_departure_date,
             "adults1": "1",
             "priceMin": user_min_price,
             "priceMax": user_max_price,
             "sortOrder": "DISTANCE_FROM_LANDMARK",
             "locale": "en_US",
             "currency": "USD",
             "landmarkIds": f"City center {user_center_distance}"
             }

    response = request_to_api(url=url_for_hotels_id_list, headers=headers, querystring=query)
    if response:
        bot.send_message(message.from_user.id, '🔍 Ищу подходящие отели...')
        hotels_result = json.loads(response)['data']['body']['searchResults']['results']
        if hotels_result:
            with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
                data['list_of_hotels'] = {i.get('id'):
                    {
                        'hotel_name': i.get('name'),
                        'hotel_address': i['address'].get('streetAddress'),
                        'distance_from_center': i['landmarks'][0].get('distance'),
                        'hotel_website': f'https://hotels.com/ho{i.get("id")}',
                        'price_for_certain_period': re.sub(r'[^0-9]+', '',
                                                           i['ratePlan']['price'].get(
                                                               'current')),
                        'full_bundle_price': re.findall(r'\$[0-9,]{0,}',
                                                        i['ratePlan']['price'].get(
                                                            'fullyBundledPricePerStay', 'Not found')),
                        'photos': []
                    } for i in hotels_result if
                    re.sub(r' miles', '', i['landmarks'][0].get('distance')) <= str(user_center_distance)
                }

                hotels_list = data['list_of_hotels']
            if not user_show_photo:
                for i_hotel in hotels_list:
                    bot.send_message(message.chat.id,
                                     f"🏨 Отель: {hotels_list[i_hotel]['hotel_name']}\n"
                                     f"🔗 Ссылка: {hotels_list[i_hotel]['hotel_website']}\n"
                                     f"🗺️ Адрес: {hotels_list[i_hotel]['hotel_address']}\n"
                                     f"📍 До центра: {hotels_list[i_hotel]['distance_from_center']}\n"
                                     f"📅 Период проживания: с {user_arrival_date} по {user_departure_date}\n"
                                     f"💵 Цена за ночь: ${hotels_list[i_hotel]['price_for_certain_period']}\n"
                                     f"💵 Цена за период проживания: "
                                     f"{''.join(hotels_list[i_hotel]['full_bundle_price'])}",
                                     disable_web_page_preview=True
                                     )
                    add_new_value(user_id, user_command, request_date, hotels_list[i_hotel]['hotel_website'])
                bot.send_message(message.from_user.id, '❤ По вашему запросу было найдено {} результата'.format(
                    len(hotels_list)
                ))
            else:
                get_photo(message)
                with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
                    for i_hotel in data['list_of_hotels']:
                        text = f"🏨 Отель: {hotels_list[i_hotel]['hotel_name']}\n" \
                               f"🔗 Ссылка: {hotels_list[i_hotel]['hotel_website']}\n" \
                               f"🗺️ Адрес: {hotels_list[i_hotel]['hotel_address']}\n" \
                               f"📍 До центра: {hotels_list[i_hotel]['distance_from_center']}\n" \
                               f"📅 Период проживания: с {user_arrival_date} по {user_departure_date}\n" \
                               f"💵 Цена за ночь: ${hotels_list[i_hotel]['price_for_certain_period']}\n" \
                               f"💵 Цена за период проживания: " \
                               f"{''.join(hotels_list[i_hotel]['full_bundle_price'])}"

                        photos = [InputMediaPhoto(media=url, caption=text) if num == 0
                                  else InputMediaPhoto(media=url)
                                  for num, url in enumerate(data['list_of_hotels'][i_hotel]['photos'])]

                        bot.send_media_group(message.chat.id, photos)
                        add_new_value(user_id, user_command, request_date, hotels_list[i_hotel]['hotel_website'])
                bot.send_message(message.from_user.id, '❤ По вашему запросу было найдено {} результата'.format(
                    len(hotels_list)
                ))
        else:
            bot.send_message(message.from_user.id, '😭 По вашему запросу ничего не найдено.')
