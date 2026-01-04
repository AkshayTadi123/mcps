from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
import os
import httpx

load_dotenv()
API_KEY = os.getenv("API_KEY")

# Create an MCP server
mcp = FastMCP("Weather Service - OpenWeatherMap API")

# Tool implementation
@mcp.tool()
async def get_current_weather(city: str, units: str) -> str:
    """Get the current weather for a specified city."""

    url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": API_KEY,
        "units": units
    }

    unit_symbol = "°F" if units == "imperial" else "°C"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        
        if response.status_code != 200:
            return f"Error: Could not find weather for '{city}'. (Status: {response.status_code})"
        
        data = response.json()
        temp = data['main']['temp']
        desc = data['weather'][0]['description']
        humidity = data['main']['humidity']
        wind_speed = data['wind']['speed']
        wind_direction = data['wind']['deg']

        return f"The current weather in {city} is {desc} with a temperature of {temp}{unit_symbol} and humidity of {humidity}%. The wind speed is {wind_speed} m/s at {wind_direction}°."



@mcp.tool()
async def get_5_day_forecast(city: str, units: str):
    """Get the 5-day weather forecast for a specified city."""
    url = "http://api.openweathermap.org/data/2.5/forecast"
    params = {
        "q": city,
        "appid": API_KEY,
        "units": units
    }
    
    unit_symbol = "°F" if units == "imperial" else "°C"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        
        if response.status_code != 200:
            return f"Error: Could not fetch forecast for {city}."
        
        data = response.json()
        forecast_list = data['list']
    
        daily_summaries = []
        for i in range(0, len(forecast_list), 8):
            day_data = forecast_list[i]
            date = day_data['dt_txt'].split(" ")[0]
            temp = day_data['main']['temp']
            desc = day_data['weather'][0]['description']
            humidity = day_data['main']['humidity']
            wind_speed = day_data['wind']['speed']
            wind_direction = day_data['wind']['deg']
    
            daily_summaries.append(
                f"{date}: {temp}{unit_symbol}, {desc}. "
                f"Humidity: {humidity}%, Wind: {wind_speed} m/s at {wind_direction}°"
            )

        return f"5-Day Forecast for {city}:\n" + "\n".join(daily_summaries)

@mcp.tool()
async def get_air_quality(lat: str, lon: str):
    """Get the air quality for a specified location (coordinates)."""
    url = "http://api.openweathermap.org/data/2.5/air_pollution"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": API_KEY,
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        
        if response.status_code != 200:
            return f"Error: Could not fetch air quality data for coordinates ({lat}, {lon})."
        
        data = response.json()
        aqi = data['list'][0]['main']['aqi']
        return f"The air quality index at coordinates ({lat}, {lon}) is {aqi}."

@mcp.tool()
async def get_uv_index(lat: str, lon: str) -> str:
    """Get the UV index for a specified location (coordinates)."""

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "uv_index_max",
        "timezone": "auto"
    }
    
    async with httpx.AsyncClient() as client:
        res = await client.get(url, params=params)
        data = res.json()
        uv_max = data['daily']['uv_index_max'][0]

    return f"The maximum UV index at coordinates ({lat}, {lon}) today is {uv_max}."

@mcp.tool()
async def search_coordinates(city: str):
    """Search for the geographical coordinates of a city."""
    url = "http://api.openweathermap.org/geo/1.0/direct"
    params = {
        "q": city,
        "limit": 1,
        "appid": API_KEY,
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        
        if response.status_code != 200:
            return f"Error: Could not find coordinates for '{city}'."
        
        data = response.json()
        if not data:
            return f"Error: No data found for '{city}'."
    lat = data[0]['lat']
    lon = data[0]['lon']
    return f"The coordinates of {city} are Latitude: {lat}, Longitude: {lon}."

# Prompt implementation
@mcp.prompt()
def outfit_planner(city: str) -> str:
    """Prepares a clothing recommendation for the user!"""
    return f"""
    Please perform a comprehensive environmental check for {city}:
    1. Call 'get_current_weather' for immediate conditions. Check all parameters including temperature, humidity, and wind.
    2. Call 'get_5_day_forecast' to see if conditions will change soon.
    3. Call 'get_uv_index' to check for sun protection needs.
    
    Based on all this data, give me a detailed 'What to Wear' list. 
    Be specific about layers, footwear, and accessories like sunglasses or umbrellas. You can ask the user followup questions including their type of clothing style eg baggy, loose, formal, etc.
    """


# Run server
if __name__ == "__main__":
    mcp.run()