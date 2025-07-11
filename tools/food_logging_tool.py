from typing import Dict
from pydantic import BaseModel, Field
import json
import chainlit as cl
from .configs import mistral_model, client
from .data_manager import data_manager
from loguru import logger

FOOD_LOGGING_TOOL = {
    "type": "function",
    "function": {
        "name": "food_log",
        "description": "Log food consumption with nutritional information including calories, protein, carbs, and fat.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_query": {
                    "type": "string",
                    "description": "The user's food logging request (e.g., 'I had 2 eggs for breakfast')"
                },
            },
            "required": ["user_query"]
        },
    },
}

class FoodLoggingAgent(BaseModel):
    """Structured output for food logging"""
    food: str = Field(description="Food name/item consumed")
    quantity: str = Field(description="Quantity consumed (e.g., '2 eggs', '1 cup', '200g')")
    calories: str = Field(description="Estimated calories")
    protein: str = Field(description="Estimated protein in grams")
    carbs: str = Field(description="Estimated carbohydrates in grams")
    fat: str = Field(description="Estimated fat in grams")
    meal_type: str = Field(description="Meal type (breakfast, lunch, dinner, snack)")

def food_logging(user_query: str) -> str:
    """
    Log food consumption provided by user with nutritional analysis.
    
    Args:
        user_query: The user's food logging request
        
    Returns:
        JSON string with logged food details
    """
    try:
        # Get current session ID
        session_id = cl.user_session.get("conversation_id", "default_session")
        
        # Parse food details using Mistral
        chat_response = client.chat.parse(
            model=mistral_model,
            messages=[
                {
                    "role": "system",
                    "content": """Analyze the food consumed by the user and provide nutritional information.
                    
                    Guidelines:
                    - Extract food name, quantity, and meal type
                    - Provide realistic calorie and macronutrient estimates
                    - Use standard serving sizes if quantity is unclear
                    - For meal_type, choose from: breakfast, lunch, dinner, snack
                    - Give numeric values only (no units in the response)
                    """
                },
                {
                    "role": "user",
                    "content": user_query
                },
            ],
            response_format=FoodLoggingAgent,
            max_tokens=256,
            temperature=0
        )
        
        # Extract the food details from the response
        food_details = json.loads(chat_response.choices[0].message.content)
        
        # Save to database
        success = data_manager.add_food_log(
            session_id=session_id,
            food_item=food_details.get("food", ""),
            meal_type=food_details.get("meal_type", ""),
            quantity=food_details.get("quantity", ""),
            calories_estimated=int(food_details.get("calories", "0") or "0")
        )
        
        if success:
            # Update session activity
            data_manager.update_session_activity(session_id)
            
            # Return user-friendly response
            response = {
                "status": "success",
                "message": f"Food logged successfully! 🍽️",
                "food_details": food_details
            }
            logger.info(f"Food logged for session {session_id}: {food_details.get('food', 'Unknown')}")
        else:
            response = {
                "status": "error",
                "message": "Sorry, I couldn't save your food log. Please try again.",
                "food_details": food_details
            }
            logger.error(f"Failed to log food for session {session_id}")
        
        return json.dumps(response, indent=2)
        
    except Exception as e:
        logger.error(f"Error in food_logging: {e}")
        return json.dumps({
            "status": "error",
            "message": "An error occurred while logging your food. Please try again.",
            "error": str(e)
        }, indent=2)

