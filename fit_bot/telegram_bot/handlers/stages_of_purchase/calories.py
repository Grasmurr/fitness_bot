from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from datetime import date
from telebot import custom_filters

from ...loader import bot
from ...states import PurchaseStates, TestStates
from ...handlers.mainmenu import get_id, create_inline_markup, create_keyboard_markup
from ...models import PaidUser
from .define_timezone import start_timezone_check

user_data = {}


def add_data(user, tag, info):
    if user not in user_data:
        user_data[user] = {}
    user_data[user][tag] = info


def is_valid_number(text):
    if text.isdigit():
        number = int(text)
        return 0 < number < 300
    return False


@bot.message_handler(commands=['test'])
def run_test(message):
    markup = InlineKeyboardMarkup()
    button1 = InlineKeyboardButton(text='go', callback_data='hi')
    markup.add(button1)
    bot.send_message(message.from_user.id, text='h', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'hi')
def run(call):
    start_calories_norm(call)


@bot.callback_query_handler(state=PurchaseStates.choose_bank,
                            func=lambda call: call.data == 'fillthetest')
def start_calories_norm(call):
    user_id, chat_id = get_id(call=call)

    markup = create_inline_markup(('Старт!', 'startsurvey'), ('Отмена', 'stopsurvey'))

    bot.send_message(text='Итак, вам будут заданы 8 вопросов касающиеся ваших данных, '
                          'по которым мы сможем определить вашу ежедневную норму калорий, '
                          'а также подобрать наилучший курс. '
                          'Чтобы начать, нажимайте старт!', chat_id=user_id, reply_markup=markup)
    bot.set_state(user_id, TestStates.start_test, chat_id)


@bot.callback_query_handler(state=TestStates.start_test,
                            func=lambda call: call.data in ['startsurvey', 'stopsurvey'])
def start_survey(call):
    user_id, chat_id = get_id(call=call)
    req = call.data
    if req == 'startsurvey':
        bot.send_message(user_id, "Какой у Вас пол? Введите 'М' или 'Ж'.", reply_markup=ReplyKeyboardRemove())
        bot.set_state(user_id, TestStates.choose_gender, chat_id)
    else:
        bot.delete_message(chat_id=user_id, message_id=call.message.message_id)


def process_start_state(message):
    name = message.from_user.full_name
    user_id, chat_id = get_id(message=message)
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

    if user_data[user_id]['gender'] == 'м':

        PaidUser.objects.filter(user=user_id).update(пол='M', цель=goal,
                                                     full_name=name, место=place, уровень=experience,
                                                     proteins=round(user_data[user_id]['weight'] * 1.6, 1))

        if goal == 'G':
            PaidUser.objects.filter(user=user_id).update(calories = round((88.362 + 13.397 * user_data[user_id][
            'weight'] + 4.799 * user_data[user_id]['height'] + 5.677 * user_data[user_id]['age']) * activity_level, 1) * 1.1)
            bot.send_message(user_id, f"Спасибо! Ваша норма калорийности составляет: "
                                      f"{round(round((88.362 + 13.397 * user_data[user_id]['weight'] + 4.799 * user_data[user_id]['height'] + 5.677 * user_data[user_id]['age']) * activity_level) * 1.1, 1)} ккал в день"
                                      f"\n\nУчитывайте это значение при составлении своего"
                                      f" рациона питания во время прохождения курса 21 день.")
        else:
            PaidUser.objects.filter(user=user_id).update(calories=round((88.362 + 13.397 * user_data[user_id][
                'weight'] + 4.799 * user_data[user_id]['height'] + 5.677 * user_data[user_id]['age']) * activity_level,
                                                                        1) * 0.9)
            bot.send_message(user_id, f"Спасибо! Ваша норма калорийности составляет: "
                                  f"{round(round((88.362 + 13.397 * user_data[user_id]['weight'] + 4.799 * user_data[user_id]['height'] + 5.677 * user_data[user_id]['age']) * activity_level, 1) * 0.9, 1)} ккал в день"
                                  f"\n\nУчитывайте это значение при составлении своего"
                                  f" рациона питания во время прохождения курса 21 день.")

    elif user_data[user_id]['gender'] == 'ж':
        PaidUser.objects.filter(user=user_id).update(пол='F', цель=goal, full_name=name, место=place,
                                                     уровень=experience,
                                                     proteins=round(user_data[user_id]['weight'] * 1.6, 1))
        if goal == 'G':
            PaidUser.objects.filter(user=user_id).update(calories=round((447.593 + 9.247 * user_data[user_id][
            'weight'] + 3.098 * user_data[user_id]['height'] + 4.33 * user_data[user_id]['age']) * activity_level, 1) * 1.125)
            bot.send_message(user_id, f"Спасибо! Ваша норма калорийности составляет: "
                                      f"{round(round((447.593 + 9.247 * user_data[user_id]['weight'] + 3.098 * user_data[user_id]['height'] + 4.33 * user_data[user_id]['age']) * activity_level, 1) * 1.125, 1)} ккал в день"
                                      f"\n\nУчитывайте это значение при составлении"
                                      f" своего рациона питания во время прохождения курса 21 день.")
        else:
            PaidUser.objects.filter(user=user_id).update(calories=round((447.593 + 9.247 * user_data[user_id][
            'weight'] + 3.098 * user_data[user_id]['height'] + 4.33 * user_data[user_id]['age']) * activity_level, 1) * 0.875)
            bot.send_message(user_id, f"Спасибо! Ваша норма калорийности составляет: "
                                  f"{round(round((447.593 + 9.247 * user_data[user_id]['weight'] + 3.098 * user_data[user_id]['height'] + 4.33 * user_data[user_id]['age']) * activity_level, 1) * 0.875, 1)} ккал в день"
                                  f"\n\nУчитывайте это значение при составлении"
                                  f" своего рациона питания во время прохождения курса 21 день.")


    start_timezone_check(message)


