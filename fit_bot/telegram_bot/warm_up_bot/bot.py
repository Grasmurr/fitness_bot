from ..loader import bot
from telebot.types import Message
from .handlers import main_menu, send_mails, mailings
from .handlers.mailings import scheduler_thread
from .handlers.models import create_table


def start_warmup_bot():
    create_table()
    scheduler_thread.start()
    bot.infinity_polling()



