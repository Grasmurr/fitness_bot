import time
import os
import sys

# os.chdir(os.path.dirname(os.path.abspath(__file__)))

# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fit_bot.settings")

from .loader import bot
from django.core.management import execute_from_command_line
execute_from_command_line(["manage.py", "check"])
from . import handlers

from .filters.is_admin import IsAdminFilter

bot.add_custom_filter(IsAdminFilter(bot))


def start_bot():
    # bot.infinity_polling(restart_on_change=True)
    bot.infinity_polling()
    # while True:
    #     try:
    #         bot.polling(none_stop=True)
    #     except:
    #         print("Read timeout occurred, restarting polling...")
    #         time.sleep(1)
    #         continue