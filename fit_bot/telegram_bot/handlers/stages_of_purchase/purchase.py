from telebot.types import Message, InlineKeyboardMarkup, \
    InlineKeyboardButton, CallbackQuery, ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton
from telebot import custom_filters

from datetime import date
from django.shortcuts import get_object_or_404
from django.db.models import F

from ..mainmenu import create_inline_markup, get_id, create_keyboard_markup
from ...loader import bot
from ...states import PurchaseStates
from ...models import UnpaidUser, PaidUser, BankCards

ADMIN_CHAT_ID = 58790442
# ADMIN_CHAT_ID = 305378717
user_data = {}


def add_data(user, tag, info):
    if user not in user_data:
        user_data[user] = {}
    user_data[user][tag] = info


@bot.callback_query_handler(func=lambda call: call.data == 'Go_for_it')
def after_greeting(call: CallbackQuery):
    user_id, chat_id = get_id(call=call)

    markup = create_keyboard_markup('Появились вопросики...')

    test = 'AgACAgIAAxkBAAIxZmTWibqN_mHYK-1uJs08CdoexIw0AAI4zDEb8Jm5SqYMWroMFb56AQADAgADeQADMAQ'
    official = 'AgACAgIAAxkBAAEBJA9k2rj2-rChgpOYjuzj5M0XhhxWVwAC4coxG3dI2EqAfXmGAAHDqlABAAMCAAN5AAMwBA'
    text = '👋 Привет, меня зовут Лиза\n\n' \
           'Я – виртуальный ассистент Ибрата и буду помогать вам на всем ' \
           'пути взаимодействия с ботом ☺️'

    bot.send_photo(chat_id, photo=official, caption=text, reply_markup=markup)

    markup = create_inline_markup(('Тинькофф (Россия)', 'tinkoff'), ('Click/Payme (Узбекистан)', 'click'),
                                  ('Другое', 'other'))

    bot.send_message(chat_id, text='Чтобы получить доступ к программе, выберите удобный для вас способ оплаты:',
                     reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data in ['tinkoff', 'click', 'other'])
def after_greeting(call: CallbackQuery):
    user_id, chat_id = get_id(call=call)

    answer = call.data
    if answer == 'other':
        markup = create_inline_markup(('назад', 'back_to_bank_choose'))
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id,
                              text='Чтобы выбрать другой способ оплаты, напишите Ибрату @ibrat21', reply_markup=markup)
    elif answer == 'tinkoff':
        markup = create_inline_markup(('назад', 'back_to_bank_choose'))

        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id,
                              text='Введите, пожалуйста, свои инициалы, чтобы после оплаты мы смогли проверить '
                                   'ваш перевод\n\nНапример: "Иван И."', reply_markup=markup)
        add_data(user_id, 'chosen_method', 'тинькоф')
        bot.set_state(user_id, PurchaseStates.initial, chat_id)

    elif answer == 'click':
        markup = create_inline_markup(('назад', 'back_to_bank_choose'))

        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id,
                              text='Введите, пожалуйста, свои имя и фамилию, чтобы после оплаты мы смогли '
                                   'проверить ваш перевод\n\nНапример: "Иван Иванов"', reply_markup=markup)
        add_data(user_id, 'chosen_method', 'click')
        bot.set_state(user_id, PurchaseStates.initial, chat_id)


@bot.callback_query_handler(func=lambda call: call.data == 'back_to_bank_choose')
def back_button_while_purchase(call: CallbackQuery):
    user_id, chat_id = get_id(call=call)
    markup = create_inline_markup(('Тинькофф (Россия)', 'tinkoff'), ('Click/Payme (Узбекистан)', 'click'),
                                  ('Другое', 'other'))

    bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id,
                          text='Чтобы получить доступ к программе, выберите удобный для вас способ оплаты:',
                          reply_markup=markup)


