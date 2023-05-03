from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from django.utils import timezone
from telebot import types

from telegram_bot.loader import bot
from telegram_bot.states import States
from telegram_bot.models import PaidUser, UnpaidUser, UserCalories

user_data = {}


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
        remaining_calories = daily_norm - (user_calories[0] + user_calories[1] + user_calories[2] + total_snacks_calories)

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
    button_back = types.InlineKeyboardButton("Назад", callback_data="back")

    markup.row(button_add_remove)
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
                        text = "❗️Ты переел(а) свою норму ккал, твой результат на 80% зависит от твоего питания, поэтому желательно ничего больше за сегодня не ешь, если очень тяжело, то лучше отдать предпочтение овощам (например: огурцы, морковь, капуста, брокколи)"
                    else:
                        text = "Количество калорий успешно обновлено!"
                    bot.send_message(user_id, text)

                else:
                    bot.send_message(user_id, 'Пожалуйста, введите число, больше 0')
            else:
                bot.send_message(user_id, 'Пожалуйста, введите число, больше 0')
