import csv
import re
from collections import Counter

from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove, CallbackQuery
from telebot import custom_filters
from django.utils import timezone
from telebot import types
import re
import requests
import json
import csv
from collections import Counter

from .edit_calories_backends import create_calories_menu,\
    create_calories_add_or_remove_menu, return_calories_and_norm, get_id, \
    create_main_editing_menu, get_meal_info_text, create_keyboard_markup, meal_info, check_correctness, \
    update_courseday_calories, update_meal, one_five_markup, food_choosing_menu
from ...loader import bot
from ...states import States, CourseInteraction
from ...models import PaidUser, UnpaidUser, CourseDay, Meal
from ..mainmenu import paid_user_main_menu
from .edit_calories import user_data


calories_data = {}


@bot.message_handler(content_types=['photo'])
def return_photo_id(message: Message):
    file_id = message.photo[-1].file_id
    bot.send_message(message.from_user.id, f"Received photo with id: {file_id}")
    print(f"Received photo with id: {file_id}")
    bot.send_photo(message.chat.id, file_id)


@bot.callback_query_handler(state=CourseInteraction.initial, func=lambda call: call.data == 'add_product')
def add_new_product(call: CallbackQuery):
    user_id, chat_id = get_id(call=call)
    if user_id not in calories_data:
        calories_data[user_id] = {}

    bot.delete_message(chat_id=chat_id, message_id=call.message.message_id)
    text = "⚡️Я тут, готова помочь!\n\n" \
           "- Введите текстом название продукта/блюда"
    markup = create_keyboard_markup('Отмена!')
    bot.set_state(user_id, CourseInteraction.enter_new_product)
    bot.send_photo(photo='AgACAgIAAxkBAAIlvGSZZSve3u6eHwdvffFT25_CmUgxAALfyzEbqbHRSCITmUvvInNJAQADAgADeQADLwQ',
                   caption=text, chat_id=chat_id, reply_markup=markup)
    # bot.send_photo(photo='AgACAgIAAxkBAAL6LGSZk6v6A55yfB8rGn2U_K-VyiRtAALfyzEbqbHRSCOlCtFXAAHOJgEAAwIAA3kAAy8E',
    #                caption=text, chat_id=chat_id, reply_markup=markup)


@bot.message_handler(state=CourseInteraction.enter_new_product, content_types=['text'])
def handle_new_product(message: Message):
    user_id, chat_id = get_id(message=message)
    answer = message.text
    user = PaidUser.objects.get(user=user_id)
    current_day = (timezone.now().date() - user.paid_day).days
    meal = user_data[user_id][current_day]['selected_meal']
    course_day = CourseDay.objects.get(user=user, day=current_day)
    text, markup = meal_info(user, current_day, user_data, user_id, meal)
    if answer == 'Отмена!':
        paid_user_main_menu(message)
        bot.send_message(user_id, 'Отменено!')
        bot.send_message(text=text, chat_id=chat_id, reply_markup=markup)
    else:
        calories_data[user_id]['chosen_dish'] = answer
        bot.send_message(user_id, 'Выберите один из предложенных вариантов:', reply_markup=ReplyKeyboardRemove())
        text_answer, data, list_for_me, one_five = food_choosing_menu(answer, user_id)
        calories_data[user_id]['needed_data'] = [data, list_for_me]
        calories_data[user_id]['variants'] = text_answer
        calories_data[user_id]['needed_data_keyboard'] = one_five
        bot.send_message(user_id, text=f'{text_answer}', reply_markup=one_five)
        calories_data[user_id]['needed_data'] = [data, list_for_me]
        bot.set_state(user_id, CourseInteraction.choose_product, chat_id)


@bot.callback_query_handler(state=CourseInteraction.choose_product, func=lambda call: call.data)
def handle_choosen_product(call: CallbackQuery):
    user_id, chat_id = get_id(call=call)

    answer = call.data

    if answer == 'cancel_product':
        bot.delete_message(chat_id, message_id=call.message.message_id)
        markup = create_keyboard_markup('Получить тренировки 🎾', 'Мой дневник калорий 📆',
                                        'Сколько еще можно ккал?👀', 'Появились вопросики...')
        bot.set_state(user_id, CourseInteraction.initial, chat_id)
        bot.send_message(chat_id=chat_id, text='Главное меню', reply_markup=markup)
    else:
        nutrient_dict = {"11": "Калорий", "13": "Белков"}
        nutrients_list = calories_data[user_id]['needed_data'][0]
        choice = answer
        markup = InlineKeyboardMarkup()
        button1 = InlineKeyboardButton(text='Продолжить', callback_data='continue')
        button2 = InlineKeyboardButton(text='Назад', callback_data='back')
        markup.add(button1)
        markup.add(button2)
        if answer != 'cancelamount1':
            answer_text = f'📍Итак, вы добавляете: \n\n{calories_data[user_id]["needed_data"][1][int(choice) - 1]}\n\n'
            calories_data[user_id]['chosen_number'] = int(choice) - 1
        else:
            answer_text = f'📍Итак, вы добавляете: \n\n' \
                          f'{calories_data[user_id]["needed_data"][1][calories_data[user_id]["chosen_number"]]}\n\n'

        calories_data[user_id]['KBJU_data'] = []

        for nutrient, value in nutrients_list[calories_data[user_id]["chosen_number"]].items():
            if nutrient in nutrient_dict:  # Проверяем, есть ли питательное вещество в нашем фильтрованном словаре
                nutrient_name = nutrient_dict.get(str(nutrient), nutrient)
                value = value if value is not None else 0
                answer_text += f"{nutrient_name}: {value}\n"
                calories_data[user_id]['KBJU_data'].append(int(value))

        calories_data[user_id]['chosen_dish'] = [calories_data[user_id]["needed_data"][1][calories_data[user_id]["chosen_number"]],
                                                 calories_data[user_id]['KBJU_data']]

        bot.edit_message_text(chat_id=user_id, text=answer_text,
                              message_id=call.message.message_id, reply_markup=markup)
        bot.set_state(user_id, CourseInteraction.continue_choosing_product, chat_id)


