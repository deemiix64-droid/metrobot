import os, asyncio, json
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import LabeledPrice, PreCheckoutQuery, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo

TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = 8239542728  # ВСТАВЬ СВОЙ ID
APP_URL = "https://deemiix64-droid.github.io/metro/"
MANAGER = "@timixXmetro"

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(m: types.Message):
    # Используем ReplyKeyboardMarkup, чтобы работала кнопка 'Купить'
    kb = [
        [KeyboardButton(text="🛒 ОТКРЫТЬ МАГАЗИН", web_app=WebAppInfo(url=APP_URL))]
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    
    await m.answer(f"Привет! Магазин TIMIX готов.\nНажми кнопку ниже, чтобы открыть товары:", 
                   reply_markup=keyboard)

# Этот блок ловит нажатие кнопки "КУПИТЬ" в Mini App
@dp.message(F.web_app_data)
async def process_buy(m: types.Message):
    try:
        data = json.loads(m.web_app_data.data)
        item_name = data.get("item")
        item_price = int(data.get("price"))

        await bot.send_invoice(
            m.chat.id,
            title=f"Оплата: {item_name}",
            description=f"После оплаты напиши {MANAGER}",
            payload="metro_order",
            currency="XTR",
            prices=[LabeledPrice(label="⭐ Stars", amount=item_price)],
            provider_token=""
        )
    except Exception as e:
        print(f"Ошибка данных: {e}")

@dp.pre_checkout_query()
async def pre_pay(q: PreCheckoutQuery):
    await q.answer(ok=True)

@dp.message(F.successful_payment)
async def pay_ok(m: types.Message):
    await m.answer(f"✅ Оплата прошла! Напиши менеджеру {MANAGER} для получения товара.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
