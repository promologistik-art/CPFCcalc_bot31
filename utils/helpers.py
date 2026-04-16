import re
from config import ADMIN_CONTACT, ACTIVITY_LEVELS


def format_daily_stats(stats: dict, tdee: float = None) -> str:
    """Форматирует статистику за день"""
    text = f"""
📊 Статистика за сегодня:
🔥 Калории: {stats['calories']:.0f} ккал
🥩 Белки: {stats['protein']:.1f} г
🧈 Жиры: {stats['fat']:.1f} г
🍚 Углеводы: {stats['carbs']:.1f} г
"""
    if tdee and tdee > 0:
        percent = (stats['calories'] / tdee) * 100
        text += f"\n📈 От суточной нормы: {percent:.0f}% (норма: {tdee:.0f} ккал)"
    
    return text


def format_subscription_status(subscription: dict) -> str:
    """Форматирует статус подписки"""
    if subscription.get("is_forever"):
        return "✅ Активна (бессрочно)"
    days = subscription.get("days_left", 0)
    if days > 0:
        return f"✅ Активна. Осталось дней: {days}"
    else:
        return f"❌ Истекла. Для продления свяжитесь с админом: {ADMIN_CONTACT}"


def is_affirmative(text: str) -> bool:
    """Проверяет, является ли текст утвердительным ответом"""
    text = text.lower().strip()
    affirmative = ["да", "yes", "+", "ок", "окей", "хорошо", "верно", "ага", "дада", "записывай", "сохранить", "подтвердить"]
    return any(word in text for word in affirmative)


def is_negative(text: str) -> bool:
    """Проверяет, является ли текст отрицательным ответом"""
    text = text.lower().strip()
    negative = ["нет", "no", "-", "не", "неверно", "не правильно", "не так", "отмена", "отменить"]
    return any(word in text for word in negative)


def is_correction(text: str) -> bool:
    """Проверяет, содержит ли текст корректировку (цифры или единицы измерения)"""
    has_numbers = bool(re.search(r'\d+', text))
    has_units = bool(re.search(r'г|гр|грамм|кг|шт|штук|ложк|стакан|чашка|мл|л', text.lower()))
    return has_numbers or has_units


def is_delete_command(text: str) -> bool:
    """Проверяет, является ли текст командой удаления"""
    text = text.lower().strip()
    delete_words = ["удали", "убрать", "удалить", "убри", "убери", "delete", "remove"]
    return any(word in text for word in delete_words)


def has_profile(user_db, user_id: int) -> bool:
    """Проверяет, заполнен ли профиль пользователя"""
    return user_db.get_profile(user_id) is not None


def extract_product_data(product: dict) -> dict:
    """Извлекает данные продукта для сохранения в БД"""
    return {
        "name": product.get("name", "Неизвестный продукт"),
        "weight_grams": product.get("weight_grams", 100),
        "calories": product.get("calories", 0),
        "protein": product.get("protein", 0),
        "fat": product.get("fat", 0),
        "carbs": product.get("carbs", 0)
    }


async def get_user_id_or_username(user_db, user_input: str) -> int | None:
    """Получает ID пользователя по строке (ID или @username)"""
    user_input = user_input.strip()
    if user_input.isdigit():
        return int(user_input)
    else:
        username = user_input.lstrip('@')
        return user_db.get_user_id_by_username(username)