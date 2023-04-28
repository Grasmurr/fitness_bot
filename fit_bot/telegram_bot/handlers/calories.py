from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton
from datetime import date
from telegram_bot.loader import bot
from telegram_bot.states import States
from .mainmenu import just_main_menu
from telegram_bot.models import UnpaidUser, PaidUser, UserCalories
from telegram_bot.handlers.define_timezone import start_timezone_check

user_data = {}


def is_valid_number(text):
    if text.isdigit():
        number = int(text)
        return 0 < number < 300
    return False


@bot.callback_query_handler(func=lambda call: call.data == 'fillthetest')
def start_calories_norm(call):
    user_id = call.from_user.id

    if user_id not in user_data:
        user_data[user_id] = {'state': States.START}
    markup = InlineKeyboardMarkup()
    button1 = InlineKeyboardButton('Старт!', callback_data='startsurvey')
    button2 = InlineKeyboardButton('Отмена', callback_data='stopsurvey')
    markup.add(button1, button2)
    bot.send_message(text='Итак, вам будут заданы 8 вопросов касающиеся ваших данных, '
                          'по которым мы сможем определить вашу ежедневную норму калорий, '
                          'а также подобрать наилучший курс. '
                          'Чтобы начать, нажимайте старт!', chat_id=user_id, reply_markup=markup)


@bot.callback_query_handler(func = lambda call: call.from_user.id in user_data and user_data[call.from_user.id]['state'] == States.START and call.data in ['startsurvey', 'stopsurvey'])
def start_survey(call):
    user_id = call.message.chat.id
    req = call.data
    if req == 'startsurvey':
        if user_data[user_id]['state'] == States.START:
            user_data[user_id]['state'] = States.ASK_GENDER
            bot.send_message(user_id, "Какой у Вас пол? Введите 'М' или 'Ж'.", reply_markup=ReplyKeyboardRemove())
    else:
        bot.delete_message(chat_id=user_id, message_id=call.message.message_id)


