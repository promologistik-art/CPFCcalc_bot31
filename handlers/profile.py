from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from states.states import ProfileState
from keyboards.inline import (
    get_gender_keyboard, 
    get_activity_keyboard, 
    get_profile_menu_keyboard,
    get_main_menu_keyboard
)
from config import ACTIVITY_LEVELS

router = Router()


@router.message(Command("profile"))
async def cmd_profile(message: types.Message, user_db):
    profile = user_db.get_profile(message.from_user.id)
    
    if profile:
        bmr = user_db.calculate_bmr(profile)
        tdee = user_db.calculate_tdee(profile)
        activity_name = ACTIVITY_LEVELS.get(profile["activity_level"], {"name": "Не указано"})["name"]
        gender_text = "Мужской" if profile["gender"] == "male" else "Женский"
        
        text = (
            f"👤 Ваш профиль\n\n"
            f"📝 Имя: {profile['name']}\n"
            f"⚖️ Вес: {profile['weight']} кг\n"
            f"📏 Рост: {profile['height']} см\n"
            f"🎂 Возраст: {profile['age']} лет\n"
            f"🚻 Пол: {gender_text}\n"
            f"🏃 Активность: {activity_name}\n\n"
            f"📊 Расчёты:\n"
            f"🔥 Базовый метаболизм (BMR): {bmr:.0f} ккал\n"
            f"⚡ Суточная норма (TDEE): {tdee:.0f} ккал"
        )
        
        await message.answer(text, reply_markup=get_profile_menu_keyboard())
    else:
        await message.answer(
            "👋 Давайте познакомимся!\n\nКак вас зовут?",
            reply_markup=types.ReplyKeyboardRemove()
        )
        await message.bot.state.set_state(ProfileState.waiting_for_name)


@router.message(Command("profile_edit"))
async def cmd_profile_edit(message: types.Message, state: FSMContext):
    await message.answer("📝 Как вас зовут?", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(ProfileState.waiting_for_name)


@router.callback_query(lambda c: c.data == "profile_view")
async def profile_view_callback(callback: types.CallbackQuery, user_db):
    await cmd_profile(callback.message, user_db)
    await callback.answer()


@router.callback_query(lambda c: c.data == "profile_edit")
async def profile_edit_callback(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("📝 Как вас зовут?")
    await state.set_state(ProfileState.waiting_for_name)
    await callback.answer()


@router.callback_query(lambda c: c.data == "profile_tdee")
async def profile_tdee_callback(callback: types.CallbackQuery, user_db):
    profile = user_db.get_profile(callback.from_user.id)
    if profile:
        tdee = user_db.calculate_tdee(profile)
        await callback.message.answer(
            f"⚡ Ваша суточная норма калорий: {tdee:.0f} ккал",
            reply_markup=get_main_menu_keyboard()
        )
    else:
        await callback.message.answer(
            "❌ Профиль не заполнен. Используйте /profile",
            reply_markup=get_main_menu_keyboard()
        )
    await callback.answer()


@router.message(ProfileState.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 2:
        await message.answer("❌ Имя слишком короткое. Введите нормальное имя:")
        return
    
    await state.update_data(name=name)
    await message.answer("🎂 Сколько вам лет? (напишите число)")
    await state.set_state(ProfileState.waiting_for_age)


@router.message(ProfileState.waiting_for_age)
async def process_age(message: types.Message, state: FSMContext):
    try:
        age = int(message.text.strip())
        if age < 10 or age > 100:
            await message.answer("❌ Возраст должен быть от 10 до 100 лет:")
            return
        
        await state.update_data(age=age)
        await message.answer("⚖️ Ваш вес? (в кг, например: 75)")
        await state.set_state(ProfileState.waiting_for_weight)
    except ValueError:
        await message.answer("❌ Пожалуйста, введите число (например: 30)")


@router.message(ProfileState.waiting_for_weight)
async def process_weight(message: types.Message, state: FSMContext):
    try:
        weight = float(message.text.strip().replace(',', '.'))
        if weight < 30 or weight > 250:
            await message.answer("❌ Вес должен быть от 30 до 250 кг:")
            return
        
        await state.update_data(weight=weight)
        await message.answer("📏 Ваш рост? (в см, например: 175)")
        await state.set_state(ProfileState.waiting_for_height)
    except ValueError:
        await message.answer("❌ Пожалуйста, введите число (например: 75.5)")


@router.message(ProfileState.waiting_for_height)
async def process_height(message: types.Message, state: FSMContext):
    try:
        height = float(message.text.strip().replace(',', '.'))
        if height < 120 or height > 230:
            await message.answer("❌ Рост должен быть от 120 до 230 см:")
            return
        
        await state.update_data(height=height)
        await message.answer("🚻 Ваш пол?", reply_markup=get_gender_keyboard())
        await state.set_state(ProfileState.waiting_for_gender)
    except ValueError:
        await message.answer("❌ Пожалуйста, введите число (например: 175)")


@router.callback_query(lambda c: c.data.startswith("gender_"), ProfileState.waiting_for_gender)
async def process_gender(callback: types.CallbackQuery, state: FSMContext):
    gender = "male" if callback.data == "gender_male" else "female"
    await state.update_data(gender=gender)
    await callback.message.edit_text(
        "🏃 Ваш уровень физической активности?",
        reply_markup=get_activity_keyboard()
    )
    await state.set_state(ProfileState.waiting_for_activity)
    await callback.answer()


@router.callback_query(lambda c: c.data == "back_to_gender", ProfileState.waiting_for_activity)
async def back_to_gender(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("🚻 Ваш пол?", reply_markup=get_gender_keyboard())
    await state.set_state(ProfileState.waiting_for_gender)
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("activity_"), ProfileState.waiting_for_activity)
async def process_activity(callback: types.CallbackQuery, state: FSMContext, user_db):
    activity_level = callback.data.replace("activity_", "")
    await state.update_data(activity_level=activity_level)
    
    data = await state.get_data()
    user_db.save_profile(callback.from_user.id, data)
    
    tdee = user_db.calculate_tdee(data)
    activity_name = ACTIVITY_LEVELS[activity_level]['name']
    
    text = (
        f"✅ Профиль сохранён!\n\n"
        f"👤 Имя: {data['name']}\n"
        f"🎂 Возраст: {data['age']} лет\n"
        f"⚖️ Вес: {data['weight']} кг\n"
        f"📏 Рост: {data['height']} см\n"
        f"🏃 Активность: {activity_name}\n\n"
        f"⚡ Ваша суточная норма калорий: {tdee:.0f} ккал\n\n"
        f"Теперь статистика будет показывать процент от нормы!"
    )
    
    await callback.message.edit_text(text, reply_markup=get_main_menu_keyboard())
    await state.clear()
    await callback.answer()