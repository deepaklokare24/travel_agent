from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from travel_agent import TravelAgent
import os
import logging

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Update with your frontend's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Log to console
        logging.FileHandler('travel_agent.log')  # Log to file
    ]
)
logger = logging.getLogger(__name__)


class Preferences(BaseModel):
    budget: str
    interests: list
    transportation: str
    accommodation_type: str
    pace: str


class TravelRequest(BaseModel):
    from_location: str
    to_location: str
    start_date: str
    end_date: str
    preferences: Preferences
    number_of_travelers: int
    include_weather: bool
    include_local_tips: bool


# Initialize the travel agent with the OpenAI API key
agent = TravelAgent(openai_api_key=os.getenv("OPENAI_API_KEY"))


@app.post("/api/v1/generate-itinerary")
async def generate_itinerary(request: TravelRequest):
    logger.info(f"Received itinerary request for {
                request.from_location} to {request.to_location}")
    try:
        itinerary = agent.generate_itinerary(request.model_dump())
        logger.info("Itinerary generated successfully")
        return itinerary
    except Exception as e:
        error_msg = f"Error generating itinerary: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=error_msg
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
