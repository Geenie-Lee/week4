import telegram
    
def send(message):
    telegram_token = "1298837487:AAGi6GZhF1hOk_NfHymJNHFL_6-JFm0XCaw"
    bot = telegram.Bot(token=telegram_token)
    updates = bot.getUpdates()
    chat_id = updates[-1].message.chat_id
    bot.sendMessage(chat_id=chat_id, text=message)
    
    for i in updates:
        print(i)