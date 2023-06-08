from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from django.utils import timezone
from telebot import types
import re
import requests
import json
import csv
from collections import Counter

from telegram_bot.loader import bot
from telegram_bot.states import States
from telegram_bot.models import PaidUser, UnpaidUser, UserCalories

user_data = {}


def preprocess(text):
    # Приводим к нижнему регистру, удаляем специальные символы и токенизируем
    return re.findall(r'\b\w+\b', text.lower())


# Открываем и читаем файл, а также сохраняем его данные
def search_food(query):
    url = "https://fs2.tvoydnevnik.com/api2/food_search/search"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {
        "jwt": "false",
        "DeviceSize": "XSmall",
        "DeviceSizeDiary": "XSmall",
        "query[count_on_page]": 5,
        "query[page]": 1,
        "query[name]": query,
        "platformId": 101,
    }

    response = requests.post(url, headers=headers, data=data)
    response_dict = json.loads(response.text)

    dish_list = []
    for i, food_item in enumerate(response_dict["result"]["list"]):
        name = food_item['food']['name']
        nutrients = food_item['food']['nutrientsShort']
        dish_list.append((name, nutrients))

    return dish_list


def get_dish_by_number(dish_list, number):
    if 0 <= number < len(dish_list):
        return dish_list[number]
    else:
        return None


# Функция для расчета пищевой ценности на основе индекса блюда и веса в граммах
# def calculate_nutrients(top5_dishes, right_dish_index, grams):
#     # Находим выбранное блюдо по индексу
#     chosen_dish_name = top5_dishes[right_dish_index - 1]
#
#     # Находим данные о блюде в базе по названию
#     chosen_dish_data = next(dish for dish in dishes_data if dish['Title'] == chosen_dish_name)
#
#     # Рассчитываем пищевую ценность на основе веса в граммах
#     calories = float(chosen_dish_data['Calories']) * grams / 100
#     proteins = float(chosen_dish_data['Proteins']) * grams / 100
#     fats = float(chosen_dish_data['Fats']) * grams / 100
#     carbohydrates = float(chosen_dish_data['Carbohydrates']) * grams / 100
#
#     # Возвращаем рассчитанную пищевую ценность
#     return {
#         'Title': chosen_dish_name,
#         'Calories': calories,
#         'Proteins': proteins,
#         'Fats': fats,
#         'Carbohydrates': carbohydrates
#     }


@bot.message_handler(func=lambda message: message.text == 'Мой дневник калорий 📆')
def handle_update_calories(message):
    user_id = message.from_user.id
    # Здесь можно установить состояние пользователя на States.UPDATE_CALORIES

    # Получаем данные о калориях из вашей модели UserCalories и вычисляем оставшиеся калории

     # Замените нули на данные о калориях из модели UserCalories

    user = PaidUser.objects.get(user=user_id)
    delta_days = (timezone.now().date() - user.paid_day).days
    current_day = delta_days

    if current_day != 0:


        if user_id not in user_data:
            # Создаем словарь для пользователя, если он еще не существует
            user_data[user_id] = {day: [0, 0, 0, []] for day in range(1, 22)}

        user_calories = user_data[user_id][current_day]
        daily_norm = user.calories

        total_snacks_calories = sum(user_calories[3])
        remaining_calories = round(daily_norm - (user_calories[0] + user_calories[1] + user_calories[2] + total_snacks_calories), 1)

        snacks_text = ''
        for i, snack_calories in enumerate(user_calories[3], start=1):
            snacks_text += f"🍝 перекус №{i} - {snack_calories}\n"

        text = (
            f"🍳 Завтрак - {user_calories[0]} ккал\n"
            f"🥗 Обед - {user_calories[1]} ккал\n"
            f"Ужин - {user_calories[2]} ккал\n"
            f"{snacks_text}\n\n"
            f"- Текущая норма калорий: {daily_norm} ккал\n- Ты еще можешь съесть: {remaining_calories} ккал до нее\n\n"
            f"Какой прием пищи хочешь изменить/добавить?\n\n"
            f"(На каждый слот добавляй сколько суммарно ты съел(а) за один прием)"
        )
        markup = create_calories_menu()
        bot.send_message(user_id, text, reply_markup=markup)
    else:
        bot.send_message(user_id, 'Курс начнется со следующего дня! '
                                  'Поэтому и заполнение калорий будет доступно с завтрашнего дня')


