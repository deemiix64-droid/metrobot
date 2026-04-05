import os, asyncio, json, datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import LabeledPrice, PreCheckoutQuery, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton

# --- КОНФИГУРАЦИЯ ---
TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = 8239542728  # <--- ВСТАВЬ СВОЙ ID СЮДА
APP_URL = "https://deemiix64-droid.github.io/metro/" 
MANAGER = "@timixXmetro"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Списки доступа
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

# --- БЛОК ВЛАДЕЛЬЦА (УПРАВЛЕНИЕ АДМИНАМИ) ---
@dp.message(Command("add_admin"))
async def add_admin(m: types.Message):
    if m.from_user.id == OWNER_ID:
        try:
            new_id = int(m.text.split()[1])
            admins.add(new_id)
            await m.answer(f"✅ ID `{new_id}` теперь администратор.", parse_mode="Markdown")
        except:
            await m.answer("❌ Формат: `/add_admin 123456`", parse_mode="Markdown")

@dp.message(Command("del_admin"))
async def del_admin(m: types.Message):
    if m.from_user.id == OWNER_ID:
        try:
            tid = int(m.text.split()[1])
            if tid in admins and tid != OWNER_ID:
                admins.remove(tid)
                await m.answer(f"✅ ID `{tid}` удален.", parse_mode="Markdown")
        except:
            await m.answer("❌ Формат: `/del_admin 123456`", parse_mode="Markdown")

# --- ОБЩИЕ КОМАНДЫ ---
@dp.message(Command("start"))
async def cmd_start(m: types.Message):
    users.add(m.from_user.id)
    await m.answer(f"Привет! Это **TIMIX METRO**.\nЖми кнопку ниже для покупок:", 
                   reply_markup=get_main_kb(), parse_mode="Markdown")
    
    if m.from_user.id in admins:
        status = "Владелец" if m.from_user.id == OWNER_ID else "Администратор"
        await m.answer(f"🔧 Вы вошли как **{status}**.\nКоманда для панели: /admin", parse_mode="Markdown")

@dp.message(Command("admin"))
async def cmd_admin(m: types.Message):
    if m.from_user.id in admins:
        await m.answer("🔧 **Панель управления:**", reply_markup=get_admin_kb(), parse_mode="Markdown")

# --- ЛОГИКА АДМИН-ПАНЕЛИ ---
@dp.callback_query(F.data == "adm_stats")
async def adm_stats(call: types.CallbackQuery):
    await call.message.answer(f"📊 Всего пользователей: `{len(users)}`", parse_mode="Markdown")
    await call.answer()

@dp.callback_query(F.data == "adm_list")
async def adm_list_view(call: types.CallbackQuery):
    txt = "📋 **Админы:**\n" + "\n".join([f"• `{a}`" for a in admins])
    await call.message.answer(txt, parse_mode="Markdown")
    await call.answer()

@dp.callback_query(F.data == "adm_bc")
async def adm_bc_start(call: types.CallbackQuery):
    await call.message.answer("📢 Напишите текст рассылки (любое сообщение без /):")
    await call.answer()

@dp.message(lambda m: m.from_user.id in admins and not m.text.startswith('/'))
async def process_broadcast(m: types.Message):
    count = 0
    for uid in users:
        try:
            await bot.send_message(uid, f"📢 **СООБЩЕНИЕ:**\n\n{m.text}", parse_mode="Markdown")
            count += 1
        except: pass
    await m.answer(f"✅ Отправлено `{count}` пользователям.")

# --- ОБРАБОТКА ЗАКАЗА (ВАЖНО!) ---
@dp.message(F.web_app_data)
async def web_app_handler(m: types.Message):
    try:
        data = json.loads(m.web_app_data.data)
        item = data.get("item")
        price = int(data.get("price"))
        
        order_id = f"{datetime.datetime.now().strftime('%M%S')}"

        await bot.send_invoice(
            m.chat.id,
            title=f"Заказ #{order_id}",
            description=f"🛒 {item}",
            payload=json.dumps({"id": order_id, "item": item, "price": price}),
            currency="XTR",
            prices=[LabeledPrice(label="Stars", amount=price)],
            provider_token=""
        )
    except Exception as e:
        print(f"Ошибка заказа: {e}")

@dp.pre_checkout_query()
async def pre_checkout(q: PreCheckoutQuery):
    await q.answer(ok=True)

@dp.message(F.successful_payment)
async def success_pay(m: types.Message):
    info = json.loads(m.successful_payment.invoice_payload)
    await m.answer(f"✅ **Оплачено!**\nЗаказ: `{info['id']}`\nСвязь: {MANAGER}", parse_mode="Markdown")
    
    for adm in admins:
        try:
            await bot.send_message(adm, f"💰 **НОВЫЙ ЧЕК!**\nТовар: {info['item']}\nСумма: {info['price']} ⭐\nОт: @{m.from_user.username}")
        except: pass

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
