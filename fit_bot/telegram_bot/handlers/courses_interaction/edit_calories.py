from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove, CallbackQuery
from telebot import custom_filters
from django.utils import timezone
from telebot import types
import re
import requests
import json
import csv
from collections import Counter

from .edit_calories_backends import create_calories_menu, \
    create_calories_add_or_remove_menu, return_calories_and_norm, get_id, \
    create_main_editing_menu, get_meal_info_text, create_keyboard_markup, meal_info, check_correctness, \
    update_courseday_calories, update_meal, one_five_markup, redact_menu_markup
from ...loader import bot
from ...states import States, CourseInteraction
from ...models import PaidUser, UnpaidUser, CourseDay, Meal
from ..mainmenu import paid_user_main_menu

user_data = {}

for_meal_from_user = {}


@bot.message_handler(state=CourseInteraction.initial, func=lambda message: message.text == 'Мой дневник калорий 📆')
def handle_update_calories(message: Message):
    try:
        user_id, chat_id = get_id(message=message)

        user = PaidUser.objects.get(user=user_id)
        current_day = (timezone.now().date() - user.paid_day).days

        if current_day == 0:
            bot.send_message(user_id, 'Курс начнется со следующего дня! '
                                      'Поэтому и заполнение калорий будет доступно с завтрашнего дня')

        elif 0 < current_day < 22:
            text, markup = create_main_editing_menu(user, current_day)
            bot.send_message(user_id, text, reply_markup=markup, parse_mode='Markdown')

        else:
            bot.send_message(user_id, 'Кажется, курс закончился!')
    except Exception as E:
        bot.send_message(305378717, f"Ошибка {E}")


@bot.callback_query_handler(state=CourseInteraction.initial,
                            func=lambda call: call.data in ["breakfast", "lunch", "dinner", "snack", "progress"])
def handle_meal_callback(call):
    user_id, chat_id = get_id(call=call)
    meal = call.data
    user = PaidUser.objects.get(user=user_id)
    current_day = (timezone.now().date() - user.paid_day).days

    if user_id not in user_data:
        user_data[user_id] = {current_day: {}}
    if meal not in user_data[user_id][current_day]:
        user_data[user_id][current_day][meal] = {}
    user_data[user_id][current_day]['selected_meal'] = meal

    text, markup = meal_info(user, current_day, user_data, user_id, meal)

    bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup)


@bot.callback_query_handler(state=CourseInteraction.initial, func=lambda call: call.data == 'back')
def back_to_menu(call: CallbackQuery):
    user_id, chat_id = get_id(call=call)
    user = PaidUser.objects.get(user=user_id)
    current_day = (timezone.now().date() - user.paid_day).days
    text, markup = create_main_editing_menu(user, current_day)
    bot.edit_message_text(chat_id=chat_id, text=text, message_id=call.message.message_id,
                          reply_markup=markup, parse_mode='Markdown')


@bot.callback_query_handler(state=CourseInteraction.initial, func=lambda call: call.data == 'add_remove')
def handle_add_remove_callback(call):
    user_id, chat_id = get_id(call=call)

    markup = create_keyboard_markup('Отмена!')

    text = "Для начала, введите название блюда"

    bot.edit_message_text(text=text, chat_id=chat_id,
                          message_id=call.message.message_id, reply_markup=None)
    bot.send_message(user_id, 'Попробуйте: ', reply_markup=markup)
    bot.set_state(user_id, CourseInteraction.enter_meal_name, chat_id)


@bot.message_handler(state=CourseInteraction.enter_meal_name, content_types=['text'])
def handle_entered_meal_name(message: Message):
    user_id, chat_id = get_id(message=message)
    answer = message.text
    if answer == 'Отмена!':
        bot.send_message(text="Вы отменили добавление нового блюда.", chat_id=chat_id)
        paid_user_main_menu(message)
        bot.set_state(user_id, CourseInteraction.initial, chat_id)
    else:
        if user_id not in for_meal_from_user:
            for_meal_from_user[user_id] = {}
        for_meal_from_user[user_id]['name'] = answer
        markup = create_keyboard_markup('Продолжить', 'Изменить', 'Отмена!')
        bot.send_message(user_id, f'Хорошо! Вы добавляете "{answer}". Продолжить, '
                                  f'изменить или отменить?', reply_markup=markup)
        bot.set_state(user_id, CourseInteraction.continue_meal_name, chat_id)


