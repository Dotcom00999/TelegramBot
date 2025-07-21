import telebot
import yfinance as yf
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

bot = telebot.TeleBot('8028665251:AAG54py-DQvxYZDjexSmejVWFMl9nRMpvfU')

# Глобальный словарь для хранения портфолио по chat_id
portfolios = {}  # {chat_id: {ticker: quantity}}

# Фиксированные курсы валют (примерные, для тестирования)
USD_TO_EUR = 0.93  # 1 USD = 0.93 EUR
USD_TO_UAH = 41.5  # 1 USD = 41.5 UAH


# Функция для создания основной клавиатуры
def create_action_markup():
    markup = InlineKeyboardMarkup(row_width=1)
    btn1 = InlineKeyboardButton("Портфолио", callback_data='portfolio')
    btn2 = InlineKeyboardButton("Обновить котировки", callback_data='refresh')
    markup.add(btn1, btn2)
    return markup


# Функция для создания клавиатуры после просмотра портфолио
def create_portfolio_menu():
    markup = InlineKeyboardMarkup(row_width=1)
    btn1 = InlineKeyboardButton("Назад", callback_data='back')
    btn2 = InlineKeyboardButton("Добавить акции", callback_data='add_stocks')
    btn3 = InlineKeyboardButton("Удалить акции", callback_data='remove_stocks')
    markup.add(btn1, btn2, btn3)
    return markup


# Функция для создания клавиатуры при пустом портфолио
def create_empty_portfolio_menu():
    markup = InlineKeyboardMarkup(row_width=1)
    btn = InlineKeyboardButton("Добавить в портфолио", callback_data='add_to_portfolio')
    markup.add(btn)
    return markup


# Обработчик команды /start
def start(message):
    chat_id = message.chat.id
    if chat_id not in portfolios:
        portfolios[chat_id] = {}
    bot.send_message(chat_id,
                     "Привет! Используйте /setportfolio для задания начального портфолио (например, AAPL 0.25 GOOGL 5.75), затем нажмите 'Портфолио' для просмотра.")
    bot.register_next_step_handler(message, process_stock_input)


@bot.message_handler(commands=['start'])
def on_start(message):
    start(message)


# Обработчик команды /setportfolio
@bot.message_handler(commands=['setportfolio'])
def set_portfolio(message):
    chat_id = message.chat.id
    if chat_id not in portfolios:
        portfolios[chat_id] = {}
    bot.send_message(chat_id,
                     "Введите тикеры и количества через пробел (например, AAPL 0.25 GOOGL 5.75). Допускаются дробные значения, включая малые (например, 0.25).")
    bot.register_next_step_handler(message, process_set_portfolio)


# Обработка начального портфолио
def process_set_portfolio(message):
    chat_id = message.chat.id
    try:
        if chat_id not in portfolios:
            portfolios[chat_id] = {}
        parts = message.text.split()
        if len(parts) % 2 != 0:
            raise ValueError("Введите тикеры и количества попарно, например, AAPL 0.25 GOOGL 5.75.")

        for i in range(0, len(parts), 2):
            ticker = parts[i].upper()
            quantity_str = parts[i + 1].replace(',', '.')  # Заменяем запятую на точку
            try:
                quantity = float(quantity_str)  # Преобразуем в float
                if quantity <= 0:  # Разрешаем любые положительные значения, включая 0.25
                    raise ValueError(f"Количество для {ticker} должно быть положительным (например, 0.25 и выше).")
                portfolios[chat_id][ticker] = portfolios[chat_id].get(ticker,
                                                                      0) + quantity  # Суммируем, если тикер уже есть
                bot.send_message(chat_id, f"Добавлено: {ticker} - {quantity} акций (отладка).")
            except ValueError as e:
                raise ValueError(
                    f"Некорректное количество для {ticker}: {parts[i + 1]}. Используйте число (например, 0.25).")

        bot.send_message(chat_id,
                         f"Портфолио успешно обновлено! Текущие акции: {', '.join([f'{t} ({q:.4f})' for t, q in portfolios[chat_id].items()])}. Нажмите 'Портфолио' для просмотра.",
                         reply_markup=create_action_markup())
        print(f"Отладка: portfolios[{chat_id}] = {portfolios[chat_id]}")  # Отладка в консоли
    except ValueError as e:
        bot.send_message(chat_id, str(e))
        bot.register_next_step_handler(message, set_portfolio)
    except Exception as e:
        bot.send_message(chat_id, f"Произошла ошибка: {e}")
        bot.register_next_step_handler(message, set_portfolio)