@bot.message_handler(state=TestStates.choose_gender, content_types=['text'])
def conduct_calories_norm(message: Message):
    user_id, chat_id = get_id(message=message)
    text = message.text
    if text.lower() in ('м', 'ж'):
        add_data(user_id, 'gender', text.lower())
        bot.send_message(user_id, "Какой у Вас рост (в см)?")
        bot.set_state(user_id, TestStates.enter_height, chat_id)
    else:
        bot.send_message(user_id, "Пожалуйста, введите 'М' или 'Ж'.")


@bot.message_handler(state=TestStates.enter_height, content_types=['text'])
def conduct_calories_nor(message: Message):
    user_id, chat_id = get_id(message=message)
    text = message.text
    if is_valid_number(text):
        add_data(user_id, 'height', int(text))
        bot.send_message(user_id, "Какой у Вас вес (в кг)?")
        bot.set_state(user_id, TestStates.enter_weight, chat_id)
    else:
        bot.send_message(user_id, "Пожалуйста, введите корректный рост (в см).")


@bot.message_handler(state=TestStates.enter_weight, content_types=['text'])
def conduct_calories_no(message: Message):
    user_id, chat_id = get_id(message=message)
    text = message.text
    if is_valid_number(text):
        add_data(user_id, 'weight', int(text))
        bot.send_message(user_id, "Сколько Вам лет?")
        bot.set_state(user_id, TestStates.enter_age, chat_id)
    else:
        bot.send_message(user_id, "Пожалуйста, введите корректный вес (в кг).")


@bot.message_handler(state=TestStates.enter_age, content_types=['text'])
def conduct_calories_n(message: Message):
    user_id, chat_id = get_id(message=message)
    text = message.text
    if is_valid_number(text):
        add_data(user_id, 'age', int(text))
        markup = create_keyboard_markup(1, 2, 3, 4, 5, row=True)
        bot.send_message(user_id,
                         'Пожалуйста, выберите цифру, наиболее соответствующую уровню вашей активности:'
                         '\n1: Малоподвижный образ жизни (тренировок нет или их очень мало)'
                         '\n2: Небольшая активность (1-3 тренировки в неделю) '
                         '\n3: Умеренная активность (3-5 тренировок в неделю)'
                         '\n4: Высокая активность (6-7 тренировок в неделю)'
                         '\n5: Очень высокая активность (тяжелые тренировки 6-7 дней в неделю)',
                         reply_markup=markup)
        bot.set_state(user_id, TestStates.ask_activity, chat_id)
    else:
        bot.send_message(user_id, "Пожалуйста, введите корректный возраст (в годах).")


@bot.message_handler(state=TestStates.ask_activity, content_types=['text'])
def conduct_calories(message: Message):
    user_id, chat_id = get_id(message=message)
    text = message.text
    if text.isdigit() and int(text) in [1, 2, 3, 4, 5]:
        add_data(user_id, 'activity', int(text))
        markup = create_keyboard_markup('Набрать вес', 'Сбросить вес', row=True)
        bot.send_message(user_id, 'Хотите ли вы набрать или сбросить вес?', reply_markup=markup)
        bot.set_state(user_id, TestStates.ask_goal, chat_id)
    else:
        bot.send_message(user_id, "Пожалуйста, введите корректную цифру (1-5)")


@bot.message_handler(state=TestStates.ask_goal, content_types=['text'])
def conduct_calorie(message: Message):
    user_id, chat_id = get_id(message=message)
    text = message.text
    if text in ['Набрать вес', 'Сбросить вес']:
        add_data(user_id, 'goal', text)
        add_data(user_id, 'experience', 'Новичок')
        add_data(user_id, 'place', 'Дом')
        process_start_state(message)
    else:
        bot.send_message(user_id, "Пожалуйста, выберите вариант из предложенных кнопок.")


    # elif user_data[user_id]['state'] == States.ASK_GOAL:
    #     if text in ['Набрать вес', 'Сбросить вес']:
    #         user_data[user_id]['goal'] = text
    #         user_data[user_id]['state'] = States.ASK_PLACE
    #         markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    #         # markup.add(KeyboardButton("Дом"), KeyboardButton("Зал"))
    #         # bot.send_message(user_id, "Где вы хотите заниматься?", reply_markup=markup)
    #         user_data[user_id]['state'] = States.START
    #         user_data[user_id]['experience'] = 'Новичок'
    #         user_data[user_id]['place'] = 'Дом'
    #
    #         process_start_state(message)
    #     else:
    #         bot.send_message(user_id, "Пожалуйста, выберите вариант из предложенных кнопок.")

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


bot.add_custom_filter(custom_filters.StateFilter(bot))

'''💳 Отлично! Теперь давайте оформим покупку курса "21 день". 
Курс стоит ХХХ рублей. Для оплаты нажмите на кнопку "Оплатить" 
и следуйте инструкциям. После успешной оплаты вы получите доступ 
к курсу и сможете начать свою фитнес-тренировку! 🚀'''
