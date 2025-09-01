@echo off
echo Creating bot files...

:: Удаляем старые файлы
del bot.py 2>nul
del .env 2>nul
del requirements.txt 2>nul

:: Создаем requirements.txt
echo aiogram==3.0.0b7 > requirements.txt
echo python-dotenv==1.0.0 >> requirements.txt
echo aiohttp==3.8.4 >> requirements.txt

:: Создаем .env
echo API_TOKEN=your_actual_bot_token_here > .env

:: Создаем bot.py
echo import asyncio > bot.py
echo import sqlite3 >> bot.py
echo import logging >> bot.py
echo import aiohttp >> bot.py
echo from datetime import datetime, time >> bot.py
echo from typing import List, Set, Dict, Any >> bot.py
echo. >> bot.py
echo from aiogram import Bot, Dispatcher, F >> bot.py
echo from aiogram.types import Message, InlineKeyboardButton, CallbackQuery >> bot.py
echo from aiogram.filters import Command >> bot.py
echo from aiogram.utils.keyboard import InlineKeyboardBuilder >> bot.py
echo from aiogram.fsm.storage.memory import MemoryStorage >> bot.py
echo from aiogram.fsm.context import FSMContext >> bot.py
echo from aiogram.fsm.state import State, StatesGroup >> bot.py
echo. >> bot.py
echo import os >> bot.py
echo from dotenv import load_dotenv >> bot.py
echo. >> bot.py
echo # Остальной код бота... >> bot.py

echo Files created successfully!
pause