"""
Workout Planning Tool for NutriSense Diet Companion
Creates personalized workout plans based on BMI, weight, diet goals, and user preferences
"""

import json
import chainlit as cl
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
import numpy as np
from datetime import datetime
from .configs import mistral_model, client
from .data_manager import data_manager
from .memory_manager import memory_manager
from loguru import logger

WORKOUT_PLANNING_TOOL = {
    "type": "function",
    "function": {
        "name": "workout_planning",
        "description": "Generate personalized workout plans based on user's BMI, weight, diet goals, fitness level, and preferences.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_query": {
                    "type": "string",
                    "description": "The user's workout planning request (e.g., 'Create a workout plan for weight loss')"
                },
                "weight": {
                    "type": "number",
                    "description": "User's current weight in kg (optional)"
                },
                "height": {
                    "type": "number",
                    "description": "User's height in cm (optional)"
                },
                "age": {
                    "type": "integer",
                    "description": "User's age in years (optional)"
                },
                "fitness_level": {
                    "type": "string",
                    "description": "User's fitness level (beginner, intermediate, advanced)"
                },
                "workout_goal": {
                    "type": "string",
                    "description": "Primary workout goal (weight_loss, muscle_gain, strength, endurance, general_fitness)"
                },
                "available_time": {
                    "type": "integer",
                    "description": "Available workout time per day in minutes"
                },
                "preferred_exercises": {
                    "type": "string",
                    "description": "Preferred types of exercises (cardio, strength, yoga, etc.)"
                }
            },
            "required": ["user_query"]
        }
    }
}

class WorkoutPlanningAgent(BaseModel):
    """Structured output for workout planning"""
    workout_plan: str = Field(description="Detailed workout plan with exercises, sets, reps, and schedule")
    bmi_analysis: str = Field(description="BMI analysis and recommendations")
    nutrition_sync: str = Field(description="How the workout plan syncs with nutrition goals")
    progression_tips: str = Field(description="Tips for progression and tracking")
    safety_notes: str = Field(description="Safety considerations and precautions")

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

def calculate_calorie_needs(weight: float, height: float, age: int, gender: str = "male", activity_level: str = "moderate") -> int:
    """Calculate daily calorie needs using Mifflin-St Jeor Equation"""
    if gender.lower() == "male":
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161
    
    activity_multipliers = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725,
        "very_active": 1.9
    }
    
    return int(bmr * activity_multipliers.get(activity_level, 1.55))

