"""
User Profile Management Tool for NutriSense Diet Companion
Manages user profiles, physical stats, preferences, and integrates with memory layer
"""

import json
import chainlit as cl
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from .configs import mistral_model, client
from .data_manager import data_manager
from .memory_manager import memory_manager
from loguru import logger

PROFILE_MANAGEMENT_TOOL = {
    "type": "function",
    "function": {
        "name": "profile_management",
        "description": "Manage user profile including physical stats, preferences, and personal information for personalized recommendations.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_query": {
                    "type": "string",
                    "description": "The user's profile management request (e.g., 'Update my profile', 'Set my height and weight')"
                },
                "action": {
                    "type": "string",
                    "description": "Action to perform (update, view, delete)",
                    "enum": ["update", "view", "delete"]
                },
                "user_name": {
                    "type": "string",
                    "description": "User's name"
                },
                "weight": {
                    "type": "number",
                    "description": "User's current weight in kg"
                },
                "height": {
                    "type": "number",
                    "description": "User's height in cm"
                },
                "age": {
                    "type": "integer",
                    "description": "User's age in years"
                },
                "gender": {
                    "type": "string",
                    "description": "User's gender (male, female, other)"
                },
                "activity_level": {
                    "type": "string",
                    "description": "Activity level (sedentary, light, moderate, active, very_active)"
                },
                "fitness_experience": {
                    "type": "string",
                    "description": "Fitness experience level (beginner, intermediate, advanced)"
                },
                "health_conditions": {
                    "type": "string",
                    "description": "Any health conditions or limitations"
                },
                "dietary_preferences": {
                    "type": "string",
                    "description": "Dietary preferences (vegetarian, vegan, keto, etc.)"
                },
                "food_allergies": {
                    "type": "string",
                    "description": "Food allergies or intolerances"
                },
                "workout_preferences": {
                    "type": "string",
                    "description": "Preferred workout types (cardio, strength, yoga, etc.)"
                },
                "equipment_access": {
                    "type": "string",
                    "description": "Available equipment (home, gym, bodyweight, etc.)"
                }
            },
            "required": ["user_query", "action"]
        }
    }
}

class ProfileData(BaseModel):
    """User profile data structure"""
    user_name: Optional[str] = Field(default=None, description="User's name")
    weight: Optional[float] = Field(default=None, description="Weight in kg")
    height: Optional[float] = Field(default=None, description="Height in cm")
    age: Optional[int] = Field(default=None, description="Age in years")
    gender: Optional[str] = Field(default=None, description="Gender")
    activity_level: Optional[str] = Field(default=None, description="Activity level")
    fitness_experience: Optional[str] = Field(default=None, description="Fitness experience")
    health_conditions: Optional[str] = Field(default=None, description="Health conditions")
    dietary_preferences: Optional[str] = Field(default=None, description="Dietary preferences")
    food_allergies: Optional[str] = Field(default=None, description="Food allergies")
    workout_preferences: Optional[str] = Field(default=None, description="Workout preferences")
    equipment_access: Optional[str] = Field(default=None, description="Equipment access")
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())

def calculate_bmi(weight: float, height: float) -> float:
    """Calculate BMI from weight (kg) and height (cm)"""
    height_m = height / 100  # Convert cm to meters
    return weight / (height_m ** 2)

def get_bmi_category(bmi: float) -> str:
    """Get BMI category"""
    if bmi < 18.5:
        return "Underweight"
    elif bmi < 25:
        return "Normal weight"
    elif bmi < 30:
        return "Overweight"
    else:
        return "Obese"

def calculate_ideal_weight_range(height: float) -> tuple:
    """Calculate ideal weight range based on height"""
    height_m = height / 100
    min_weight = 18.5 * (height_m ** 2)
    max_weight = 24.9 * (height_m ** 2)
    return (round(min_weight, 1), round(max_weight, 1))

def profile_management(
    user_query: str,
    action: str,
    user_name: Optional[str] = None,
    weight: Optional[float] = None,
    height: Optional[float] = None,
    age: Optional[int] = None,
    gender: Optional[str] = None,
    activity_level: Optional[str] = None,
    fitness_experience: Optional[str] = None,
    health_conditions: Optional[str] = None,
    dietary_preferences: Optional[str] = None,
    food_allergies: Optional[str] = None,
    workout_preferences: Optional[str] = None,
    equipment_access: Optional[str] = None
) -> str:
    """
    Manage user profile information.
    
    Args:
        user_query: The user's profile management request
        action: Action to perform (update, view, delete)
        **kwargs: Various profile parameters
        
    Returns:
        JSON string with profile management results
    """
    try:
        # Get current session ID
        session_id = cl.user_session.get("conversation_id", "default_session")
        
        # Get existing profile data
        existing_profile = get_user_profile(session_id)
        
        if action == "view":
            return view_profile(session_id, existing_profile)
        elif action == "update":
            return update_profile(session_id, existing_profile, {
                "user_name": user_name,
                "weight": weight,
                "height": height,
                "age": age,
                "gender": gender,
                "activity_level": activity_level,
                "fitness_experience": fitness_experience,
                "health_conditions": health_conditions,
                "dietary_preferences": dietary_preferences,
                "food_allergies": food_allergies,
                "workout_preferences": workout_preferences,
                "equipment_access": equipment_access
            })
        elif action == "delete":
            return delete_profile(session_id)
        else:
            return json.dumps({
                "status": "error",
                "message": "Invalid action. Use 'view', 'update', or 'delete'."
            })
            
    except Exception as e:
        logger.error(f"Error in profile_management: {e}")
        return json.dumps({
            "status": "error",
            "message": "An error occurred while managing your profile. Please try again.",
            "error": str(e)
        }, indent=2)

