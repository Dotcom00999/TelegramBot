import telebot
import requests
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


# 🔐 Вставь свои ключи
TELEGRAM_TOKEN = ""
OPENROUTER_API_KEY = ""  # https://openrouter.ai/settings

# 🤖 Инициализация бота
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# 🔎 Обработчик команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    text = (
        "<b>Привет!</b>\n"
        "Напиши описание услуги, и я оценю её ценовой диапазон в Германии (в евро).\n\n"
        "Или выбери один из шаблонов ниже 👇"
    )

    # Создаём inline-клавиатуру
    markup = types.InlineKeyboardMarkup()
    btn1 = InlineKeyboardButton("💻 Услуги по созданию сайта", callback_data="template_website")
    markup.row(btn1)
    btn2 = InlineKeyboardButton("💶 Узнать ценовую политику", callback_data="template_pricing"),
    btn3 = InlineKeyboardButton("📅 Забронировать термин", callback_data="template_booking")
    markup.row(btn2, btn3)

    bot.send_message(
        message.chat.id,
        text,
        parse_mode="HTML",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    if call.data == "template_website":
        user_input = "Создание корпоративного сайта с адаптивным дизайном"
    elif call.data == "template_pricing":
        user_input = "Ценовая политика на услуги маркетинга в Германии"
    elif call.data == "template_booking":
        user_input = "Сколько стоит консультация и как записаться на термин?"

    # Дальше отправляем этот шаблон как будто пользователь написал сам
    # Можно вызвать общую обработку (например, ту, что запрашивает ИИ)


# 💬 Обработка текста
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_input = message.text.strip()

    prompt = f"""
    Ты эксперт по рынку услуг в Германии.

    Оцени рыночный диапазон цен на услугу, описанную ниже, строго в евро (€).

    Отвечай прямо и в конце добавляй :
   
    Свое мнение в Скобках
    
    Очень коротко и без воды со знаком евро в конце.

    Описание услуги:
    «{user_input}»
    """

    # 📡 Запрос к OpenRouter
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "mistralai/mistral-7b-instruct",  # Быстрая и бесплатная модель
        "messages": [{"role": "user", "content": prompt}],
    }

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload
        )
        data = response.json()
        reply = data["choices"][0]["message"]["content"]
        bot.send_message(message.chat.id, reply)
    except Exception as e:
        bot.send_message(message.chat.id, "Произошла ошибка при обращении к ИИ.")
        print("Ошибка:", e)

# ▶️ Запуск бота3
bot.polling(none_stop=True)
