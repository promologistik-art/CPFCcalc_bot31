from aiogram import Router, types, Bot
from aiogram.filters import Command

from filters.admin_filter import IsAdminFilter
from keyboards.inline import get_admin_menu_keyboard

router = Router()
router.message.filter(IsAdminFilter())


@router.message(Command("ref"))
async def cmd_create_referral(message: types.Message, user_db, bot: Bot):
    parts = message.text.split()
    if len(parts) < 4:
        await message.answer(
            "🔗 Использование: /ref @username процент месяцы\n\n"
            "Пример: /ref @john 50 12\n"
            "Пример: /ref @jane 20 1"
        )
        return
    
    username = parts[1].lstrip('@')
    try:
        commission_percent = int(parts[2])
        bonus_months = int(parts[3])
    except ValueError:
        await message.answer("❌ Процент и месяцы должны быть числами")
        return
    
    if commission_percent < 0 or commission_percent > 100:
        await message.answer("❌ Процент должен быть от 0 до 100")
        return
    
    if bonus_months < 0:
        await message.answer("❌ Количество месяцев не может быть отрицательным")
        return
    
    code = user_db.generate_referral_link(username, commission_percent, bonus_months)
    bot_info = await bot.get_me()
    link = f"https://t.me/{bot_info.username}?start={code}"
    
    await message.answer(
        f"🔗 Реферальная ссылка создана для @{username}\n\n"
        f"🔗 Ссылка: {link}\n\n"
        f"📋 Условия:\n"
        f"• Комиссия: {commission_percent}% от оплат\n"
        f"• Бонус рефералу: {bonus_months} месяц(ев)\n\n"
        f"🎁 При переходе по ссылке новый пользователь получит +3 дня к тестовому периоду."
    )


@router.message(Command("ref_stats"))
async def cmd_ref_stats(message: types.Message, user_db):
    stats = user_db.get_referral_stats()
    
    if not stats:
        await message.answer("📊 Нет реферальных ссылок")
        return
    
    text = "📊 Статистика рефералов:\n\n"
    total_refs = 0
    total_paid = 0
    total_commission = 0
    
    for i, s in enumerate(stats, 1):
        username = f"@{s['username']}" if s['username'] else s['first_name']
        text += f"{i}. {username}\n"
        text += f"   💰 Комиссия: {s['commission_percent']}% | 🎁 Бонус: {s['bonus_months']} мес\n"
        text += f"   👥 Привёл: {s['total_refs']} (оплатили: {s['paid_refs']})\n"
        text += f"   💵 Сумма к выплате: {s['total_commission']:.0f} ₽\n\n"
        
        total_refs += s['total_refs']
        total_paid += s['paid_refs']
        total_commission += s['total_commission']
    
    text += "━" * 30 + "\n"
    text += f"👥 Всего приведено: {total_refs}\n"
    text += f"💰 Всего оплатили: {total_paid}\n"
    text += f"💵 Общая сумма к выплате: {total_commission:.0f} ₽"
    
    await message.answer(text)


@router.message(Command("ref_link_info"))
async def cmd_ref_link_info(message: types.Message, user_db, bot: Bot):
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("🔗 Использование: /ref_link_info код_ссылки")
        return
    
    code = parts[1]
    info = user_db.get_referral_link_info(code)
    
    if not info:
        await message.answer(f"❌ Ссылка с кодом {code} не найдена")
        return
    
    username = f"@{info['username']}" if info['username'] else info['first_name']
    bot_info = await bot.get_me()
    
    text = (
        f"🔗 Информация о реферальной ссылке\n\n"
        f"🔗 Ссылка: https://t.me/{bot_info.username}?start={code}\n"
        f"👤 Реферал: {username}\n"
        f"💰 Комиссия: {info['commission_percent']}%\n"
        f"🎁 Бонус рефералу: {info['bonus_months']} мес\n"
        f"📅 Создана: {info['created_at'][:10]}\n"
        f"📊 Статистика:\n"
        f"   👥 Переходов: {info['total_refs']}\n"
        f"   💰 Оплатили: {info['paid_refs']}"
    )
    
    await message.answer(text)