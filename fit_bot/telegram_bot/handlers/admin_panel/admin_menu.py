from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, CallbackQuery
from ...loader import bot
from ...filters.is_admin import IsAdminFilter
from ...states import States
from ...models import PaidUser, UnpaidUser, FinishedUser
from ...handlers.mainmenu import paid_user_main_menu


from courses.models import Категории, Video


admin_data = {}


@bot.message_handler(commands=['admin'], is_admin=True)
def what(message: Message):
    user_id = message.from_user.id
    if user_id not in admin_data:
        admin_data[user_id] = {}
    admin_data[user_id]['state'] = States.MAILING
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = KeyboardButton('Рассылка')
    button2 = KeyboardButton('Загрузить видео')
    button3 = KeyboardButton('Вернуться назад')
    markup.add(button1)
    markup.add(button2)
    markup.add(button3)
    bot.send_message(chat_id=message.chat.id,
                     text='Это админ-панель! Пожалуйста, выберите что вы хотите сделать нажав на кнопку ниже',
                     reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == 'Рассылка', is_admin=True)
def mailing(message: Message):
    if admin_data[message.from_user.id]['state'] == States.MAILING:
        admin_data[message.from_user.id]['state'] = States.CHOOSING_MAILING_CATEGORY

        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = KeyboardButton('Рассылка по PaidUsers')
        button2 = KeyboardButton('Рассылка по FinishedUsers')
        button3 = KeyboardButton('Рассылка по Unpaid')
        button4 = KeyboardButton('Вернуться назад')
        markup.add(button1)
        markup.add(button2)
        markup.add(button3)
        markup.add(button4)
        bot.send_message(chat_id=message.chat.id,
                         text='Пожалуйста, уточните категорию рассылки', reply_markup=markup)


@bot.message_handler(func=lambda message: message.from_user.id in admin_data and admin_data[message.from_user.id]['state'] == States.CHOOSING_MAILING_CATEGORY and message.text == 'Вернуться назад', is_admin=True)
def unpaid_mailing(message: Message):
    what(message)


@bot.message_handler(func=lambda message: message.from_user.id in admin_data and admin_data[message.from_user.id]['state'] == States.MAILING and message.text == 'Вернуться назад', is_admin=True)
def back_home_from_mailing(message: Message):
    paid_user_main_menu(message)


@bot.message_handler(func=lambda message: message.from_user.id in admin_data and admin_data[message.from_user.id]['state'] == States.MAILING and message.text == 'Загрузить видео', is_admin=True)
def upload(message: Message):
    user_id = message.from_user.id
    admin_data[user_id]['state'] = States.UPLOAD_VIDEO
    bot.send_message(user_id, "Пожалуйста, загрузите видео")


@bot.message_handler(content_types=['video'], func=lambda message: message.from_user.id in admin_data and admin_data[message.from_user.id]['state'] == States.UPLOAD_VIDEO, is_admin=True)
def handle_video_upload(message: Message):
    user_id = message.from_user.id
    video = message.video
    video_file_id = video.file_id

    # Получение названия видео (если оно было указано в подписи к видео)
    video_name = message.video.file_name

    # Создание и сохранение объекта Video в базе данных
    new_video = Video(name=video_name, video_file_id=video_file_id)
    new_video.save()

    # Возвращение пользователя в состояние MAILING и отправка сообщения об успешной загрузке видео
    admin_data[user_id]['state'] = States.MAILING
    bot.send_message(user_id, "Видео успешно загружено и сохранено")
    what(message)


def create_categories_keyboard(for_unpaid=False):
    if not for_unpaid:
        markup = InlineKeyboardMarkup()
        categories = Категории.objects.all()

        for index, category in enumerate(categories, start=1):
            button = InlineKeyboardButton(str(index), callback_data=f'category_{index}')
            markup.add(button)
    else:
        markup = InlineKeyboardMarkup()

    return markup


@bot.message_handler(func=lambda message: message.text == 'Рассылка по Unpaid', is_admin=True)
def unpaid_mailing(message: Message):
    user_id = message.from_user.id
    if user_id in admin_data:
        if admin_data[user_id]['state'] == States.CHOOSING_MAILING_CATEGORY:
            admin_data[user_id]['category_of_mailing'] = 'UnpaidUser'
            markup = create_categories_keyboard(for_unpaid=True)
            markup.add(InlineKeyboardButton(text='По всем пользователям', callback_data='category_all'))
            bot.send_message(chat_id=message.chat.id,
                             text=f'Пожалуйста, выберите категорию для рассылки сообщений:',
                             reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == 'Рассылка по PaidUsers', is_admin=True)
