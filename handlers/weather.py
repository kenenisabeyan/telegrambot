from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import aiohttp
from datetime import datetime
from os import getenv

router = Router()

WEATHER_API_KEY = getenv("OPENWEATHER_API_KEY")
WEATHER_URL = "http://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "http://api.openweathermap.org/data/2.5/forecast"

class WeatherStates(StatesGroup):
    waiting_for_city = State()

async def get_weather_data(city: str) -> dict | None:
    """Fetch current weather data"""
    if not WEATHER_API_KEY:
        return get_mock_weather(city)
    
    params = {
        "q": city,
        "appid": WEATHER_API_KEY,
        "units": "metric",
        "lang": "en"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(WEATHER_URL, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {
                        "city": data["name"],
                        "country": data["sys"]["country"],
                        "temp": data["main"]["temp"],
                        "feels_like": data["main"]["feels_like"],
                        "humidity": data["main"]["humidity"],
                        "pressure": data["main"]["pressure"],
                        "wind_speed": data["wind"]["speed"],
                        "wind_deg": data["wind"].get("deg", 0),
                        "description": data["weather"][0]["description"],
                        "icon": data["weather"][0]["icon"],
                        "clouds": data["clouds"]["all"],
                        "sunrise": data["sys"]["sunrise"],
                        "sunset": data["sys"]["sunset"],
                        "visibility": data.get("visibility", 0)
                    }
                else:
                    return None
    except Exception:
        return None

async def get_forecast_data(city: str) -> list | None:
    """Get 5-day weather forecast"""
    if not WEATHER_API_KEY:
        return get_mock_forecast(city)
    
    params = {
        "q": city,
        "appid": WEATHER_API_KEY,
        "units": "metric",
        "lang": "en",
        "cnt": 40  # 5 days * 8 intervals (3 hours each)
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(FORECAST_URL, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    forecasts = []
                    
                    # Group by day
                    daily_forecasts = {}
                    for item in data["list"]:
                        date = datetime.fromtimestamp(item["dt"]).strftime("%Y-%m-%d")
                        if date not in daily_forecasts:
                            daily_forecasts[date] = []
                        daily_forecasts[date].append({
                            "time": datetime.fromtimestamp(item["dt"]).strftime("%H:%M"),
                            "temp": item["main"]["temp"],
                            "description": item["weather"][0]["description"],
                            "icon": item["weather"][0]["icon"]
                        })
                    
                    # Get daily summary
                    for date, items in list(daily_forecasts.items())[:5]:
                        avg_temp = sum(i["temp"] for i in items) / len(items)
                        max_temp = max(i["temp"] for i in items)
                        min_temp = min(i["temp"] for i in items)
                        forecasts.append({
                            "date": date,
                            "avg_temp": avg_temp,
                            "max_temp": max_temp,
                            "min_temp": min_temp,
                            "description": items[0]["description"],
                            "icon": items[0]["icon"]
                        })
                    
                    return forecasts
                else:
                    return None
    except Exception:
        return None

def get_mock_weather(city: str) -> dict:
    """Mock weather data for testing"""
    return {
        "city": city.capitalize(),
        "country": "US",
        "temp": 22.5,
        "feels_like": 21.0,
        "humidity": 65,
        "pressure": 1013,
        "wind_speed": 12,
        "wind_deg": 180,
        "description": "clear sky",
        "icon": "01d",
        "clouds": 0,
        "visibility": 10000
    }

def get_mock_forecast(city: str) -> list:
    """Mock forecast data"""
    forecasts = []
    for i in range(5):
        forecasts.append({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "avg_temp": 22,
            "max_temp": 25,
            "min_temp": 18,
            "description": "partly cloudy",
            "icon": "02d"
        })
    return forecasts

def get_wind_direction(degrees: int) -> str:
    """Convert wind degrees to cardinal direction"""
    directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    index = round(degrees / 45) % 8
    return directions[index]

@router.message(Command("weather"))
@router.message(F.text == "Weather")
async def cmd_weather(message: Message, state: FSMContext, db=None):
    """Handle /weather command"""
    if db:
        await db.log_command(message.from_user.id, "weather")
    args = message.text.split(maxsplit=1)
    
    if len(args) < 2:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📍 Send Location", callback_data="weather_location")],
                [InlineKeyboardButton(text="📅 5-Day Forecast", callback_data="weather_forecast")],
                [InlineKeyboardButton(text="❓ Help", callback_data="weather_help")]
            ]
        )
        
        await message.answer(
            "<b>🌤 Weather Service</b>\n\n"
            "Send <code>/weather [city name]</code> to get weather!\n\n"
            "<b>Examples:</b>\n"
            "• <code>/weather London</code>\n"
            "• <code>/weather New York</code>\n"
            "• <code>/weather Tokyo</code>\n\n"
            "<b>Features:</b>\n"
            "• Current conditions\n"
            "• 5-day forecast\n"
            "• Real-time data\n"
            "• Location-based weather\n\n"
            f"<i>OpenWeatherMap API: {'✅ Active' if WEATHER_API_KEY else '❌ Inactive (mock mode)'}</i>",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await state.set_state(WeatherStates.waiting_for_city)
        return
    
    city = args[1]
    await get_and_send_weather(message, city)

async def get_and_send_weather(message: Message, city: str):
    """Get weather data and send to user"""
    await message.bot.send_chat_action(message.chat.id, "typing")
    
    weather = await get_weather_data(city)
    
    if not weather:
        await message.answer(
            f"❌ Could not find weather for '{city}'.\n\n"
            "Please check the city name and try again.\n"
            "Example: /weather London"
        )
        return
    
    # Create weather icon
    temp_icon = "🔥" if weather["temp"] > 30 else "☀️" if weather["temp"] > 20 else "🌤" if weather["temp"] > 10 else "❄️"
    
    weather_text = (
        f"<b>{temp_icon} Weather in {weather['city']}, {weather['country']}</b>\n\n"
        f"<b>🌡 Temperature:</b> {weather['temp']:.1f}°C (feels like {weather['feels_like']:.1f}°C)\n"
        f"<b>☁️ Conditions:</b> {weather['description'].capitalize()}\n"
        f"<b>💧 Humidity:</b> {weather['humidity']}%\n"
        f"<b>🌀 Wind:</b> {weather['wind_speed']} m/s {get_wind_direction(weather['wind_deg'])}\n"
        f"<b>📊 Pressure:</b> {weather['pressure']} hPa\n"
        f"<b>☁️ Clouds:</b> {weather['clouds']}%\n"
    )
    
    if weather.get("visibility"):
        weather_text += f"<b>👁 Visibility:</b> {weather['visibility']/1000:.1f} km\n"
    
    # Add sunrise/sunset if available
    if weather.get("sunrise"):
        sunrise = datetime.fromtimestamp(weather["sunrise"]).strftime("%H:%M")
        sunset = datetime.fromtimestamp(weather["sunset"]).strftime("%H:%M")
        weather_text += f"\n<b>🌅 Sunrise:</b> {sunrise}\n<b>🌇 Sunset:</b> {sunset}\n"
    
    weather_text += f"\n<i>Last updated: {datetime.now().strftime('%H:%M:%S')}</i>"
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📅 5-Day Forecast", callback_data=f"weather_forecast_{city}")],
            [InlineKeyboardButton(text="🔄 Refresh", callback_data=f"weather_refresh_{city}")]
        ]
    )
    
    await message.answer(weather_text, reply_markup=keyboard, parse_mode="HTML")

@router.callback_query(F.data.startswith("weather_forecast"))
async def show_forecast(callback: CallbackQuery):
    """Show 5-day forecast"""
    parts = callback.data.split("_")
    city = parts[2] if len(parts) > 2 else None
    
    if not city:
        await callback.answer("Please provide a city name first!")
        return
    
    await callback.answer("Fetching forecast...")
    await callback.bot.send_chat_action(callback.message.chat.id, "typing")
    
    forecasts = await get_forecast_data(city)
    
    if not forecasts:
        await callback.message.answer(f"❌ Could not get forecast for {city}")
        return
    
    forecast_text = f"<b>📅 5-Day Forecast for {city}</b>\n\n"
    
    for forecast in forecasts:
        date_obj = datetime.strptime(forecast['date'], "%Y-%m-%d")
        day_name = date_obj.strftime("%A")
        
        forecast_text += (
            f"<b>{day_name}</b> ({forecast['date']})\n"
            f"🌡 {forecast['avg_temp']:.0f}°C (↑{forecast['max_temp']:.0f}° ↓{forecast['min_temp']:.0f}°)\n"
            f"☁️ {forecast['description'].capitalize()}\n\n"
        )
    
    await callback.message.answer(forecast_text, parse_mode="HTML")

@router.callback_query(F.data.startswith("weather_refresh_"))
async def refresh_weather(callback: CallbackQuery):
    """Refresh weather data"""
    city = callback.data.split("_")[2]
    await get_and_send_weather(callback.message, city)
    await callback.answer("Weather updated!")

@router.callback_query(F.data == "weather_location")
async def request_location(callback: CallbackQuery):
    """Request user location"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📍 Send Location", callback_data="weather_send_location")]
        ]
    )
    await callback.message.answer(
        "📍 To get weather for your location, please send your location.\n\n"
        "Use the button below or the attachment menu to share your location.",
        reply_markup=keyboard
    )
    await callback.answer()

@router.message(F.location)
async def handle_location(message: Message, db=None):
    """Handle location message"""
    if db:
        await db.log_command(message.from_user.id, "weather")
    lat = message.location.latitude
    lon = message.location.longitude
    
    # Reverse geocode to get city name (simplified)
    await message.answer(
        f"📍 Location received!\n"
        f"Latitude: {lat}\n"
        f"Longitude: {lon}\n\n"
        "Please use /weather [city name] instead for now.\n"
        "Location-based weather coming soon!"
    )

@router.message(WeatherStates.waiting_for_city)
async def handle_city_input(message: Message, state: FSMContext, db=None):
    """Handle city name input"""
    if db:
        await db.log_command(message.from_user.id, "weather")
    await get_and_send_weather(message, message.text)
    await state.clear()

@router.callback_query(F.data == "weather_help")
async def weather_help(callback: CallbackQuery):
    """Show weather help"""
    help_text = (
        "<b>🌤 Weather Help</b>\n\n"
        "<b>Commands:</b>\n"
        "• /weather [city] - Current weather\n"
        "• /forecast [city] - 5-day forecast\n\n"
        "<b>Examples:</b>\n"
        "• /weather London\n"
        "• /weather New York,US\n"
        "• /weather Tokyo,JP\n\n"
        "<b>Features:</b>\n"
        "• Real-time temperature\n"
        "• Humidity & pressure\n"
        "• Wind speed & direction\n"
        "• 5-day forecast\n"
        "• Sunrise/sunset times\n\n"
        "<b>Note:</b>\n"
        "Data provided by OpenWeatherMap.\n"
        "Update frequency: Every 10 minutes."
    )
    await callback.message.answer(help_text, parse_mode="HTML")
    await callback.answer()