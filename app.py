import os, asyncio, json, datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import LabeledPrice, PreCheckoutQuery, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton

# --- НАСТРОЙКИ ---
TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = 8239542728  # ВСТАВЬ СВОЙ ID (узнай в @userinfobot)
APP_URL = "https://deemiix64-droid.github.io/metro/" 
MANAGER = "@timixXmetro"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Список админов (Владелец всегда первый)
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

# --- КОМАНДЫ ВЛАДЕЛЬЦА ---
@dp.message(Command("add_admin"))
async def add_admin(m: types.Message):
    if m.from_user.id != OWNER_ID:
        return # Игнорируем, если пишет не владелец
    try:
        new_id = int(m.text.split()[1])
        admins.add(new_id)
        await m.answer(f"✅ ID `{new_id}` добавлен в список администраторов.", parse_mode="Markdown")
    except:
        await m.answer("❌ Формат: `/add_admin 12345678`", parse_mode="Markdown")

@dp.message(Command("del_admin"))
async def del_admin(m: types.Message):
    if m.from_user.id != OWNER_ID:
        return
    try:
        tid = int(m.text.split()[1])
        if tid == OWNER_ID:
            return await m.answer("❌ Нельзя удалить самого себя (Владельца).")
        if tid in admins:
            admins.remove(tid)
            await m.answer(f"✅ ID `{tid}` удален из списка администраторов.", parse_mode="Markdown")
        else:
            await m.answer("❌ Этот ID не является админом.")
    except:
        await m.answer("❌ Формат: `/del_admin 12345678`", parse_mode="Markdown")

# --- ОБЩИЕ КОМАНДЫ ---
@dp.message(Command("start"))
async def cmd_start(m: types.Message):
    users.add(m.from_user.id)
    await m.answer(f"Привет! Это магазин **TIMIX METRO**.\nЖми на кнопку ниже, чтобы выбрать товары:", 
                   reply_markup=get_main_kb(), parse_mode="Markdown")
    
    if m.from_user.id in admins:
        role = "Владелец" if m.from_user.id == OWNER_ID else "Администратор"
        await m.answer(f"🔧 **Вы вошли как {role}.**\nИспользуйте /admin для управления.", parse_mode="Markdown")

@dp.message(Command("admin"))
async def cmd_admin(m: types.Message):
    if m.from_user.id in admins:
        await m.answer("🔧 **Панель управления:**", reply_markup=get_admin_kb(), parse_mode="Markdown")

# --- ЛОГИКА АДМИНКИ ---
@dp.callback_query(F.data == "adm_stats")
async def adm_stats(call: types.CallbackQuery):
    await call.message.answer(f"📊 **Статистика:**\nВсего пользователей: `{len(users)}`", parse_mode="Markdown")
    await call.answer()

@dp.callback_query(F.data == "adm_list")
async def adm_list(call: types.CallbackQuery):
    txt = "📋 **Список всех админов:**\n\n" + "\n".join([f"• `{a}` {'(Владелец)' if a == OWNER_ID else ''}" for a in admins])
    await call.message.answer(txt, parse_mode="Markdown")
    await call.answer()

@dp.callback_query(F.data == "adm_bc")
async def adm_bc(call: types.CallbackQuery):
    await call.message.answer("✍️ **Введите текст рассылки:**\n(Следующее сообщение без '/' будет отправлено всем)", parse_mode="Markdown")
    await call.answer()

@dp.callback_query(F.data == "adm_close")
async def adm_close(call: types.CallbackQuery):
    await call.message.delete()

@dp.message(lambda m: m.from_user.id in admins and not m.text.startswith('/'))
async def run_broadcast(m: types.Message):
    count = 0
    for uid in users:
        try:
            await bot.send_message(uid, f"📢 **ОБЪЯВЛЕНИЕ ОТ TIMIX:**\n\n{m.text}", parse_mode="Markdown")
            count += 1
        except: pass
    await m.answer(f"✅ Рассылка завершена. Получили: `{count}` чел.", parse_mode="Markdown")

# --- ЛОГИКА ЗАКАЗА (ТО ЧТО НЕ РАБОТАЛО) ---
@dp.message(F.web_app_data)
async def handle_order(m: types.Message):
    try:
        # Парсим JSON из Mini App
        res = json.loads(m.web_app_data.data)
        item = res.get("item")
        price = int(res.get("price"))
        
        order_id = f"{datetime.datetime.now().strftime('%M%S')}-{m.from_user.id % 1000}"
        
        # Информация для чека (payload)
        info = {"id": order_id, "item": item, "price": price, "u": m.from_user.username or "нет"}

        await bot.send_invoice(
            m.chat.id,
            title=f"Заказ #{order_id}",
            description=f"🛒 {item}\n⭐ Цена: {price}",
            payload=json.dumps(info),
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
async def success_payment(m: types.Message):
    info = json.loads(m.successful_payment.invoice_payload)
    await m.answer(f"✅ **Оплата прошла!**\nЗаказ: `{info['id']}`\nНапишите {MANAGER}", parse_mode="Markdown")
    
    # Уведомление админам
    for adm in admins:
        try:
            await bot.send_message(adm, 
                f"💰 **НОВАЯ ПОКУПКА!**\n\nID: `{info['id']}`\nТовар: *{info['item']}*\nСумма: `{info['price']}` ⭐\nЮзер: @{info['u']}", 
                parse_mode="Markdown")
        except: pass

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
