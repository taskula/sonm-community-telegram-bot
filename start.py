#!/usr/bin/env python3

import json
from bot import Bot

config={}

try:
    with open('config/telegram.json') as telegram_config:
        config = json.load(telegram_config)
except IOError:
    print('Error opening config/telegram.json. Does the file exist? See README.md for installation instructions.')
    raise

bot = Bot(config)
bot.start()