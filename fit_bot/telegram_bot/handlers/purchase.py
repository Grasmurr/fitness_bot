from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import date
from django.shortcuts import get_object_or_404
from django.db.models import F

from telegram_bot.loader import bot
from telegram_bot.states import States
from telegram_bot.models import UnpaidUser, PaidUser, UserCalories, BankCards


ADMIN_CHAT_ID = 58790442
user_data = {}


# @bot.message_handler(func=lambda message: message.text == 'Приобрести подписку на курс')
# def subscription(message: Message):
#     user_id = message.from_user.id
#     bot.send_message(chat_id=user_id, text='Секундочку...')
#     if user_id not in user_data:
#         user_data[user_id] = {'state': States.START}
#     user_id = message.chat.id
#     markup = InlineKeyboardMarkup()
#     button1 = InlineKeyboardButton(text='Ознакомлен!', callback_data='acknowledged')
#     markup.add(button1)
#     bot.send_document(chat_id=user_id,
#                       document=open('/app/fit_bot/telegram_bot/data/assets/Original ticket-542.pdf', 'rb'),
#                       caption='Для того, чтобы приобрести подписку на продукт, '
#                               '\nВам необходимо ознакомиться с договором оферты:', reply_markup=markup)


# @bot.callback_query_handler(func=lambda call: call.data == 'acknowledged')
@bot.message_handler(func=lambda message: message.text == 'Приобрести подписку на курс')
def handle_acknowledged(call):
    user_id = call.from_user.id
    if user_id not in user_data:
        user_data[user_id] = {'state': States.START}

    bot.send_message(user_id, ' Для начала введи свои инициалы, чтобы после оплаты мы проверили перевод\n\n'
                              'Например: Имя и Отчество')
    user_data[user_id] = {'state': States.ASK_INITIALS}


@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get('state') == States.ASK_INITIALS)
def ask_initials(message: Message):
    user_id = message.chat.id
    initials = message.text.strip()

    if len(initials.split()) == 2:

        user_data[user_id]['initials'] = initials
        user_data[user_id]['state'] = States.CONTINUE_INITIALS  # Сбрасываем состояние
        continue_initials(message)
    else:
        bot.send_message(user_id, 'Пожалуйста, введите свои инициалы (имя и отчество) через пробел.')


@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get('state') == States.CONTINUE_INITIALS)
def continue_initials(message: Message):
    user_id = message.chat.id
    markup = InlineKeyboardMarkup()
    button1 = InlineKeyboardButton(text='Продолжить', callback_data=f'co{user_id}')
    button2 = InlineKeyboardButton(text='Изменить', callback_data=f'ca{user_id}')
    markup.add(button1, button2)
    bot.send_message(text=f"Ты ввел следущие инициалы: "
                          f"{user_data[user_id]['initials']}, продолжить?", chat_id=user_id, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: user_data.get(call.message.chat.id, {}).get('state') == States.CONTINUE_INITIALS)
def continue_initials2(call):
    user_id = call.message.chat.id
    req = call.data
    if req[:2] == 'co':
        user_data[user_id]['state'] = States.START
        subscription_payment(call.message)
    else:
        bot.delete_message(chat_id=user_id, message_id=call.message.message_id)
        handle_acknowledged(call)


def subscription_payment(message: Message):
    initials = message.text

    user_id = message.chat.id
    user_data[user_id]['initials'] = initials

    markup = InlineKeyboardMarkup()

    # Получаем список банков из модели BankCards
    banks = BankCards.objects.filter(number_of_activations__lte=46)
    for bank in banks:
        # Добавляем кнопку выбора банка
        bank_button = InlineKeyboardButton(bank.bank_name, callback_data=f'bank_{bank.card_number}')
        markup.add(bank_button)

    bot.send_message(user_id, f"Хорошо, а теперь выбери удобный банк оплаты:", reply_markup=markup)


