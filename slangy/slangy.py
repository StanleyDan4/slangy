import os
import logging
import json
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackQueryHandler
)
from gigachat import GigaChat

# Загрузка переменных окружения
load_dotenv()

# Настройка логгирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
TELEGRAM_TOKEN = '8130340983:AAGWwFkgpFFjv-i_nQt1pO-FppjzET80kBw'
GIGACHAT_API_KEY = 'NjAwZGRjMjctN2I1Yi00YTk5LWE3MTYtNjI1MTkwMGMyZTE4OjlhYWVmYTNhLTk1ODItNDg0ZC1iM2MyLWRhMzAyNzI1MzFhYw=='  # Вставьте ваш сырой API-ключ



# Инициализация GigaChat
try:
    giga = GigaChat(
        credentials=GIGACHAT_API_KEY,
        verify_ssl_certs=False,
      
    )
except Exception as e:
    logger.error(f"Ошибка инициализации GigaChat: {e}")
    giga = None

# Файл для хранения пользовательских сленговых слов
SLANG_FILE = "user_slang.json"

# Загрузка сленговых слов из файла
def load_slang():
    if not os.path.exists(SLANG_FILE):
        return {}
    with open(SLANG_FILE, "r", encoding="utf-8") as file:
        return json.load(file)

# Сохранение сленговых слов в файл
def save_slang(slang_data):
    with open(SLANG_FILE, "w", encoding="utf-8") as file:
        json.dump(slang_data, file, ensure_ascii=False, indent=4)

# Системный промт для GigaChat
SYSTEM_PROMPT = """Ты эксперт по современному молодежному сленгу.
Форматируй ответ так:

📌 [Слово] - [часть речи]

🔹 Значение: [простое объяснение]
🔹 Пример: "[пример предложения]"
🔹 Происхождение: [история появления]
🔹 Синонимы: [похожие слова]

Если слово не является сленгом, скажи: "Это не похоже на сленг. Попробуйте другое слово".
Ответ должен быть коротким и понятным, без лишних символов или текста."""

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Я бот для расшифровки сленга!\n"
        "Используйте команду /add [слово] [значение], чтобы добавить новое слово."
    )

# Команда /add
async def add_slang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Получаем аргументы команды
        args = context.args
        if len(args) < 2:
            await update.message.reply_text("❌ Неправильный формат. Используйте: /add [слово] [значение]")
            return
        
        word = args[0].lower()
        definition = " ".join(args[1:])
        
        # Загружаем текущие сленговые слова
        slang_data = load_slang()
        
        # Добавляем новое слово
        slang_data[word] = definition
        
        # Сохраняем обновленные данные
        save_slang(slang_data)
        
        await update.message.reply_text(f"✅ Спасибо! Я запомнил новое слово: {word} - {definition}")
    except Exception as e:
        logger.error(f"Ошибка при добавлении слова: {e}")
        await update.message.reply_text("⚠️ Ошибка при добавлении слова")

# Обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_msg = update.message.text.strip().lower()
    
    if not user_msg:
        await update.message.reply_text("Пожалуйста, введите слово")
        return
    
    try:
        # Проверяем, есть ли слово в пользовательском словаре
        slang_data = load_slang()
        if user_msg in slang_data:
            await update.message.reply_text(slang_data[user_msg])
            return
        
        # Если GigaChat недоступен, используем только пользовательский словарь
        if giga is None:
            await update.message.reply_text(
                "⚠️ GigaChat временно недоступен. Попробуйте другое слово или добавьте новое значение."
            )
            return
        
        # Генерация ответа через GigaChat
        response = giga.chat(f"{SYSTEM_PROMPT}\n\nСлово: {user_msg}")
        generated_text = response.choices[0].message.content
        
        # Если GigaChat считает, что это не сленг
        if "Это не похоже на сленг" in generated_text:
            await update.message.reply_text(
                "🤔 Я пока не знаю такого сленга.\n"
                "Добавьте значение с помощью команды /add [слово] [значение]."
            )
        else:
            # Отправляем ответ от GigaChat
            await update.message.reply_text(generated_text)
        
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        if "402 Payment Required" in str(e):
            await update.message.reply_text(
                "⚠️ Бесплатный лимит GigaChat исчерпан. Пожалуйста, свяжитесь с администратором для активации платного тарифа."
            )
        else:
            await update.message.reply_text("⚠️ Ошибка при обработке запроса")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add_slang))
    
    # Текстовые сообщения
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    app.run_polling()

if __name__ == '__main__':
    main()