@bot.message_handler(func=lambda message: message.text == 'Сколько еще можно ккал?👀')
def calories_info(message: Message):
    user_id = message.from_user.id

    user = PaidUser.objects.get(user=user_id)
    delta_days = (timezone.now().date() - user.paid_day).days
    current_day = delta_days
    if current_day == 0:
        bot.send_message(user_id, 'Курс начнется со следующего дня! '
                                  'Поэтому и заполнение калорий будет доступно с завтрашнего дня')
    else:
        if user_id not in user_data:
            user_data[user_id] = {day: [0, 0, 0, []] for day in range(1, 22)}

        user_calories = user_data[user_id][current_day]
        daily_norm = user.calories
        total_snacks_calories = sum(user_calories[3])
        total_calories = user_calories[0] + user_calories[1] + user_calories[2] + total_snacks_calories
        remaining_calories = daily_norm - total_calories

        if remaining_calories <= 0:
            text = "❗️Ты переел(а) свою норму ккал, твой результат на 80% зависит от твоего питания, поэтому желательно ничего больше за сегодня не ешь, если очень тяжело, то лучше отдать предпочтение овощам (например: огурцы, морковь, капуста, брокколи)"
        else:
            text = f"🔥 Тебе можно съесть еще: {remaining_calories} ккал"
        bot.send_message(user_id, text)


def create_calories_menu():
    markup = types.InlineKeyboardMarkup()

    button_breakfast = types.InlineKeyboardButton("Завтрак", callback_data="breakfast")
    button_lunch = types.InlineKeyboardButton("Обед", callback_data="lunch")
    button_dinner = types.InlineKeyboardButton("Ужин", callback_data="dinner")
    button_snack = types.InlineKeyboardButton("Перекус", callback_data="snack")
    button_progress = types.InlineKeyboardButton("Отчет за весь период", callback_data="progress")

    markup.row(button_breakfast, button_lunch)
    markup.row(button_dinner, button_snack)
    markup.row(button_progress)

    return markup


def create_calories_add_or_remove_menu():
    markup = types.InlineKeyboardMarkup()

    button_add_remove = types.InlineKeyboardButton("Ввести новое количество", callback_data="add_remove")
    button_add_product = types.InlineKeyboardButton("Добавить продукт", callback_data="add_product")
    button_back = types.InlineKeyboardButton("Назад", callback_data="back")

    markup.row(button_add_remove)
    markup.row(button_add_product)
    markup.row(button_back)

    return markup


@bot.callback_query_handler(func=lambda call: call.data in ["breakfast", "lunch", "dinner", "snack", "progress"])
def handle_meal_callback(call):
    meal = call.data
    user_id = call.from_user.id
    # Здесь можно обновить состояние пользователя, например:
    user_data[call.from_user.id]['state'] = States.ADD_REMOVE_CALORIES
    user = PaidUser.objects.get(user=user_id)
    delta_days = (timezone.now().date() - user.paid_day).days
    current_day = delta_days

    if user_id not in user_data:
        # Создаем словарь для пользователя, если он еще не существует
        user_data[user_id] = {day: [0, 0, 0, []] for day in range(1, 22)}

    user_calories = user_data[user_id][current_day]
    user_data[call.from_user.id]['current_meal'] = meal

    if meal == "breakfast":
        text = f"Вы съели на завтрак - {user_calories[0]}\n\nХотите добавить/убавить?"
        markup = create_calories_add_or_remove_menu()
    elif meal == "lunch":
        text = f"Вы съели на обед - {user_calories[1]}\n\nХотите добавить/убавить?"
        markup = create_calories_add_or_remove_menu()
    elif meal == "dinner":
        text = f"Вы съели на ужин - {user_calories[2]}\n\nХотите добавить/убавить?"
        markup = create_calories_add_or_remove_menu()
    elif meal == 'snack':
        text = f"Хотите добавить перекус?"
        markup = create_calories_add_or_remove_menu()
    else:
        user_calories_obj = UserCalories.objects.get(user=user)
        progress_text = ''
        for day in range(1, current_day + 1):
            day_calories = getattr(user_calories_obj, f'day{day}')
            progress_text += f'День {day}: {day_calories} калорий\n'
        text = f'🧾 Тут отчет о том, сколько ккалорий ты употреблял каждый день за весь период:\n\n#21FIT\n\n{progress_text}'
        markup = types.InlineKeyboardMarkup()
        button_back = types.InlineKeyboardButton("Назад", callback_data="back")
        markup.add(button_back)

    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "add_product")
