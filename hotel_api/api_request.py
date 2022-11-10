import json
import re
from typing import Dict, Optional

import requests
from telebot.types import InputMediaPhoto, Message

from loader import bot, headers


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
        return None


def parse_destinations(city_name: str) -> Dict[str, str]:
    """
    Функция, которая парсит айди назначений по городу, который ввёл пользователь.
    Добавляет все результаты в словарь destinations_ids.
    :param city_name: город, который ввёл пользователь боту.
    :return destinations_ids: словарь, где "Наименование места: Номер назначения".
    """
    url = 'https://hotels4.p.rapidapi.com/locations/v2/search'
    query = {'query': city_name, 'locate': 'en_EN', 'currency': 'USD'}
    response = request_to_api(url, headers, query)

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
    url = 'https://hotels4.p.rapidapi.com/properties/get-hotel-photos'

    with bot.retrieve_data(message.chat.id) as data:
        for hotel in data['list_of_hotels']:
            query = {'id': hotel}
            response_for_hotels_photo = request_to_api(url=url, headers=headers, querystring=query)
            if response_for_hotels_photo:
                result_of_photos = json.loads(response_for_hotels_photo)['roomImages'][0]['images'][0:data[
                    'photos_to_show']]

                for photo in result_of_photos:
                    photo_url = photo['baseUrl'].format(size="z")
                    data['list_of_hotels'][hotel]['photos'].append(photo_url)


def find_hotels_lowprice(message: Message) -> None:
    """
    Функция нахождения отелей по низкой цене с параметрами пользователя.
    Собираем все критерии для поиска в отдельные переменные.
    Отправляем соответствующий запрос к API и получаем результат.
    Далее обрабатываем этот результат и записываем в data['list_of_hotels'].
    Если пользователь не желает просматривать фотографии отелей, то просто
    выводим информацию о каждом отеле.
    Если пользователь хочет посмотреть фотографии отелей, то вызывается функция get_photo.
    :param message: (Message) сообщение пользователя, нужно для обращения к его id, чтобы взять
    оттуда параметры для запроса.
    """
    url_for_hotels_id_list = 'https://hotels4.p.rapidapi.com/properties/list'

    with bot.retrieve_data(message.chat.id) as data:
        user_destinationid = data['destinationID']
        user_show_photo = data['show_photo']
        user_total_hotels = data['hotels_to_show']
        user_arrival_date = data['arrival_date']
        user_departure_date = data['departure_date']

    query = {"destinationId": user_destinationid,
             "pageNumber": "1",
             "pageSize": user_total_hotels,
             "checkIn": user_arrival_date,
             "checkOut": user_departure_date,
             "adults1": "1",
             "sortOrder": "PRICE",
             "locale": "en_EN",
             "currency": "USD",
             }

    response_hotels_id_list = request_to_api(url=url_for_hotels_id_list, headers=headers, querystring=query)
    if response_hotels_id_list:
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
                                               "photos": []
                                               } for i in result_for_hotels_id
                                          }
                user_lowprice_hotels_list = data['list_of_hotels']
            if not user_show_photo:
                for hotel in user_lowprice_hotels_list:
                    bot.send_message(message.chat.id,
                                     f"🏨 Отель: {user_lowprice_hotels_list[hotel]['hotel_name']}\n"
                                     f"🔗 Ссылка: {user_lowprice_hotels_list[hotel]['hotel_website']}\n"
                                     f"🗺️ Адрес: {user_lowprice_hotels_list[hotel]['hotel_address']}\n"
                                     f"📍 До центра: {user_lowprice_hotels_list[hotel]['distance_from_center']}\n"
                                     f"📅 Период проживания: с {user_arrival_date} по {user_departure_date}\n"
                                     f"💵 Цена: {user_lowprice_hotels_list[hotel]['price_for_certain_period']} $ (USD)",
                                     disable_web_page_preview=True
                                     )
            else:
                get_photo(message)
                with bot.retrieve_data(message.chat.id) as data:
                    for hotel in data['list_of_hotels']:
                        text = f"🏨 Отель: {data['list_of_hotels'][hotel]['hotel_name']}\n" \
                               f"🔗 Ссылка: {data['list_of_hotels'][hotel]['hotel_website']}\n" \
                               f"🗺️ Адрес: {data['list_of_hotels'][hotel]['hotel_address']}\n" \
                               f"📍 До центра: {data['list_of_hotels'][hotel]['distance_from_center']}\n" \
                               f"📅 Период проживания: с {user_arrival_date} по {user_departure_date}\n" \
                               f"💵 Цена: {data['list_of_hotels'][hotel]['price_for_certain_period']} $ (USD)"

                        photos = [InputMediaPhoto(media=url, caption=text) if num == 0
                                  else InputMediaPhoto(media=url)
                                  for num, url in enumerate(data['list_of_hotels'][hotel]['photos'])]

                        bot.send_media_group(message.chat.id, photos)
        else:
            bot.send_message(message.chat.id, '😭 По вашему запросу ничего не найдено.')


