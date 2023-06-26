import time

from telebot.types import Message, ReplyKeyboardMarkup, KeyboardButton,\
    InlineKeyboardMarkup, InlineKeyboardButton
from telebot import custom_filters

from ..loader import bot
from ..models import UnpaidUser, PaidUser
from ..states import CourseInteraction
from courses.models import Mailing


def get_id(message=None, call=None):
    if message:
        return message.from_user.id, message.chat.id
    elif call:
        return call.from_user.id, call.message.chat.id


def create_inline_markup(*args):
    markup = InlineKeyboardMarkup()
    for b, callback_data in args:
        button = InlineKeyboardButton(text=b, callback_data=callback_data)
        markup.add(button)
    return markup


def create_keyboard_markup(*args, row=False):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    if row:
        markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=len(args))
        buttons = [KeyboardButton(i) for i in args]
        markup.add(*buttons)
        return markup
    else:
        for i in args:
            button = KeyboardButton(i)
            markup.add(button)
        return markup


@bot.message_handler(commands=['start'])
def start_message(message: Message):
    user_id = message.from_user.id
    user, created = UnpaidUser.objects.get_or_create(user_id=user_id)
    if created:
        user.save()
    if user.has_paid:
        paid_user_main_menu(message)
    else:
        user = UnpaidUser(user_id=message.from_user.id)
        user.save()
        markup = create_keyboard_markup('Приобрести подписку на курс', 'Появились вопросики...')

        daily_contents = Mailing.objects.filter(day=0)

        for content in daily_contents:
            if content.content_type == 'V':
                bot.send_video(chat_id=user.user_id, video=content.video_file_id,
                               caption=content.caption, reply_markup=markup)
            elif content.content_type == 'T':
                bot.send_message(chat_id=user.user_id, text=content.caption,
                                 reply_markup=markup)
            elif content.content_type == 'P':
                bot.send_photo(chat_id=user.user_id, photo=content.photo_file_id,
                               caption=content.caption, reply_markup=markup)
            elif content.content_type == 'G':
                bot.send_document(chat_id=user.user_id, document=content.gif_file_id,
                                  caption=content.caption, reply_markup=markup)
            time.sleep(3)


@bot.message_handler(func=lambda message: message.text == 'Появились вопросики...')
def info(message: Message):
    bot.send_message(chat_id=message.chat.id,
                     text='Наш бот техподдержки - @help_fit_bot')


def just_main_menu(message: Message):
    markup = create_keyboard_markup('Приобрести подписку на курс', 'Контакт оператора')
    bot.send_message(chat_id=message.chat.id, text='Главное меню', reply_markup=markup)


def paid_user_main_menu(message: Message):
    user_id, chat_id = get_id(message=message)
    markup = create_keyboard_markup('Получить тренировки 🎾', 'Мой дневник калорий 📆',
                                    'Сколько еще можно ккал?👀', 'Появились вопросики...')
    bot.set_state(user_id, CourseInteraction.initial, chat_id)
    bot.send_message(user_id, text='Главное меню', reply_markup=markup)



bot.add_custom_filter(custom_filters.StateFilter(bot))

