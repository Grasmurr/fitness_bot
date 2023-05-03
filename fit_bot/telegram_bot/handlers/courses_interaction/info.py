from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from django.utils import timezone
from telegram_bot.loader import bot
from telegram_bot.states import States


from courses.models import Категории, Content, Mailing, Training
from telegram_bot.models import PaidUser, UnpaidUser, UserCalories


@bot.message_handler(func=lambda message: message.text == 'Получить тренировки 🎾')
def get_courses(message: Message):
    user_id = message.from_user.id
    user = PaidUser.objects.filter(user=user_id).first()

    # Находим соответствующую категорию контента на основе характеристик пользователя
    try:
        matching_category = Категории.objects.get(
            пол=user.пол,
            цель=user.цель,
            место=user.место,
            уровень=user.уровень
        )

        # Вычисляем номер дня на основе оплаченного дня
        delta_days = (timezone.now().date() - user.paid_day).days
        current_day = delta_days

        daily_contents = Training.objects.filter(category=matching_category, day=current_day)
        if daily_contents:
            # Отправляем контент пользователю через Telegram Bot API
            for content in daily_contents:
                user_calories = UserCalories.objects.get(user=user)
                setattr(user_calories, f'day{current_day}_requested', True)
                user_calories.save()

                updated_caption = content.caption.replace("calories", str(user.calories)).replace("name",
                                                                                                  user.full_name)
                if content.content_type == 'V':
                    bot.send_video(chat_id=user.user, video=content.video_file_id, caption=updated_caption)
                elif content.content_type == 'T':
                    bot.send_message(chat_id=user.user, text=updated_caption)
                elif content.content_type == 'P':
                    bot.send_photo(chat_id=user.user, photo=content.photo_file_id, caption=updated_caption)
                elif content.content_type == 'G':
                    bot.send_document(chat_id=user.user, document=content.gif_file_id, caption=updated_caption)
        else:
            bot.send_message(chat_id=user.user, text='Кажется, что на сегодня для вас нет тренировок! следуйте инструкциям')
    except:
        bot.send_message(chat_id=user.user,
                         text='Кажется, что на сегодня для вас нет тренировок! следуйте инструкциям')