def find_hotels_highprice(message: Message) -> None:
    """
    Функция нахождения отелей по высокой цене с параметрами пользователя.
    Собираем все критерии для поиска в отдельные переменные.
    Отправляем соответствующий запрос к API и получаем результат.
    Далее обрабатываем этот результат и записываем в data['list_of_hotels'].
    Если пользователь не желает просматривать фотографии отелей, то просто
    выводим информацию о каждом отеле.
    Если пользователь хочет посмотреть фотографии отелей, то вызывается функция get_photo.
    :param message: (Message) сообщение пользователя, нужно для обращения к его id, чтобы взять
    оттуда параметры для запроса.
    """
    url_for_hotels_id_list = 'https://hotels4.p.rapidapi.com/properties/list'

    with bot.retrieve_data(message.chat.id) as data:
        print(data)
        user_destinationid_hp = data['destinationID']
        user_show_photo_hp = data['show_photo']
        user_total_hotels_hp = data['hotels_to_show']
        user_arrival_date_hp = data['arrival_date']
        user_departure_date_hp = data['departure_date']

    query_hp = {"destinationId": user_destinationid_hp,
                "pageNumber": "1",
                "pageSize": user_total_hotels_hp,
                "checkIn": user_arrival_date_hp,
                "checkOut": user_departure_date_hp,
                "adults1": "1",
                "sortOrder": "PRICE_HIGHEST_FIRST",
                "locale": "en_EN",
                "currency": "USD",
                }

    response_hotels_id_list = request_to_api(url=url_for_hotels_id_list, headers=headers, querystring=query_hp)
    if response_hotels_id_list:
        result_for_hotels_id = json.loads(response_hotels_id_list)['data']['body']['searchResults']['results']
        if result_for_hotels_id:
            print(result_for_hotels_id)
            with bot.retrieve_data(message.chat.id) as data:
                data['list_of_hotels'] = {i.get('id'):
                                              {'hotel_name': i.get('name'),
                                               'hotel_address': i['address'].get('streetAddress'),
                                               "distance_from_center": i["landmarks"][0].get("distance"),
                                               "hotel_website": f"https://hotels.com/ho{i.get('id')}",
                                               'price_for_certain_period': int(re.sub(r'[^0-9]+', '',
                                                                                      i['ratePlan']['price'].get(
                                                                                          'current'))),
                                               "photos": []
                                               } for i in result_for_hotels_id
                                          }
                user_highprice_hotels_list = data['list_of_hotels']
                print(len(user_highprice_hotels_list))
            if not user_show_photo_hp:
                for hotel in user_highprice_hotels_list:
                    bot.send_message(message.chat.id,
                                     f"🏨 Отель: {user_highprice_hotels_list[hotel]['hotel_name']}\n"
                                     f"🔗 Ссылка: {user_highprice_hotels_list[hotel]['hotel_website']}\n"
                                     f"🗺️ Адрес: {user_highprice_hotels_list[hotel]['hotel_address']}\n"
                                     f"📍 До центра: {user_highprice_hotels_list[hotel]['distance_from_center']}\n"
                                     f"📅 Период проживания: с {user_arrival_date_hp} по {user_departure_date_hp}\n"
                                     f"💵 Цена: {user_highprice_hotels_list[hotel]['price_for_certain_period']} $ (USD)",
                                     disable_web_page_preview=True
                                     )
            else:
                get_photo(message)
                with bot.retrieve_data(message.chat.id) as data:
                    for hotel in data['list_of_hotels']:
                        text = f"🏨 Отель: {data['list_of_hotels'][hotel]['hotel_name']}\n" \
                               f"🔗 Ссылка: {data['list_of_hotels'][hotel]['hotel_website']}\n" \
                               f"🗺️ Адрес: {data['list_of_hotels'][hotel]['hotel_address']}\n" \
                               f"📍 До центра: {data['list_of_hotels'][hotel]['distance_from_center']}\n" \
                               f"📅 Период проживания: с {user_arrival_date_hp} по {user_departure_date_hp}\n" \
                               f"💵 Цена: {data['list_of_hotels'][hotel]['price_for_certain_period']} $ (USD)"

                        photos = [InputMediaPhoto(media=url, caption=text) if num == 0
                                  else InputMediaPhoto(media=url) for num, url in enumerate(
                            data['list_of_hotels'][hotel]['photos']
                        )]

                        bot.send_media_group(message.chat.id, photos)
        else:
            bot.send_message(message.chat.id, '😭 По вашему запросу ничего не найдено.')
