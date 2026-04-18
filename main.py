import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from config import BOT_TOKEN, ADMIN_ID, USER_DB_PATH
from db import UserDB

# Импорты хендлеров
from handlers import common, profile, meals, admin, referral

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def set_bot_commands(bot: Bot):
    """Устанавливает команды бота в меню"""
    commands = [
        BotCommand(command="start", description="🍎 Начать работу"),
        BotCommand(command="menu", description="📋 Главное меню"),
        BotCommand(command="stats", description="📊 Статистика за сегодня"),
        BotCommand(command="history", description="📜 История записей"),
        BotCommand(command="clear", description="🧹 Очистить статистику"),
        BotCommand(command="profile", description="👤 Мой профиль"),
        BotCommand(command="profile_edit", description="✏️ Изменить профиль"),
        BotCommand(command="subscription", description="💳 Статус подписки"),
        BotCommand(command="help", description="ℹ️ Помощь"),
        BotCommand(command="admin", description="👑 Админ-панель"),
    ]
    await bot.set_my_commands(commands)


async def main():
    """Точка входа"""
    logger.info("🚀 Запуск бота...")
    
    # Инициализация бота и диспетчера
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    
    # Инициализация БД
    user_db = UserDB()
    logger.info(f"📂 База данных подключена: {USER_DB_PATH}")
    
    # Сохраняем user_db в bot для доступа из хендлеров
    bot.user_db = user_db
    bot.admin_id = ADMIN_ID
    
    # ВАЖНО: Порядок регистрации роутеров!
    # Сначала регистрируем роутеры с конкретными командами
    dp.include_router(common.router)
    dp.include_router(profile.router)
    dp.include_router(admin.router)      # Админ-панель
    dp.include_router(referral.router)   # Реферальные команды
    # Обработчик еды должен быть ПОСЛЕДНИМ, так как он ловит все остальные сообщения
    dp.include_router(meals.router)
    
    # Устанавливаем команды
    await set_bot_commands(bot)
    
    logger.info("✅ Бот запущен и готов к работе!")
    
    # Запуск поллинга
    try:
        await dp.start_polling(bot, user_db=user_db)
    finally:
        user_db.close()
        logger.info("👋 Бот остановлен")


if __name__ == "__main__":
    asyncio.run(main())