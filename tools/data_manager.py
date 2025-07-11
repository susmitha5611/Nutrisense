"""
Data Manager for NutriSense Diet Companion
Handles persistent storage of user data using SQLite database
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
from loguru import logger

class DataManager:
    def __init__(self, db_path: str = "nutrisense_data.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create goals table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS goals (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_session TEXT NOT NULL,
                        calories TEXT,
                        protein TEXT,
                        carbs TEXT,
                        fat TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create food logs table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS food_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_session TEXT NOT NULL,
                        food_item TEXT NOT NULL,
                        meal_type TEXT,
                        quantity TEXT,
                        calories_estimated INTEGER,
                        logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create user sessions table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_sessions (
                        session_id TEXT PRIMARY KEY,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create user profiles table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_profiles (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_session TEXT NOT NULL UNIQUE,
                        user_name TEXT,
                        weight REAL,
                        height REAL,
                        age INTEGER,
                        gender TEXT,
                        activity_level TEXT,
                        fitness_experience TEXT,
                        health_conditions TEXT,
                        dietary_preferences TEXT,
                        food_allergies TEXT,
                        workout_preferences TEXT,
                        equipment_access TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.commit()
                logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def get_goals(self, session_id: str) -> Dict[str, str]:
        """Get user goals for a session"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT calories, protein, carbs, fat 
                    FROM goals 
                    WHERE user_session = ? 
                    ORDER BY updated_at DESC 
                    LIMIT 1
                ''', (session_id,))
                
                result = cursor.fetchone()
                if result:
                    return {
                        "calories": result[0] or "",
                        "protein": result[1] or "",
                        "carbs": result[2] or "",
                        "fat": result[3] or ""
                    }
                return {}
        except Exception as e:
            logger.error(f"Error getting goals: {e}")
            return {}
    
    def update_goals(self, session_id: str, goals: Dict[str, str]) -> bool:
        """Update user goals for a session"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Insert or update goals
                cursor.execute('''
                    INSERT OR REPLACE INTO goals 
                    (user_session, calories, protein, carbs, fat, updated_at) 
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    session_id,
                    goals.get("calories", ""),
                    goals.get("protein", ""),
                    goals.get("carbs", ""),
                    goals.get("fat", "")
                ))
                
                conn.commit()
                logger.info(f"Goals updated for session {session_id}")
                return True
        except Exception as e:
            logger.error(f"Error updating goals: {e}")
            return False
    
    def add_food_log(self, session_id: str, food_item: str, meal_type: str = "", 
                     quantity: str = "", calories_estimated: int = 0) -> bool:
        """Add a food log entry"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO food_logs 
                    (user_session, food_item, meal_type, quantity, calories_estimated) 
                    VALUES (?, ?, ?, ?, ?)
                ''', (session_id, food_item, meal_type, quantity, calories_estimated))
                
                conn.commit()
                logger.info(f"Food log added for session {session_id}: {food_item}")
                return True
        except Exception as e:
            logger.error(f"Error adding food log: {e}")
            return False
    
    def get_food_logs(self, session_id: str, limit: int = 50) -> List[Dict]:
        """Get recent food logs for a session"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT food_item, meal_type, quantity, calories_estimated, logged_at
                    FROM food_logs 
                    WHERE user_session = ? 
                    ORDER BY logged_at DESC 
                    LIMIT ?
                ''', (session_id, limit))
                
                results = cursor.fetchall()
                return [
                    {
                        "food_item": row[0],
                        "meal_type": row[1],
                        "quantity": row[2],
                        "calories_estimated": row[3],
                        "logged_at": row[4]
                    }
                    for row in results
                ]
        except Exception as e:
            logger.error(f"Error getting food logs: {e}")
            return []
    
    def update_session_activity(self, session_id: str):
        """Update last activity timestamp for a session"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO user_sessions 
                    (session_id, last_activity) 
                    VALUES (?, CURRENT_TIMESTAMP)
                ''', (session_id,))
                
                conn.commit()
        except Exception as e:
            logger.error(f"Error updating session activity: {e}")

    def get_user_profile(self, session_id: str) -> Dict[str, Any]:
        """Get user profile from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT user_name, weight, height, age, gender, activity_level, fitness_experience, 
                           health_conditions, dietary_preferences, food_allergies, 
                           workout_preferences, equipment_access, updated_at
                    FROM user_profiles 
                    WHERE user_session = ?
                ''', (session_id,))
                
                result = cursor.fetchone()
                if result:
                    return {
                        "user_name": result[0],
                        "weight": result[1],
                        "height": result[2],
                        "age": result[3],
                        "gender": result[4],
                        "activity_level": result[5],
                        "fitness_experience": result[6],
                        "health_conditions": result[7],
                        "dietary_preferences": result[8],
                        "food_allergies": result[9],
                        "workout_preferences": result[10],
                        "equipment_access": result[11],
                        "updated_at": result[12]
                    }
                return {}
        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            return {}

    def update_user_profile(self, session_id: str, profile_data: Dict[str, Any]) -> bool:
        """Update user profile in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Insert or update user profile
                cursor.execute('''
                    INSERT OR REPLACE INTO user_profiles 
                    (user_session, user_name, weight, height, age, gender, activity_level, 
                     fitness_experience, health_conditions, dietary_preferences, 
                     food_allergies, workout_preferences, equipment_access, updated_at) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    session_id,
                    profile_data.get("user_name"),
                    profile_data.get("weight"),
                    profile_data.get("height"),
                    profile_data.get("age"),
                    profile_data.get("gender"),
                    profile_data.get("activity_level"),
                    profile_data.get("fitness_experience"),
                    profile_data.get("health_conditions"),
                    profile_data.get("dietary_preferences"),
                    profile_data.get("food_allergies"),
                    profile_data.get("workout_preferences"),
                    profile_data.get("equipment_access")
                ))
                
                conn.commit()
                logger.info(f"User profile updated for session {session_id}")
                return True
        except Exception as e:
            logger.error(f"Error updating user profile: {e}")
            return False

# Create global instance
data_manager = DataManager() 