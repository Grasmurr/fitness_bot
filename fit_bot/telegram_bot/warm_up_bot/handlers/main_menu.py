from ..loader import bot
from telebot.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telebot.handler_backends import State, StatesGroup
from telebot.storage import memory_storage
from telebot import custom_filters

import os

user_data = {}


class States(StatesGroup):
    START = State()
    enter_name = State()
    confirm_name = State()
    enter_phone = State()
    enter_age = State()
    enter_gender = State()
    enter_weight = State()
    enter_height = State()
    enter_activity_level = State()
    describe_problem = State()
    ask_place = State()


def get_id(message):
    return message.from_user.id, message.chat.id


@bot.message_handler(commands=['start'])
def start_message(message: Message):
    user_id, chat_id = get_id(message)
    if user_id not in user_data:
        user_data[user_id] = {'username': message.from_user.username}
    bot.set_state(user_id, States.enter_name, chat_id)
    print(list(os.walk('data/photos')))

    bot.send_photo(user_id, photo='AgACAgIAAxkBAAIB62SBvAYVsNSOmu0dsjDGXqqHNF50AAIxyzEbta8RSLtRZv9ss1SSAQADAgADeQADLwQ',
                   caption=f'👋 Привет, меня зовут Лиза\n\n'
                           f'Я виртуальный ассистент Ибрата, '
                           f'готова принять вашу заявку на личную диагностику!\n\n'
                           f'👀 *Кстати, как к вам обращаться?*\n\n'
                           f'(Введите свое имя)', reply_markup=ReplyKeyboardRemove(), parse_mode='Markdown')


@bot.message_handler(state=States.enter_name)
def get_name(message: Message):
    user_id, chat_id = get_id(message)
    name = message.text

    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = KeyboardButton('Отправить телефон', request_contact=True)
    markup.row(button1)
    text = f'*Очень приятно, {name} ❣️*\n\n' \
           'А теперь поделитесь пожалуйста *своим номером телефона*, чтобы Ибрат лично мог с вами связаться!\n\n' \
           '(Жмите на кнопку в меню)'
    bot.send_photo(user_id, photo='AgACAgIAAxkBAAIB7WSBvCk7Iocal_ss4QskerBkF9ZJAAIyyzEbta8RSCls76749M6ZAQADAgADeQADLwQ',
                   caption=text,
                   reply_markup=markup, parse_mode='Markdown')
    user_data[user_id]['name'] = name
    bot.set_state(user_id, States.enter_phone, chat_id)


@bot.message_handler(state=States.enter_phone, content_types=['contact'])
def get_age(message: Message):
    user_id, chat_id = get_id(message)

    if message.contact is not None:
        number = message.contact.phone_number
        user_data[user_id]['phone'] = number

        markup = ReplyKeyboardMarkup()
        button1 = KeyboardButton('Погнали!')
        markup.add(button1)
        bot.send_voice(chat_id, 'AwACAgIAAxkBAAIBe2SAcF8hmzZQSJNDsKLI-3ZlXDX3AAJDLAAC3ckAAUg2ON27vliZXC8E',
                       caption='📞🔥 Ибрат на связи, скорее слушайте аудио!',
                       reply_markup=markup)
    else:
        bot.send_message(user_id, 'Кажется, что-то пошло не так. Попробуйте нажать на кнопку ниже')


@bot.message_handler(state=States.enter_phone, func=lambda message: message.text == 'Погнали!')
def start_test(message: Message):
    user_id, chat_id = get_id(message)
    markup = ReplyKeyboardMarkup()
    button1 = KeyboardButton('М')
    button2 = KeyboardButton('Ж')
    markup.row(button1, button2)
    bot.send_message(user_id, '📌 *Укажите ваш пол:*\n\nМ/Ж:', reply_markup=markup, parse_mode='Markdown')
    bot.set_state(user_id, States.enter_gender, chat_id)


@bot.message_handler(state=States.enter_gender)
def get_gender(message: Message):
    user_id, chat_id = get_id(message)

    text = message.text.lower()

    if text in ['м', 'ж']:
        gender = text
        user_data[user_id]['gender'] = gender
        bot.send_message(user_id, '📌 *Укажите ваш возраст:*\n\n'
                                  '(Только цифру):', reply_markup=ReplyKeyboardRemove(), parse_mode='Markdown')
        bot.set_state(user_id, States.enter_age, chat_id)
    else:
        bot.send_message(user_id, 'Пожалуйста, введите корректный пол (М/Ж).')


@bot.message_handler(state=States.enter_age)
def get_gender(message: Message):
    user_id, chat_id = get_id(message)

    age = message.text

    if age.isdigit() and 0 < int(age) < 100:
        user_data[user_id]['age'] = int(age)
        bot.send_message(user_id, '📌 *Укажите ваш вес:*\n\n(Только цифру в кг):',
                         reply_markup=ReplyKeyboardRemove(), parse_mode='Markdown')
        bot.set_state(user_id, States.enter_weight, chat_id)
    else:
        bot.send_message(user_id, 'Пожалуйста, введите корректный возраст (только цифру от 1 до 99).')