def get_user_profile(session_id: str) -> Dict:
    """Get user profile from database"""
    try:
        # Use the proper user profiles table
        profile_data = data_manager.get_user_profile(session_id)
        return profile_data
        
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        return {}

def view_profile(session_id: str, profile: Dict) -> str:
    """View user profile"""
    try:
        # Get personalized memories for additional context
        memories = []
        if memory_manager.is_available():
            memories = memory_manager.get_user_memories(session_id, "profile preferences", limit=5)
        
        # Calculate BMI and related metrics if data is available
        bmi_info = {}
        if profile.get("weight") and profile.get("height"):
            weight = float(profile["weight"])
            height = float(profile["height"])
            bmi = calculate_bmi(weight, height)
            bmi_category = get_bmi_category(bmi)
            ideal_weight_range = calculate_ideal_weight_range(height)
            
            bmi_info = {
                "bmi": round(bmi, 1),
                "bmi_category": bmi_category,
                "ideal_weight_range": ideal_weight_range
            }
        
        # Update session activity
        data_manager.update_session_activity(session_id)
        
        # Create personalized greeting message
        greeting_message = "Here's your profile! 👤"
        if profile.get("user_name"):
            greeting_message = f"Hello {profile['user_name']}! Here's your profile! 👤"
        
        result = {
            "status": "success",
            "message": greeting_message,
            "profile": profile,
            "health_metrics": bmi_info,
            "memories_count": len(memories),
            "last_updated": profile.get("updated_at", "Never"),
            "profile_completeness": calculate_profile_completeness(profile)
        }
        
        logger.info(f"Profile viewed for session {session_id}")
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error viewing profile: {e}")
        return json.dumps({
            "status": "error",
            "message": "Error viewing profile.",
            "error": str(e)
        })

def update_profile(session_id: str, existing_profile: Dict, updates: Dict) -> str:
    """Update user profile"""
    try:
        # Filter out None values
        updates = {k: v for k, v in updates.items() if v is not None}
        
        # Merge with existing profile
        updated_profile = existing_profile.copy()
        updated_profile.update(updates)
        updated_profile["updated_at"] = datetime.now().isoformat()
        
        # Save to database using proper user profiles table
        success = data_manager.update_user_profile(session_id, updated_profile)
        
        if success:
            # Store preferences in memory for personalization
            if memory_manager.is_available():
                profile_summary = create_profile_summary(updated_profile)
                memory_manager.update_user_profile(session_id, updated_profile)
                
                # Add user name to memory if provided
                if updates.get("user_name"):
                    memory_manager.add_user_preference(
                        session_id, 
                        f"User name: {updates['user_name']}", 
                        "profile"
                    )
                
                # Add specific preferences to memory
                if updates.get("dietary_preferences"):
                    memory_manager.add_user_preference(
                        session_id, 
                        f"Dietary preference: {updates['dietary_preferences']}", 
                        "nutrition"
                    )
                
                if updates.get("workout_preferences"):
                    memory_manager.add_workout_preference(
                        session_id, 
                        f"Workout preference: {updates['workout_preferences']}", 
                        "fitness"
                    )
            
            # Calculate health metrics
            health_metrics = {}
            if updated_profile.get("weight") and updated_profile.get("height"):
                weight = float(updated_profile["weight"])
                height = float(updated_profile["height"])
                bmi = calculate_bmi(weight, height)
                bmi_category = get_bmi_category(bmi)
                ideal_weight_range = calculate_ideal_weight_range(height)
                
                health_metrics = {
                    "bmi": round(bmi, 1),
                    "bmi_category": bmi_category,
                    "ideal_weight_range": ideal_weight_range
                }
            
            # Update session activity
            data_manager.update_session_activity(session_id)
            
            # Create personalized success message
            success_message = "Profile updated successfully! ✅"
            if updated_profile.get("user_name"):
                success_message = f"Hello {updated_profile['user_name']}! Profile updated successfully! ✅"
            
            result = {
                "status": "success",
                "message": success_message,
                "updated_fields": list(updates.keys()),
                "profile": updated_profile,
                "health_metrics": health_metrics,
                "profile_completeness": calculate_profile_completeness(updated_profile)
            }
            
            logger.info(f"Profile updated for session {session_id}: {list(updates.keys())}")
            return json.dumps(result, indent=2)
        else:
            return json.dumps({
                "status": "error",
                "message": "Failed to update profile. Please try again."
            })
            
    except Exception as e:
        logger.error(f"Error updating profile: {e}")
        return json.dumps({
            "status": "error",
            "message": "Error updating profile.",
            "error": str(e)
        })

