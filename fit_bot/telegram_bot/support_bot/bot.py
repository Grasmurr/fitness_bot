import time
from .loader import bot
from . import handlers


def start_support_bot():
    bot.infinity_polling()
    # while True:
    #     try:
    #
    #     except:
    #         print("Read timeout occurred, restarting polling...")
    #         time.sleep(1)
    #         continue
