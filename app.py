# -*- coding: utf-8 -*-
#import config
import telebot

token = '478680072:AAHLM8h9Y-pYXkn-THQA-YoVeI7ueo1lhw0'

bot = telebot.TeleBot(token)

@bot.message_handler(content_types=["text"])
def repeat_all_messages(message): # Название функции не играет никакой роли, в принципе
    if message.text[0] == '/':
        bot.send_message(message.chat.id, 'Command: ' + message.text)
    else:
        bot.send_message(message.chat.id, 'You wrote: ' + message.text)

if __name__ == '__main__':

    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(e)
            continue