def delete_profile(session_id: str) -> str:
    """Delete user profile"""
    try:
        # Clear profile data
        empty_profile = {"updated_at": datetime.now().isoformat()}
        success = data_manager.update_goals(session_id, empty_profile)
        
        if success:
            result = {
                "status": "success",
                "message": "Profile deleted successfully! 🗑️",
                "note": "You can create a new profile anytime by updating your information."
            }
            
            logger.info(f"Profile deleted for session {session_id}")
            return json.dumps(result, indent=2)
        else:
            return json.dumps({
                "status": "error",
                "message": "Failed to delete profile. Please try again."
            })
            
    except Exception as e:
        logger.error(f"Error deleting profile: {e}")
        return json.dumps({
            "status": "error",
            "message": "Error deleting profile.",
            "error": str(e)
        })

def calculate_profile_completeness(profile: Dict) -> Dict:
    """Calculate profile completeness percentage"""
    required_fields = [
        "user_name", "weight", "height", "age", "gender", "activity_level", 
        "fitness_experience", "dietary_preferences"
    ]
    
    completed_fields = sum(1 for field in required_fields if profile.get(field))
    completeness_percentage = (completed_fields / len(required_fields)) * 100
    
    return {
        "percentage": round(completeness_percentage, 1),
        "completed_fields": completed_fields,
        "total_fields": len(required_fields),
        "missing_fields": [field for field in required_fields if not profile.get(field)]
    }

def create_profile_summary(profile: Dict) -> str:
    """Create a summary of the profile for memory storage"""
    summary_parts = []
    
    if profile.get("user_name"):
        summary_parts.append(f"Name: {profile['user_name']}")
    
    if profile.get("age"):
        summary_parts.append(f"Age: {profile['age']} years")
    
    if profile.get("weight") and profile.get("height"):
        bmi = calculate_bmi(float(profile["weight"]), float(profile["height"]))
        summary_parts.append(f"BMI: {bmi:.1f}")
    
    if profile.get("activity_level"):
        summary_parts.append(f"Activity level: {profile['activity_level']}")
    
    if profile.get("fitness_experience"):
        summary_parts.append(f"Fitness experience: {profile['fitness_experience']}")
    
    if profile.get("dietary_preferences"):
        summary_parts.append(f"Dietary preferences: {profile['dietary_preferences']}")
    
    return "; ".join(summary_parts)

def get_user_identity(session_id: str) -> str:
    """Get user identity from profile or memory"""
    try:
        # First check the profile
        profile = get_user_profile(session_id)
        if profile.get("user_name"):
            return profile["user_name"]
        
        # Then check memory
        if memory_manager.is_available():
            memories = memory_manager.get_user_memories(session_id, "name", limit=5)
            for memory in memories:
                if isinstance(memory, dict):
                    memory_text = memory.get('memory', memory.get('text', ''))
                    if 'name:' in memory_text.lower() or 'i am' in memory_text.lower():
                        return memory_text.split(':')[-1].strip() if ':' in memory_text else "User"
        
        return "User"
    except Exception as e:
        logger.error(f"Error getting user identity: {e}")
        return "User"

def auto_store_user_name(session_id: str, user_message: str) -> bool:
    """Automatically detect and store user name from messages like 'I am Mihir'"""
    try:
        # Simple pattern matching for self-introduction
        message_lower = user_message.lower().strip()
        
        # Check for patterns like "I am [name]", "My name is [name]", "I'm [name]"
        patterns = [
            "i am ", "my name is ", "i'm ", "im ", "call me ", "this is "
        ]
        
        for pattern in patterns:
            if pattern in message_lower:
                # Extract the name part
                name_part = message_lower.split(pattern)[1].strip()
                # Take only the first word as the name (to avoid getting full sentences)
                name = name_part.split()[0] if name_part.split() else ""
                
                # Clean up the name (remove punctuation, capitalize)
                name = name.strip('.,!?').capitalize()
                
                if name and len(name) > 1:  # Valid name
                    # Store in profile
                    profile_management(
                        user_query=f"Store user name: {name}",
                        action="update",
                        user_name=name
                    )
                    return True
        
        return False
    except Exception as e:
        logger.error(f"Error auto-storing user name: {e}")
        return False 