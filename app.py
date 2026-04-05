import os
import asyncio
import json
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import LabeledPrice, PreCheckoutQuery, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

# --- НАСТРОЙКИ (Railway берет это из Variables) ---
TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = 8239542728  # ЗАМЕНИ НА СВОЙ ID (узнай в @userinfobot)
APP_URL = "https://deemiix64-droid.github.io/metro/" 
MANAGER = "@timixXmetro"

bot = Bot(token=TOKEN)
dp = Dispatcher()
users = set() # Список пользователей для рассылки

def main_kb(user_id):
    kb = [[InlineKeyboardButton(text="🛒 ОТКРЫТЬ МАГАЗИН", web_app=WebAppInfo(url=APP_URL))]]
    if user_id == OWNER_ID:
        kb.append([InlineKeyboardButton(text="⚙️ АДМИН-МЕНЮ", callback_data="adm_main")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

@dp.message(Command("start"))
async def start(m: types.Message):
    users.add(m.from_user.id)
    await m.answer(f"Привет, {m.from_user.first_name}! Это TIMIX METRO.\nВыбирай товары в Mini App ниже:", 
                   reply_markup=main_kb(m.from_user.id))

# --- АДМИН-ПАНЕЛЬ ---
@dp.callback_query(F.data == "adm_main")
async def adm_menu(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика", callback_data="adm_stats")],
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="adm_broadcast")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="adm_close")]
    ])
    await call.message.edit_text("🔧 Управление магазином", reply_markup=kb)

@dp.callback_query(F.data == "adm_stats")
async def adm_stats(call: types.CallbackQuery):
    await call.answer(f"Пользователей в базе: {len(users)}", show_alert=True)

@dp.callback_query(F.data == "adm_broadcast")
async def adm_bc(call: types.CallbackQuery):
    await call.message.answer("Напиши текст рассылки (он уйдет всем пользователям):")

@dp.message(F.text, lambda m: m.from_user.id == OWNER_ID and not m.text.startswith('/'))
async def run_bc(m: types.Message):
    count = 0
    for uid in users:
        try:
            await bot.send_message(uid, f"📢 **СООБЩЕНИЕ ОТ АДМИНА:**\n\n{m.text}", parse_mode="Markdown")
            count += 1
        except: pass
    await m.answer(f"✅ Рассылка завершена! Получили: {count}")

@dp.callback_query(F.data == "adm_close")
async def adm_close(call: types.CallbackQuery):
    await call.message.edit_text("Магазин работает.", reply_markup=main_kb(call.from_user.id))

# --- ОПЛАТА (STARS) ---
@dp.message(F.web_app_data)
async def buy_process(m: types.Message):
    data = json.loads(m.web_app_data.data)
    await bot.send_invoice(
        m.chat.id, title=data['item'], description=f"Оплата товара. Менеджер: {MANAGER}",
        payload="order", currency="XTR", 
        prices=[LabeledPrice(label="⭐ Stars", amount=int(data['price']))], 
        provider_token=""
    )

@dp.pre_checkout_query()
async def pre_pay(q: PreCheckoutQuery): await q.answer(ok=True)

@dp.message(F.successful_payment)
async def pay_ok(m: types.Message):
    await m.answer(f"✅ Оплачено! Напиши {MANAGER} для получения.")

async def main(): await dp.start_polling(bot)
if __name__ == "__main__": asyncio.run(main())