# Обработка ввода (оставим для совместимости)
def process_stock_input(message):
    chat_id = message.chat.id
    try:
        parts = message.text.split()
        if len(parts) != 2:
            raise ValueError(
                "Введите тикер и количество через пробел, например, AAPL 0.25, но эта функция сейчас не используется для покупки.")

        ticker, quantity_str = parts[0].upper(), parts[1].replace(',', '.')
        quantity = float(quantity_str)
        if quantity <= 0:
            raise ValueError("Количество должно быть положительным (например, 0.25 и выше).")

        stock = yf.Ticker(ticker)
        history = stock.history(period="1d")
        if history.empty:
            raise ValueError(f"Данные для тикера {ticker} недоступны.")
        current_price = history['Close'].iloc[-1]
        if current_price <= 0:
            raise ValueError(f"Некорректная цена для {ticker}.")

        stock_data = {'ticker': ticker, 'price': current_price}
        bot.send_message(chat_id,
                         f"Текущая цена {ticker}: {current_price:.2f} USD. Используйте /setportfolio для управления портфолио.",
                         reply_markup=create_action_markup())
    except ValueError as e:
        bot.send_message(chat_id, str(e))
        bot.register_next_step_handler(message, start)
    except Exception as e:
        bot.send_message(chat_id, f"Произошла ошибка: {e}")
        bot.register_next_step_handler(message, start)


# Обработчик callback
def callback(call):
    chat_id = call.message.chat.id
    try:
        if call.data == 'portfolio':
            if chat_id not in portfolios or not portfolios[chat_id]:
                bot.send_message(chat_id, "Ваше портфолио пусто.", reply_markup=create_empty_portfolio_menu())
            else:
                portfolio_msg = "Ваше портфолио:\n"
                total_value_usd = 0
                for ticker, qty in portfolios[chat_id].items():
                    stock = yf.Ticker(ticker)
                    history = stock.history(period="1d")
                    current_price_usd = history['Close'].iloc[-1]
                    open_price_usd = history['Open'].iloc[-1]
                    change_usd = current_price_usd - open_price_usd
                    change_percent = (change_usd / open_price_usd) * 100 if open_price_usd != 0 else 0
                    trend = "📈 Рост" if change_usd > 0 else "📉 Падение" if change_usd < 0 else "Без изменений"
                    stock_value_usd = qty * current_price_usd
                    total_value_usd += stock_value_usd
                    current_price_eur = current_price_usd * USD_TO_EUR
                    current_price_uah = current_price_usd * USD_TO_UAH
                    portfolio_msg += f"{ticker}: {qty:.4f} акций, Цена: {current_price_usd:.2f} USD / {current_price_eur:.2f} EUR / {current_price_uah:.2f} UAH, Изменение: {change_usd:.2f} USD ({change_percent:.2f}%), {trend}, Итого: {stock_value_usd:.2f} USD\n"
                    # Проверка на резкое изменение (рост или падение на 10% и более)
                    if abs(change_percent) >= 10:
                        notification = f"⚠️ Уведомление: Акция {ticker} изменилась на {change_percent:.2f}% ({'рост' if change_usd > 0 else 'падение'})!"
                        bot.send_message(chat_id, notification)
                total_value_eur = total_value_usd * USD_TO_EUR  # Конвертация общей стоимости в евро
                portfolio_msg += f"\nОбщая стоимость портфолио: {total_value_eur:.2f} EUR"
                bot.send_message(chat_id, portfolio_msg, reply_markup=create_portfolio_menu())
        elif call.data == 'refresh':
            if chat_id not in portfolios or not portfolios[chat_id]:
                bot.send_message(chat_id, "Ваше портфолио пусто.", reply_markup=create_empty_portfolio_menu())
            else:
                portfolio_msg = "Обновленные котировки:\n"
                total_value_usd = 0
                for ticker, qty in portfolios[chat_id].items():
                    stock = yf.Ticker(ticker)
                    history = stock.history(period="1d")
                    current_price_usd = history['Close'].iloc[-1]
                    open_price_usd = history['Open'].iloc[-1]
                    change_usd = current_price_usd - open_price_usd
                    change_percent = (change_usd / open_price_usd) * 100 if open_price_usd != 0 else 0
                    trend = "📈 Рост" if change_usd > 0 else "📉 Падение" if change_usd < 0 else "Без изменений"
                    stock_value_usd = qty * current_price_usd
                    total_value_usd += stock_value_usd
                    current_price_eur = current_price_usd * USD_TO_EUR
                    current_price_uah = current_price_usd * USD_TO_UAH
                    portfolio_msg += f"{ticker}: {qty:.4f} акций, Цена: {current_price_usd:.2f} USD / {current_price_eur:.2f} EUR / {current_price_uah:.2f} UAH, Изменение: {change_usd:.2f} USD ({change_percent:.2f}%), {trend}, Итого: {stock_value_usd:.2f} USD\n"
                    # Проверка на резкое изменение (рост или падение на 10% и более)
                    if abs(change_percent) >= 10:
                        notification = f"⚠️ Уведомление: Акция {ticker} изменилась на {change_percent:.2f}% ({'рост' if change_usd > 0 else 'падение'})!"
                        bot.send_message(chat_id, notification)
                total_value_eur = total_value_usd * USD_TO_EUR  # Конвертация общей стоимости в евро
                portfolio_msg += f"\nОбщая стоимость портфолио: {total_value_eur:.2f} EUR"
                bot.send_message(chat_id, portfolio_msg, reply_markup=create_action_markup())
        elif call.data == 'back':
            bot.send_message(chat_id, "Вернулись к основному меню.", reply_markup=create_action_markup())
        elif call.data == 'add_stocks':
            bot.send_message(chat_id,
                             "Введите тикеры и количества через пробел (например, AAPL 0.25 GOOGL 5.75) для добавления акций.",
                             reply_markup=create_action_markup())
            bot.register_next_step_handler(call.message, process_set_portfolio)
        elif call.data == 'add_to_portfolio':
            bot.send_message(chat_id,
                             "Введите тикеры и количества через пробел (например, AAPL 0.25 GOOGL 5.75) для добавления в портфолио.",
                             reply_markup=create_action_markup())
            bot.register_next_step_handler(call.message, process_set_portfolio)
        elif call.data == 'remove_stocks':
            bot.send_message(chat_id,
                             "Введите тикер и количество для удаления через пробел (например, AAPL 0.25) или тикер для полного удаления (например, AAPL).",
                             reply_markup=create_action_markup())
            bot.register_next_step_handler(call.message, process_remove_stocks)
    except Exception as e:
        bot.send_message(chat_id, f"Ошибка: {e}")


