# -*- coding: utf-8 -*-


# !/usr/bin/python3
from math import log
import requests
import time
from pymongo import MongoClient
import sys

import pandas as pd

from config import token
import telebot
from telebot import types
import time


class Book:
    timestamp = None
    powers = [2, 4, 8]
    trades_ts_start = None
    trades_ts_stop = None
    trades = None
    bids = None
    asks = None
    width = None
    mid = None
    power_imbalance_list = []
    power_adjusted_prices = []

    def __init__(self, book):
        self.timestamp = book['_id']
        self.trades_ts_start
        self.asks = pd.DataFrame(book['asks'])
        self.bids = pd.DataFrame(book['bids'])
        best_bid = self.bids['price'].max()
        best_ask = self.asks['price'].min()
        self.width = best_ask - best_bid
        self.mid = (best_ask + best_bid) / 2

        self.power_imbalance_list =[self.calc_power_imbalance(p) for p in self.powers]
        self.power_adjusted_prices = [self.calc_power_adjusted_price(p) for p in self.powers]


    def calc_weighted_amount(self, order, power):
        weight = (.5 * self.width / (order.price - self.mid)) ** power
        return order.amount * weight

    def calc_power_imbalance(self, power):
        bid_imbalance = self.bids.iloc[:].apply(self.calc_weighted_amount, axis=1, args=(power,))
        ask_imbalance = self.asks.iloc[:].apply(self.calc_weighted_amount, axis=1, args=(power,))
        return (bid_imbalance - ask_imbalance).sum()

    def calc_power_adjusted_price(self, power):
        bid_inv = 1 / self.bids.iloc[:].apply(self.calc_weighted_amount, axis=1, args=(power,))
        ask_inv = 1 / self.asks.iloc[:].apply(self.calc_weighted_amount, axis=1, args=(power,))
        bid_price = self.bids.price.iloc[:]
        ask_price = self.asks.price.iloc[:]
        ap = (bid_price * bid_inv + ask_price * ask_inv).sum() / (bid_inv + ask_inv).sum()
        return log(ap / self.mid)


def format_orderbook(orderbook):

    for orders in orderbook.values():
        for order in orders:
            if all(key in order for key in ('amount', 'price', 'timestamp')):
                order['amount'] = float(order['amount'])
                order['price'] = float(order['price'])
                order['timestamp'] = float(order['timestamp'])
            else:
                return
    return orderbook


def get_orderbook(url):

    response = requests.request("GET", url)
    response.raise_for_status()
    return response.json()

bot = telebot.TeleBot(token)


# Обработчик команд '/start' и '/help'.
@bot.message_handler(commands=['start', 'help'])
def handle_start_help(message):
    keyboard = types.InlineKeyboardMarkup()

#    url_button = types.InlineKeyboardButton(text="Перейти на Яндекс", url="https://ya.ru")
#    keyboard.add(url_button)
#    bot.send_message(message.chat.id, "Привет! Нажми на кнопку и перейди в поисковик.", reply_markup=keyboard)

    markup = types.ReplyKeyboardMarkup()
    markup.row('/btc', '/zec')
    markup.row('/xrp', '/eth', '/bch')
    bot.send_message(message.chat.id, "Choose currency:", reply_markup=markup)
    pass


@bot.message_handler(content_types=["text"])
def repeat_all_messages(message): # Название функции не играет никакой роли, в принципе


    if message.text[0] == '/' and message.text != '/start':


#        bot.send_message(message.chat.id, 'Command: ' + message.text)

        api = 'https://api.bitfinex.com/v1'
        symbol = message.text[1:4]

        if symbol in ('btc', 'zec', 'bch', 'xrp', 'eth'):


            limit = 500
            url = '{0}/book/{1}usd?limit_bids={2}&limit_asks={2}' \
                .format(api, symbol, limit)

            start = time.time()
            try:

                orderbook = get_orderbook(url)
                orderbook = format_orderbook(orderbook)

                orderbook['_id'] = time.time()
                #      ltc_orderbooks.insert_one(orderbook)

                book = Book(orderbook)

                mid = book.mid
                width = book.width
                power_imbalance_2, power_imbalance_4, power_imbalance_8 = book.power_imbalance_list
                power_adjusted_price_2, power_adjusted_price_4, power_adjusted_price_8, = book.power_adjusted_prices
                bot.send_message(message.chat.id, symbol.upper()+' features:\n' + ("MID: %s\n"
                       "WID: %.2f\n"
                       "PI2: %.2f\n"
                       "PI4: %.2f\n"
                       "PI8: %.2f\n"
                       "PA2: %.2f\n"
                       "PA4: %.2f\n"
                       "PA8: %.2f")
                      % (mid,
                         width,
                         power_imbalance_2,
                         power_imbalance_4,
                         power_imbalance_8,
                         power_adjusted_price_2,
                         power_adjusted_price_4,
                         power_adjusted_price_8,
                         )+'\n'+time.strftime("%a, %d %b %Y %H:%M:%S", time.gmtime(time.time()+180*60)))

            except Exception as e:
               print(e)

        else:
            bot.send_message(message.chat.id, 'The available commands are: \n/btc\n/zec\n/bch\n/xrp\n/eth')

    else:
        bot.send_message(message.chat.id, 'The available commands are: \n/btc\n/zec\n/bch\n/xrp\n/eth')

    print(time.strftime("%a, %d %b %Y %H:%M:%S", time.gmtime(time.time())) + ' Added one: '+message.text)

if __name__ == '__main__':

    while True:
        start = time.time()
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(e)
            continue

        time_delta = time.time()-start
        if time_delta < 10.0:
            time.sleep(10-time_delta)