# Обработчик нажатия на кнопку выбора банка
@bot.callback_query_handler(func=lambda call: call.data.startswith('bank_'))
def select_bank(call):
    bank_id = call.data.split('_')[1]
    bank = get_object_or_404(BankCards, card_number=bank_id)
    user_data[call.message.chat.id]['selected_bank'] = bank.card_number

    # Отправляем сообщение с реквизитами для оплаты и кнопкой "Я оплатил"
    markup = InlineKeyboardMarkup()
    pay_button = InlineKeyboardButton('Я оплатил', callback_data='paid')
    markup.add(pay_button)
    bot.send_message(call.message.chat.id, f"Круто, а теперь лови реквизиты для оплаты: "
                                           f"\n\nНомер карты: {bank.card_number}", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'paid')
def handle_payment(call):
    user_id = call.message.chat.id
    markup = InlineKeyboardMarkup()
    confirm_button = InlineKeyboardButton('Подтверждаю', callback_data='confirm_payment')
    back_button = InlineKeyboardButton('Назад', callback_data='go_back')
    markup.add(confirm_button, back_button)
    bot.edit_message_text(chat_id=user_id, message_id=call.message.message_id,
                          text="Вы уверены, что перевели?",
                          reply_markup=markup)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data == 'confirm_payment')
def confirm_payment(call):
    user_id = call.message.chat.id
    markup = InlineKeyboardMarkup()
    button1 = InlineKeyboardButton(text='Подтвердить', callback_data=f'confsubs{user_id}')
    button2 = InlineKeyboardButton(text='Отмена', callback_data=f'canc{user_id}')
    markup.add(button1, button2)
    if call.from_user.username is not None:
        bot.send_message(ADMIN_CHAT_ID,
                         f"Пользователь {user_id}, {' '.join(user_data[user_id]['initials'].split()[-3:-1])} "
                         f"@{call.from_user.username} оплатил подписку.",
                         reply_markup=markup)
    else:
        bot.send_message(ADMIN_CHAT_ID,
                         f"Пользователь {user_id}, {' '.join(user_data[user_id]['initials'].split()[-3:-1])} "
                         f"username отсутствует, оплатил подписку.",
                         reply_markup=markup)
    bot.send_message(user_id, "Доступ к 21FIT отправим не более чем за 24 часа...")
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data[:8] == 'confsubs' or call.data[:4] == 'canc')
def approve_payment(call):
    if call.data[:8] == 'confsubs':

        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        markup = InlineKeyboardMarkup()
        button1 = InlineKeyboardButton(text='Заполнить!', callback_data='fillthetest')
        markup.add(button1)
        UnpaidUser.objects.filter(user_id=int(call.data[8:])).update(has_paid=True)

        BankCards.objects.filter(card_number=user_data[int(call.data[8:])]['selected_bank']).update(
            number_of_activations=F('number_of_activations') + 1)

        bot.send_message(chat_id=int(call.data[8:]), text='Ваша подписка подтверждена! '
                                             'С завтрашнего дня вам начнут приходить тренировки и инструкции к ним!'
                                             '\nА пока что, просим вас заполнить небольшой опросник!',
                         reply_markup=markup)

    else:
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        bot.send_message(int(call.data[4:]),
                         'Кажется, что-то пошло не так и вам не одобрили подписку,'
                         ' либо вы случайно нажали на кнопку оплаты')


@bot.callback_query_handler(func=lambda call: call.data == 'go_back')
def go_back(call):
    user_id = call.message.chat.id
    markup = InlineKeyboardMarkup()
    pay_button = InlineKeyboardButton('Я оплатил', callback_data='paid')
    markup.add(pay_button)
    bot.edit_message_text(chat_id=user_id, message_id=call.message.message_id,
                          text=f"Хорошо! Вот реквизиты для оплаты: \n\nномер карты: {CARD_NUMBER}",
                          reply_markup=markup)
    bot.answer_callback_query(call.id)


