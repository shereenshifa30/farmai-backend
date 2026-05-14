from fastapi import APIRouter
import requests
import os
from dotenv import load_dotenv

load_dotenv()
router = APIRouter()

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

@router.get("/{city}")
def get_weather(city: str):
    try:
        # ── Current + 5 day forecast ──
        url = "https://api.weatherapi.com/v1/forecast.json"
        params = {
            "key": WEATHER_API_KEY,
            "q": city,
            "days": 5,
            "aqi": "no",
            "alerts": "no"
        }
        response = requests.get(url, params=params)
        data = response.json()

        if "error" in data:
            return {"error": data["error"]["message"]}

        # ── Current weather ──
        current = {
            "city":      data["location"]["name"],
            "region":    data["location"]["region"],
            "country":   data["location"]["country"],
            "temp_c":    data["current"]["temp_c"],
            "feels_like":data["current"]["feelslike_c"],
            "humidity":  data["current"]["humidity"],
            "wind_kph":  data["current"]["wind_kph"],
            "condition": data["current"]["condition"]["text"],
            "icon":      data["current"]["condition"]["icon"],
            "uv":        data["current"]["uv"],
        }

        # ── 5 day forecast ──
        forecast = []
        for day in data["forecast"]["forecastday"]:
            forecast.append({
                "date":      day["date"],
                "max_temp":  day["day"]["maxtemp_c"],
                "min_temp":  day["day"]["mintemp_c"],
                "condition": day["day"]["condition"]["text"],
                "icon":      day["day"]["condition"]["icon"],
                "humidity":  day["day"]["avghumidity"],
                "rain_chance": day["day"]["daily_chance_of_rain"],
            })

        # ── Farming advice based on weather ──
        advice = get_farming_advice(current)

        return {
            "current":  current,
            "forecast": forecast,
            "advice":   advice
        }

    except Exception as e:
        return {"error": str(e)}


def get_farming_advice(current):
    advice = []
    temp = current["temp_c"]
    humidity = current["humidity"]
    condition = current["condition"].lower()

    if "rain" in condition:
        advice.append("🌧️ Rain expected — avoid irrigation today")
        advice.append("⚠️ Check drainage in your fields")
    if temp > 38:
        advice.append("🌡️ Very hot — water crops early morning or evening")
    if temp < 15:
        advice.append("❄️ Cool weather — protect sensitive crops from cold")
    if humidity > 80:
        advice.append("💧 High humidity — watch for fungal diseases")
    if humidity < 30:
        advice.append("🏜️ Low humidity — increase irrigation frequency")
    if not advice:
        advice.append("✅ Weather looks good for farming today!")

    return advice