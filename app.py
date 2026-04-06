import os, asyncio, json, datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import LabeledPrice, PreCheckoutQuery, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton

# --- НАСТРОЙКИ ---
TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = 8239542728  # <--- ТВОЙ ID
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

# --- КОМАНДЫ ДЛЯ ВЛАДЕЛЬЦА (ТОЛЬКО ТЕБЕ) ---
@dp.message(Command("add_admin"))
async def add_admin(m: types.Message):
    if m.from_user.id == OWNER_ID:
        try:
            new_id = int(m.text.split()[1])
            admins.add(new_id)
            await m.answer(f"✅ ID `{new_id}` теперь администратор.", parse_mode="Markdown")
        except:
            await m.answer("❌ Напиши: `/add_admin 12345678`", parse_mode="Markdown")

@dp.message(Command("del_admin"))
async def del_admin(m: types.Message):
    if m.from_user.id == OWNER_ID:
        try:
            tid = int(m.text.split()[1])
            if tid in admins and tid != OWNER_ID:
                admins.remove(tid)
                await m.answer(f"✅ ID `{tid}` удален из админов.", parse_mode="Markdown")
        except:
            await m.answer("❌ Напиши: `/del_admin 12345678`", parse_mode="Markdown")

# --- ОБЩИЕ КОМАНДЫ ---
@dp.message(Command("start"))
async def cmd_start(m: types.Message):
    users.add(m.from_user.id)
    await m.answer(f"Привет! Это **TIMIX METRO**.\nВыбирай товары в корзину и оплачивай в один клик!", 
                   reply_markup=get_main_kb(), parse_mode="Markdown")
    
    if m.from_user.id in admins:
        role = "Владелец" if m.from_user.id == OWNER_ID else "Администратор"
        await m.answer(f"🔧 **Вы вошли как {role}.**\nПанель управления: /admin", parse_mode="Markdown")

@dp.message(Command("admin"))
async def cmd_admin(m: types.Message):
    if m.from_user.id in admins:
        await m.answer("🔧 **Админ-панель:**", reply_markup=get_admin_kb(), parse_mode="Markdown")

# --- ЛОГИКА АДМИНКИ (КНОПКИ) ---
@dp.callback_query(F.data == "adm_stats")
async def adm_stats(call: types.CallbackQuery):
    await call.message.answer(f"📊 **Всего уникальных юзеров:** `{len(users)}`", parse_mode="Markdown")
    await call.answer()

@dp.callback_query(F.data == "adm_list")
async def adm_list_view(call: types.CallbackQuery):
    txt = "📋 **Администраторы:**\n" + "\n".join([f"• `{a}` {'(Владелец)' if a == OWNER_ID else ''}" for a in admins])
    await call.message.answer(txt, parse_mode="Markdown")
    await call.answer()

@dp.callback_query(F.data == "adm_bc")
async def adm_bc_start(call: types.CallbackQuery):
    await call.message.answer("📢 **Введите текст рассылки:**\n(Любое следующее сообщение без / отправится всем)", parse_mode="Markdown")
    await call.answer()

@dp.callback_query(F.data == "adm_close")
async def adm_close(call: types.CallbackQuery):
    await call.message.delete()

# Сама рассылка
@dp.message(lambda m: m.from_user.id in admins and not m.text.startswith('/'))
async def run_broadcast(m: types.Message):
    count = 0
    for uid in users:
        try:
            await bot.send_message(uid, f"📢 **ОБЪЯВЛЕНИЕ ОТ TIMIX:**\n\n{m.text}", parse_mode="Markdown")
            count += 1
        except: pass
    await m.answer(f"✅ Рассылка завершена. Получили: `{count}` чел.", parse_mode="Markdown")

# --- ОБРАБОТКА ЗАКАЗА ИЗ КОРЗИНЫ ---
@dp.message(F.web_app_data)
async def handle_cart_order(m: types.Message):
    try:
        data = json.loads(m.web_app_data.data)
        items_list = data.get("items") # Строка товаров
        total_price = int(data.get("total")) # Общая сумма
        
        order_id = datetime.datetime.now().strftime("%M%S")
        info = {"id": order_id, "items": items_list, "total": total_price, "user": m.from_user.username or "нет"}

        await bot.send_invoice(
            m.chat.id,
            title=f"Заказ #{order_id}",
            description=f"🛒 Товары: {items_list}",
            payload=json.dumps(info),
            currency="XTR",
            prices=[LabeledPrice(label="К оплате", amount=total_price)],
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
    await m.answer(f"✅ **Оплата прошла успешно!**\nЗаказ: `{info['id']}`\nДля получения напишите менеджеру: {MANAGER}", parse_mode="Markdown")
    
    # Отчет админам
    for adm in admins:
        try:
            await bot.send_message(adm, 
                f"💰 **НОВАЯ ОПЛАТА!**\n\n🆔 Заказ: `{info['id']}`\n🛒 Состав: {info['items']}\n💵 Сумма: {info['total']} ⭐\n👤 Покупатель: @{info['user']}", 
                parse_mode="Markdown")
        except: pass

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
