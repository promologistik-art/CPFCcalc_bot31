from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ACTIVITY_LEVELS


def get_gender_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора пола"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👨 Мужской", callback_data="gender_male"),
            InlineKeyboardButton(text="👩 Женский", callback_data="gender_female")
        ]
    ])


def get_activity_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора уровня активности"""
    buttons = []
    emojis = {"1": "🪑", "2": "🚶", "3": "🏃", "4": "💪", "5": "🔥"}
    for key, value in ACTIVITY_LEVELS.items():
        emoji = emojis.get(key, "•")
        buttons.append([
            InlineKeyboardButton(
                text=f"{emoji} {value['name']}",
                callback_data=f"activity_{key}"
            )
        ])
    buttons.append([
        InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_gender")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_confirm_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения сохранения еды"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Сохранить", callback_data="meal_save"),
            InlineKeyboardButton(text="✏️ Исправить", callback_data="meal_edit")
        ],
        [
            InlineKeyboardButton(text="❌ Отменить", callback_data="meal_cancel")
        ]
    ])


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Главное меню"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Статистика", callback_data="menu_stats"),
            InlineKeyboardButton(text="📜 История", callback_data="menu_history")
        ],
        [
            InlineKeyboardButton(text="👤 Профиль", callback_data="menu_profile"),
            InlineKeyboardButton(text="💳 Подписка", callback_data="menu_subscription")
        ],
        [
            InlineKeyboardButton(text="ℹ️ Помощь", callback_data="menu_help")
        ]
    ])


def get_profile_menu_keyboard() -> InlineKeyboardMarkup:
    """Меню профиля"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👀 Посмотреть", callback_data="profile_view"),
            InlineKeyboardButton(text="✏️ Изменить", callback_data="profile_edit")
        ],
        [
            InlineKeyboardButton(text="📊 Моя норма", callback_data="profile_tdee")
        ],
        [
            InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main")
        ]
    ])


def get_admin_menu_keyboard() -> InlineKeyboardMarkup:
    """Меню админ-панели"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users"),
            InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")
        ],
        [
            InlineKeyboardButton(text="📨 Рассылка", callback_data="admin_broadcast"),
            InlineKeyboardButton(text="🔗 Рефералы", callback_data="admin_refs")
        ],
        [
            InlineKeyboardButton(text="➕ Добавить пользователя", callback_data="admin_add_user"),
            InlineKeyboardButton(text="⏱ Продлить", callback_data="admin_extend")
        ],
        [
            InlineKeyboardButton(text="💾 Бэкап БД", callback_data="admin_backup"),
            InlineKeyboardButton(text="📤 Экспорт в Excel", callback_data="admin_export")
        ]
    ])


def get_clear_confirm_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения очистки статистики"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да, очистить", callback_data="clear_confirm"),
            InlineKeyboardButton(text="❌ Нет", callback_data="clear_cancel")
        ]
    ])