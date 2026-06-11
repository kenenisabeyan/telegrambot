from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

router = Router()

@router.message(Command("weather"))
async def cmd_weather(message: Message):
    args = message.text.split(maxsplit=1)
    
    if len(args) < 2:
        await message.answer(
            "🌤 Weather Forecast\n\n"
            "Usage: /weather [city name]\n"
            "Example: /weather London\n\n"
            "Real-time weather coming soon with OpenWeatherMap API!"
        )
        return
    
    city = args[1]
    await message.answer(f"🌍 Weather for {city}\n\n🌡 Temperature: 22°C\n💧 Humidity: 65%\n🌬 Wind: 12 km/h\n\n✨ Live weather data will be available after API configuration!")