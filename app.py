import os, asyncio, json, datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import LabeledPrice, PreCheckoutQuery, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = 8239542728  # ТВОЙ ID
APP_URL = "https://deemiix64-droid.github.io/metro/" 
MANAGER = "@timixXmetro"

bot = Bot(token=TOKEN)
dp = Dispatcher()
admins = {OWNER_ID}
users = set()

@dp.message(Command("start"))
async def cmd_start(m: types.Message):
    users.add(m.from_user.id)
    kb = [[KeyboardButton(text="🛒 ОТКРЫТЬ МАГАЗИН", web_app=WebAppInfo(url=APP_URL))]]
    await m.answer(f"Привет! Это **TIMIX METRO**.\nЖми на кнопку ниже, чтобы войти в магазин:", 
                   reply_markup=ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True),
                   parse_mode="Markdown")

@dp.message(Command("admin"))
async def cmd_admin(m: types.Message):
    if m.from_user.id in admins:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Рассылка", callback_data="adm_bc")],
            [InlineKeyboardButton(text="📊 Статистика", callback_data="adm_stats")]
        ])
        await m.answer("🔧 *Админ-панель:*", reply_markup=kb, parse_mode="Markdown")

@dp.message(F.web_app_data)
async def process_pay(m: types.Message):
    try:
        data = json.loads(m.web_app_data.data)
        order_id = f"{datetime.datetime.now().strftime('%M%S')}-{m.from_user.id % 1000}"
        now = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")

        payload = {
            "id": order_id, "item": data['item'], "price": data['price'],
            "user": m.from_user.full_name, "username": m.from_user.username or "none", "time": now
        }

        await bot.send_invoice(
            m.chat.id, 
            title=f"Заказ #{order_id}", 
            description=f"📦 Товар: {data['item']}\n📅 Дата: {now}",
            payload=json.dumps(payload), 
            currency="XTR", 
            prices=[LabeledPrice(label="⭐ Stars", amount=int(data['price']))], 
            provider_token="",
            payload_inline=True # Для стабильности в Mini Apps
        )
    except Exception as e:
        print(f"Error: {e}")

@dp.pre_checkout_query()
async def pre_pay(q: PreCheckoutQuery): await q.answer(ok=True)

@dp.message(F.successful_payment)
async def pay_ok(m: types.Message):
    info = json.loads(m.successful_payment.invoice_payload)
    
    await m.answer(
        f"✅ **Оплата принята!**\n\n"
        f"🆔 Заказ: `{info['id']}`\n"
        f"🛒 Товар: *{info['item']}*\n"
        f"👤 Менеджер: {MANAGER}", 
        parse_mode="Markdown"
    )

    for adm in admins:
        try:
            await bot.send_message(adm, 
                f"💰 **НОВЫЙ ЗАКАЗ**\n\n"
                f"🆔 ID: `{info['id']}`\n"
                f"🛒 Товар: *{info['item']}*\n"
                f"💵 Сумма: `{info['price']}` ⭐\n"
                f"👤 Покупатель: {info['user']} (@{info['username']})", 
                parse_mode="Markdown")
        except: pass

async def main(): await dp.start_polling(bot)
if __name__ == "__main__": asyncio.run(main())
