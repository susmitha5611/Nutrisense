from dotenv import load_dotenv
import json
import chainlit as cl
from .configs import mistral_model, client
from .data_manager import data_manager
from loguru import logger
from datetime import datetime

load_dotenv()

DAILY_PROGRESS_TOOL = {
    "type": "function",
    "function": {
        "name": "daily_progress",
        "description": "Provide comprehensive daily progress analysis based on user's goals and food logs.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_query": {
                    "type": "string",
                    "description": "The user's request for daily progress (e.g., 'How am I doing today?')"
                },
            },
            "required": ["user_query"]
        },
    },
}

def daily_progress(user_query: str) -> str:
    """
    Provide daily progress of the user based on their goals and food intake.
    
    Args:
        user_query: The user's progress inquiry
        
    Returns:
        JSON string with progress analysis
    """
    try:
        # Get current session ID
        session_id = cl.user_session.get("conversation_id", "default_session")
        
        # Get user's goals and food logs
        goals = data_manager.get_goals(session_id)
        food_logs = data_manager.get_food_logs(session_id, limit=20)  # Get today's logs
        
        # Update session activity
        data_manager.update_session_activity(session_id)
        
        # Prepare context for analysis
        goals_summary = {
            "calories": goals.get("calories", "Not set"),
            "protein": goals.get("protein", "Not set"),
            "carbs": goals.get("carbs", "Not set"),
            "fat": goals.get("fat", "Not set")
        }
        
        # Format food logs for analysis
        foods_summary = []
        for log in food_logs:
            foods_summary.append({
                "food": log.get("food_item", "Unknown"),
                "meal_type": log.get("meal_type", "Unknown"),
                "quantity": log.get("quantity", "Unknown"),
                "calories": log.get("calories_estimated", 0),
                "time": log.get("logged_at", "Unknown")
            })
        
        # Create comprehensive prompt
        prompt = f"""
        You are a nutrition analysis assistant. Provide an insightful analysis of the user's food logs.

        User's Goals: {json.dumps(goals_summary, indent=2)}
        Today's Food Logs: {json.dumps(foods_summary, indent=2)}

        Analyze the following:
        1. Total calories and macronutrients consumed today
        2. Progress towards daily goals (percentage completed)
        3. Identify nutritional strengths or gaps
        4. Provide helpful insights based on eating patterns
        5. Suggest improvements if needed

        Special cases:
        - If no food logs: Suggest they log some meals first
        - If no goals: Encourage them to set goals for meaningful analysis
        - If goals are met: Congratulate and provide maintenance tips
        - If goals are exceeded: Provide gentle guidance

        Provide your response in a friendly, encouraging tone with specific numbers and percentages.
        Keep it concise but informative.

        User Query: {user_query}
        """
        
        # Get AI analysis
        response = client.chat.complete(
            model=mistral_model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.3
        )
        
        analysis = response.choices[0].message.content
        
        # Structure the response
        result = {
            "status": "success",
            "message": analysis,
            "summary": {
                "goals_set": any(v != "Not set" for v in goals_summary.values()),
                "foods_logged": len(foods_summary),
                "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        }
        
        logger.info(f"Daily progress generated for session {session_id}: {len(foods_summary)} food logs analyzed")
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error in daily_progress: {e}")
        return json.dumps({
            "status": "error",
            "message": "An error occurred while analyzing your progress. Please try again.",
            "error": str(e)
        }, indent=2)