def process_start_state(message):
    name = message.from_user.full_name
    user_id = message.chat.id
    response = f"Спасибо! Вот Ваши данные:\n" \
               f"Пол: {user_data[user_id]['gender']}\n" \
               f"Рост: {user_data[user_id]['height']} см\n" \
               f"Вес: {user_data[user_id]['weight']} кг\n" \
               f"Возраст: {user_data[user_id]['age']} лет\n" \
               f"Место: {user_data[user_id]['place']}\n" \
               f"Уровень: {user_data[user_id]['experience']}\n" \
               f"Цель: {user_data[user_id]['goal']}"
    bot.send_message(user_id, response)
    activity_levels = [1.2, 1.375, 1.55, 1.725, 1.9]
    activity_level = activity_levels[user_data[user_id]['activity'] - 1]

    if user_data[user_id]['experience'] == 'Новичок': experience = 'N'
    else: experience = 'P'

    if user_data[user_id]['place'] == 'Дом': place = 'H'
    else: place = 'G'

    if user_data[user_id]['goal'] == 'Набрать вес': goal = 'G'
    else: goal = 'L'

    user_info = bot.get_chat(user_id)
    username = user_info.username
    unregistered_user = PaidUser(user=user_id, username=username, paid_day=date.today())
    unregistered_user.save()
    user_calories = UserCalories(user=unregistered_user, day1=0, day2=0, day3=0, day4=0, day5=0, day6=0, day7=0,
                                 day8=0, day9=0, day10=0, day11=0, day12=0, day13=0, day14=0, day15=0, day16=0,
                                 day17=0, day18=0, day19=0, day20=0, day21=0)
    user_calories.save()

    if user_data[user_id]['gender'] == 'м':

        PaidUser.objects.filter(user=user_id).update(пол='M', цель=goal, full_name=name, место=place, уровень=experience)

        if goal == 'G':
            PaidUser.objects.filter(user=user_id).update(calories = round((88.362 + 13.397 * user_data[user_id][
            'weight'] + 4.799 * user_data[user_id]['height'] + 5.677 * user_data[user_id]['age']) * activity_level, 1) * 1.1)
            bot.send_message(user_id, f"Спасибо! Ваша норма калорийности составляет: "
                                      f"{round((88.362 + 13.397 * user_data[user_id]['weight'] + 4.799 * user_data[user_id]['height'] + 5.677 * user_data[user_id]['age']) * activity_level, 1) * 1.1} ккал в день"
                                      f"\n\nУчитывайте это значение при составлении своего"
                                      f" рациона питания во время прохождения курса 21 день.")
        else:
            PaidUser.objects.filter(user=user_id).update(calories=round((88.362 + 13.397 * user_data[user_id][
                'weight'] + 4.799 * user_data[user_id]['height'] + 5.677 * user_data[user_id]['age']) * activity_level,
                                                                        1) * 0.9)
            bot.send_message(user_id, f"Спасибо! Ваша норма калорийности составляет: "
                                  f"{round((88.362 + 13.397 * user_data[user_id]['weight'] + 4.799 * user_data[user_id]['height'] + 5.677 * user_data[user_id]['age']) * activity_level, 1) * 0.9} ккал в день"
                                  f"\n\nУчитывайте это значение при составлении своего"
                                  f" рациона питания во время прохождения курса 21 день.")

    elif user_data[user_id]['gender'] == 'ж':
        PaidUser.objects.filter(user=user_id).update(пол='F', цель=goal, full_name=name, место=place,
                                                     уровень=experience)

        if goal == 'G':
            PaidUser.objects.filter(user=user_id).update(calories=round((447.593 + 9.247 * user_data[user_id][
            'weight'] + 3.098 * user_data[user_id]['height'] + 4.33 * user_data[user_id]['age']) * activity_level, 1) * 1.1)
            bot.send_message(user_id, f"Спасибо! Ваша норма калорийности составляет: "
                                      f"{round((447.593 + 9.247 * user_data[user_id]['weight'] + 3.098 * user_data[user_id]['height'] + 4.33 * user_data[user_id]['age']) * activity_level, 1) * 1.1} ккал в день"
                                      f"\n\nУчитывайте это значение при составлении"
                                      f" своего рациона питания во время прохождения курса 21 день.")
        else:
            PaidUser.objects.filter(user=user_id).update(calories=round((447.593 + 9.247 * user_data[user_id][
            'weight'] + 3.098 * user_data[user_id]['height'] + 4.33 * user_data[user_id]['age']) * activity_level, 1) * 0.9)
            bot.send_message(user_id, f"Спасибо! Ваша норма калорийности составляет: "
                                  f"{round((447.593 + 9.247 * user_data[user_id]['weight'] + 3.098 * user_data[user_id]['height'] + 4.33 * user_data[user_id]['age']) * activity_level, 1) * 0.9} ккал в день"
                                  f"\n\nУчитывайте это значение при составлении"
                                  f" своего рациона питания во время прохождения курса 21 день.")
    start_timezone_check(message)


