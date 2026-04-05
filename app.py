import os, asyncio, json
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import LabeledPrice, PreCheckoutQuery, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

# Берем токен из настроек Koyeb
TOKEN = os.getenv("BOT_TOKEN")
MANAGER = "@timixXmetro"
# ТВОЙ ID (для доступа к админке)
OWNER_ID = 8239542728 
# Ссылка, которую даст GitHub Pages
APP_URL = "https://deemiix64-droid.github.io/metro/"

bot = Bot(token=TOKEN)
dp = Dispatcher()
admins = set() # Временный список админов в памяти

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    kb = [[InlineKeyboardButton(text="🛒 МАГАЗИН", web_app=WebAppInfo(url=APP_URL))]]
    
    # Если пишет владелец или админ, добавляем кнопку управления
    if message.from_user.id == OWNER_ID or message.from_user.id in admins:
        kb.append([InlineKeyboardButton(text="⚙️ Админ-панель", callback_data="adm")])
        
    await message.answer(
        f"👋 Добро пожаловать в TIMIX!\n\nТвой ID: `{message.from_user.id}`",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "adm")
async def adm_panel(call: types.CallbackQuery):
    await call.message.answer("Чтобы добавить админа, просто перешли мне его ID (числа).")

@dp.message(lambda m: m.text.isdigit() and m.from_user.id == OWNER_ID)
async def add_admin(message: types.Message):
    admins.add(int(message.text))
    await message.answer(f"✅ Пользователь {message.text} теперь админ.")

# Обработка покупки из Mini App
@dp.message(F.web_app_data)
async def process_buy(message: types.Message):
    data = json.loads(message.web_app_data.data)
    await bot.send_invoice(
        chat_id=message.chat.id,
        title=data['item'],
        description=f"Оплата товара. Менеджер: {MANAGER}",
        payload=f"pay_{data['item']}",
        currency="XTR", # Telegram Stars
        prices=[LabeledPrice(label="Звезды", amount=int(data['price']))],
        provider_token=""
    )

@dp.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery):
    await query.answer(ok=True)

@dp.message(F.successful_payment)
async def success_pay(message: types.Message):
    await message.answer(
        f"✅ Оплата прошла!\n\nСделай скриншот и отправь менеджеру: {MANAGER}",
        parse_mode="Markdown"
    )

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
