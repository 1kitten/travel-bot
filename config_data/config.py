import os
from dotenv import load_dotenv, find_dotenv
from dataclasses import dataclass

if not find_dotenv():
    exit('Переменные окружения не загружены т.к отсутствует файл .env')
else:
    load_dotenv()


@dataclass(frozen=True)
class BotConfig:
    bot_token: str
    api_key: str
    default_commands: tuple


my_config = BotConfig(
    bot_token=os.getenv('BOT_TOKEN'),
    api_key=os.getenv('RAPIDAPI_KEY'),
    default_commands=(
        ('start', "Запустить бота"),
        ('help', "Вывести справку"),
        ('hello', 'Поздороваться'),
        ('lowprice', 'Вывод самых дешевых отелей'),
        ('highprice', 'Вывод самых дорогих отелей'),
        ('bestdeal', 'Вывод отелей, наиболее подходящих по цене и расположению от центра')
    )
)

headers = {
        "X-RapidAPI-Key": my_config.api_key,
        "X-RapidAPI-Host": "hotels4.p.rapidapi.com"
    }

url_destinations = 'https://hotels4.p.rapidapi.com/locations/v2/search'
url_for_photos = 'https://hotels4.p.rapidapi.com/properties/get-hotel-photos'
url_for_hotels_id_list = 'https://hotels4.p.rapidapi.com/properties/list'
