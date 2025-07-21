import telebot
from currency_converter import CurrencyConverter
from telebot import types

bot = telebot.TeleBot(token='7565746666:AAHY0DztnktoGtpu9U_pNkD2lD4dD3ydqgI')
currency = CurrencyConverter()
amount = 0

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id,'Введите сумму')
    bot.register_next_step_handler(message, summa)

def summa(message):
    global amount
    try:
            amount = int(message.text.strip())
    except ValueError:
        bot.send_message(message.chat.id, 'Неверный формат')
        bot.register_next_step_handler(message, summa)
        return

    if amount > 0:
        markup = types.InlineKeyboardMarkup(row_width=3)
        btn1 = types.InlineKeyboardButton('USD/GBP',callback_data='usd/gbp')
        btn2 = types.InlineKeyboardButton('EUR/GBP',callback_data='eur/GBP')
        btn3 = types.InlineKeyboardButton('JPY/USD',callback_data='jpy/usd')
        btn4 = types.InlineKeyboardButton('EUR/USD',callback_data='EUR/usd')
        btn5 = types.InlineKeyboardButton('Другое значение', callback_data='else')
        markup.add(btn1, btn2, btn3, btn4, btn5)
        bot.send_message(message.chat.id,'Выберите пару валют', reply_markup=markup)
    else:
        bot.send_message(message.chat.id, 'Число должно быть больше нуля')
        bot.register_next_step_handler(message, summa)
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.data != 'else':
        gm = call.data.upper().split('/')
        res = currency.convert(amount, gm[0], gm[1])
        bot.send_message(call.message.chat.id, f'Результат: {round(res, 2)} Впишите новое число')
        bot.register_next_step_handler(call.message, summa)
    else:
        bot.send_message(callback.message.chat.id, 'Введите пару значений через слеш ')
        bot.register_next_step_handler(call.message, my_currency)
def my_currency(message):
    try:
        gm = message.text.upper().split('/')
        res = currency.convert(amount, gm[0], gm[1])
        bot.send_message(message.chat.id, f'Результат: {round(res, 2)} Впишите новое число')
        bot.register_next_step_handler(message, summa)
    except Exception:
        bot.send_message(message.chat.id, 'Что то пошло не так: Попробуйте снова')
        bot.register_next_step_handler(message, summa)

bot.polling(none_stop=True)
