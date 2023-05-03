import time

from telebot.types import Message, ReplyKeyboardMarkup, KeyboardButton
from telegram_bot.loader import bot
from telegram_bot.models import UnpaidUser, PaidUser, UserCalories
from courses.models import Mailing


@bot.message_handler(commands=['start'])
def start_message(message: Message):
    user_id = message.from_user.id
    user, created = UnpaidUser.objects.get_or_create(user_id=user_id)
    if created:
        user.save()
    if user.has_paid:
        # Отправьте сообщение для пользователей с подпиской на курс
        bot.send_message(chat_id=user_id, text="Вы уже приобрели подписку на курс.")
        paid_user_main_menu(message)
    else:

        user = UnpaidUser(user_id=message.from_user.id)
        user.save()

        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        button3 = KeyboardButton('Приобрести подписку на курс')
        button4 = KeyboardButton('Появились вопросики...')

        markup.add(button3)
        markup.add(button4)

        daily_contents = Mailing.objects.filter(day=0)

        # Отправляем контент пользователю через Telegram Bot API
        for content in daily_contents:
            if content.content_type == 'V':
                bot.send_video(chat_id=user.user_id, video=content.video_file_id, caption=content.caption, reply_markup=markup)
            elif content.content_type == 'T':
                bot.send_message(chat_id=user.user_id, text=content.caption, reply_markup=markup)
            elif content.content_type == 'P':
                bot.send_photo(chat_id=user.user_id, photo=content.photo_file_id, caption=content.caption, reply_markup=markup)
            elif content.content_type == 'G':
                bot.send_document(chat_id=user.user_id, document=content.gif_file_id, caption=content.caption, reply_markup=markup)
            time.sleep(3)


@bot.message_handler(func=lambda message: message.text == 'Появились вопросики...')
def info(message: Message):
    bot.send_message(chat_id=message.chat.id,
                     text='Наш бот техподдержки - @help_fit_bot')


def just_main_menu(message: Message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    button3 = KeyboardButton('Приобрести подписку на курс')
    button4 = KeyboardButton('Контакт оператора')

    markup.add(button3)
    markup.add(button4)
    bot.send_message(chat_id=message.chat.id, text='Главное меню', reply_markup=markup)


def paid_user_main_menu(message: Message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = KeyboardButton('Получить тренировки 🎾')
    button2 = KeyboardButton('Мой дневник калорий 📆')
    button3 = KeyboardButton('Сколько еще можно ккал?👀')
    button4 = KeyboardButton('Появились вопросики...')

    markup.add(button1)
    markup.add(button2)
    markup.add(button3)
    markup.add(button4)
    bot.send_message(chat_id=message.chat.id, text='Главное меню', reply_markup=markup)
