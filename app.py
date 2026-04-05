import os, asyncio, json, datetime
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

# Списки (в оперативной памяти)
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

# --- ОБРАБОТЧИКИ ---

@dp.message(Command("start"))
async def cmd_start(m: types.Message):
    users.add(m.from_user.id) # Сохраняем для рассылки
    
    text = f"Привет! Это магазин **TIMIX METRO**.\nЖми на кнопку ниже, чтобы войти."
    await m.answer(text, reply_markup=get_main_kb(), parse_mode="Markdown")
    
    # Оповещение для админа
    if m.from_user.id in admins:
        await m.answer("🔧 **Вы зашли как администратор.**\nДоступны команды: /admin, /add_admin, /del_admin", parse_mode="Markdown")

@dp.message(Command("admin"))
async def cmd_admin(m: types.Message):
    if m.from_user.id in admins:
        await m.answer("🔧 **Панель управления:**", reply_markup=get_admin_kb(), parse_mode="Markdown")

@dp.message(Command("admin_list"))
async def cmd_admin_list(m: types.Message):
    if m.from_user.id in admins:
        txt = "📋 **Список администраторов:**\n\n" + "\n".join([f"• `{a}`" for a in admins])
        await m.answer(txt, parse_mode="Markdown")

# Управление админами
@dp.message(Command("add_admin"))
async def add_admin(m: types.Message):
    if m.from_user.id == OWNER_ID:
        try:
            new_id = int(m.text.split()[1])
            admins.add(new_id)
            await m.answer(f"✅ ID `{new_id}` добавлен в админы.", parse_mode="Markdown")
        except:
            await m.answer("❌ Ошибка. Напиши: `/add_admin 123456`", parse_mode="Markdown")

@dp.message(Command("del_admin"))
async def del_admin(m: types.Message):
    if m.from_user.id == OWNER_ID:
        try:
            tid = int(m.text.split()[1])
            if tid in admins and tid != OWNER_ID:
                admins.remove(tid)
                await m.answer(f"✅ ID `{tid}` удален.", parse_mode="Markdown")
        except:
            await m.answer("❌ Ошибка. Напиши: `/del_admin 123456`", parse_mode="Markdown")

# Коллбэки админки
@dp.callback_query(F.data == "adm_stats")
async def adm_stats(call: types.CallbackQuery):
    await call.message.answer(f"📊 **Статистика:**\nВсего пользователей: `{len(users)}`", parse_mode="Markdown")
    await call.answer()

@dp.callback_query(F.data == "adm_list")
async def adm_list_call(call: types.CallbackQuery):
    txt = "📋 **Список админов:**\n\n" + "\n".join([f"• `{a}`" for a in admins])
    await call.message.answer(txt, parse_mode="Markdown")
    await call.answer()

@dp.callback_query(F.data == "adm_bc")
async def adm_bc(call: types.CallbackQuery):
    await call.message.answer("✍️ **Введите текст рассылки:**\n(Следующее ваше текстовое сообщение будет отправлено всем)", parse_mode="Markdown")
    await call.answer()

@dp.callback_query(F.data == "adm_close")
async def adm_close(call: types.CallbackQuery):
    await call.message.delete()

# Рассылка (ловит любое текстовое сообщение от админа, которое не команда)
@dp.message(lambda m: m.from_user.id in admins and not m.text.startswith('/'))
async def process_broadcast(m: types.Message):
    count = 0
    for uid in users:
        try:
            await bot.send_message(uid, f"📢 **СООБЩЕНИЕ ОТ TIMIX:**\n\n{m.text}", parse_mode="Markdown")
            count += 1
        except: pass
    await m.answer(f"✅ Рассылка завершена. Получили: `{count}` чел.", parse_mode="Markdown")

# --- ЛОГИКА ПОКУПКИ ---
@dp.message(F.content_type == "web_app_data") # КОРРЕКТНЫЙ ФИЛЬТР
async def web_app_data_handler(m: types.Message):
    try:
        res = json.loads(m.web_app_data.data)
        item = res.get("item")
        price = int(res.get("price"))
        
        order_id = f"{datetime.datetime.now().strftime('%M%S')}-{m.from_user.id % 1000}"
        
        invoice_data = {
            "id": order_id, "item": item, "price": price,
            "user": m.from_user.full_name, "username": m.from_user.username or "нет"
        }

        await bot.send_invoice(
            m.chat.id, 
            title=f"Заказ #{order_id}", 
            description=f"🛒 {item}\n⭐ К оплате: {price}",
            payload=json.dumps(invoice_data), 
            currency="XTR", 
            prices=[LabeledPrice(label="Stars", amount=price)], 
            provider_token=""
        )
    except Exception as e:
        print(f"Error in web_app: {e}")

@dp.pre_checkout_query()
async def checkout_handler(q: PreCheckoutQuery):
    await q.answer(ok=True)

@dp.message(F.successful_payment)
async def success_pay(m: types.Message):
    info = json.loads(m.successful_payment.invoice_payload)
    
    await m.answer(f"✅ **Оплата прошла!**\n\nЗаказ: `{info['id']}`\nНапишите {MANAGER}", parse_mode="Markdown")
    
    # Уведомление админам
    for adm in admins:
        try:
            await bot.send_message(adm, 
                f"💰 **НОВАЯ ПОКУПКА!**\n\nID: `{info['id']}`\nТовар: *{info['item']}*\nСумма: `{info['price']}` ⭐\nЮзер: {info['user']} (@{info['username']})", 
                parse_mode="Markdown")
        except: pass

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