@bot.message_handler(state=States.enter_weight)
def get_weight(message: Message):
    user_id, chat_id = get_id(message)
    text = message.text

    if text.isdigit():
        weight = int(text)
        user_data[user_id]['weight'] = weight
        bot.send_message(user_id, '📌 *Укажите ваш рост:*\n\n(Только цифру в см):',
                         reply_markup=ReplyKeyboardRemove(), parse_mode='Markdown')
        bot.set_state(user_id, States.enter_height, chat_id)
    else:
        bot.send_message(user_id, 'Пожалуйста, введите корректный вес (целое число).')


activity_levels = {1: 'Малоподвижный образ жизни (тренировок нет / тренируюсь очень редко)',
                   2: 'Небольшая активность (1-3 тренировки в неделю)',
                   3: 'Умеренная активность (3-5 тренировок в неделю)',
                   4: 'Высокая активность (6-7 тренировок в неделю)',
                   5: 'Очень высокая активность (тяжелые тренировки 6-7 дней в неделю)'}


@bot.message_handler(state=States.enter_height)
def get_height(message: Message):
    user_id, chat_id = get_id(message)
    text = message.text

    if text.isdigit():
        height = int(text)
        user_data[user_id]['height'] = height
        message = '📌*Укажите ваш уровень физической активности:*\n\n' \
                  '1: Малоподвижный образ жизни (тренировок нет / тренируюсь очень редко)\n' \
                  '2: Небольшая активность (1-3 тренировки в неделю)\n' \
                  '3: Умеренная активность (3-5 тренировок в неделю)\n' \
                  '4: Высокая активность (6-7 тренировок в неделю)\n' \
                  '5: Очень высокая активность (тяжелые тренировки 6-7 дней в неделю)'

        markup = ReplyKeyboardMarkup()
        button1 = KeyboardButton('1')
        button2 = KeyboardButton('2')
        button3 = KeyboardButton('3')
        button4 = KeyboardButton('4')
        button5 = KeyboardButton('5')
        markup.row(button1, button2, button3, button4, button5)

        bot.send_message(user_id, message, reply_markup=markup, parse_mode='Markdown')
        bot.set_state(user_id, States.enter_activity_level, chat_id)
    else:
        bot.send_message(user_id, 'Пожалуйста, введите корректный рост (целое число).')


@bot.message_handler(state=States.enter_activity_level)
def get_activity_level(message: Message):
    user_id, chat_id = get_id(message)
    text = message.text

    if text.isdigit() and int(text) in [1, 2, 3, 4, 5]:
        activity_level = int(text)
        user_data[user_id]['activity_level'] = activity_level
        bot.send_message(user_id, '*И самое важное...*\n\n- Опишите вкратце, что вас '
                                  '*беспокоит и какой результат* вы бы хотели '
                                  'от совместной работы с Ибратом?\n\n'
                                  '(Напишите короткий текст с ответом на вопрос):',
                         reply_markup=ReplyKeyboardRemove(), parse_mode='Markdown')
        bot.set_state(user_id, States.describe_problem, chat_id)
    else:
        bot.send_message(user_id, 'Пожалуйста, введите корректный уровень активности (число от 1 до 5).')


@bot.message_handler(state=States.describe_problem)
def describe_problem(message: Message):
    user_id, chat_id = get_id(message)
    text = message.text

    user_data[user_id]['problem'] = text

    bot.send_photo(user_id,
                   photo='AgACAgIAAxkBAAICEGSBvWgqfkLWQ-1mlbfMQPwDDBl7AAIzyzEbta8RSArObAbGEt9wAQADAgADeQADLwQ',
                   caption='Спасибо за предоставленную информацию!\n\n'
                           '*Ибрат свяжется с вами в течение 24 часов.*\n\n'
                           'Добро пожаловать в 21FIT! ❣️\nЕще увидимся!')

    text = f"🧾 Новая заявка, Босс!\n\n" \
           f"*Имя:* {user_data[user_id]['name']}\n" \
           f"*Пол:* {user_data[user_id]['gender']}\n" \
           f"*Телефон:* {user_data[user_id]['phone']}\n" \
           f"*Возраст:* {user_data[user_id]['age']}\n" \
           f"*Вес:* {user_data[user_id]['weight']}\n" \
           f"*Рост:* {user_data[user_id]['height']}\n" \
           f"*Физ активность:* {activity_levels[user_data[user_id]['activity_level']]}\n" \
           f"*Проблема:* {user_data[user_id]['problem']}\n" \
           f"*Username:* @{user_data[user_id]['username']}" \
           f"\n\nРада была помочь!\nС любовью, Лиза❣️"

    bot.send_message(58790442, text=text, parse_mode='Markdown')
    bot.set_state(user_id, States.START, chat_id)


# @bot.message_handler(content_types=['voice'])
# def handle_voice(message):
#     file_id = message.voice.file_id
#     print(f"Received voice with id: {file_id}", )
#     bot.send_voice(message.chat.id, file_id)
#
# @bot.message_handler(content_types=['photo'])
# def handle_photo(message):
#     file_id = message.photo[-1].file_id  # Получаем ID последней (наибольшей) фотографии
#     print(f"Received photo with id: {file_id}")
#     bot.send_photo(message.chat.id, file_id)


bot.add_custom_filter(custom_filters.StateFilter(bot))