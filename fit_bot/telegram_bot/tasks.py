import threading

import schedule
import time
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q, F
from apscheduler.schedulers.background import BackgroundScheduler
import pytz
import datetime

from telegram_bot.models import PaidUser, FinishedUser, UserCalories
from courses.models import Категории, Content, Mailing, Training
from telegram_bot.loader import bot
from telegram_bot.states import States

from telegram_bot.warm_up_bot.handlers.mailings import check_unfinished_users

user_data = {}

def send_daily_content():
    paid_users = PaidUser.objects.all()

    for user in paid_users:

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
        daily_contents = Mailing.objects.filter(
            category=matching_category,
            day=current_day,
        )
        # Отправляем контент пользователю через Telegram Bot API
        for content in daily_contents:
            updated_caption = content.caption.replace("calories", str(user.calories)).replace("name", user.full_name)

            if content.content_type == 'V':
                video_file_id = content.video.video_file_id
                bot.send_video(chat_id=user.user, video=video_file_id, caption=updated_caption)
            elif content.content_type == 'T':
                bot.send_message(chat_id=user.user, text=updated_caption)
            elif content.content_type == 'P':
                bot.send_photo(chat_id=user.user, photo=content.photo_file_id, caption=updated_caption)
            elif content.content_type == 'G':
                bot.send_document(chat_id=user.user, document=content.gif_file_id, caption=updated_caption)


def check_calories():
    paid_users = PaidUser.objects.all()

    for user in paid_users:
        bot.send_message(chat_id=user.user, text='Дорогой участник курса! '
                                                 'Пожалуйста, не забывайте заполнять '
                                                 'количество калорий, которые вы за сегодня '
                                                 'употребили, если еще не сделали этого!')


def check_for_daily_content():

    paid_users = PaidUser.objects.all()

    for user in paid_users:
        current_day = (timezone.now().date() - user.paid_day).days

        try:
            matching_category = Категории.objects.get(
                пол=user.пол,
                цель=user.цель,
                место=user.место,
                уровень=user.уровень
            )

            if current_day != 0:
                daily_contents = Mailing.objects.filter(category=matching_category, day=current_day)
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


schedule.every().day.at("09:00").do(send_daily_content)
schedule.every().day.at("18:00").do(check_calories)
schedule.every().day.at("11:00").do(check_for_daily_content)
schedule.every(1).minutes.do(check_unfinished_users)


# Запускаем планировщик в отдельном потоке


def run_scheduler():
    while True:
        try:
            schedule.run_pending()
        except Exception as e:
            bot.send_message(305378717, f"Ошибка: {e}")
        time.sleep(1)


scheduler_thread = threading.Thread(target=run_scheduler)

