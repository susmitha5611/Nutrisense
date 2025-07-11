import json
import chainlit as cl
from .configs import mistral_model, client
from .data_manager import data_manager
from loguru import logger
from datetime import datetime

FOOD_RECOMMENDATIONS_TOOL = {
    "type": "function",
    "function": {
        "name": "food_recommendations",
        "description": "Provide personalized meal and nutrition recommendations based on user's goals and food logs.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_query": {
                    "type": "string",
                    "description": "The user's request for food recommendations (e.g., 'What should I eat for dinner?')"
                },
            },
            "required": ["user_query"]
        },
    },
}

def food_recommendations(user_query: str) -> str:
    """
    Provide personalized meal and nutrition recommendations.
    
    Args:
        user_query: The user's request for food recommendations
        
    Returns:
        JSON string with food recommendations
    """
    try:
        # Get current session ID
        session_id = cl.user_session.get("conversation_id", "default_session")
        
        # Get user's goals and food logs
        goals = data_manager.get_goals(session_id)
        food_logs = data_manager.get_food_logs(session_id, limit=10)  # Recent logs
        
        # Update session activity
        data_manager.update_session_activity(session_id)
        
        # Prepare context for recommendations
        goals_summary = {
            "calories": goals.get("calories", "Not set"),
            "protein": goals.get("protein", "Not set"),
            "carbs": goals.get("carbs", "Not set"),
            "fat": goals.get("fat", "Not set")
        }
        
        # Format recent food logs
        recent_foods = []
        for log in food_logs:
            recent_foods.append({
                "food": log.get("food_item", "Unknown"),
                "meal_type": log.get("meal_type", "Unknown"),
                "quantity": log.get("quantity", "Unknown"),
                "calories": log.get("calories_estimated", 0),
                "time": log.get("logged_at", "Unknown")
            })
        
        # Create comprehensive prompt
        prompt = f"""
        You are a nutrition recommendation assistant. Provide personalized food and meal suggestions.

        User's Goals: {json.dumps(goals_summary, indent=2)}
        Recent Food Logs: {json.dumps(recent_foods, indent=2)}

        Based on their goals and what they've consumed:
        1. Suggest appropriate meals or foods that help meet nutritional targets
        2. Consider what they've already eaten for balanced nutrition
        3. Provide specific recommendations with portion sizes
        4. Include variety and practical meal ideas
        5. Consider any nutritional gaps that need filling

        Guidelines:
        - If no goals set: Provide general healthy recommendations and encourage goal setting
        - If no food logs: Assume fresh start and provide full-day meal suggestions
        - If goals are being met: Suggest maintenance foods
        - If goals are exceeded in certain areas: Suggest lighter alternatives
        - Always consider meal timing and practicality

        Provide your response in a friendly, helpful tone with specific food suggestions.
        Keep it concise but informative.

        User Query: {user_query}
        """
        
        # Get AI recommendations
        response = client.chat.complete(
            model=mistral_model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.3
        )
        
        recommendations = response.choices[0].message.content
        
        # Structure the response
        result = {
            "status": "success",
            "message": recommendations,
            "context": {
                "goals_available": any(v != "Not set" for v in goals_summary.values()),
                "recent_meals": len(recent_foods),
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        }
        
        logger.info(f"Food recommendations generated for session {session_id}")
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error in food_recommendations: {e}")
        return json.dumps({
            "status": "error",
            "message": "An error occurred while generating food recommendations. Please try again.",
            "error": str(e)
        }, indent=2)