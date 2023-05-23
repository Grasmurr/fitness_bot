import time

import os, django, sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fit_bot.settings')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
django.setup()

from telegram_bot.support_bot.bot import start_support_bot


if __name__ == '__main__':
    while True:
        try:
            start_support_bot()
        except:
            time.sleep(1)
            continue