# Обработка удаления акций
def process_remove_stocks(message):
    chat_id = message.chat.id
    try:
        parts = message.text.split()
        if len(parts) not in (1, 2):
            raise ValueError("Введите тикер или тикер и количество через пробел (например, AAPL 0.25 или AAPL).")

        ticker = parts[0].upper()
        if chat_id not in portfolios or ticker not in portfolios[chat_id]:
            raise ValueError(f"Тикер {ticker} не найден в вашем портфолио.")

        if len(parts) == 1:
            del portfolios[chat_id][ticker]  # Полное удаление акции
            bot.send_message(chat_id, f"Акция {ticker} полностью удалена из портфолио.")
        else:
            quantity_str = parts[1].replace(',', '.')  # Заменяем запятую на точку
            try:
                quantity = float(quantity_str)
                if quantity <= 0:
                    raise ValueError("Количество для удаления должно быть положительным (например, 0.25 и выше).")
                if quantity > portfolios[chat_id][ticker]:
                    raise ValueError(
                        f"Нельзя удалить {quantity} акций, так как в портфолио только {portfolios[chat_id][ticker]}.")
                portfolios[chat_id][ticker] -= quantity
                if portfolios[chat_id][ticker] == 0:
                    del portfolios[chat_id][ticker]
                bot.send_message(chat_id, f"Удалено {quantity} акций {ticker} из портфолио.")
            except ValueError as e:
                raise ValueError(f"Некорректное количество для {ticker}: {parts[1]}. {str(e)}")

        if not portfolios[chat_id]:
            bot.send_message(chat_id, "Ваше портфолио теперь пусто.", reply_markup=create_empty_portfolio_menu())
        else:
            bot.send_message(chat_id,
                             f"Портфолио обновлено! Текущие акции: {', '.join([f'{t} ({q:.4f})' for t, q in portfolios[chat_id].items()])}.",
                             reply_markup=create_action_markup())
        print(f"Отладка: portfolios[{chat_id}] = {portfolios[chat_id]}")  # Отладка в консоли
    except ValueError as e:
        bot.send_message(chat_id, str(e))
        bot.register_next_step_handler(message, process_remove_stocks)
    except Exception as e:
        bot.send_message(chat_id, f"Произошла ошибка: {e}")
        bot.register_next_step_handler(message, process_remove_stocks)


bot.callback_query_handler(func=lambda call: True)(callback)

# Запуск бота
bot.polling(non_stop=True)