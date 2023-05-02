from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q, F
from apscheduler.schedulers.background import BackgroundScheduler
import pytz
import datetime

from telegram_bot.models import PaidUser, FinishedUser, UserCalories
from courses.models import Категории, Content, DailyContent
from telegram_bot.loader import bot
from telegram_bot.states import States

user_data = {}

def send_daily_content(user):
    # Находим соответствующую категорию
    # контента на основе характеристик пользователя
    matching_category = Категории.objects.get(
        пол=user.пол,
        цель=user.цель,
        место=user.место,
        уровень=user.уровень
    )

    # Вычисляем номер дня на основе оплаченного дня
    delta_days = (timezone.now().date() - user.paid_day).days
    current_day = delta_days

    # Получаем контент для соответствующей категории и дня
    daily_contents = DailyContent.objects.filter(
        category=matching_category,
        day=current_day,
        **(Q(sequence_number=1) | Q(sequence_number=2))
    )
    # Отправляем контент пользователю через Telegram Bot API
    for content in daily_contents:
        updated_caption = content.caption.replace("calories", str(user.calories)).replace("name", user.full_name)

        if content.content_type == 'V':
            bot.send_video(chat_id=user.user, video=content.video_file_id, caption=updated_caption)
        elif content.content_type == 'T':
            bot.send_message(chat_id=user.user, text=updated_caption)
        elif content.content_type == 'P':
            bot.send_photo(chat_id=user.user, photo=content.photo_file_id, caption=updated_caption)
        elif content.content_type == 'G':
            bot.send_document(chat_id=user.user, document=content.gif_file_id, caption=updated_caption)


def check_calories(user):
    bot.send_message(chat_id=user.user, text='Дорогой участник курса! '
                                             'Пожалуйста, не щабывайте заполнять '
                                             'количество калорий, которые вы за сегодня '
                                             'употребили, если еще не сделали этого!')


def check_for_daily_content(user, current_day):
    try:
        matching_category = Категории.objects.get(
            пол=user.пол,
            цель=user.цель,
            место=user.место,
            уровень=user.уровень
        )

        if current_day != 0:
            daily_contents = DailyContent.objects.filter(category=matching_category, day=current_day, sequence_number__gte=3)
            if daily_contents:
                user_calories = UserCalories.objects.get(user=user)
                is_requested = getattr(user_calories, f'day{current_day}_requested')

                if not is_requested:
                    bot.send_message(chat_id=user.user, text="Не забудьте открыть тренировки на сегодня!")
    except:
        pass

def check_and_send_content():
    current_time_utc = datetime.datetime.now(pytz.utc)

    paid_users = PaidUser.objects.all()

    for user in paid_users:
        delta_days = (timezone.now().date() - user.paid_day).days
        user_timezone_str = user.timezone

        if user_timezone_str:
            user_timezone = pytz.timezone(user_timezone_str)
            current_time_local = current_time_utc.astimezone(user_timezone)

            if current_time_local.hour == 9 and current_time_local.minute == 0:
                bot.send_message(chat_id=305378717, text='да, это работает')
                send_daily_content(user)

            if current_time_local.hour == 18 and current_time_local.minute == 40:
                check_calories(user)

            if current_time_local.hour == 11 and current_time_local.minute == 0:
                check_for_daily_content(user, delta_days)

            if current_time_local.hour == 18 and current_time_local.minute == 0:
                check_for_daily_content(user, delta_days)

            if current_time_local.hour == 22 and current_time_local.minute == 0:
                check_for_daily_content(user, delta_days)

        if delta_days == 22:
            finished_user = FinishedUser(
                user=user.user,
                username=user.username,
                full_name=user.full_name,
                paid_day=user.paid_day,
                calories=user.calories,
                timezone=user.timezone,
                пол=user.пол,
                цель=user.цель,
                место=user.место,
                уровень=user.уровень,
            )
            finished_user.save()
            user.delete()


def change_calories_norm():
    paid_users = PaidUser.objects.all()
    for user in paid_users:
        delta_days = (timezone.now().date() - user.paid_day).days

        if delta_days == 8:
            if user.цель == "G":
                PaidUser.objects.filter(user=user.user).update(calories=F('calories') * 1.022)
            else:
                PaidUser.objects.filter(user=user.user).update(calories=F('calories') * 0.858)


def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_and_send_content, 'interval', minutes=1)
    scheduler.add_job(change_calories_norm, 'interval', hours=24)
    scheduler.start()

