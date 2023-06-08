from .loader import bot
from telebot.types import Message
from . import handlers


def start_warmup_bot():
    bot.infinity_polling()

