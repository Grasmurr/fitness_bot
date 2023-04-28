from telebot import TeleBot
import telebot.apihelper as apihelper
from .data import token

apihelper.TIMEOUT = 45
bot = TeleBot(token)
