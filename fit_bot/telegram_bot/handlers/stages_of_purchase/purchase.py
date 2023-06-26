from telebot.types import Message, InlineKeyboardMarkup, \
    InlineKeyboardButton, CallbackQuery, ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton
from telebot import custom_filters

from datetime import date
from django.shortcuts import get_object_or_404
from django.db.models import F

from ..mainmenu import create_inline_markup, get_id
from ...loader import bot
from ...states import PurchaseStates
from ...models import UnpaidUser, PaidUser, BankCards

ADMIN_CHAT_ID = 58790442
ADMIN_CHAT_ID = 305378717
user_data = {}


def add_data(user, tag, info):
    if user not in user_data:
        user_data[user] = {}
    user_data[user][tag] = info


@bot.message_handler(func=lambda message: message.text == 'Приобрести подписку на курс')
def handle_acknowledged(message: Message):
    user_id, chat_id = get_id(message=message)
    bot.set_state(user_id, PurchaseStates.initial, chat_id)
    bot.send_message(user_id, ' Для начала введи свои инициалы, чтобы после оплаты мы проверили перевод\n\n'
                              'Например: Имя и Отчество')


@bot.message_handler(state=PurchaseStates.initial)
def ask_initials(message: Message):
    user_id, chat_id = get_id(message=message)
    initials = message.text.strip()
    if len(initials.split()) == 2:
        markup = create_inline_markup(('Продолжить', 'continue'), ('Изменить', 'back'))
        bot.send_message(user_id, text=f'Ты ввел следущие инициалы: {initials}, продолжить?', reply_markup=markup)
        add_data(user_id, 'initials', initials)
    else:
        bot.send_message(user_id, 'Пожалуйста, введите свои инициалы (имя и отчество) через пробел.')


@bot.callback_query_handler(state=PurchaseStates.initial,
                            func=lambda call: call.data in ['continue', 'back'])
def handle_initials(call: CallbackQuery):
    user_id, chat_id = get_id(call=call)
    answer = call.data
    if answer == 'continue':
        bot.set_state(user_id, PurchaseStates.added_initials, chat_id)
        banks = BankCards.objects.filter(number_of_activations__lte=46)
        markup = InlineKeyboardMarkup()
        for bank in banks:
            button = InlineKeyboardButton(text=f'{bank.bank_name}', callback_data=f'bank_{bank.card_number}')
            markup.add(button)
        bot.send_message(user_id, f"Хорошо, а теперь выбери удобный банк оплаты:", reply_markup=markup)
        bot.set_state(user_id, PurchaseStates.choose_bank, chat_id)

    else:
        bot.edit_message_text(chat_id=chat_id, text='Хорошо! Можешь ввести инициалы еще раз:',
                              message_id=call.message.message_id, reply_markup=None)


# Обработчик нажатия на кнопку выбора банка
@bot.callback_query_handler(state=PurchaseStates.choose_bank, func=lambda call: call.data.startswith('bank_'))
def select_bank(call):
    user_id, chat_id = get_id(call=call)
    if call.data.startswith('bank_'):
        bank_id = call.data.split('_')[1]
        bank = get_object_or_404(BankCards, card_number=bank_id)
        add_data(user_id, 'selected_bank', bank.card_number)
    markup = create_inline_markup(('Я оплатил', 'paid'),)
    bot.edit_message_text(chat_id=call.message.chat.id, text=f"Круто, а теперь лови реквизиты для оплаты: "
                                           f"\n\nНомер карты: {user_data[user_id]['selected_bank']}",
                          message_id=call.message.message_id, reply_markup=markup)


@bot.callback_query_handler(state=PurchaseStates.choose_bank, func=lambda call: call.data == 'paid')
def handle_payment(call):
    user_id, chat_id = get_id(call=call)
    markup = create_inline_markup(('Подтверждаю', 'confirm_payment'), ('Назад', 'go_back'))
    bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id,
                          text="Вы уверены, что перевели?",
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
    else:
        select_bank(call)


@bot.callback_query_handler(state=PurchaseStates.choose_bank,
                            func=lambda call: call.data[:8] == 'confsubs' or call.data[:4] == 'canc')
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
                                                          'С завтрашнего дня вам начнут приходить '
                                                          'тренировки и инструкции к ним!'
                                                          '\nА пока что, просим вас заполнить небольшой опросник!',
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
