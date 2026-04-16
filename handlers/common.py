from aiogram import Router, types, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from keyboards.inline import get_main_menu_keyboard
from utils.helpers import format_subscription_status

router = Router()


async def notify_admin(bot: Bot, admin_id: int, user_id: int, username: str, first_name: str):
    """Уведомляет админа о новом пользователе"""
    if admin_id:
        msg = f"🆕 Новый пользователь!\n\nID: {user_id}\nИмя: {first_name}"
        if username:
            msg += f"\nUsername: @{username}"
        try:
            await bot.send_message(admin_id, msg)
        except:
            pass


@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext, user_db, bot: Bot, admin_id: int):
    await state.clear()
    
    args = message.text.split()
    referral_code = None
    if len(args) > 1:
        referral_code = args[1]
        if not referral_code.startswith('ref_'):
            referral_code = None
    
    user, is_new = user_db.get_or_create_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name,
        referral_code
    )
    
    if is_new:
        await notify_admin(bot, admin_id, message.from_user.id, 
                          message.from_user.username, message.from_user.first_name)
        
        welcome_extra = ""
        if referral_code:
            welcome_extra = "\n\n🎁 Вы перешли по реферальной ссылке и получили +3 дня к тестовому периоду!"
        
        await message.answer(
            f"🍎 Добро пожаловать в FoodTracker Bot!{welcome_extra}\n\n"
            f"Просто напишите, что съели — я всё посчитаю!",
            reply_markup=get_main_menu_keyboard()
        )
    
    subscription = user_db.get_subscription_status(message.from_user.id)
    profile = user_db.get_profile(message.from_user.id)
    
    welcome_text = (
        f"🍎 FoodTracker Bot\n\n"
        f"Просто напишите, что съели — я всё посчитаю!\n\n"
        f"💳 Статус подписки: {format_subscription_status(subscription)}"
    )
    
    if not profile:
        welcome_text += "\n\n👤 Давайте познакомимся! Используйте кнопку «Профиль» ниже."
    
    await message.answer(welcome_text, reply_markup=get_main_menu_keyboard())


@router.message(Command("help"))
async def cmd_help(message: types.Message):
    help_text = (
        "ℹ️ Помощь:\n\n"
        "📊 /stats — статистика за сегодня\n"
        "📜 /history — история записей\n"
        "🧹 /clear — очистить статистику\n"
        "👤 /profile — мой профиль\n"
        "✏️ /profile_edit — изменить профиль\n"
        "💳 /subscription — статус подписки\n\n"
        "🍽 Просто напишите, что съели, например:\n"
        "• борщ 400г\n"
        "• яичница 4 яйца\n"
        "• гречка 200г, курица 150\n\n"
        f"📞 Связаться с админом: @{message.bot._me.username}\n\n"
        "👑 Администраторам: /admin"
    )
    
    await message.answer(help_text, reply_markup=get_main_menu_keyboard())


@router.message(Command("subscription"))
async def cmd_subscription(message: types.Message, user_db):
    subscription = user_db.get_subscription_status(message.from_user.id)
    await message.answer(
        f"💳 Статус подписки: {format_subscription_status(subscription)}",
        reply_markup=get_main_menu_keyboard()
    )


@router.message(Command("menu"))
async def cmd_menu(message: types.Message):
    await message.answer("🍎 Главное меню:", reply_markup=get_main_menu_keyboard())


# Обработчики callback-запросов для навигации по меню

@router.callback_query(lambda c: c.data == "menu_stats")
async def menu_stats_callback(callback: types.CallbackQuery):
    await callback.message.delete()
    await callback.message.answer("📊 Статистика загружается...")
    # Перенаправляем на команду stats
    from handlers.meals import cmd_stats
    await cmd_stats(callback.message, callback.bot.user_db)
    await callback.answer()


@router.callback_query(lambda c: c.data == "menu_history")
async def menu_history_callback(callback: types.CallbackQuery):
    await callback.message.delete()
    from handlers.meals import cmd_history
    await cmd_history(callback.message, callback.bot.user_db)
    await callback.answer()


@router.callback_query(lambda c: c.data == "menu_profile")
async def menu_profile_callback(callback: types.CallbackQuery):
    await callback.message.delete()
    from handlers.profile import cmd_profile
    await cmd_profile(callback.message, callback.bot.user_db)
    await callback.answer()


@router.callback_query(lambda c: c.data == "menu_subscription")
async def menu_subscription_callback(callback: types.CallbackQuery):
    await callback.message.delete()
    await cmd_subscription(callback.message, callback.bot.user_db)
    await callback.answer()


@router.callback_query(lambda c: c.data == "menu_help")
async def menu_help_callback(callback: types.CallbackQuery):
    await callback.message.delete()
    await cmd_help(callback.message)
    await callback.answer()


@router.callback_query(lambda c: c.data == "back_to_main")
async def back_to_main_callback(callback: types.CallbackQuery):
    await callback.message.edit_text("🍎 Главное меню:", reply_markup=get_main_menu_keyboard())
    await callback.answer()