from typing import Dict, List
from pydantic import BaseModel, Field
import json
import chainlit as cl
from .configs import mistral_model, client
from .data_manager import data_manager
from loguru import logger

GOAL_SETTING_TOOL = {
    "type": "function",
    "function": {
        "name": "goal_setting",
        "description": "Set/Update the dietary goals for the user including calories, protein, carbs, and fat targets.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_query": {
                    "type": "string",
                    "description": "The user's goal-setting request"
                },
            },
            "required": ["user_query"]
        },
    },
}

class GoalSettingAgent(BaseModel):
    """Structured output for goal setting"""
    calories: str = Field(description="Daily calorie target in kcal")
    protein: str = Field(description="Daily protein target in grams")
    carbs: str = Field(description="Daily carbohydrate target in grams")
    fat: str = Field(description="Daily fat target in grams")

def goal_setting(user_query: str) -> str:
    """
    Set/update the dietary goals for the user based on their input.
    
    Args:
        user_query: The user's goal-setting request
        
    Returns:
        JSON string with the updated goals
    """
    try:
        # Get current session ID
        session_id = cl.user_session.get("conversation_id", "default_session")
        
        # Get existing goals for context
        existing_goals = data_manager.get_goals(session_id)
        
        # Create system prompt with existing goals context
        system_prompt = """Extract the dietary goals from the user input.
        
        Current goals (if any):
        - Calories: {calories}
        - Protein: {protein}g
        - Carbs: {carbs}g
        - Fat: {fat}g
        
        For any goal not mentioned by the user, keep the existing value or leave empty if no existing value.
        Extract numeric values only (no units in the response).
        """.format(
            calories=existing_goals.get("calories", "Not set"),
            protein=existing_goals.get("protein", "Not set"),
            carbs=existing_goals.get("carbs", "Not set"),
            fat=existing_goals.get("fat", "Not set")
        )
        
        # Parse goals using Mistral
        chat_response = client.chat.parse(
            model=mistral_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ],
            response_format=GoalSettingAgent,
            max_tokens=256,
            temperature=0
        )
        
        # Extract the goals from the response
        new_goals = json.loads(chat_response.choices[0].message.content)
        
        # Merge with existing goals (only update non-empty values)
        updated_goals = existing_goals.copy()
        for key, value in new_goals.items():
            if value and value.strip():  # Only update if value is provided
                updated_goals[key] = value.strip()
        
        # Save to database
        success = data_manager.update_goals(session_id, updated_goals)
        
        if success:
            # Update session activity
            data_manager.update_session_activity(session_id)
            
            # Return user-friendly response
            response = {
                "status": "success",
                "message": "Goals updated successfully! 🎯",
                "goals": updated_goals
            }
            logger.info(f"Goals updated for session {session_id}: {updated_goals}")
        else:
            response = {
                "status": "error",
                "message": "Sorry, I couldn't save your goals. Please try again.",
                "goals": existing_goals
            }
            logger.error(f"Failed to update goals for session {session_id}")
        
        return json.dumps(response, indent=2)
        
    except Exception as e:
        logger.error(f"Error in goal_setting: {e}")
        return json.dumps({
            "status": "error",
            "message": "An error occurred while setting your goals. Please try again.",
            "error": str(e)
        }, indent=2)