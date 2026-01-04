from mcp.server.fastmcp import FastMCP, Context
from typing import Optional
from dotenv import load_dotenv
import os
import httpx

load_dotenv()
API_KEY = os.getenv("API_KEY")

# Create an MCP server
mcp = FastMCP("Weather Service - OpenWeatherMap API")

# Tool implementation
@mcp.tool()
async def get_current_weather(lat: float, lon: float, units: str) -> str:
    """Get the current weather for a specified location (coordinates). Uses positive float for North latitudes, negative for South latitudes. Uses positive longitude for East longitudes, negative for West longitudes. Imperial units for Fahrenheit, metric for Celsius."""

    url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": API_KEY,
        "units": units
    }

    unit_symbol = "°F" if units == "imperial" else "°C"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        
        if response.status_code != 200:
            return f"Error: Could not find weather for '{lat}, {lon}'. (Status: {response.status_code})"
        
        data = response.json()
        temp = data['main']['temp']
        desc = data['weather'][0]['description']
        humidity = data['main']['humidity']
        wind_speed = data['wind']['speed']
        wind_direction = data['wind']['deg']

        return f"The current weather in ({lat}, {lon}) is {desc} with a temperature of {temp}{unit_symbol} and humidity of {humidity}%. The wind speed is {wind_speed} m/s at {wind_direction}°."


@mcp.tool()
async def get_5_day_forecast(lat: float, lon: float, units: str):
    """Get the 5-day weather forecast for a specified location (coordinates). Imperial units for Fahrenheit, metric for Celsius."""
    url = "http://api.openweathermap.org/data/2.5/forecast"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": API_KEY,
        "units": units
    }
    
    unit_symbol = "°F" if units == "imperial" else "°C"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        
        if response.status_code != 200:
            return f"Error: Could not fetch forecast for ({lat}, {lon})."
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

        return f"5-Day Forecast for ({lat}, {lon}):\n" + "\n".join(daily_summaries)

@mcp.tool()
async def get_air_quality(lat: float, lon: float):
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
async def get_uv_index(lat: float, lon: float) -> str:
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
async def get_coordinates(location: str) -> str:
    """
    Converts a location name (city, state, country) into latitude and longitude.
    Example input: 'Blue Mountain, Ontario, Canada'
    """
    url = "http://api.openweathermap.org/geo/1.0/direct"
    params = {
        "q": location,
        "limit": 1,
        "appid": API_KEY
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        
        if response.status_code != 200:
            return f"Error: API call failed with status {response.status_code}"
            
        data = response.json()
        
        if not data:
            return f"Error: Could not find coordinates for '{location}'."
        
        place = data[0]
        lat = place['lat']
        lon = place['lon']
        name = place['name']
        state = place.get('state', 'N/A')
        
        return f"Location: {name}, {state} | Latitude: {lat}, Longitude: {lon}"
    
# tool with sampling - not quite sure if this will work well due to the recursive nature.
@mcp.tool()
async def get_location_recommendation(city: str, region: str, vacation_type: Optional[str], ctx: Context) -> str:
    """User provides city they are planning to visit and region for their vacation. Checks weather conditions in coming few days and compares if the city would be good to visit for intended vacation type. If not, suggests an alternative city in the same region with better weather conditions for the vacation type."""

    lat, lon = await ctx.call_tool("get_coordinates", city)
    current_weather_data = await get_current_weather(city, "metric")
    weather_data_5_days = await get_5_day_forecast(city, "metric")

    result = await ctx.sample(
        f"""The user is planning a {vacation_type} vacation in {city}, {region}. 
        The current weather is: {current_weather_data}
        The 5-day forecast is: {weather_data_5_days}.

        Based on all this data, give me a detailed recommendation on whether this city is suitable for the vacation type and what to expect. If not, suggest an alternative city in the same region with better weather conditions for the vacation type. Use the get_location_recommendation tool to find the alternative city.
        """
    )

    return result.text   

# Resource implementation
@mcp.resource("weather://safety-manual")
def weather_safety_manual() -> str:
    """A guide on staying safe in varying weather conditions."""

    return """
    # Weather Safety Manual
    - If UV > 8: Wear a hat and stay in shade.
    - If Wind > 40mph: Secure loose outdoor furniture.
    - If Humidity > 90%: Stay hydrated and watch for heat stroke.
    """

# Prompt implementation
@mcp.prompt()
def outfit_planner(city: str) -> str:
    """Prepares a clothing recommendation for the user!"""
    return f"""
    Please perform a comprehensive environmental check for {city}:
    1. Call 'get_coordinates' to get latitude and longitude.
    2. Use those coordinates to:
     - Call 'get_current_weather' for immediate conditions. Check all parameters including temperature, humidity, and wind.
     - Call 'get_5_day_forecast' to see if conditions will change soon.
     - Call 'get_uv_index' to check for sun protection needs.
    
    Based on all this data, give me a detailed 'What to Wear' list. 
    Be specific about layers, footwear, and accessories like sunglasses or umbrellas. You can ask the user followup questions including their type of clothing style eg baggy, loose, formal, etc.
    """


# Run server
if __name__ == "__main__":
    mcp.run()