def handle_add_product_callback(call):
    user_data[call.from_user.id]['state'] = States.CHOOSE_PRODUCT
    text = "Введите название продукта:"
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data in ["add_remove", "back"])
def handle_add_remove_callback(call):
    if user_data[call.from_user.id]['state'] == States.ADD_REMOVE_CALORIES:
        action = call.data
        # Здесь можно обновить состояние пользователя в зависимости от выбора, например:
        user_data[call.from_user.id]['state'] = States.ADD_REMOVE_CALORIES if action == "add_remove" else States.START
        user_id = call.from_user.id
        user = PaidUser.objects.get(user=user_id)
        delta_days = (timezone.now().date() - user.paid_day).days
        current_day = delta_days

        user_calories = user_data[user_id][current_day]
        daily_norm = user.calories
        total_snacks_calories = sum(user_calories[3])
        remaining_calories = daily_norm - (user_calories[0] + user_calories[1] + user_calories[2] + total_snacks_calories)

        snacks_text = ''
        for i, snack_calories in enumerate(user_calories[3], start=1):
            snacks_text += f"🍝 перекус №{i} - {snack_calories}\n"

        if action == "back":
            text = (
                f"🍳 Завтрак - {user_calories[0]} ккал\n"
                f"🥗 Обед - {user_calories[1]} ккал\n"
                f"Ужин - {user_calories[2]} ккал\n"
                f"{snacks_text}\n\n"
                f"- Текущая норма калорий: {daily_norm} ккал\n- Ты еще можешь съесть: {remaining_calories} ккал до нее\n\n"
                f"Какой прием пищи хочешь изменить/добавить?\n\n"
                f"(На каждый слот добавляй сколько сумарно ты съел(а) за один прием)"
            )
            markup = create_calories_menu()
        else:
            text = "Введите новое количество калорий:"
            markup = None

        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)


def search_product(product_name):
    return ['Морковка - 30', 'Картошка - 50', 'Биг Мак - 350', 'Чизбургер - 150', 'Вода - 0']


