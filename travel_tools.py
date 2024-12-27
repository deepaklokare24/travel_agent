from typing import Dict, List, Optional, Union
import requests
from datetime import datetime
import os
from dotenv import load_dotenv
from serpapi import GoogleSearch
from tavily import TavilyClient
import logging

load_dotenv()

# Configure logging for tools
logger = logging.getLogger(__name__)


def get_transportation(from_location: str, to_location: str, travel_date: str) -> List[str]:
    """Get real transportation options between two locations using SERP API."""
    logger.info(f"Fetching transportation options from {from_location} to {to_location}")
    try:
        search_query = f"transportation from {from_location} to {to_location}"
        logger.debug(f"SERP API search query: {search_query}")

        search = GoogleSearch({
            "q": search_query,
            "api_key": os.getenv("SERPAPI_API_KEY")
        })
        results = search.get_dict()
        logger.debug(f"SERP API raw response: {results}")

        transportation_options = []
        if "organic_results" in results:
            for result in results["organic_results"][:5]:
                transportation_options.append({
                    "type": "transportation",
                    "title": result["title"],
                    "description": result.get("snippet", ""),
                    "link": result["link"]
                })
            logger.info(f"Found {len(transportation_options)} transportation options")
        else:
            logger.warning("No transportation results found in SERP API response")
        return transportation_options
    except Exception as e:
        logger.error(f"Error getting transportation info: {str(e)}", exc_info=True)
        return []


def get_weather_forecast(location: str, date: str) -> Dict[str, Union[float, str, int]]:
    """Get real weather forecast using OpenWeatherMap API."""
    logger.info(f"Fetching weather forecast for {location}")
    try:
        api_key = os.getenv("OPENWEATHERMAP_API_KEY")
        base_url = "http://api.openweathermap.org/data/2.5/weather"

        # Get coordinates for the location
        logger.debug(f"Getting coordinates for {location}")
        geo_url = f"http://api.openweathermap.org/geo/1.0/direct"
        geo_params = {
            "q": location,
            "limit": 1,
            "appid": api_key
        }
        geo_response = requests.get(geo_url, params=geo_params)
        geo_data = geo_response.json()
        logger.debug(f"Geocoding response: {geo_data}")

        if not geo_data:
            logger.warning(f"No coordinates found for location: {location}")
            return {}

        lat = geo_data[0]["lat"]
        lon = geo_data[0]["lon"]
        logger.info(f"Found coordinates: lat={lat}, lon={lon}")

        # Get weather data
        params = {
            "lat": lat,
            "lon": lon,
            "appid": api_key,
            "units": "metric"
        }

        response = requests.get(base_url, params=params)
        data = response.json()
        logger.debug(f"Weather API response: {data}")

        weather_data = {
            "temperature": f"{data['main']['temp']:.1f}°C",
            "feels_like": f"{data['main']['feels_like']:.1f}°C",
            "status": data["weather"][0]["description"],
            "humidity": data["main"]["humidity"]
        }
        logger.info(f"Weather data retrieved successfully for {location}")
        return weather_data
    except Exception as e:
        logger.error(f"Error getting weather forecast: {str(e)}", exc_info=True)
        return {}


def get_attractions(location: str) -> List[Dict[str, Union[str, float, int]]]:
    """Get real attractions using Tavily API."""
    logger.info(f"Fetching attractions for {location}")
    try:
        client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        search_query = f"top tourist attractions in {location}"

        logger.debug(f"Tavily API query: {search_query}")
        response = client.search(
            query=search_query,
            search_depth="advanced",
            include_images=True,
            include_raw_content=True
        )
        logger.debug(f"Tavily API raw response: {response}")

        attractions = []
        for result in response.get("results", [])[:5]:
            try:
                attraction = {
                    "title": result.get("title", "Unknown Attraction"),
                    "description": result.get("content", result.get("snippet", "No description available")),
                    "url": result.get("url", ""),
                    "image": result.get("image_url", ""),
                    "rating": float(result.get("rating", 4.0)),
                    "category": "Tourist Spot"
                }
                attractions.append(attraction)
                logger.debug(f"Processed attraction: {attraction['title']}")
            except Exception as e:
                logger.warning(f"Error processing attraction result: {str(e)}")
                continue

        logger.info(f"Found {len(attractions)} attractions for {location}")
        return attractions
    except Exception as e:
        logger.error(f"Error getting attractions: {str(e)}", exc_info=True)
        return []


def get_restaurants(location: str) -> List[Dict[str, Union[str, float, int]]]:
    """Get real restaurant recommendations using SERP API."""
    try:
        search_query = f"best restaurants in {location}"
        search = GoogleSearch({
            "q": search_query,
            "api_key": os.getenv("SERPAPI_API_KEY")
        })
        results = search.get_dict()

        restaurants = []
        if "organic_results" in results:
            for result in results["organic_results"][:5]:
                restaurants.append({
                    "name": result["title"],
                    "description": result.get("snippet", ""),
                    "url": result["link"],
                    "rating": result.get("rating", 4.0),
                    "cuisine": "Local",  # You might want to extract this from the description
                    "price_level": "$$"  # This could be extracted from the data if available
                })
        return restaurants
    except Exception as e:
        print(f"Error getting restaurants: {e}")
        return []


def get_hotels(location: str, check_in: str) -> List[Dict[str, Union[str, float, int]]]:
    """Get real hotel recommendations using SERP API."""
    try:
        search_query = f"hotels in {location}"
        search = GoogleSearch({
            "q": search_query,
            "api_key": os.getenv("SERPAPI_API_KEY")
        })
        results = search.get_dict()

        hotels = []
        if "organic_results" in results:
            for result in results["organic_results"][:5]:
                hotels.append({
                    "name": result["title"],
                    "description": result.get("snippet", ""),
                    "url": result["link"],
                    "rating": result.get("rating", 4.0),
                    "location": location,
                    # This could be extracted from the description
                    "amenities": ["WiFi"]
                })
        return hotels
    except Exception as e:
        print(f"Error getting hotels: {e}")
        return []


def get_local_tips(location: str) -> List[Dict[str, Union[str, float, int]]]:
    """Get real local tips using Tavily API."""
    logger.info(f"Fetching local tips for {location}")
    try:
        client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        search_query = f"local tips and customs in {location}"

        logger.debug(f"Tavily API query: {search_query}")
        response = client.search(
            query=search_query,
            search_depth="advanced",
            include_raw_content=True
        )
        logger.debug(f"Tavily API raw response: {response}")

        tips = []
        for result in response.get("results", [])[:3]:
            try:
                tip = {
                    "title": result.get("title", "Local Tip"),
                    "description": result.get("content", result.get("snippet", "No description available")),
                    "url": result.get("url", ""),
                    "category": "Local Tips"
                }
                tips.append(tip)
                logger.debug(f"Processed tip: {tip['title']}")
            except Exception as e:
                logger.warning(f"Error processing tip result: {str(e)}")
                continue

        logger.info(f"Found {len(tips)} local tips for {location}")
        return tips
    except Exception as e:
        logger.error(f"Error getting local tips: {str(e)}", exc_info=True)
        return []