def paid_mailing(message: Message):
    user_id = message.from_user.id
    if user_id in admin_data:
        if admin_data[user_id]['state'] == States.CHOOSING_MAILING_CATEGORY:
            admin_data[user_id]['category_of_mailing'] = 'PaidUser'
            markup = create_categories_keyboard()
            categories_text = '\n'.join([f'{index} - {category.название}' for index, category in enumerate(Категории.objects.all(), start=1)])
            markup.add(InlineKeyboardButton(text='По всем пользователям', callback_data='category_all'))
            bot.send_message(chat_id=message.chat.id,
                             text=f'Пожалуйста, выберите категорию для рассылки сообщений:\n{categories_text}',
                             reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == 'Рассылка по FinishedUsers', is_admin=True)
def finished_mailing(message: Message):
    user_id = message.from_user.id
    if user_id in admin_data:
        if admin_data[user_id]['state'] == States.CHOOSING_MAILING_CATEGORY:
            admin_data[user_id]['category_of_mailing'] = 'FinishedUser'
            markup = create_categories_keyboard()
            categories_text = '\n'.join([f'{index} - {category.название}' for index, category in enumerate(Категории.objects.all(), start=1)])
            markup.add(InlineKeyboardButton(text='По всем пользователям', callback_data='category_all'))
            bot.send_message(chat_id=message.chat.id,
                             text=f'Пожалуйста, выберите категорию для рассылки сообщений:\n{categories_text}',
                             reply_markup=markup)


def create_message_type_keyboard():
    markup = InlineKeyboardMarkup()
    button1 = InlineKeyboardButton('Текст', callback_data='message_type_text')
    button2 = InlineKeyboardButton('Фото', callback_data='message_type_photo')
    markup.add(button1, button2)
    return markup


@bot.callback_query_handler(func=lambda call: call.data.startswith('category_'))
def category_callback(call: CallbackQuery):
    if not call.data.split('_')[1] == 'all':
        category_index = int(call.data.split('_')[1])
        selected_category = Категории.objects.all()[category_index - 1]
    else:
        selected_category = 'all'

    # Сохранение выбранной категории в admin_data
    admin_data[call.from_user.id]['category'] = selected_category
    markup = create_message_type_keyboard()
    if selected_category == 'all':
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text=f'Выберите тип сообщения для рассылки по всем пользователям:',
                              reply_markup=markup)
    else:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                         text=f'Выберите тип сообщения для рассылки в категории "{selected_category.название}":',
                         reply_markup=markup)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data == 'message_type_text')
def message_type_text_callback(call: CallbackQuery):
    admin_data[call.from_user.id]['message_type'] = 'text'

    admin_data[call.from_user.id]['state'] = States.ENTER_TEXT_FOR_MAILING
    bot.edit_message_text(chat_id=call.message.chat.id,
                          message_id=call.message.message_id, text='Пожалуйста, отправьте текст сообщения для рассылки.')
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data == 'message_type_photo')
def message_type_photo_callback(call: CallbackQuery):
    admin_data[call.from_user.id]['message_type'] = 'photo'

    markup = InlineKeyboardMarkup()
    button_yes = InlineKeyboardButton('Да', callback_data='add_caption_yes')
    button_no = InlineKeyboardButton('Нет', callback_data='add_caption_no')
    markup.add(button_yes, button_no)

    bot.edit_message_text(chat_id=call.message.chat.id,
                          message_id=call.message.message_id,
                          text='Хотите добавить заголовок к фотографии?', reply_markup=markup)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data in ('add_caption_yes', 'add_caption_no'))
def add_caption_callback(call: CallbackQuery):
    if call.data == 'add_caption_yes':
        admin_data[call.from_user.id]['add_caption'] = True
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text='Пожалуйста, отправьте фотографию с заголовком, '
                              'которую вы хотите разослать (бот получит file_id фотографии).')
    else:
        admin_data[call.from_user.id]['add_caption'] = False
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text='Пожалуйста, отправьте фотографию без заголовка, '
                              'которую вы хотите разослать (бот получит file_id фотографии).')

    bot.answer_callback_query(call.id)


@bot.message_handler(func=lambda message: message.from_user.id in admin_data and 'message_type' in admin_data[message.from_user.id] and admin_data[message.from_user.id]['state'] == States.ENTER_TEXT_FOR_MAILING, content_types=['text'], is_admin=True)
def text_handler(message: Message):
    if message.from_user.id in admin_data and admin_data[message.from_user.id]['message_type'] == 'text':
        text = message.text

        markup = InlineKeyboardMarkup()
        button_yes = InlineKeyboardButton('Да', callback_data='send_text_yes')
        button_no = InlineKeyboardButton('Нет', callback_data='send_text_no')
        markup.add(button_yes, button_no)

        bot.send_message(chat_id=message.chat.id,
                         text=f'Вы уверены, что хотите отправить данное текстовое сообщение?\n\n{text}',
                         reply_markup=markup)
        admin_data[message.from_user.id]['state'] = States.CHOOSING_MAILING_CATEGORY