@bot.callback_query_handler(func=lambda call: call.data in ["change_product", "cancel_product"])
def handle_change_cancel_product_callback(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    if call.data == "change_product":
        user_data[user_id]['state'] = States.CHOOSE_PRODUCT
        bot.edit_message_text("Введите название продукта:", chat_id, message_id)
    else:
        user_data[user_id]['state'] = States.START
        bot.edit_message_text("Отменено", chat_id, message_id)


@bot.callback_query_handler(func=lambda call: call.data.startswith('product'))
def handle_product_callback(call):
    user_id = call.from_user.id
    # Обработка выбора продукта, получение ID продукта и сохранение его в данных пользователя
    product_id = int(call.data.split('_')[1])
    user_data[user_id]['current_product'] = product_id

    text = "Введите количество грамм продукта."
    bot.send_message(user_id, text)
    user_data[user_id]['state'] = States.ADD_GRAMS


@bot.message_handler(func=lambda message: message.from_user.id in user_data and user_data[message.from_user.id]['state'] == States.ADD_GRAMS)
def handle_grams_input(message):
    user_id = message.from_user.id
    if message.text.isdigit():
        grams = int(message.text)
        # Получаем ID продукта, который пользователь выбрал
        product_id = user_data[user_id]['current_product']
        # Получаем продукт
        product = user_data[message.from_user.id]['product_options'][product_id - 1]
        # Вычисляем калории с учетом введенного количества грамм
        calories = get_dish_by_number(user_data[message.from_user.id]['product_options'], product_id)

        # сохраняем продукт и его калории в данных пользователя
        if 'products' not in user_data[user_id]:
            user_data[user_id]['products'] = {}
        user_data[user_id]['products'][product_id] = {'name': product, 'calories': calories}


        # генерируем текст с текущим списком продуктов
        text = "Вы добавляете следующие продукты:\n"
        for i, (product_id, product_data) in enumerate(user_data[user_id]['products'].items(), 1):
            text += f"{i}. {product_data['name']}, {product_data['calories']['Calories']} ккал\n"

        # генерируем клавиатуру с кнопками "сохранить", "добавить еще" и "изменить продукт"
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        save_button = types.InlineKeyboardButton("Сохранить", callback_data="save")
        add_more_button = types.InlineKeyboardButton("Добавить еще", callback_data="add_more")
        change_button = types.InlineKeyboardButton("Изменить продукт", callback_data="change")
        keyboard.add(save_button, add_more_button, change_button)

        bot.send_message(user_id, text, reply_markup=keyboard)
        user_data[user_id]['state'] = States.PRODUCT_ACTIONS


@bot.message_handler(func=lambda message: message.from_user.id in user_data and user_data[message.from_user.id]['state'] == States.CHOOSE_PRODUCT)
def handle_product_name(message):
    user_data[message.from_user.id]['state'] = States.CHOOSE_PRODUCT
    product_name = message.text

    product_options = search_food(product_name)  # Запустите функцию search_product

    user_data[message.from_user.id]['product_options'] = product_options

    text = "Выберите один из предложенных вариантов:\n\n"
    for i, option in enumerate(product_options, 1):
        text += f"{i}. {option}\n"

    markup = types.InlineKeyboardMarkup()
    for i in range(1, len(product_options) + 1):
        button = types.InlineKeyboardButton(str(i), callback_data=f"product_{i}")
        markup.add(button)
    button_change = types.InlineKeyboardButton("Изменить", callback_data="change_product")
    button_cancel = types.InlineKeyboardButton("Отмена", callback_data="cancel_product")
    markup.add(button_change, button_cancel)
    bot.send_message(message.chat.id, text, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("choose_product_"))
def handle_choose_product_callback(call):
    user_id = call.from_user.id
    if user_id not in user_data:
        user_data[user_id] = {}

    chosen_option = int(call.data.split("_")[-1]) - 1
    product = user_data[user_id]['product_options'][chosen_option]
    calories = int(product.split()[-1])  # Извлеките калории из строки продукта

    # Определение индекса приема пищи
    meal_index = {
        "breakfast": 0,
        "lunch": 1,
        "dinner": 2,
        "snack": 3,
    }

    # Возвращает текущее состояние приема пищи, которое было выбрано в handle_meal_callback
    current_meal = user_data[user_id]['current_meal']
    current_meal_index = meal_index[current_meal]

    user = PaidUser.objects.get(user=user_id)
    delta_days = (timezone.now().date() - user.paid_day).days
    current_day = delta_days

    user_calories = user_data[user_id][current_day]
    if current_meal == 'snack':
        user_calories[current_meal_index].append(calories)
    else:
        user_calories[current_meal_index] = calories

    user_calories_obj = UserCalories.objects.get(user=user)

    day_attr = f'day{current_day}'
    total_calories = sum(user_calories[:-1]) + sum(user_calories[-1])
    setattr(user_calories_obj, day_attr, total_calories)
    user_calories_obj.save()

    if total_calories > user.calories:
        text = "❗️Ты переел(а) свою норму ккал, твой результат на 80% зависит от твоего питания, поэтому желательно ничего больше за сегодня не ешь, если очень тяжело, то лучше отдать предпочтение овощам (например: огурцы, морковь, капуста, брокколи)"
    else:
        text = "Количество калорий успешно обновлено!"
    bot.send_message(user_id, text)

    # Возвращаемся к начальному состоянию
    user_data[call.from_user.id]['state'] = States.START


# Обработчик сообщений для ввода нового количества калорий
@bot.message_handler(func=lambda message: message.from_user.id in user_data)
def handle_new_calories(message):
    if message.from_user.id in user_data:
        if user_data[message.from_user.id]['state'] == States.ADD_REMOVE_CALORIES:
            user_id = message.from_user.id
            if message.text.isdigit():
                new_calories = int(message.text)  # Получаем новое количество калорий из сообщения пользователя
                if new_calories > 0:
                    # Определение индекса приема пищи
                    meal_index = {
                        "breakfast": 0,
                        "lunch": 1,
                        "dinner": 2,
                        "snack": 3,
                    }

                    # Здесь нужно обновить данные о калориях пользователя
                    # Возвращает текущее состояние приема пищи, которое было выбрано в handle_meal_callback
                    current_meal = user_data[user_id]['current_meal']
                    current_meal_index = meal_index[current_meal]

                    user = PaidUser.objects.get(user=user_id)
                    delta_days = (timezone.now().date() - user.paid_day).days
                    current_day = delta_days

                    user_calories = user_data[user_id][current_day]
                    if current_meal == 'snack':
                        user_calories[current_meal_index].append(new_calories)
                    else:
                        user_calories[current_meal_index] = new_calories

                    user_calories_obj = UserCalories.objects.get(user=user)

                    day_attr = f'day{current_day}'
                    total_calories = sum(user_calories[:-1]) + sum(user_calories[-1])
                    setattr(user_calories_obj, day_attr, total_calories)
                    user_calories_obj.save()

                    if total_calories > user.calories:
                        text = "❗️Ты переел(а) свою норму ккал, твой результат на 80% зависит от" \
                               " твоего питания, поэтому желательно ничего больше " \
                               "за сегодня не ешь, если очень тяжело, то лучше отдать" \
                               " предпочтение овощам (например: огурцы, морковь, капуста, брокколи)"
                    else:
                        text = "Количество калорий успешно обновлено!"
                    bot.send_message(user_id, text)

                else:
                    bot.send_message(user_id, 'Пожалуйста, введите число, больше 0')
            else:
                bot.send_message(user_id, 'Пожалуйста, введите число, больше 0')


@bot.callback_query_handler(func=lambda call: call.data in ['save', 'add_more', 'change'])
def handle_product_actions_callback(call):
    user_id = call.from_user.id
    action = call.data

    if action == 'save':
        meal_index = {
            "breakfast": 0,
            "lunch": 1,
            "dinner": 2,
            "snack": 3,
        }
        total_calories = sum(product_data['calories']['Calories'] for product_data in user_data[user_id]['products'].values())
        user = PaidUser.objects.get(user=user_id)
        delta_days = (timezone.now().date() - user.paid_day).days
        current_day = delta_days
        # Здесь нужно обновить данные о калориях пользователя
        # Возвращает текущее состояние приема пищи,
        # которое было выбрано в handle_meal_callback
        current_meal = user_data[user_id]['current_meal']
        current_meal_index = meal_index[current_meal]

        user_calories = user_data[user_id][current_day]
        if current_meal == 'snack':
            user_calories[current_meal_index].append(total_calories)
        else:
            user_calories[current_meal_index] = total_calories

        # Обработка кнопки "Сохранить"

        user_calories_obj = UserCalories.objects.get(user=user)

        day_attr = f'day{current_day}'
        setattr(user_calories_obj, day_attr, total_calories)
        user_calories_obj.save()

        bot.send_message(user_id, 'Количество калорий успешно сохранено!')
    elif action == 'add_more':
        # Обработка кнопки "Добавить еще"
        bot.send_message(user_id, 'Введите название следующего продукта.')
        user_data[user_id]['state'] = States.CHOOSE_PRODUCT
    elif action == 'change':
        # Обработка кнопки "Изменить продукт"
        text = "Выберите продукт, который вы хотите изменить:\n"
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        for i, (product_id, product_data) in enumerate(user_data[user_id]['products'].items(), 1):
            button_text = f"{i}. {product_data['name']}"  # можно использовать только i,
            # если название продукта слишком длинное
            button = types.InlineKeyboardButton(button_text, callback_data=f'change_{product_id}')
            keyboard.add(button)

        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text,
                              reply_markup=keyboard)
        user_data[user_id]['state'] = States.CHANGE_PRODUCT


