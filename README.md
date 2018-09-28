# SONM Community Telegram Bot

## Installation

First, provide your Telegram Bot Token (given by @BotFather) into a terminal window
`TELEGRAM_BOT_TOKEN=123456789:ABCDEFhijklmn123OPQRSTUvw4567xyz890`

Then, run the following commands
```
cp config/telegram.json.template config/telegram.json
sed -i "s/ADD_BOT_TOKEN_HERE/$TELEGRAM_BOT_TOKEN/g" config/telegram.json
```