@bot.message_handler(state=CourseInteraction.continue_meal_name, content_types=['text'])
def handle_meal_name(message: Message):
    user_id, chat_id = get_id(message=message)
    answer = message.text
    if answer == 'Продолжить':
        bot.send_message(user_id, 'Хорошо! Введите количество калорий для блюда.', reply_markup=ReplyKeyboardRemove())
        bot.set_state(user_id, CourseInteraction.enter_meal_calories, chat_id)
    elif answer == 'Изменить':
        markup = create_keyboard_markup('Отмена!')
        bot.send_message(user_id, 'Введите новое название блюда:', reply_markup=markup)
        bot.set_state(user_id, CourseInteraction.enter_meal_name, chat_id)
    else:
        bot.send_message(text="Вы отменили добавление нового блюда.", chat_id=chat_id)
        paid_user_main_menu(message)
        bot.set_state(user_id, CourseInteraction.initial, chat_id)


@bot.message_handler(state=CourseInteraction.enter_meal_calories, content_types=['text'])
def handle_meal_calories(message: Message):
    user_id, chat_id = get_id(message=message)
    answer = message.text
    if answer.isdigit() and 0 < int(answer) < 5000:
        for_meal_from_user[user_id]['calories'] = answer
        bot.send_message(user_id, 'Хорошо! А теперь введите количество белков для данного продукта:')
        bot.set_state(user_id, CourseInteraction.enter_meal_protein, chat_id)
    else:
        bot.send_message(user_id, 'Кажется, вы ввели что-то неправильно. Попробуйте снова.')


@bot.message_handler(state=CourseInteraction.enter_meal_protein, content_types=['text'])
def handle_meal_calories(message: Message):
    user_id, chat_id = get_id(message=message)
    answer = message.text
    if answer.isdigit() and 0 < int(answer) < 5000:
        for_meal_from_user[user_id]['proteins'] = answer
        user = PaidUser.objects.get(user=user_id)
        current_day = (timezone.now().date() - user.paid_day).days

        bot.send_message(user_id, 'Замечательно!')
        paid_user_main_menu(message)

        user_data[user_id][current_day][user_data[user_id][current_day]['selected_meal']][
            f"{for_meal_from_user[user_id]['name']}"] = f"{for_meal_from_user[user_id]['calories']} " \
                                                        f"ккал {for_meal_from_user[user_id]['proteins']}г белков"

        course_day, created = CourseDay.objects.get_or_create(user=user, day=current_day)
        meal, _ = Meal.objects.get_or_create(course_day=course_day,
                                             meal_type=user_data[user_id][current_day]['selected_meal'])
        update_meal(meal,
                    int(for_meal_from_user[user_id]['calories']),  # калории
                    int(for_meal_from_user[user_id]['proteins']))

        update_courseday_calories(course_day)

        text, markup = meal_info(user, current_day, user_data, user_id,
                                 user_data[user_id][current_day]['selected_meal'])
        bot.send_message(text=text, chat_id=chat_id, reply_markup=markup)
        bot.set_state(user_id, CourseInteraction.initial, chat_id)

    else:
        bot.send_message(user_id, 'Кажется, вы ввели что-то неправильно. Попробуйте снова.')