@bot.callback_query_handler(func=lambda call: call.data.startswith('change_') and call.from_user.id in user_data and user_data[call.from_user.id]['state'] == States.CHANGE_PRODUCT)
def handle_selected_product_callback(call):

    user_id = call.from_user.id
    product_id = int(call.data.split('_')[1])

    # Сохраняем текущий продукт для изменения
    user_data[user_id]['current_product'] = product_id

    # Генерируем клавиатуру с кнопками "назад", "удалить" и "изменить"
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    back_button = types.InlineKeyboardButton("Назад", callback_data="back")
    delete_button = types.InlineKeyboardButton("Удалить продукт", callback_data=f'delete_{product_id}')
    change_button = types.InlineKeyboardButton("Изменить количество грамм", callback_data=f'change_grams_{product_id}')
    keyboard.add(back_button, delete_button, change_button)

    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='Что вы хотите сделать с этим продуктом?', reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data == 'back' and call.from_user.id in user_data and user_data[call.from_user.id]['state'] == States.CHANGE_PRODUCT)
def handle_back_callback(call):
    user_id = call.from_user.id
    # генерируем текст с текущим списком продуктов
    text = "Вы добавляете следующие продукты:\n"
    for i, (product_id, product_data) in enumerate(user_data[user_id]['products'].items(), 1):
        text += f"{i}. {product_data['name']}, {product_data['calories']['Calories']} ккал\n"

    # генерируем клавиатуру с кнопками "сохранить", "добавить еще" и "изменить продукт"
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    save_button = types.InlineKeyboardButton("Сохранить", callback_data="save")
    add_more_button = types.InlineKeyboardButton("Добавить еще", callback_data="add_more")
    change_button = types.InlineKeyboardButton("Изменить продукт", callback_data="change")
    keyboard.add(save_button, add_more_button, change_button)

    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data.startswith('delete_') and call.from_user.id in user_data and user_data[call.from_user.id]['state'] == States.CHANGE_PRODUCT)