@bot.message_handler(func=lambda message: message.chat.id in user_data and user_data[message.chat.id]['state'] != States.START)
def conduct_calories_norm(message: Message):
    user_id = message.chat.id
    text = message.text

    if user_data[user_id]['state'] == States.ASK_GENDER:
        if text.lower() in ('м', 'ж'):
            user_data[user_id]['gender'] = text.lower()
            user_data[user_id]['state'] = States.ASK_HEIGHT
            bot.send_message(user_id, "Какой у Вас рост (в см)?")
        else:
            bot.send_message(user_id, "Пожалуйста, введите 'М' или 'Ж'.")

    elif user_data[user_id]['state'] == States.ASK_HEIGHT:
        if is_valid_number(text):
            user_data[user_id]['height'] = int(text)
            user_data[user_id]['state'] = States.ASK_WEIGHT
            bot.send_message(user_id, "Какой у Вас вес (в кг)?")
        else:
            bot.send_message(user_id, "Пожалуйста, введите корректный рост (в см).")

    elif user_data[user_id]['state'] == States.ASK_WEIGHT:
        if is_valid_number(text):
            user_data[user_id]['weight'] = int(text)
            user_data[user_id]['state'] = States.ASK_AGE
            bot.send_message(user_id, "Сколько Вам лет?")
        else:
            bot.send_message(user_id, "Пожалуйста, введите корректный вес (в кг).")

    elif user_data[user_id]['state'] == States.ASK_AGE:
        if is_valid_number(text):
            user_data[user_id]['age'] = int(text)
            user_data[user_id]['state'] = States.ASK_ACTIVITY
            markup = ReplyKeyboardMarkup(row_width=5, resize_keyboard=True)
            markup.add(KeyboardButton("1"), KeyboardButton("2"), KeyboardButton("3"), KeyboardButton("4"), KeyboardButton("5"))

            bot.send_message(user_id,
                             'Пожалуйста, выберите цифру, наиболее соответствующую уровню вашей активности:'
                             '\n1: Малоподвижный образ жизни (тренировок нет или их очень мало)'
                             '\n2: Небольшая активность (1-3 тренировки в неделю) '
                             '\n3: Умеренная активность (3-5 тренировок в неделю)'
                             '\n4: Высокая активность (6-7 тренировок в неделю)'
                             '\n5: Очень высокая активность (тяжелые тренировки 6-7 дней в неделю)', reply_markup=markup)

        else:
            bot.send_message(user_id, "Пожалуйста, выберите одну из кнопок ниже.")

    elif user_data[user_id]['state'] == States.ASK_ACTIVITY:
        if text.isdigit() and int(text) in [1, 2, 3, 4, 5]:
            user_data[user_id]['activity'] = int(text)
            user_data[user_id]['state'] = States.ASK_GOAL
            markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
            markup.add(KeyboardButton("Набрать вес"), KeyboardButton("Сбросить вес"))
            bot.send_message(user_id, 'Хотите ли вы набрать или сбросить вес?', reply_markup=markup)
        else:
            bot.send_message(user_id, "Пожалуйста, введите корректную цифру (1-5)")

    elif user_data[user_id]['state'] == States.ASK_GOAL:
        if text in ['Набрать вес', 'Сбросить вес']:
            user_data[user_id]['goal'] = text
            user_data[user_id]['state'] = States.ASK_PLACE
            markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
            # markup.add(KeyboardButton("Дом"), KeyboardButton("Зал"))
            # bot.send_message(user_id, "Где вы хотите заниматься?", reply_markup=markup)
            user_data[user_id]['state'] = States.START
            user_data[user_id]['experience'] = 'Новичок'
            user_data[user_id]['place'] = 'Дом'

            process_start_state(message)
        else:
            bot.send_message(user_id, "Пожалуйста, выберите вариант из предложенных кнопок.")

    # elif user_data[user_id]['state'] == States.ASK_PLACE:
    #     if text in ['Зал', 'Дом']:
    #         user_data[user_id]['place'] = text
    #         if user_data[user_id]['place'] == 'Зал':
    #             user_data[user_id]['state'] = States.ASK_EXPERIENCE
    #
    #             markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    #             markup.add(KeyboardButton("Никогда"), KeyboardButton("Больше 2 мес назад"),
    #                        KeyboardButton("Не занимался около 1 месяца"), KeyboardButton("Занимаюсь регулярно"))
    #             bot.send_message(user_id, "Насколько давно вы занимались в зале?", reply_markup=markup)
    #         else:
    #             user_data[user_id]['experience'] = 'Новичок'
    #             user_data[user_id]['state'] = States.START
    #             process_start_state(message)
    #     else:
    #         bot.send_message(user_id, "Пожалуйста, выберите вариант из предложенных кнопок.")
    #
    # elif user_data[user_id]['state'] == States.ASK_EXPERIENCE:
    #     if text in ['Никогда', 'Больше 2 мес назад', 'Не занимался около 1 месяца', 'Занимаюсь регулярно']:
    #         if text in ['Никогда', 'Больше 2 мес назад']:
    #             user_data[user_id]['experience'] = 'Новичок'
    #         else:
    #             user_data[user_id]['experience'] = 'Профессиональный'
    #         user_data[user_id]['state'] = States.START
    #         process_start_state(message)
    #     else:
    #         bot.send_message(user_id, "Пожалуйста, выберите вариант из предложенных кнопок.")


'''💳 Отлично! Теперь давайте оформим покупку курса "21 день". 
Курс стоит ХХХ рублей. Для оплаты нажмите на кнопку "Оплатить" 
и следуйте инструкциям. После успешной оплаты вы получите доступ 
к курсу и сможете начать свою фитнес-тренировку! 🚀'''