@bot.message_handler(state=PurchaseStates.initial)
def ask_initials(message: Message):
    user_id, chat_id = get_id(message=message)
    initials = message.text.strip()
    if len(initials.split()) == 2:
        markup = create_inline_markup(('Продолжить', 'continue'), ('Изменить', 'back'))
        bot.send_message(user_id, text=f'Вы ввели следущие инициалы: *{initials}*, продолжить?',
                         reply_markup=markup, parse_mode='Markdown')
        add_data(user_id, 'initials', initials)
    else:
        bot.send_message(user_id, 'Пожалуйста, введите свои инициалы через пробел. ')


@bot.callback_query_handler(state=PurchaseStates.initial, func=lambda call: call.data in ['continue', 'back'])
def handle_initials(call: CallbackQuery):
    user_id, chat_id = get_id(call=call)
    answer = call.data
    if answer == 'continue':
        search_term = user_data[user_id]['chosen_method']
        cards_with_term = BankCards.objects.filter(bank_name__icontains=search_term)
        card_number = [card.card_number for card in cards_with_term][0]

        markup = create_inline_markup(('Оплатил(а)', 'paid'), ('Назад', 'back'))

        bot.send_message(user_id, f"Доступ к программе уже близко!\n\nОсталось перевести оплату по реквизитам: "
                                  f"\n\n{card_number}", reply_markup=markup)
        bot.set_state(user_id, PurchaseStates.choose_bank, chat_id)

    else:
        bot.edit_message_text(chat_id=chat_id, text='Хорошо! Можешь ввести инициалы еще раз:',
                              message_id=call.message.message_id, reply_markup=None)


@bot.callback_query_handler(state=PurchaseStates.choose_bank, func=lambda call: call.data == 'paid')
def handle_payment(call):
    user_id, chat_id = get_id(call=call)
    markup = create_inline_markup(('Подтверждаю', 'confirm_payment'), ('Назад', 'go_back'))
    bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id,
                          text="Подтвердите, что совершили перевод 👀",
                          reply_markup=markup)


@bot.callback_query_handler(state=PurchaseStates.choose_bank,
                            func=lambda call: call.data in ['confirm_payment', 'go_back'])
def confirm_payment(call):
    user_id, chat_id = get_id(call=call)
    markup = create_inline_markup(('Подтвердить', f'confsubs{user_id}'), ('Отмена', f'canc{user_id}'))
    bot.set_state(ADMIN_CHAT_ID, PurchaseStates.choose_bank, ADMIN_CHAT_ID)
    if call.data == 'confirm_payment':
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


@bot.callback_query_handler(state=PurchaseStates.choose_bank,
                            func=lambda call: call.data[:8] == 'confsubs' or call.data[:4] == 'canc')
def approve_payment(call):
    if call.data[:8] == 'confsubs':
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        markup = InlineKeyboardMarkup()
        button1 = InlineKeyboardButton(text='Заполнить!', callback_data='fillthetest')
        markup.add(button1)
        UnpaidUser.objects.filter(user_id=int(call.data[8:])).update(has_paid=True)

        search_term = user_data[int(call.data[8:])]['chosen_method']
        BankCards.objects.filter(bank_name__icontains=search_term).update(
            number_of_activations=F('number_of_activations') + 1)
        official = 'AgACAgIAAxkBAAEBJBJk2rllWOyWYpscLJxfu7UWvw_dmwACgswxG3Rr2Er9A73F4DaK6QEAAwIAA3kAAzAE'
        bot.send_photo(chat_id=int(call.data[8:]), photo=official, caption='Ваша подписка подтверждена! '
                                                                           'С завтрашнего дня вам начнут приходить '
                                                                           'тренировки и инструкции к ним!'
                                                                           '\nА пока что, просим вас заполнить '
                                                                           'небольшой опросник!',
                       reply_markup=markup)

    else:
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        bot.send_message(int(call.data[4:]),
                         'Кажется, что-то пошло не так и вам не одобрили подписку,'
                         ' либо вы случайно нажали на кнопку оплаты')



bot.add_custom_filter(custom_filters.StateFilter(bot))

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