@bot.callback_query_handler(state=CourseInteraction.initial, func=lambda call: call.data == 'redact')
def redact_entered_meals(call: CallbackQuery):
    user_id, chat_id = get_id(call=call)
    user = PaidUser.objects.get(user=user_id)
    current_day = (timezone.now().date() - user.paid_day).days

    user_calories, remaining_calories, daily_norm, daily_proteins_norm, \
        remaining_proteins = return_calories_and_norm(user, current_day)

    text, meals_text = get_meal_info_text(user_data[user_id][current_day]['selected_meal'],
                                          user_calories['breakfast'], user_data[user_id][current_day][
                                              user_data[user_id][current_day]['selected_meal']])
    if meals_text != 'Кажется, вы еще ничего не добавили!':

        to_send = ''
        oo = meals_text.split("\n")
        markup = redact_menu_markup(len(oo) - 1)
        user_data[user_id][current_day]['variants_to_delete'] = {}
        for i in range(1, len(oo)):
            to_send += f'{i} {oo[i - 1]}\n'
            user_data[user_id][current_day]['variants_to_delete'][i] = oo[i - 1]

        bot.edit_message_text(message_id=call.message.message_id, chat_id=chat_id,
                              text=f'Хорошо! Выберите номер блюда, которое вы хотите отредактировать: \n\n{to_send}',
                              reply_markup=markup)
    else:
        markup = InlineKeyboardMarkup()
        button = InlineKeyboardButton(text='Назад', callback_data='back')
        markup.add(button)
        bot.edit_message_text(message_id=call.message.message_id, chat_id=chat_id,
                              text=f'Кажется, вы еще ничего не добавили!',
                              reply_markup=markup)
    bot.set_state(user_id, CourseInteraction.redacting, chat_id)


@bot.callback_query_handler(state=CourseInteraction.redacting,
                            func=lambda call: call.data)
def handle_redacting(call: CallbackQuery):
    user_id, chat_id = get_id(call=call)

    if call.data.isdigit():
        user = PaidUser.objects.get(user=user_id)
        current_day = (timezone.now().date() - user.paid_day).days
        user_data[user_id][current_day]['selected_meal_to_delete'] = int(call.data)
        markup = InlineKeyboardMarkup()
        button = InlineKeyboardButton(text='Удалить', callback_data='delete')
        button1 = InlineKeyboardButton(text='Назад', callback_data='back')
        markup.add(button)
        markup.add(button1)
        bot.edit_message_text(chat_id=chat_id, text='Хотите удалить данное блюдо?',
                              message_id=call.message.message_id, reply_markup=markup)

        bot.set_state(user_id, CourseInteraction.delete_product, chat_id)

    else:
        user = PaidUser.objects.get(user=user_id)
        current_day = (timezone.now().date() - user.paid_day).days

        text, markup = meal_info(user, current_day, user_data, user_id,
                                 user_data[user_id][current_day]['selected_meal'])

        bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup)
        bot.set_state(user_id, CourseInteraction.initial, chat_id)


@bot.callback_query_handler(state=CourseInteraction.delete_product, func=lambda call: call.data)
def delete_or_not_product(call: CallbackQuery):
    user_id, chat_id = get_id(call=call)
    answer = call.data
    if answer == 'back':
        redact_entered_meals(call)
    else:
        user = PaidUser.objects.get(user=user_id)
        current_day = (timezone.now().date() - user.paid_day).days

        text, markup = meal_info(user, current_day, user_data, user_id,
                                 user_data[user_id][current_day]['selected_meal'])

        keyboard_markup = create_keyboard_markup('Получить тренировки 🎾', 'Мой дневник калорий 📆',
                                        'Сколько еще можно ккал?👀', 'Появились вопросики...')

        bot.send_message(user_id, 'Главное меню', reply_markup=keyboard_markup)



        selected_to_delete = user_data[user_id][current_day]['variants_to_delete'][user_data[user_id][current_day]['selected_meal_to_delete']]

        user_data[user_id][current_day][user_data[user_id][current_day]['selected_meal']].pop(selected_to_delete, None)
        bot.send_message(user_id, text=f'{selected_to_delete} - {user_data[user_id][current_day][user_data[user_id][current_day]["selected_meal"]]}')
        bot.edit_message_text('удалено!', chat_id, call.message.message_id, reply_markup=None)
        bot.set_state(user_id, CourseInteraction.initial, chat_id)






