import threading

import schedule
import time
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from telebot import apihelper
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q, F
from apscheduler.schedulers.background import BackgroundScheduler
import pytz
import datetime

from .models import PaidUser, FinishedUser, CourseDay, UnpaidUser
from courses.models import Категории, Content, Mailing, Training
from .loader import bot
from .states import States

from .warm_up_bot.handlers.mailings import check_unfinished_users

user_data = {}


def send_daily_content():
    paid_users = PaidUser.objects.all()

    for user in paid_users:
        try:
            matching_category = Категории.objects.get(
                пол=user.пол,
                цель=user.цель,
                место=user.место,
                уровень=user.уровень
            )

            delta_days = (timezone.now().date() - user.paid_day).days
            current_day = delta_days

            daily_contents = Mailing.objects.filter(
                category=matching_category,
                day=current_day,
            )

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
        except apihelper.ApiException as e:
            error_code = e.result.status_code
            if error_code == 403:
                bot.send_message(305378717, f"User {user.user} blocked the bot. Removing from the database.")
                user.delete()
            else:
                bot.send_message(305378717, f"Error {error_code}: {e.result.reason}")
        except Exception as E:
            bot.send_message(305378717, f"Ошибка: {E}")


def check_calories():
    paid_users = PaidUser.objects.all()

    for user in paid_users:
        try:
            bot.send_message(chat_id=user.user, text='Дорогой участник курса! '
                                                'Пожалуйста, не забывайте заполнять '
                                                'количество калорий, которые вы за сегодня '
                                                'употребили, если еще не сделали этого!')
        except apihelper.ApiException as e:
            error_code = e.result.status_code
            if error_code == 403:
                bot.send_message(305378717, f"User {user.user} blocked the bot. Removing from the database.")
                user.delete()
            else:
                bot.send_message(305378717, f"Error {error_code}: {e.result.reason}")
        except Exception as E:
            bot.send_message(305378717, f"Ошибка: {E}")


def check_for_daily_content():
    paid_users = PaidUser.objects.all()

    for user in paid_users:
        current_day = (timezone.now().date() - user.paid_day).days
        try:
            if current_day != 0:
                course_day, created = CourseDay.objects.get_or_create(user=user, day=current_day, defaults={'has_requested': False})
                if not course_day.has_requested:
                    bot.send_message(chat_id=user.user, text="Не забудьте открыть тренировки на сегодня!")
        except apihelper.ApiException as e:
            error_code = e.result.status_code
            if error_code == 403:
                bot.send_message(305378717, f"User {user.user} blocked the bot. Removing from the database.")
                user.delete()
            else:
                bot.send_message(305378717, f"Error {error_code}: {e.result.reason}")
        except Exception as E:
            bot.send_message(305378717, f"Ошибка: {E}")


def check_and_send_content():
    current_time_utc = datetime.datetime.now(pytz.utc)

    paid_users = PaidUser.objects.all()

    for user in paid_users:
        try:
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
                UnpaidUser.objects.filter(user_id=user.user).update(has_paid=False)
                user.delete()

        except Exception as E:
            bot.send_message(305378717, f"Ошибка: {E}")


def change_calories_norm():
    paid_users = PaidUser.objects.all()
    for user in paid_users:
        try:
            delta_days = (timezone.now().date() - user.paid_day).days
            if delta_days == 8:
                if user.цель == "G":
                    PaidUser.objects.filter(user=user.user).update(calories=F('calories') * 1.022)
                else:
                    PaidUser.objects.filter(user=user.user).update(calories=F('calories') * 0.858)
        except Exception as E:
            bot.send_message(305378717, f"Ошибка: {E}")


schedule.every().day.at("01:00").do(change_calories_norm)
schedule.every().day.at("09:00").do(send_daily_content)
schedule.every().day.at("18:00").do(check_calories)
schedule.every().day.at("20:00").do(check_for_daily_content)
schedule.every(1).minutes.do(check_unfinished_users)


def run_scheduler():
    while True:
        try:
            schedule.run_pending()
        except Exception as e:
            bot.send_message(305378717, f"Ошибка: {e}")
        time.sleep(1)


scheduler_thread = threading.Thread(target=run_scheduler)



