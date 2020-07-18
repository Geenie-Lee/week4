import telegram

telegram_token = "1298837487:AAGi6GZhF1hOk_NfHymJNHFL_6-JFm0XCaw"
bot = telegram.Bot(token=telegram_token)
updates = bot.getUpdates()
print(updates)

for i in updates:
    print(i)
    
print("start telegram chat bot")    

bot.sendMessage(chat_id = '57116486', text = "Hi Bot")