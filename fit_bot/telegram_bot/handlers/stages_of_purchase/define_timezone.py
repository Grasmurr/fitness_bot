from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from telebot import types
import pytz
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
from ...loader import bot
from ..mainmenu import just_main_menu, paid_user_main_menu, create_keyboard_markup, get_id
from ...models import PaidUser


def start_timezone_check(message):
    user_id, chat_id = get_id(message=message)
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    location_button = types.KeyboardButton(text="Отправить местоположение",
                                           request_location=True)
    skip_button = types.KeyboardButton(text="Пропустить")
    markup.add(location_button, skip_button)
    bot.send_message(user_id, "Хотите отправить свое местоположение для определения часового пояса?",
                     reply_markup=markup)


@bot.message_handler(content_types=['location'])
def handle_location(message):
    user_id, chat_id = get_id(message=message)
    latitude = message.location.latitude
    longitude = message.location.longitude
    timezone_finder = TimezoneFinder()
    timezone_name = timezone_finder.timezone_at(lng=longitude, lat=latitude)
    timezone = pytz.timezone(timezone_name)
    PaidUser.objects.filter(user=user_id).update(timezone=timezone)
    bot.send_message(user_id, f"Ваш часовой пояс: {timezone}")
    bot.send_message(user_id, "Спасибо!", reply_markup=types.ReplyKeyboardRemove())
    paid_user_main_menu(message)


@bot.message_handler(func=lambda message: message.text == 'Пропустить')
def skip_location(message):
    user_id, chat_id = get_id(message=message)
    default_timezone = pytz.timezone("Europe/Moscow")
    bot.send_message(message.chat.id, f"Ваш часовой пояс: {default_timezone}")
    PaidUser.objects.filter(user=user_id).update(timezone=default_timezone)
    bot.send_message(user_id, "Спасибо!", reply_markup=types.ReplyKeyboardRemove())
    paid_user_main_menu(message)