# def search_product(product_name):
#     return ['Морковка - 30', 'Картошка - 50', 'Биг Мак - 350', 'Чизбургер - 150', 'Вода - 0']
#
#
# @bot.callback_query_handler(func=lambda call: call.data in ["change_product", "cancel_product"])
# def handle_change_cancel_product_callback(call):
#     user_id = call.from_user.id
#     chat_id = call.message.chat.id
#     message_id = call.message.message_id
#
#     if call.data == "change_product":
#         user_data[user_id]['state'] = States.CHOOSE_PRODUCT
#         bot.edit_message_text("Введите название продукта:", chat_id, message_id)
#     else:
#         user_data[user_id]['state'] = States.START
#         bot.edit_message_text("Отменено", chat_id, message_id)
#
#
# @bot.callback_query_handler(func=lambda call: call.data.startswith('product'))
# def handle_product_callback(call):
#     user_id = call.from_user.id
#     # Обработка выбора продукта, получение ID продукта и сохранение его в данных пользователя
#     product_id = int(call.data.split('_')[1])
#     user_data[user_id]['current_product'] = product_id
#
#     text = "Введите количество грамм продукта."
#     bot.send_message(user_id, text)
#     user_data[user_id]['state'] = States.ADD_GRAMS
#
#
# @bot.message_handler(func=lambda message: message.from_user.id in user_data and user_data[message.from_user.id]['state'] == States.ADD_GRAMS)
# def handle_grams_input(message):
#     user_id = message.from_user.id
#     if message.text.isdigit():
#         grams = int(message.text)
#         # Получаем ID продукта, который пользователь выбрал
#         product_id = user_data[user_id]['current_product']
#         # Получаем продукт
#         product = user_data[message.from_user.id]['product_options'][product_id - 1]
#         # Вычисляем калории с учетом введенного количества грамм
#         calories = get_dish_by_number(user_data[message.from_user.id]['product_options'], product_id)
#
#         # сохраняем продукт и его калории в данных пользователя
#         if 'products' not in user_data[user_id]:
#             user_data[user_id]['products'] = {}
#         user_data[user_id]['products'][product_id] = {'name': product, 'calories': calories}
#         text = "Вы добавляете следующие продукты:\n"
#         for i, (product_id, product_data) in enumerate(user_data[user_id]['products'].items(), 1):
#             text += f"{i}. {product_data['name']}, {product_data['calories']['Calories']} ккал\n"
#
#         keyboard = types.InlineKeyboardMarkup(row_width=2)
#         save_button = types.InlineKeyboardButton("Сохранить", callback_data="save")
#         add_more_button = types.InlineKeyboardButton("Добавить еще", callback_data="add_more")
#         change_button = types.InlineKeyboardButton("Изменить продукт", callback_data="change")
#         keyboard.add(save_button, add_more_button, change_button)
#
#         bot.send_message(user_id, text, reply_markup=keyboard)
#         user_data[user_id]['state'] = States.PRODUCT_ACTIONS
#
#
# @bot.message_handler(func=lambda message: message.from_user.id in user_data and user_data[message.from_user.id]['state'] == States.CHOOSE_PRODUCT)
# def handle_product_name(message):
#     user_data[message.from_user.id]['state'] = States.CHOOSE_PRODUCT
#     product_name = message.text
#
#     product_options = search_food(product_name)
#
#     user_data[message.from_user.id]['product_options'] = product_options
#
#     text = "Выберите один из предложенных вариантов:\n\n"
#     for i, option in enumerate(product_options, 1):
#         text += f"{i}. {option}\n"
#
#     markup = types.InlineKeyboardMarkup()
#     for i in range(1, len(product_options) + 1):
#         button = types.InlineKeyboardButton(str(i), callback_data=f"product_{i}")
#         markup.add(button)
#     button_change = types.InlineKeyboardButton("Изменить", callback_data="change_product")
#     button_cancel = types.InlineKeyboardButton("Отмена", callback_data="cancel_product")
#     markup.add(button_change, button_cancel)
#     bot.send_message(message.chat.id, text, reply_markup=markup)
#
#
# @bot.callback_query_handler(func=lambda call: call.data.startswith("choose_product_"))
# def handle_choose_product_callback(call):
#     user_id = call.from_user.id
#     if user_id not in user_data:
#         user_data[user_id] = {}
#
#     chosen_option = int(call.data.split("_")[-1]) - 1
#     product = user_data[user_id]['product_options'][chosen_option]
#     calories = int(product.split()[-1])  # Извлеките калории из строки продукта
#
#     # Определение индекса приема пищи
#     meal_index = {
#         "breakfast": 0,
#         "lunch": 1,
#         "dinner": 2,
#         "snack": 3,
#     }
#
#     # Возвращает текущее состояние приема пищи, которое было выбрано в handle_meal_callback
#     current_meal = user_data[user_id]['current_meal']
#     current_meal_index = meal_index[current_meal]
#
#     user = PaidUser.objects.get(user=user_id)
#     delta_days = (timezone.now().date() - user.paid_day).days
#     current_day = delta_days
#
#     user_calories = user_data[user_id][current_day]
#     if current_meal == 'snack':
#         user_calories[current_meal_index].append(calories)
#     else:
#         user_calories[current_meal_index] = calories
#
#     # user_calories_obj = UserCalories.objects.get(user=user)
#
#     day_attr = f'day{current_day}'
#     total_calories = sum(user_calories[:-1]) + sum(user_calories[-1])
#     # setattr(user_calories_obj, day_attr, total_calories)
#     # user_calories_obj.save()
#
#     if total_calories > user.calories:
#         text = "❗️Ты переел(а) свою норму ккал, твой результат на 80% зависит от твоего питания, поэтому желательно ничего больше за сегодня не ешь, если очень тяжело, то лучше отдать предпочтение овощам (например: огурцы, морковь, капуста, брокколи)"
#     else:
#         text = "Количество калорий успешно обновлено!"
#     bot.send_message(user_id, text)
#
#     # Возвращаемся к начальному состоянию
#     user_data[call.from_user.id]['state'] = States.START
#
#
# # Обработчик сообщений для ввода нового количества калорий
# @bot.message_handler(func=lambda message: message.from_user.id in user_data)
# def handle_new_calories(message):
#     if message.from_user.id in user_data:
#         if user_data[message.from_user.id]['state'] == States.ADD_REMOVE_CALORIES:
#             user_id = message.from_user.id
#             if message.text.isdigit():
#                 new_calories = int(message.text)  # Получаем новое количество калорий из сообщения пользователя
#                 if new_calories > 0:
#                     # Определение индекса приема пищи
#                     meal_index = {
#                         "breakfast": 0,
#                         "lunch": 1,
#                         "dinner": 2,
#                         "snack": 3,
#                     }
#
#                     # Здесь нужно обновить данные о калориях пользователя
#                     # Возвращает текущее состояние приема пищи, которое было выбрано в handle_meal_callback
#                     current_meal = user_data[user_id]['current_meal']
#                     current_meal_index = meal_index[current_meal]
#
#                     user = PaidUser.objects.get(user=user_id)
#                     delta_days = (timezone.now().date() - user.paid_day).days
#                     current_day = delta_days
#
#                     user_calories = user_data[user_id][current_day]
#                     if current_meal == 'snack':
#                         user_calories[current_meal_index].append(new_calories)
#                     else:
#                         user_calories[current_meal_index] = new_calories
#
#                     # user_calories_obj = UserCalories.objects.get(user=user)
#
#                     day_attr = f'day{current_day}'
#                     total_calories = sum(user_calories[:-1]) + sum(user_calories[-1])
#                     # setattr(user_calories_obj, day_attr, total_calories)
#                     # user_calories_obj.save()
#
#                     if total_calories > user.calories:
#                         text = "❗️Ты переел(а) свою норму ккал, твой результат на 80% зависит от" \
#                                " твоего питания, поэтому желательно ничего больше " \
#                                "за сегодня не ешь, если очень тяжело, то лучше отдать" \
#                                " предпочтение овощам (например: огурцы, морковь, капуста, брокколи)"
#                     else:
#                         text = "Количество калорий успешно обновлено!"
#                     bot.send_message(user_id, text)
#
#                 else:
#                     bot.send_message(user_id, 'Пожалуйста, введите число, больше 0')
#             else:
#                 bot.send_message(user_id, 'Пожалуйста, введите число, больше 0')
#
#
# @bot.callback_query_handler(func=lambda call: call.data in ['save', 'add_more', 'change'])
# def handle_product_actions_callback(call):
#     user_id = call.from_user.id
#     action = call.data
#
#     if action == 'save':
#         meal_index = {
#             "breakfast": 0,
#             "lunch": 1,
#             "dinner": 2,
#             "snack": 3,
#         }
#         total_calories = sum(product_data['calories']['Calories'] for product_data in user_data[user_id]['products'].values())
#         user = PaidUser.objects.get(user=user_id)
#         delta_days = (timezone.now().date() - user.paid_day).days
#         current_day = delta_days
#         # Здесь нужно обновить данные о калориях пользователя
#         # Возвращает текущее состояние приема пищи,
#         # которое было выбрано в handle_meal_callback
#         current_meal = user_data[user_id]['current_meal']
#         current_meal_index = meal_index[current_meal]
#
#         user_calories = user_data[user_id][current_day]
#         if current_meal == 'snack':
#             user_calories[current_meal_index].append(total_calories)
#         else:
#             user_calories[current_meal_index] = total_calories
#
#         # Обработка кнопки "Сохранить"
#
#         # user_calories_obj = UserCalories.objects.get(user=user)
#         #
#         # day_attr = f'day{current_day}'
#         # setattr(user_calories_obj, day_attr, total_calories)
#         # user_calories_obj.save()
#
#         bot.send_message(user_id, 'Количество калорий успешно сохранено!')
#     elif action == 'add_more':
#         # Обработка кнопки "Добавить еще"
#         bot.send_message(user_id, 'Введите название следующего продукта.')
#         user_data[user_id]['state'] = States.CHOOSE_PRODUCT
#     elif action == 'change':
#         # Обработка кнопки "Изменить продукт"
#         text = "Выберите продукт, который вы хотите изменить:\n"
#         keyboard = types.InlineKeyboardMarkup(row_width=1)
#         for i, (product_id, product_data) in enumerate(user_data[user_id]['products'].items(), 1):
#             button_text = f"{i}. {product_data['name']}"  # можно использовать только i,
#             # если название продукта слишком длинное
#             button = types.InlineKeyboardButton(button_text, callback_data=f'change_{product_id}')
#             keyboard.add(button)
#
#         bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text,
#                               reply_markup=keyboard)
#         user_data[user_id]['state'] = States.CHANGE_PRODUCT
#
#
# @bot.callback_query_handler(func=lambda call: call.data.startswith('change_') and call.from_user.id in user_data and user_data[call.from_user.id]['state'] == States.CHANGE_PRODUCT)
# def handle_selected_product_callback(call):
#
#     user_id = call.from_user.id
#     product_id = int(call.data.split('_')[1])
#
#     # Сохраняем текущий продукт для изменения
#     user_data[user_id]['current_product'] = product_id
#
#     # Генерируем клавиатуру с кнопками "назад", "удалить" и "изменить"
#     keyboard = types.InlineKeyboardMarkup(row_width=1)
#     back_button = types.InlineKeyboardButton("Назад", callback_data="back")
#     delete_button = types.InlineKeyboardButton("Удалить продукт", callback_data=f'delete_{product_id}')
#     change_button = types.InlineKeyboardButton("Изменить количество грамм", callback_data=f'change_grams_{product_id}')
#     keyboard.add(back_button, delete_button, change_button)
#
#     bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='Что вы хотите сделать с этим продуктом?', reply_markup=keyboard)
#
#
# @bot.callback_query_handler(func=lambda call: call.data == 'back' and call.from_user.id in user_data and user_data[call.from_user.id]['state'] == States.CHANGE_PRODUCT)
# def handle_back_callback(call):
#     user_id = call.from_user.id
#     # генерируем текст с текущим списком продуктов
#     text = "Вы добавляете следующие продукты:\n"
#     for i, (product_id, product_data) in enumerate(user_data[user_id]['products'].items(), 1):
#         text += f"{i}. {product_data['name']}, {product_data['calories']['Calories']} ккал\n"
#
#     # генерируем клавиатуру с кнопками "сохранить", "добавить еще" и "изменить продукт"
#     keyboard = types.InlineKeyboardMarkup(row_width=2)
#     save_button = types.InlineKeyboardButton("Сохранить", callback_data="save")
#     add_more_button = types.InlineKeyboardButton("Добавить еще", callback_data="add_more")
#     change_button = types.InlineKeyboardButton("Изменить продукт", callback_data="change")
#     keyboard.add(save_button, add_more_button, change_button)
#
#     bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, reply_markup=keyboard)
#
#
# @bot.callback_query_handler(func=lambda call: call.data.startswith('delete_') and call.from_user.id in user_data and user_data[call.from_user.id]['state'] == States.CHANGE_PRODUCT)
# def handle_delete_product_callback(call):
#     user_id = call.from_user.id
#     product_id = int(call.data.split('_')[1])
#
#     # удаляем продукт
#     del user_data[user_id]['products'][product_id]
#
#     # генерируем текст с текущим списком продуктов
#     text = "Вы добавляете следующие продукты:\n"
#     for i, (product_id, product_data) in enumerate(user_data[user_id]['products'].items(), 1):
#         text += f"{i}. {product_data['name']}, {product_data['calories']} ккал\n"
#
#     # генерируем клавиатуру с кнопками "сохранить", "добавить еще" и "изменить продукт"
#     keyboard = types.InlineKeyboardMarkup(row_width=2)
#     save_button = types.InlineKeyboardButton("Сохранить", callback_data="save")
#     add_more_button = types.InlineKeyboardButton("Добавить еще", callback_data="add_more")
#     change_button = types.InlineKeyboardButton("Изменить продукт", callback_data="change")
#     keyboard.add(save_button, add_more_button, change_button)
#
#     bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, reply_markup=keyboard)
#
#
# @bot.callback_query_handler(func=lambda call: call.data.startswith('change_grams_'))
# def handle_change_grams_callback(call):
#     user_id = call.from_user.id
#     product_id = int(call.data.split('_')[2])
#
#     # сохраняем ID продукта, количество грамм которого пользователь хочет изменить
#     user_data[user_id]['current_product'] = product_id
#
#     text = "Введите новое количество грамм продукта."
#     bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text)
#     user_data[user_id]['state'] = States.CHANGE_GRAMS
#
#
# @bot.message_handler(func=lambda message: message.from_user.id in user_data and user_data[message.from_user.id]['state'] == States.CHANGE_GRAMS)
# def handle_change_grams_input(message):
#     user_id = message.from_user.id
#     if message.text.isdigit():
#         grams = int(message.text)
#         product_id = user_data[user_id]['current_product']
#         product = user_data[user_id]['products'][product_id]
#
#         # Вычисляем калории с учетом нового введенного количества грамм
#         # calories = calculate_nutrients(user_data[user_id]['product_options'], product_id, grams)
#         # product['calories'] = calories
#
#         # генерируем текст с текущим списком продуктов
#         text = "Вы добавляете следующие продукты:\n"
#         for i, (product_id, product_data) in enumerate(user_data[user_id]['products'].items(), 1):
#             text += f"{i}. {product_data['name']}, {product_data['calories']} ккал\n"
#
#         # генерируем клавиатуру с кнопками "сохранить", "добавить еще" и "изменить продукт"
#         keyboard = types.InlineKeyboardMarkup(row_width=2)
#         save_button = types.InlineKeyboardButton("Сохранить", callback_data="save")
#         add_more_button = types.InlineKeyboardButton("Добавить еще", callback_data="add_more")
#         change_button = types.InlineKeyboardButton("Изменить продукт", callback_data="change")
#         keyboard.add(save_button, add_more_button, change_button)
#
#         bot.send_message(user_id, text, reply_markup=keyboard)
#         user_data[user_id]['state'] = States.PRODUCT_ACTIONS


bot.add_custom_filter(custom_filters.StateFilter(bot))
