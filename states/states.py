from aiogram.fsm.state import State, StatesGroup


class ProfileState(StatesGroup):
    """Состояния для заполнения профиля"""
    waiting_for_name = State()
    waiting_for_age = State()
    waiting_for_weight = State()
    waiting_for_height = State()
    waiting_for_gender = State()
    waiting_for_activity = State()


class MealState(StatesGroup):
    """Состояния для работы с приёмами пищи"""
    waiting_for_correction = State()


class AdminState(StatesGroup):
    """Состояния для админ-панели"""
    waiting_for_user_id = State()
    waiting_for_days = State()
    waiting_for_days_value = State()
    waiting_for_broadcast = State()
    waiting_for_broadcast_text = State()