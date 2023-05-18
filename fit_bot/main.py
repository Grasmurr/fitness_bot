import time

import os, django, sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fit_bot.settings')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
django.setup()

from telegram_bot.bot import start_bot
from telegram_bot.tasks import run_scheduler


if __name__ == '__main__':
    while True:
        try:
            start_bot()
            run_scheduler()
        except:
            time.sleep(1)
            continue
