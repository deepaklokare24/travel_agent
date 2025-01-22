from typing import Dict, List, Optional, Union
import requests
from datetime import datetime
import os
from dotenv import load_dotenv
from tavily import TavilyClient
import logging
from googlemaps import Client as GoogleMapsClient

load_dotenv()

# Configure logging for tools
logger = logging.getLogger(__name__)


def get_transportation(from_location: str, to_location: str, travel_date: str) -> List[str]:
    """Get transportation options between two locations using Google Maps Directions API."""
    logger.info(f"Fetching transportation options from {from_location} to {to_location}")
    try:
        gmaps = GoogleMapsClient(key=os.getenv("GOOGLE_MAPS_API_KEY"))
        
        # Get directions with alternative routes
        directions = gmaps.directions(
            from_location,
            to_location,
            mode="transit",  # Gets public transportation options
            alternatives=True,
            transit_mode=["bus", "train", "subway", "train"]
        )
        
        transportation_options = []
        for route in directions[:5]:
            legs = route.get("legs", [])[0]
            steps = legs.get("steps", [])
            
            option = {
                "type": "transportation",
                "title": f"From {legs.get('start_address')} to {legs.get('end_address')}",
                "description": f"Duration: {legs.get('duration', {}).get('text')}, Distance: {legs.get('distance', {}).get('text')}",
                "steps": [step.get("html_instructions") for step in steps]
            }
            transportation_options.append(option)
            
        logger.info(f"Found {len(transportation_options)} transportation options")
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
    """Get restaurant recommendations using Google Places API."""
    try:
        gmaps = GoogleMapsClient(key=os.getenv("GOOGLE_MAPS_API_KEY"))
        
        # First, get the location coordinates
        geocode_result = gmaps.geocode(location)
        if not geocode_result:
            return []
            
        location_coords = geocode_result[0]['geometry']['location']
        lat = location_coords['lat']
        lng = location_coords['lng']
        
        # Search for restaurants
        places_result = gmaps.places_nearby(
            location=(lat, lng),
            radius=5000,  # 5km radius
            type='restaurant'
        )
        
        restaurants = []
        for place in places_result.get('results', [])[:5]:
            # Get detailed information for each place
            detail_result = gmaps.place(place['place_id'], fields=['name', 'formatted_address', 'rating', 'price_level', 'website', 'formatted_phone_number'])
            detail = detail_result.get('result', {})
            
            restaurants.append({
                "name": detail.get('name', ''),
                "description": f"Located at: {detail.get('formatted_address', '')}",
                "url": detail.get('website', ''),
                "rating": detail.get('rating', 4.0),
                "cuisine": place.get('types', ['Local'])[0].replace('_', ' ').title(),
                "price_level": '$' * (detail.get('price_level', 2) or 2)
            })
        return restaurants
    except Exception as e:
        logger.error(f"Error getting restaurants: {str(e)}", exc_info=True)
        return []


def get_hotels(location: str, check_in: str) -> List[Dict[str, Union[str, float, int]]]:
    """Get hotel recommendations using Google Places API."""
    try:
        gmaps = GoogleMapsClient(key=os.getenv("GOOGLE_MAPS_API_KEY"))
        
        # First, get the location coordinates
        geocode_result = gmaps.geocode(location)
        if not geocode_result:
            return []
            
        location_coords = geocode_result[0]['geometry']['location']
        lat = location_coords['lat']
        lng = location_coords['lng']
        
        # Search for hotels
        places_result = gmaps.places_nearby(
            location=(lat, lng),
            radius=5000,  # 5km radius
            type='lodging'
        )
        
        hotels = []
        for place in places_result.get('results', [])[:5]:
            # Get detailed information for each place
            detail_result = gmaps.place(place['place_id'], fields=['name', 'formatted_address', 'rating', 'price_level', 'website', 'formatted_phone_number'])
            detail = detail_result.get('result', {})
            
            hotels.append({
                "name": detail.get('name', ''),
                "description": f"Located at: {detail.get('formatted_address', '')}",
                "url": detail.get('website', ''),
                "rating": detail.get('rating', 4.0),
                "location": location,
                "amenities": [amenity.replace('_', ' ').title() for amenity in place.get('types', [])]
            })
        return hotels
    except Exception as e:
        logger.error(f"Error getting hotels: {str(e)}", exc_info=True)
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
