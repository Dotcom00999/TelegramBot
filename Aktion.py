import telebot
import yfinance as yf
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

bot = telebot.TeleBot('8028665251:AAG54py-DQvxYZDjexSmejVWFMl9nRMpvfU')

# Глобальные переменные
amount = 0
stock_data = {}


# Функция для создания inline-клавиатуры
def create_action_markup():
    markup = InlineKeyboardMarkup(row_width=2)
    btn1 = InlineKeyboardButton("Купить", callback_data='buy')
    btn2 = InlineKeyboardButton("Продать", callback_data='sell')
    btn3 = InlineKeyboardButton("Информация", callback_data='info')
    markup.add(btn1, btn2, btn3)
    return markup


# Обработчик команды /start
def start(message):
    bot.send_message(message.chat.id,
                     "Привет! Введите тикер акции (например, AAPL) и количество через пробел (например, AAPL 10).")
    bot.register_next_step_handler(message, process_stock_input)


@bot.message_handler(commands=['start'])
def on_start(message):
    start(message)


# Обработка ввода тикера и количества
def process_stock_input(message):
    global amount, stock_data
    try:
        parts = message.text.split()
        if len(parts) != 2:
            raise ValueError("Введите тикер и количество через пробел, например, AAPL 10.")

        ticker, quantity = parts[0].upper(), int(parts[1])
        if quantity <= 0:
            raise ValueError("Количество должно быть положительным.")

        stock = yf.Ticker(ticker)
        history = stock.history(period="1d")
        if history.empty:
            raise ValueError(f"Данные для тикера {ticker} недоступны.")
        current_price = history['Close'].iloc[-1]
        if current_price <= 0:
            raise ValueError(f"Некорректная цена для {ticker}.")

        amount = quantity
        stock_data = {'ticker': ticker, 'price': current_price}

        bot.send_message(message.chat.id, f"Текущая цена {ticker}: {current_price:.2f} USD. Выберите действие:",
                         reply_markup=create_action_markup())
    except ValueError as e:
        bot.send_message(message.chat.id, str(e))
        bot.register_next_step_handler(message, start)
    except Exception as e:
        bot.send_message(message.chat.id, f"Произошла ошибка: {e}")
        bot.register_next_step_handler(message, start)


# Обработчик callback
def callback(call):
    try:
        if call.data == 'buy':
            total = amount * stock_data['price']
            bot.send_message(call.message.chat.id,
                             f"Стоимость покупки {amount} акций {stock_data['ticker']}: {total:.2f} USD.")
        elif call.data == 'sell':
            total = amount * stock_data['price']
            bot.send_message(call.message.chat.id,
                             f"Стоимость продажи {amount} акций {stock_data['ticker']}: {total:.2f} USD.")
        elif call.data == 'info':
            bot.send_message(call.message.chat.id,
                             f"Тикер: {stock_data['ticker']}, Цена: {stock_data['price']:.2f} USD.")
        bot.answer_callback_query(call.id)
    except Exception as e:
        bot.send_message(call.message.chat.id, f"Ошибка: {e}")


bot.callback_query_handler(func=lambda call: True)(callback)

# Запуск бота
bot.polling(non_stop=True)