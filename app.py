import os, asyncio, json
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import LabeledPrice, PreCheckoutQuery, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton

# --- НАСТРОЙКИ ---
TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = 8239542728  # ВСТАВЬ СВОЙ ID СЮДА
APP_URL = "https://deemiix64-droid.github.io/metro/" 
MANAGER = "@timixXmetro"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# База данных в памяти
admins = {OWNER_ID}
users = set()

# --- КЛАВИАТУРЫ ---
def get_main_kb():
    kb = [[KeyboardButton(text="🛒 ОТКРЫТЬ МАГАЗИН", web_app=WebAppInfo(url=APP_URL))]]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_admin_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="adm_bc")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="adm_stats")],
        [InlineKeyboardButton(text="👥 Список админов", callback_data="adm_list")],
        [InlineKeyboardButton(text="❌ Закрыть", callback_data="adm_close")]
    ])

# --- ОСНОВНЫЕ КОМАНДЫ ---
@dp.message(Command("start"))
async def cmd_start(m: types.Message):
    users.add(m.from_user.id)
    await m.answer(f"Привет! Это магазин **TIMIX METRO**.\nЖми кнопку ниже, чтобы войти.", 
                   reply_markup=get_main_kb())
    if m.from_user.id in admins:
        await m.answer("🔧 Вы вошли как администратор. Используйте /admin")

@dp.message(Command("admin"))
async def cmd_admin(m: types.Message):
    if m.from_user.id in admins:
        await m.answer("🔧 Панель управления магазином:", reply_markup=get_admin_kb())

# --- УПРАВЛЕНИЕ АДМИНАМИ ---
@dp.message(Command("add_admin"))
async def add_admin(m: types.Message):
    if m.from_user.id == OWNER_ID:
        try:
            new_id = int(m.text.split()[1])
            admins.add(new_id)
            await m.answer(f"✅ ID {new_id} теперь админ!")
        except:
            await m.answer("❌ Формат: `/add_admin 12345678`", parse_mode="Markdown")

@dp.message(Command("del_admin"))
async def del_admin(m: types.Message):
    if m.from_user.id == OWNER_ID:
        try:
            target_id = int(m.text.split()[1])
            if target_id == OWNER_ID:
                return await m.answer("❌ Нельзя удалить владельца!")
            if target_id in admins:
                admins.remove(target_id)
                await m.answer(f"✅ ID {target_id} удален из админов.")
            else:
                await m.answer("❌ Этот ID не является админом.")
        except:
            await m.answer("❌ Формат: `/del_admin 12345678`", parse_mode="Markdown")

# --- ЛОГИКА ПАНЕЛИ ---
@dp.callback_query(F.data == "adm_stats")
async def adm_stats(call: types.CallbackQuery):
    await call.answer(f"Всего пользователей: {len(users)}", show_alert=True)

@dp.callback_query(F.data == "adm_list")
async def adm_list(call: types.CallbackQuery):
    list_txt = "📋 **Список админов:**\n\n" + "\n".join([f"• `{a}`" for a in admins])
    await call.message.answer(list_txt, parse_mode="Markdown")
    await call.answer()

@dp.callback_query(F.data == "adm_bc")
async def adm_bc(call: types.CallbackQuery):
    await call.message.answer("✍️ Отправь текст для рассылки всем пользователям:")
    await call.answer()

@dp.callback_query(F.data == "adm_close")
async def adm_close(call: types.CallbackQuery):
    await call.message.delete()

@dp.message(F.text, lambda m: m.from_user.id in admins and not m.text.startswith('/'))
async def run_broadcast(m: types.Message):
    count = 0
    for uid in users:
        try:
            await bot.send_message(uid, f"📢 **ОБЪЯВЛЕНИЕ:**\n\n{m.text}")
            count += 1
        except: pass
    await m.answer(f"✅ Рассылка завершена!\nПолучили: {count} человек.")

# --- ОПЛАТА ---
@dp.message(F.web_app_data)
async def process_pay(m: types.Message):
    data = json.loads(m.web_app_data.data)
    await bot.send_invoice(
        m.chat.id, title=data['item'], 
        description=f"Оплата товара. Менеджер: {MANAGER}",
        payload="order", currency="XTR", 
        prices=[LabeledPrice(label="⭐ Stars", amount=int(data['price']))], 
        provider_token=""
    )

@dp.pre_checkout_query()
async def pre_pay(q: PreCheckoutQuery): await q.answer(ok=True)

@dp.message(F.successful_payment)
async def pay_ok(m: types.Message):
    await m.answer(f"✅ Оплата принята! Напиши менеджеру {MANAGER}")

async def main(): await dp.start_polling(bot)
if __name__ == "__main__": asyncio.run(main())
