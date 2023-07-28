from telebot.types import Message
from django.utils import timezone
from telebot import custom_filters

from ...loader import bot
from ...states import CourseInteraction
from ...models import PaidUser
from .edit_calories_backends import get_id, return_calories_and_norm


@bot.message_handler(state=CourseInteraction.initial,
                     func=lambda message: message.text == 'Сколько еще можно ккал?👀')
def calories_info(message: Message):
    user_id, chat_id = get_id(message=message)
    user_model = PaidUser.objects.get(user=user_id)
    current_day = (timezone.now().date() - user_model.paid_day).days

    if current_day == 0:
        bot.send_message(user_id, 'Курс начнется со следующего дня! '
                                  'Поэтому и заполнение калорий будет доступно с завтрашнего дня')
    else:
        user_calories, remaining_calories, daily_norm, daily_proteins_norm, remaining_proteins = \
            return_calories_and_norm(user_model, current_day)

        if remaining_calories < 0:
            text = "❗️Вы переели свою норму ккал, ваш результат на 70% зависит от вашего питания, " \
                   "поэтому желательно больше ничего не есть за сегодня…\n\n" \
                   "Если крайне тяжело, то лучше отдать предпочтение овощам (огурцы, капуста, броколли, помидоры…)"
        else:
            text = f"🔥Вам можно съесть еще: {remaining_calories} ккал / {remaining_proteins}г белка"
        bot.send_message(user_id, text)


bot.add_custom_filter(custom_filters.StateFilter(bot))