@bot.message_handler(func=lambda message: 'message_type' in admin_data[message.from_user.id], content_types=['photo'], is_admin=True)
def photo_handler(message: Message):
    if message.from_user.id in admin_data and admin_data[message.from_user.id]['message_type'] == 'photo':
        photo = message.photo[-1]  # Получение самой большой версии фотографии
        file_id = photo.file_id

        caption = message.caption if admin_data[message.from_user.id]['add_caption'] else None

        # Спрашиваем у пользователя, отправлять или нет
        markup = InlineKeyboardMarkup()
        button_yes = InlineKeyboardButton('Да', callback_data='send_photo_yes')
        button_no = InlineKeyboardButton('Нет', callback_data='send_photo_no')
        markup.add(button_yes, button_no)

        if caption:
            bot.send_photo(chat_id=message.chat.id, photo=file_id,
                           caption=f'Вы уверены, что хотите отправить данную фотографию с заголовком: "{caption}"?',
                           reply_markup=markup)
        else:
            bot.send_photo(chat_id=message.chat.id, photo=file_id,
                           caption='Вы уверены, что хотите отправить данную фотографию без заголовка?',
                           reply_markup=markup)


def get_users_by_category_name(model_class, category_name=False):
    if category_name:
        category = Категории.objects.get(название=category_name)
        users = model_class.objects.filter(
            пол=category.пол,
            цель=category.цель,
            место=category.место,
            уровень=category.уровень
        )
    else:
        if not model_class == UnpaidUser:
            users = model_class.objects.all()
        else:
            users = model_class.objects.filter(
                has_paid=False
            )
    return users


def send_message_to_users(users, message_text=None, photo_file_id=None, caption=None):
    for user in users:
        try:
            chat_id = user.user
        except AttributeError:
            chat_id = user.user_id
        if photo_file_id:
            bot.send_photo(chat_id, photo_file_id, caption=caption)
        elif message_text:
            bot.send_message(chat_id, message_text)


@bot.callback_query_handler(func=lambda call: call.data in ('send_text_yes', 'send_text_no'))
def send_text_callback(call: CallbackQuery):
    if call.data == 'send_text_yes':
        text = call.message.text
        model_class = PaidUser if admin_data[call.from_user.id]['category_of_mailing'] == 'PaidUser' \
            else FinishedUser if admin_data[call.from_user.id]['category_of_mailing'] == 'FinishedUser' else UnpaidUser

        if admin_data[call.from_user.id]['category'] == 'all':
            users_to_send = get_users_by_category_name(
                model_class=model_class)
        else:
            users_to_send = get_users_by_category_name(
                model_class=model_class,
                category_name=admin_data[call.from_user.id]['category'])

        send_message_to_users(users_to_send, message_text=' '.join(text.split()[8:]))
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='Отправлено!')
    else:
        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=call.message.message_id, text='Отправка текстового сообщения отменена.')

    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data in ('send_photo_yes', 'send_photo_no'))
def send_photo_callback(call: CallbackQuery):
    if call.data == 'send_photo_yes':
        photo = call.message.photo[-1]  # Получение самой большой версии фотографии
        file_id = photo.file_id

        caption = call.message.caption
        model_class = PaidUser if admin_data[call.from_user.id]['category_of_mailing'] == 'PaidUser' \
            else FinishedUser if admin_data[call.from_user.id]['category_of_mailing'] == 'FinishedUser' else UnpaidUser

        if admin_data[call.from_user.id]['category'] == 'all':
            users_to_send = get_users_by_category_name(
                model_class=model_class)
        else:
            users_to_send = get_users_by_category_name(
                model_class=model_class,
                category_name=admin_data[call.from_user.id]['category'])
        send_message_to_users(users_to_send, photo_file_id=file_id, caption=' '.join(caption.split()[9:])[1:-2])
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        bot.send_message(chat_id=call.message.chat.id, text='Отправлено!')


        # admin_data[call.from_user.id]['category'] - это сама категория (может быть all)
        # admin_data[call.from_user.id]['category_of_mailing'] - PaidUsers etc.
    else:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text='Отправка фотографии отменена.')

    bot.answer_callback_query(call.id)
