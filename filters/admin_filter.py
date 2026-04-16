from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery
from config import ADMIN_ID, ADMIN_USERNAME


class IsAdminFilter(BaseFilter):
    """Фильтр для проверки прав администратора"""
    
    async def __call__(self, event: Message | CallbackQuery) -> bool:
        user_id = event.from_user.id
        username = event.from_user.username
        
        if ADMIN_ID and user_id == ADMIN_ID:
            return True
        if ADMIN_USERNAME and username and username.lower() == ADMIN_USERNAME.lower():
            return True
        return False