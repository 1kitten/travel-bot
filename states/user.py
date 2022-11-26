from telebot.handler_backends import State, StatesGroup


class UserInfoState(StatesGroup):
    """
    Класс состояния пользователя для lowprice.
    """
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


class UserInfoHighPriceState(StatesGroup):
    """
    Класс состояния пользователя для highprice.
    """
    # Information about destination
    cityHigh = State()
    destinationHigh = State()
    # Information about Hotels
    hotels_to_showHigh = State()
    arrival_dateHigh = State()
    departure_dateHigh = State()
    # Information about hotels photos
    show_photoHigh = State()
    photos_to_showHigh = State()


class UserInfoBestDealsState(StatesGroup):
    """
    Класс состояния пользователя для bestdeal
    """
    # Information about destination
    cityBest = State()
    destinationBest = State()
    # Information about Hotels
    price_range = State()
    center_distance = State()
    hotels_to_showBest = State()
    arrival_dateBest = State()
    departure_dateBest = State()
    # Information about hotels photos
    show_photoBest = State()
    photos_to_showBest = State()
