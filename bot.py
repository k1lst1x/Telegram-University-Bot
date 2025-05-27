import logging
from aiogram import Bot, Dispatcher, types
import g4f
from aiogram.utils import executor
import re

def clean_markdown(text):
    # Заголовки #### → **Жирный**
    text = re.sub(r'####\s*(.+)', r'*\1*', text)
    
    # Сноски типа [[1]](url) → просто удалить
    text = re.sub(r'\[\[[^\]]+]]\([^)]+\)', '', text)
    
    # Удалить лишние пробелы
    text = text.strip()
    
    return text

# Логирование
logging.basicConfig(level=logging.INFO)

# Токен бота
API_TOKEN = '6704850793:AAG1qXpkSDwv0pDUlCyEyP1PSGUjKFyIJiU'

# Создание бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Хранилище истории сообщений
conversation_history = {}

# 📌 Сюда вставляешь системный промпт под конкретный ВУЗ
SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "Ты бот, который помогает отвечать на вопросы о вузе.\n\n"
        "Название вуза: Алматинский университет энергетики и связи имени Гумарбека Даукеева (АУЭС), также известный как Energo University.\n\n"
        "Адрес: г. Алматы, улица Байтурсынұлы 126/1, индекс 050013.\n\n"
        "Сайт университета: https://energo.university/\n"
        "Приёмная комиссия: https://energo.university/admission-committee/\n"
        "Образовательные программы: https://energo.university/education_programs/\n"
        "Видео-тур по кампусу: https://youtu.be/zcKQ_dRyKVs\n\n"
        "АУЭС — один из ведущих технических вузов Казахстана. Университет готовит специалистов в области энергетики, информационных технологий, телекоммуникаций, кибербезопасности и автоматизации. "
        "Более 90% студентов обучаются на государственных грантах. Лаборатории и учебные пространства созданы при поддержке международных компаний: Siemens, Schneider Electric, Huawei, Ordamed и др.\n\n"
        "Известные энергетики страны — выпускники АУЭС.\n\n"
        "Контакты:\n"
        "✉️ Email: aues@aues.kz | info@aues.kz\n"
        "📞 Call-центр: Пн–Пт с 9:00 до 18:00 — +7 (727) 323-11-75\n\n"
        "Отвечай вежливо, кратко и по делу. Если вопрос не относится к университету, вежливо сообщи об этом."
    )
}

# Функция обрезки длинной истории
def trim_history(history, max_length=4096):
    current_length = sum(len(msg["content"]) for msg in history)
    while history and current_length > max_length:
        removed = history.pop(1)  # не удаляем system prompt
        current_length -= len(removed["content"])
    return history

# /start — приветствие и краткая инструкция
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    user_id = message.from_user.id
    # При старте — чистим историю, чтобы был свежий диалог
    conversation_history[user_id] = [SYSTEM_PROMPT.copy()]
    text = (
        "👋 Привет! Я бот, который помогает отвечать на вопросы об Алматинском университете энергетики и связи (АУЭС / Energo University).\n\n"
        "Вы можете задавать любые вопросы о поступлении, обучении, факультетах, программах и жизни в университете. "
        "Просто напишите свой вопрос, и я постараюсь ответить!\n\n"
        "ℹ️ Для справки по командам — напишите /help."
    )
    await message.answer(text)

# /help — список команд и короткая инструкция
@dp.message_handler(commands=['help'])
async def send_help(message: types.Message):
    text = (
        "ℹ️ <b>Справка по боту:</b>\n\n"
        "/start — начать диалог сначала\n"
        "/help — показать эту справку\n"
        "/clear — очистить историю диалога\n\n"
        "❓ Просто напишите свой вопрос про университет — и получите ответ!"
    )
    await message.answer(text, parse_mode="HTML")

# Очистка истории по команде
@dp.message_handler(commands=['clear'])
async def clear_conversation(message: types.Message):
    user_id = message.from_user.id
    conversation_history[user_id] = [SYSTEM_PROMPT.copy()]
    await message.reply("История диалога очищена.")

# Обработка сообщений
@dp.message_handler()
async def handle_message(message: types.Message):
    user_id = message.from_user.id
    user_input = message.text

    if user_id not in conversation_history:
        # Начинаем историю с системного промпта
        conversation_history[user_id] = [SYSTEM_PROMPT.copy()]

    # Добавляем пользовательский запрос
    conversation_history[user_id].append({"role": "user", "content": user_input})
    conversation_history[user_id] = trim_history(conversation_history[user_id])

    try:
        response = await g4f.ChatCompletion.create_async(
            model=g4f.models.default,
            messages=conversation_history[user_id],
            provider=g4f.Provider.You,
        )
        reply = response
    except Exception as e:
        print("Ошибка:", e)
        reply = "Произошла ошибка при генерации ответа."

    # Добавляем ответ в историю
    conversation_history[user_id].append({"role": "assistant", "content": reply})
    cleaned_reply = clean_markdown(reply)

    try:
        await message.answer(cleaned_reply, parse_mode="Markdown")
    except Exception as e:
        # Fallback на обычный текст, если Markdown ломается
        print("Ошибка отправки Markdown:", e)
        await message.answer(reply)

# Запуск
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