def handle_delete_product_callback(call):
    user_id = call.from_user.id
    product_id = int(call.data.split('_')[1])

    # удаляем продукт
    del user_data[user_id]['products'][product_id]

    # генерируем текст с текущим списком продуктов
    text = "Вы добавляете следующие продукты:\n"
    for i, (product_id, product_data) in enumerate(user_data[user_id]['products'].items(), 1):
        text += f"{i}. {product_data['name']}, {product_data['calories']} ккал\n"

    # генерируем клавиатуру с кнопками "сохранить", "добавить еще" и "изменить продукт"
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    save_button = types.InlineKeyboardButton("Сохранить", callback_data="save")
    add_more_button = types.InlineKeyboardButton("Добавить еще", callback_data="add_more")
    change_button = types.InlineKeyboardButton("Изменить продукт", callback_data="change")
    keyboard.add(save_button, add_more_button, change_button)

    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data.startswith('change_grams_'))
def handle_change_grams_callback(call):
    user_id = call.from_user.id
    product_id = int(call.data.split('_')[2])

    # сохраняем ID продукта, количество грамм которого пользователь хочет изменить
    user_data[user_id]['current_product'] = product_id

    text = "Введите новое количество грамм продукта."
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text)
    user_data[user_id]['state'] = States.CHANGE_GRAMS


@bot.message_handler(func=lambda message: message.from_user.id in user_data and user_data[message.from_user.id]['state'] == States.CHANGE_GRAMS)
def handle_change_grams_input(message):
    user_id = message.from_user.id
    if message.text.isdigit():
        grams = int(message.text)
        product_id = user_data[user_id]['current_product']
        product = user_data[user_id]['products'][product_id]

        # Вычисляем калории с учетом нового введенного количества грамм
        calories = calculate_nutrients(user_data[user_id]['product_options'], product_id, grams)
        product['calories'] = calories

        # генерируем текст с текущим списком продуктов
        text = "Вы добавляете следующие продукты:\n"
        for i, (product_id, product_data) in enumerate(user_data[user_id]['products'].items(), 1):
            text += f"{i}. {product_data['name']}, {product_data['calories']} ккал\n"

        # генерируем клавиатуру с кнопками "сохранить", "добавить еще" и "изменить продукт"
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        save_button = types.InlineKeyboardButton("Сохранить", callback_data="save")
        add_more_button = types.InlineKeyboardButton("Добавить еще", callback_data="add_more")
        change_button = types.InlineKeyboardButton("Изменить продукт", callback_data="change")
        keyboard.add(save_button, add_more_button, change_button)

        bot.send_message(user_id, text, reply_markup=keyboard)
        user_data[user_id]['state'] = States.PRODUCT_ACTIONS

