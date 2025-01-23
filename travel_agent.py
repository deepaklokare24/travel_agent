import os
from datetime import datetime
from typing import Dict, Any
from dotenv import load_dotenv
import json
import logging

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI  # Updated import
from langchain.agents import AgentExecutor
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.agents import create_openai_functions_agent
from langchain.tools import StructuredTool
from langchain.schema import SystemMessage
from travel_tools import (
    get_transportation,
    get_weather_forecast,
    get_attractions,
    get_restaurants,
    get_hotels,
    get_local_tips,
)
from langchain_core.messages import HumanMessage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class TravelAgent:
    def __init__(self, openai_api_key: str):
        logger.info("Initializing TravelAgent...")
        self.llm = ChatOpenAI(
            model="gpt-4-turbo-preview",
            temperature=0.5,
            openai_api_key=openai_api_key,
        )

    def generate_itinerary(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a travel itinerary with comprehensive information."""
        from_location = request_data["from_location"]
        to_location = request_data["to_location"]
        start_date = request_data["start_date"]
        end_date = request_data["end_date"]
        preferences = request_data.get("preferences", {})
        num_travelers = request_data.get("number_of_travelers", 1)
        include_weather = request_data.get("include_weather", True)
        include_local_tips = request_data.get("include_local_tips", True)

        # Calculate number of days
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        num_days = (end - start).days + 1

        # Get trip information
        transportation_options = get_transportation(
            from_location,
            to_location,
            start_date,
            mode=preferences.get("transportation", "mixed")
        )
        weather = get_weather_forecast(to_location, start_date)
        attractions = get_attractions(to_location)
        restaurants = get_restaurants(to_location)
        hotels = get_hotels(to_location, start_date)
        local_tips = get_local_tips(to_location)

        # Create the prompt
        prompt = f"""Create a {num_days}-day travel itinerary from {from_location} to {to_location}.

TRIP DETAILS:
- Start Date: {start_date}
- End Date: {end_date}
- Duration: {num_days} days
- Travelers: {num_travelers}
- Budget: {preferences.get('budget')}
- Transportation: {preferences.get('transportation')}
- Accommodation: {preferences.get('accommodation_type')}

AVAILABLE INFORMATION:
Transportation Options:
{json.dumps(transportation_options, indent=2)}

Local Attractions:
{json.dumps(attractions, indent=2)}

Restaurants:
{json.dumps(restaurants, indent=2)}

Hotels:
{json.dumps(hotels, indent=2)}

Weather:
{json.dumps(weather, indent=2)}

Local Tips:
{json.dumps(local_tips, indent=2)}

Format the response as a detailed day-by-day itinerary starting with:
"Here is your {num_days}-day itinerary from {from_location} to {to_location}:"

Include for each day:
1. Date and day number
2. Morning activities with times
3. Afternoon activities with times
4. Evening activities with times
5. Restaurant recommendations for meals
6. Transportation details
7. Hotel/accommodation information

End with practical travel tips."""

        # Generate itinerary using direct LLM call
        messages = [
            HumanMessage(content=prompt)
        ]

        response = self.llm.invoke(messages)

        # Return the formatted response matching frontend requirements
        return {
            "itinerary": response.content,
            "from_location": from_location,
            "to_location": to_location,
            "start_date": start_date,
            "end_date": end_date,
            "generated_at": datetime.utcnow().isoformat(),
            "metadata": {
                "includes_weather": include_weather,
                "includes_local_tips": include_local_tips,
                "number_of_travelers": num_travelers
            },
            "transportation_info": transportation_options,
            "weather_info": weather,
            "attractions": attractions,
            "restaurants": restaurants,
            "hotels": hotels,
            "local_tips": local_tips,
            "request_details": {
                "from_location": from_location,
                "to_location": to_location,
                "start_date": start_date,
                "end_date": end_date,
                "duration_days": num_days,
                "preferences": preferences,
                "number_of_travelers": num_travelers
            }
        }


def main():
    openai_api_key = os.getenv("OPENAI_API_KEY")
    # Example usage
    agent = TravelAgent(openai_api_key=openai_api_key)

    # Example itinerary request
    itinerary = agent.generate_itinerary(
        {
            "from_location": "San Francisco",
            "to_location": "Los Angeles",
            "start_date": "2024-02-01",
            "end_date": "2024-02-05",
            "preferences": {
                "budget": "medium",
                "interests": ["food", "culture", "nature"],
                "transportation": "car"
            }
        }
    )

    print("Generated Itinerary:")
    print(itinerary)


if __name__ == "__main__":
    main()
