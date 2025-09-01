import asyncio
import sqlite3
import logging
from datetime import datetime, time
from typing import List, Set

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Состояния бота
class UserState(StatesGroup):
    choosing_topics = State()

# Конфигурация
API_TOKEN = os.getenv('API_TOKEN')
if not API_TOKEN:
    raise ValueError("API_TOKEN not found")

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Определение тем
TOPICS = {
    'cv': {'name': '🤖 Computer Vision (CV)', 'emoji': '🤖'},
    'nlp': {'name': '🗣️ NLP', 'emoji': '🗣️'},
    'llm': {'name': '📚 LLM', 'emoji': '📚'},
    'rl': {'name': '🎮 Reinforcement Learning (RL)', 'emoji': '🎮'},
    'mlops': {'name': '⚙️ MLOps', 'emoji': '⚙️'}
}

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS subscriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        topic TEXT,
        subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (user_id),
        UNIQUE(user_id, topic)
    )''')
    conn.commit()
    conn.close()
    logger.info("Database initialized")

def add_user(user_id: int, username: str, first_name: str, last_name: str):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO users (user_id, username, first_name, last_name) VALUES (?, ?, ?, ?)',
                   (user_id, username, first_name, last_name))
    conn.commit()
    conn.close()

def update_user_topics(user_id: int, topics: List[str]):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM subscriptions WHERE user_id = ?', (user_id,))
    for topic in topics:
        cursor.execute('INSERT INTO subscriptions (user_id, topic) VALUES (?, ?)', (user_id, topic))
    conn.commit()
    conn.close()
    logger.info(f"User {user_id} subscribed to: {topics}")

def get_user_topics(user_id: int) -> Set[str]:
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT topic FROM subscriptions WHERE user_id = ?', (user_id,))
    topics = {row[0] for row in cursor.fetchall()}
    conn.close()
    return topics

def get_all_subscribed_users() -> List[int]:
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT user_id FROM subscriptions')
    user_ids = [row[0] for row in cursor.fetchall()]
    conn.close()
    return user_ids

def get_user_subscriptions(user_id: int) -> List[str]:
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT topic FROM subscriptions WHERE user_id = ?', (user_id,))
    topics = [row[0] for row in cursor.fetchall()]
    conn.close()
    return topics

# Создание клавиатуры с темами
def create_topics_keyboard(selected_topics: Set[str] = None) -> InlineKeyboardBuilder:
    if selected_topics is None:
        selected_topics = set()
    
    builder = InlineKeyboardBuilder()
    
    for topic_key, topic_data in TOPICS.items():
        prefix = "✅ " if topic_key in selected_topics else ""
        text = f"{prefix}{topic_data['name']}"
        builder.add(InlineKeyboardButton(text=text, callback_data=f"topic_{topic_key}"))
    
    builder.add(InlineKeyboardButton(text="🚀 Готово! Отправлять новости", callback_data="done"))
    builder.adjust(1)
    return builder

# Получение новостей
async def get_news_for_topic(topic: str):
    news = {
        'cv': [
            {'title': 'Новые достижения в компьютерном зрении', 'url': 'https://arxiv.org/list/cs.CV/recent'},
            {'title': 'OpenCV 4.8 released с новыми функциями', 'url': 'https://opencv.org'}
        ],
        'nlp': [
            {'title': 'Тренды в обработке естественного языка 2024', 'url': 'https://huggingface.co'},
            {'title': 'Новые трансформеры для NLP задач', 'url': 'https://arxiv.org/list/cs.CL/recent'}
        ],
        'llm': [
            {'title': 'Обновления в мире больших языковых моделей', 'url': 'https://openai.com'},
            {'title': 'Local LLM: новые возможности', 'url': 'https://github.com/topics/llm'}
        ],
        'rl': [
            {'title': 'Reinforcement Learning в играх', 'url': 'https://arxiv.org/list/cs.LG/recent'},
            {'title': 'Новые алгоритмы RL', 'url': 'https://deepmind.com'}
        ],
        'mlops': [
            {'title': 'Лучшие практики MLOps 2024', 'url': 'https://mlops.community'},
            {'title': 'Инструменты для развертывания ML моделей', 'url': 'https://github.com/topics/mlops'}
        ]
    }
    return news.get(topic, [])

# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    add_user(user_id, message.from_user.username, message.from_user.first_name, message.from_user.last_name)
    current_topics = get_user_topics(user_id)
    
    welcome_text = (
        "🤖🚀📊 *Привет! Я KulisML* \n\n"
        "Я собрал для тебя самые свежие новости из мира AI! "
        "Выбери направления, которые тебе интересны 🎯\n\n"
        "*Выбери одну или несколько тем:*"
    )
    
    keyboard = create_topics_keyboard(current_topics)
    await message.answer(welcome_text, parse_mode="Markdown", reply_markup=keyboard.as_markup())
    await state.set_state(UserState.choosing_topics)
    logger.info(f"User {user_id} started bot")

@dp.callback_query(UserState.choosing_topics, F.data.startswith("topic_"))
async def process_topic_selection(callback: CallbackQuery, state: FSMContext):
    topic_key = callback.data.split("_")[1]
    user_id = callback.from_user.id
    current_data = await state.get_data()
    selected_topics = current_data.get('selected_topics', set(get_user_topics(user_id)))
    
    if topic_key in selected_topics:
        selected_topics.remove(topic_key)
    else:
        selected_topics.add(topic_key)
    
    await state.update_data(selected_topics=selected_topics)
    keyboard = create_topics_keyboard(selected_topics)
    await callback.message.edit_reply_markup(reply_markup=keyboard.as_markup())
    await callback.answer()

@dp.callback_query(UserState.choosing_topics, F.data == "done")
async def process_done(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    current_data = await state.get_data()
    selected_topics = current_data.get('selected_topics', set())
    update_user_topics(user_id, list(selected_topics))
    
    if selected_topics:
        topics_list = "\n".join([f"• {TOPICS[topic]['name']}" for topic in selected_topics])
        message_text = f"🎉 *Отлично!* Твои подписки:\n\n{topics_list}\n\nЕжедневно в 09:00 новости! 📨"
    else:
        message_text = "⚠️ Ты не выбрал ни одной темы. Напиши /start снова 🔄"
    
    await callback.message.edit_text(message_text, parse_mode="Markdown", reply_markup=None)
    await state.clear()
    await callback.answer()

# Функция отправки новостей
async def send_daily_news():
    try:
        user_ids = get_all_subscribed_users()
        if not user_ids:
            return
        
        for user_id in user_ids:
            try:
                user_topics = get_user_subscriptions(user_id)
                if not user_topics:
                    continue
                
                news_text = "📰 *Ежедневные новости AI* 🚀\n\n"
                for topic in user_topics:
                    topic_news = await get_news_for_topic(topic)
                    if topic_news:
                        news_text += f"🔥 *{TOPICS[topic]['name']}:*\n"
                        for i, news_item in enumerate(topic_news[:2], 1):
                            news_text += f"{i}. {news_item['title']}\n🔗 [Читать]({news_item['url']})\n"
                        news_text += "\n"
                
                news_text += "*Хорошего дня!* ⚡️"
                await bot.send_message(user_id, news_text, parse_mode="Markdown", disable_web_page_preview=True)
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error sending to user {user_id}: {e}")
        
    except Exception as e:
        logger.error(f"Error in daily news: {e}")

# Планировщик
async def scheduler():
    while True:
        now = datetime.now().time()
        target_time = time(9, 0)
        now_datetime = datetime.now()
        target_datetime = datetime.combine(now_datetime.date(), target_time)
        if now > target_time:
            target_datetime = target_datetime.replace(day=target_datetime.day + 1)
        wait_seconds = (target_datetime - now_datetime).total_seconds()
        await asyncio.sleep(wait_seconds)
        await send_daily_news()

# Тестовая команда
@dp.message(Command("test_news"))
async def cmd_test_news(message: Message):
    user_id = message.from_user.id
    user_topics = get_user_subscriptions(user_id)
    if not user_topics:
        await message.answer("❌ Сначала выбери темы через /start")
        return
    
    news_text = "📰 *Тестовые новости* 🚀\n\n"
    for topic in user_topics:
        topic_news = await get_news_for_topic(topic)
        if topic_news:
            news_text += f"🔥 *{TOPICS[topic]['name']}:*\n"
            for i, news_item in enumerate(topic_news[:2], 1):
                news_text += f"{i}. {news_item['title']}\n🔗 [Читать]({news_item['url']})\n"
            news_text += "\n"
    
    await message.answer(news_text, parse_mode="Markdown", disable_web_page_preview=True)

# Основная функция
async def main():
    init_db()
    logger.info("🤖 KulisML Bot starting...")
    asyncio.create_task(scheduler())
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped")
    except Exception as e:
        logger.error(f"Bot error: {e}")
