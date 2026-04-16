import asyncio
from aiogram import Router, types, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from states.states import MealState
from keyboards.inline import get_confirm_keyboard, get_clear_confirm_keyboard, get_main_menu_keyboard
from utils.helpers import (
    format_daily_stats,
    is_affirmative,
    is_negative,
    is_correction,
    is_delete_command,
    has_profile,
    extract_product_data
)
from food_search import FoodSearch

router = Router()
food_search = FoodSearch()


@router.message(Command("stats"))
async def cmd_stats(message: types.Message, user_db):
    subscription = user_db.get_subscription_status(message.from_user.id)
    if subscription["days_left"] <= 0 and not subscription.get("is_forever"):
        await message.answer(
            f"❌ Ваш тестовый период истёк.\n\nДля продолжения оформите подписку."
        )
        return
    
    stats = user_db.get_today_stats(message.from_user.id)
    profile = user_db.get_profile(message.from_user.id)
    tdee = user_db.calculate_tdee(profile) if profile else None
    
    await message.answer(
        format_daily_stats(stats, tdee),
        reply_markup=get_main_menu_keyboard()
    )


@router.message(Command("history"))
async def cmd_history(message: types.Message, user_db):
    subscription = user_db.get_subscription_status(message.from_user.id)
    if subscription["days_left"] <= 0 and not subscription.get("is_forever"):
        await message.answer(
            f"❌ Ваш тестовый период истёк.\n\nДля продолжения оформите подписку."
        )
        return
    
    meals = user_db.get_recent_meals(message.from_user.id, 10)
    if not meals:
        await message.answer("📜 История пуста.", reply_markup=get_main_menu_keyboard())
        return
    
    text = "📜 Последние записи:\n\n"
    for meal in meals:
        weight = meal.get("weight_grams", 0)
        text += f"🍽 {meal['product_name']} - {weight}г — {meal['calories']:.0f} ккал\n"
    
    await message.answer(text, reply_markup=get_main_menu_keyboard())


@router.message(Command("clear"))
async def cmd_clear(message: types.Message):
    await message.answer(
        "🧹 Очистить статистику за сегодня?",
        reply_markup=get_clear_confirm_keyboard()
    )


@router.callback_query(lambda c: c.data == "clear_confirm")
async def clear_confirm_callback(callback: types.CallbackQuery, user_db):
    user_db.clear_today(callback.from_user.id)
    await callback.message.edit_text("✅ Статистика очищена!")
    await callback.answer()


@router.callback_query(lambda c: c.data == "clear_cancel")
async def clear_cancel_callback(callback: types.CallbackQuery):
    await callback.message.edit_text("❌ Отменено.")
    await callback.answer()


@router.message()
async def handle_meal_input(message: types.Message, state: FSMContext, user_db, bot: Bot):
    """Основной обработчик ввода еды"""
    user_id = message.from_user.id
    
    # Проверка подписки
    subscription = user_db.get_subscription_status(user_id)
    if subscription["days_left"] <= 0 and not subscription.get("is_forever"):
        await message.answer(
            f"❌ Ваш тестовый период истёк.\n\nДля продолжения оформите подписку."
        )
        return
    
    # Если пользователь в состоянии ожидания корректировки
    current_state = await state.get_state()
    if current_state == MealState.waiting_for_correction.state:
        await handle_correction(message, state, user_db, bot)
        return
    
    # Новый запрос
    waiting_msg = await message.answer("🔍 Считаю...")
    await bot.send_chat_action(message.chat.id, "typing")
    
    result = await food_search.parse_and_calculate(message.text)
    await waiting_msg.delete()
    
    if not result["success"] or not result["data"].get("products"):
        await message.answer(
            "❌ Не удалось обработать. Попробуйте написать по-другому:\n"
            "• борщ 400г\n"
            "• яичница 4 яйца\n"
            "• стакан кефира"
        )
        return
    
    data = result["data"]
    products = data.get("products", [])
    user_text = result.get("user_text", "")
    
    if not products:
        await message.answer("❌ Не удалось распознать продукты.")
        return
    
    await state.set_state(MealState.waiting_for_correction)
    await state.update_data(original_products=products)
    
    if user_text:
        await message.answer(user_text + "\n\nЗаписываю?", reply_markup=get_confirm_keyboard())
    else:
        lines = []
        for p in products:
            name = p.get("name", "")
            weight = p.get("weight_grams", 0)
            cal = p.get("calories", 0)
            prot = p.get("protein", 0)
            fat = p.get("fat", 0)
            carbs = p.get("carbs", 0)
            lines.append(f"🍽 {name} - {weight}г\n   🔥 {cal:.0f} ккал | Б: {prot:.1f} | Ж: {fat:.1f} | У: {carbs:.1f}")
        
        total = data.get("total", {})
        result_text = "\n\n".join(lines)
        result_text += f"\n\n📊 ИТОГО: {total.get('calories', 0):.0f} ккал | Б: {total.get('protein', 0):.1f}г | Ж: {total.get('fat', 0):.1f}г | У: {total.get('carbs', 0):.1f}г"
        result_text += "\n\nЗаписываю?"
        
        await message.answer(result_text, reply_markup=get_confirm_keyboard())


@router.callback_query(lambda c: c.data == "meal_save")
async def meal_save_callback(callback: types.CallbackQuery, state: FSMContext, user_db):
    data = await state.get_data()
    products = data.get("original_products", [])
    
    for p in products:
        product_data = extract_product_data(p)
        user_db.add_meal(callback.from_user.id, product_data)
    
    stats = user_db.get_today_stats(callback.from_user.id)
    profile = user_db.get_profile(callback.from_user.id)
    tdee = user_db.calculate_tdee(profile) if profile else None
    
    response = f"✅ Сохранено!\n\n{format_daily_stats(stats, tdee)}"
    
    if not has_profile(user_db, callback.from_user.id):
        response += "\n\n👤 Заполните профиль для точных расчётов: /profile"
    
    await callback.message.edit_text(response, reply_markup=get_main_menu_keyboard())
    await state.clear()
    await callback.answer()