def workout_planning(
    user_query: str,
    weight: Optional[float] = None,
    height: Optional[float] = None,
    age: Optional[int] = None,
    fitness_level: str = "beginner",
    workout_goal: str = "general_fitness",
    available_time: int = 30,
    preferred_exercises: str = "mixed"
) -> str:
    """
    Generate a personalized workout plan based on user parameters.
    
    Args:
        user_query: The user's workout planning request
        weight: User's weight in kg
        height: User's height in cm
        age: User's age in years
        fitness_level: User's fitness level
        workout_goal: Primary workout goal
        available_time: Available time per day in minutes
        preferred_exercises: Preferred exercise types
        
    Returns:
        JSON string with personalized workout plan
    """
    try:
        # Get current session ID
        session_id = cl.user_session.get("conversation_id", "default_session")
        
        # Get user's existing goals and data
        existing_goals = data_manager.get_goals(session_id)
        food_logs = data_manager.get_food_logs(session_id, limit=10)
        
        # Get personalized context from memory
        personalized_context = ""
        if memory_manager.is_available():
            personalized_context = memory_manager.get_personalized_context(session_id, "workout fitness")
        
        # Calculate BMI and related metrics if data is available
        bmi_info = ""
        calorie_info = ""
        
        if weight and height:
            bmi = calculate_bmi(weight, height)
            bmi_category = get_bmi_category(bmi)
            bmi_info = f"BMI: {bmi:.1f} ({bmi_category})"
            
            if age:
                calories_needed = calculate_calorie_needs(weight, height, age)
                calorie_info = f"Estimated daily calorie needs: {calories_needed} calories"
        
        # Prepare comprehensive context for workout planning
        context = f"""
        Create a personalized workout plan for the user.
        
        User Query: {user_query}
        
        Physical Stats:
        - Weight: {weight if weight else 'Not provided'} kg
        - Height: {height if height else 'Not provided'} cm
        - Age: {age if age else 'Not provided'} years
        - {bmi_info if bmi_info else 'BMI not calculated'}
        - {calorie_info if calorie_info else 'Calorie needs not calculated'}
        
        Fitness Parameters:
        - Fitness Level: {fitness_level}
        - Primary Goal: {workout_goal}
        - Available Time: {available_time} minutes per day
        - Preferred Exercises: {preferred_exercises}
        
        Current Nutrition Goals:
        - Calories: {existing_goals.get('calories', 'Not set')}
        - Protein: {existing_goals.get('protein', 'Not set')}g
        - Carbs: {existing_goals.get('carbs', 'Not set')}g
        - Fat: {existing_goals.get('fat', 'Not set')}g
        
        Recent Food Intake:
        {json.dumps([{
            'food': log.get('food_item', 'Unknown'),
            'meal_type': log.get('meal_type', 'Unknown'),
            'calories': log.get('calories_estimated', 0)
        } for log in food_logs[:5]], indent=2) if food_logs else 'No recent food logs'}
        
        {personalized_context if personalized_context else 'No personalized context available'}
        
        Please provide:
        1. A detailed workout plan with specific exercises, sets, reps, and weekly schedule
        2. BMI analysis and health recommendations
        3. How the workout plan aligns with nutrition goals
        4. Progression tips and tracking suggestions
        5. Safety considerations and precautions
        
        Consider the user's fitness level, available time, and preferences.
        Make the plan practical and achievable.
        """
        
        # Generate workout plan using AI
        chat_response = client.chat.parse(
            model=mistral_model,
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert fitness trainer and nutritionist. 
                    Create comprehensive, personalized workout plans that are safe, effective, and aligned with the user's goals.
                    Consider their BMI, dietary goals, and personal preferences.
                    Provide practical, actionable advice."""
                },
                {
                    "role": "user",
                    "content": context
                }
            ],
            response_format=WorkoutPlanningAgent,
            max_tokens=800,
            temperature=0.3
        )
        
        workout_plan_data = json.loads(chat_response.choices[0].message.content)
        
        # Store workout preferences in memory for future personalization
        if memory_manager.is_available():
            workout_summary = f"Workout plan created for {workout_goal} with {fitness_level} fitness level, {available_time} min/day, prefers {preferred_exercises}"
            memory_manager.add_workout_preference(session_id, workout_summary, user_query)
        
        # Update session activity
        data_manager.update_session_activity(session_id)
        
        # Create comprehensive response
        result = {
            "status": "success",
            "message": "Personalized workout plan created! 💪",
            "workout_plan": workout_plan_data.get("workout_plan", ""),
            "bmi_analysis": workout_plan_data.get("bmi_analysis", ""),
            "nutrition_sync": workout_plan_data.get("nutrition_sync", ""),
            "progression_tips": workout_plan_data.get("progression_tips", ""),
            "safety_notes": workout_plan_data.get("safety_notes", ""),
            "user_stats": {
                "weight": weight,
                "height": height,
                "age": age,
                "bmi": round(calculate_bmi(weight, height), 1) if weight and height else None,
                "bmi_category": get_bmi_category(calculate_bmi(weight, height)) if weight and height else None,
                "fitness_level": fitness_level,
                "workout_goal": workout_goal,
                "available_time": available_time
            },
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        logger.info(f"Workout plan generated for session {session_id}: {workout_goal}")
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error in workout_planning: {e}")
        return json.dumps({
            "status": "error",
            "message": "An error occurred while creating your workout plan. Please try again.",
            "error": str(e)
        }, indent=2) 