@bot.callback_query_handler(state=CourseInteraction.continue_choosing_product, func=lambda call: call.data)
def continue_handle_choose_product(call: CallbackQuery):
    answer = call.data
    user_id, chat_id = get_id(call=call)
    if answer == 'back':
        text_answer = calories_data[user_id]['variants']
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id,
                              text=f'{text_answer}', reply_markup=calories_data[user_id]['needed_data_keyboard'])
        bot.set_state(user_id, CourseInteraction.choose_product, chat_id)
    else:
        dish = calories_data[user_id]['chosen_dish'][0]
        if 'штука' in dish.lower():
            text = f"Выберите количество штук для продукта {dish}"
            one_five = one_five_markup(second=True)
            bot.edit_message_text(chat_id=chat_id, text=text, message_id=call.message.message_id,
                                  reply_markup=one_five)
            bot.set_state(user_id, CourseInteraction.choose_amount, chat_id)
        else:
            text = 'Хорошо, введите количество грамм для данного продукта:'
            bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id,
                                  text=text, reply_markup=None)
            bot.set_state(user_id, CourseInteraction.enter_grams, chat_id)


@bot.message_handler(state=CourseInteraction.enter_grams, content_types=['text'])
def handle_grams_count(message: Message):
    user_id, chat_id = get_id(message=message)
    answer = message.text
    if answer.isdigit() and 0 < int(answer) < 5000:
        amount = int(message.text)
        markup = create_keyboard_markup('Получить тренировки 🎾', 'Мой дневник калорий 📆',
                                        'Сколько еще можно ккал?👀', 'Появились вопросики...')
        bot.send_message(chat_id=chat_id, text='Добавлено!', reply_markup=markup)
        user = PaidUser.objects.get(user=user_id)
        current_day = (timezone.now().date() - user.paid_day).days
        user_data[user_id][current_day][user_data[user_id][current_day]['selected_meal']][
            f"{calories_data[user_id]['needed_data'][1][calories_data[user_id]['chosen_number']]}"] = f"{int(calories_data[user_id]['KBJU_data'][0]) * (amount / 100)} ккал {int(calories_data[user_id]['KBJU_data'][1]) * (amount / 100)}г белков"
        # bot.send_message(user_id, text=f"{user_data[user_id][current_day][user_data[user_id][current_day]['selected_meal']]}")
        course_day, created = CourseDay.objects.get_or_create(user=user, day=current_day)
        meal, _ = Meal.objects.get_or_create(course_day=course_day,
                                             meal_type=user_data[user_id][current_day]['selected_meal'])
        update_meal(meal,
                    int(calories_data[user_id]['KBJU_data'][0]) * (amount / 100),  # калории
                    int(calories_data[user_id]['KBJU_data'][1]) * (amount / 100))

        update_courseday_calories(course_day)

        text, markup = meal_info(user, current_day, user_data, user_id,
                                 meal=user_data[user_id][current_day]['selected_meal'])
        bot.send_message(text=text, chat_id=chat_id, reply_markup=markup)
        bot.set_state(user_id, CourseInteraction.initial, chat_id)


@bot.callback_query_handler(state=CourseInteraction.choose_amount, func=lambda call: call.data)
def handle_amount(call: CallbackQuery):
    user_id, chat_id = get_id(call=call)
    answer = call.data
    if answer == 'cancelamount1':
        handle_choosen_product(call)
    else:
        amount = int(answer)
        bot.delete_message(chat_id, message_id=call.message.message_id)
        markup = create_keyboard_markup('Получить тренировки 🎾', 'Мой дневник калорий 📆',
                                        'Сколько еще можно ккал?👀', 'Появились вопросики...')
        bot.send_message(chat_id=chat_id, text='Добавлено!', reply_markup=markup)
        user = PaidUser.objects.get(user=user_id)
        current_day = (timezone.now().date() - user.paid_day).days
        user_data[user_id][current_day][user_data[user_id][current_day]['selected_meal']][
            f"{calories_data[user_id]['needed_data'][1][calories_data[user_id]['chosen_number']]}"] = f"{int(calories_data[user_id]['KBJU_data'][0]) * amount} ккал {int(calories_data[user_id]['KBJU_data'][1]) * amount}г белков"
        # bot.send_message(user_id, text=f"{user_data[user_id][current_day][user_data[user_id][current_day]['selected_meal']]}")
        course_day, created = CourseDay.objects.get_or_create(user=user, day=current_day)
        meal, _ = Meal.objects.get_or_create(course_day=course_day, meal_type=user_data[user_id][current_day]['selected_meal'])
        update_meal(meal,
                    int(calories_data[user_id]['KBJU_data'][0]) * amount,  # калории
                    int(calories_data[user_id]['KBJU_data'][1]) * amount)

        update_courseday_calories(course_day)

        text, markup = meal_info(user, current_day, user_data, user_id,
                                 meal=user_data[user_id][current_day]['selected_meal'])
        bot.send_message(text=text, chat_id=chat_id, reply_markup=markup)
        bot.set_state(user_id, CourseInteraction.initial, chat_id)





# def preprocess(text):
#     return re.findall(r'\b\w+\b', text.lower())
#
#



bot.add_custom_filter(custom_filters.StateFilter(bot))