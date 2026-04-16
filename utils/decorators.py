from functools import wraps
from aiogram.types import Message, CallbackQuery
from config import ADMIN_CONTACT, SUBSCRIPTION_PRICE


def require_subscription(func):
    """Декоратор для проверки активной подписки"""
    @wraps(func)
    async def wrapper(event: Message | CallbackQuery, *args, **kwargs):
        # Получаем user_db из аргументов или из объекта бота
        user_db = kwargs.get('user_db')
        if not user_db:
            # Пробуем получить из bot
            bot = kwargs.get('bot')
            if bot:
                user_db = bot.get('user_db')
        
        if not user_db:
            return await func(event, *args, **kwargs)
        
        user_id = event.from_user.id
        subscription = user_db.get_subscription_status(user_id)
        
        if subscription["days_left"] <= 0 and not subscription.get("is_forever"):
            text = (
                f"❌ Ваш тестовый период истёк.\n\n"
                f"Для продолжения использования оформите подписку за {SUBSCRIPTION_PRICE}₽/мес.\n"
                f"Свяжитесь с админом: {ADMIN_CONTACT}"
            )
            if isinstance(event, Message):
                await event.answer(text)
            else:
                await event.message.answer(text)
                await event.answer()
            return
        
        return await func(event, *args, **kwargs)
    
    return wrapper