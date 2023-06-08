from telebot import TeleBot
from telegram_bot.warm_up_bot.data.config import warm_up_token
from telebot.storage import StateMemoryStorage


bot = TeleBot(warm_up_token, state_storage=StateMemoryStorage())