@router.callback_query(lambda c: c.data == "meal_cancel")
async def meal_cancel_callback(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("❌ Отменено.", reply_markup=get_main_menu_keyboard())
    await state.clear()
    await callback.answer()


@router.callback_query(lambda c: c.data == "meal_edit")
async def meal_edit_callback(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "✏️ Напишите правильные данные, например:\n"
        "• борщ 300г\n"
        "• кефир 200г\n"
        "• удали яйца"
    )
    await callback.answer()


async def handle_correction(message: types.Message, state: FSMContext, user_db, bot: Bot):
    """Обработка корректировки блюда"""
    user_text = message.text.strip()
    user_text_lower = user_text.lower()
    data = await state.get_data()
    original_products = data.get("original_products", [])
    
    # Утвердительный ответ - сохраняем
    if is_affirmative(user_text_lower):
        for p in original_products:
            product_data = extract_product_data(p)
            user_db.add_meal(message.from_user.id, product_data)
        
        stats = user_db.get_today_stats(message.from_user.id)
        profile = user_db.get_profile(message.from_user.id)
        tdee = user_db.calculate_tdee(profile) if profile else None
        
        response = f"✅ Сохранено!\n\n{format_daily_stats(stats, tdee)}"
        
        if not has_profile(user_db, message.from_user.id):
            response += "\n\n👤 Заполните профиль: /profile"
        
        await message.answer(response, reply_markup=get_main_menu_keyboard())
        await state.clear()
        return
    
    # Отрицательный ответ - ждём корректировку
    if is_negative(user_text_lower) and not is_correction(user_text_lower):
        await message.answer(
            "✏️ Напишите правильные данные, например:\n"
            "• борщ 300г\n"
            "• кефир 200г\n"
            "• удали яйца"
        )
        return
    
    # Команда удаления
    if is_delete_command(user_text_lower):
        import re
        words_to_delete = re.findall(r'[\w]+', user_text.replace("удали", "").replace("убрать", "").replace("удалить", ""))
        if words_to_delete:
            to_delete = words_to_delete[0]
            new_products = []
            for p in original_products:
                if to_delete not in p.get("name", "").lower():
                    new_products.append(p)
            
            if len(new_products) == len(original_products):
                await message.answer(f"❌ Не найден продукт '{to_delete}' для удаления.")
                return
            
            total = {"calories": 0, "protein": 0, "fat": 0, "carbs": 0}
            lines = []
            for p in new_products:
                name = p.get("name", "")
                weight = p.get("weight_grams", 0)
                cal = p.get("calories", 0)
                prot = p.get("protein", 0)
                fat = p.get("fat", 0)
                carbs = p.get("carbs", 0)
                lines.append(f"🍽 {name} - {weight}г\n   🔥 {cal:.0f} ккал | Б: {prot:.1f} | Ж: {fat:.1f} | У: {carbs:.1f}")
                total["calories"] += cal
                total["protein"] += prot
                total["fat"] += fat
                total["carbs"] += carbs
            
            result_text = "✅ Обновлено:\n\n" + "\n\n".join(lines)
            result_text += f"\n\n📊 ИТОГО: {total['calories']:.0f} ккал | Б: {total['protein']:.1f}г | Ж: {total['fat']:.1f}г | У: {total['carbs']:.1f}г"
            result_text += "\n\nЗаписываю?"
            
            await state.update_data(original_products=new_products)
            await message.answer(result_text, reply_markup=get_confirm_keyboard())
        return
    
    # Корректировка - новый расчёт
    if is_correction(user_text_lower):
        waiting_msg = await message.answer("🔄 Пересчитываю...")
        await bot.send_chat_action(message.chat.id, "typing")
        
        result = await food_search.parse_and_calculate(user_text)
        await waiting_msg.delete()
        
        if not result["success"] or not result["data"].get("products"):
            await message.answer(
                "❌ Не удалось распознать корректировку. Напишите, например:\n"
                "• борщ 300г\n"
                "• кефир 200г"
            )
            return
        
        new_products = result["data"].get("products", [])
        total = result["data"].get("total", {})
        
        lines = []
        for p in new_products:
            name = p.get("name", "")
            weight = p.get("weight_grams", 0)
            cal = p.get("calories", 0)
            prot = p.get("protein", 0)
            fat = p.get("fat", 0)
            carbs = p.get("carbs", 0)
            lines.append(f"🍽 {name} - {weight}г\n   🔥 {cal:.0f} ккал | Б: {prot:.1f} | Ж: {fat:.1f} | У: {carbs:.1f}")
        
        result_text = "✅ Обновлено:\n\n" + "\n\n".join(lines)
        result_text += f"\n\n📊 ИТОГО: {total.get('calories', 0):.0f} ккал | Б: {total.get('protein', 0):.1f}г | Ж: {total.get('fat', 0):.1f}г | У: {total.get('carbs', 0):.1f}г"
        result_text += "\n\nЗаписываю?"
        
        await state.update_data(original_products=new_products)
        await message.answer(result_text, reply_markup=get_confirm_keyboard())
        return
    
    # Непонятный ввод
    await message.answer(
        "❓ Не понял. Напишите:\n"
        "• «да» — для сохранения\n"
        "• «нет» — для исправления\n"
        "• новые данные, например: борщ 300г\n"
        "• «удали X» — чтобы удалить продукт"
    )