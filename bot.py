import logging
import telegram
from telegram.ext import CommandHandler, Updater

class Bot(telegram.Bot):
    def __init__(self, config, *args, **kwargs):
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                            level=logging.INFO)
        self.config = config
        super(Bot,self).__init__(self.config['Bot']['TOKEN'], *args, **kwargs)

    def __commands(self, dispatcher):
        # /start => respond_start()
        start_handler = CommandHandler('start', self.respond_start)
        dispatcher.add_handler(start_handler)

    def start(self):
        updater = Updater(token=self.config['Bot']['TOKEN'])
        dispatcher = updater.dispatcher

        self.__commands(dispatcher)

        updater.start_polling()
        updater.idle()

    def respond_start(self, bot, update):
        bot.send_message(chat_id=update.message.chat_id, text="test")