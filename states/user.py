from telebot.handler_backends import State, StatesGroup


class UserInfoState(StatesGroup):
    # Information about destination
    city = State()
    destination = State()
    # Information about Hotels
    hotels_to_show = State()
    arrival_date = State()
    departure_date = State()
    # Information about hotels photos
    show_photo = State()
    photos_to_show = State()
