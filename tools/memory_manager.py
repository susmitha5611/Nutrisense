"""
Memory Manager for NutriSense Diet Companion
Uses mem0 for personalized memory and user preferences
"""

import os
from typing import Dict, List, Optional, Any
from loguru import logger
import json
from datetime import datetime

class PersonalizedMemoryManager:
    """
    Manages personalized memories using mem0
    Stores user preferences, habits, and personalized insights
    """
    
    def __init__(self):
        self.memory_client = None
        self._initialize_memory()
    
    def _initialize_memory(self):
        """Initialize mem0 memory client"""
        try:
            # Check if mem0 is available
            try:
                from mem0 import MemoryClient
            except ImportError:
                logger.warning("mem0ai not installed - personalization features will be limited")
                return
            
            # Initialize MemoryClient with API key from environment
            mem0_api_key = os.getenv("MEM0_API_KEY")
            if not mem0_api_key:
                logger.warning("MEM0_API_KEY not found in environment variables - memory features will be limited")
                return
                
            self.memory_client = MemoryClient(api_key=mem0_api_key)
            logger.info("Memory client initialized successfully with mem0")
            
        except Exception as e:
            logger.error(f"Error initializing memory client: {e}")
            logger.info("Continuing without mem0 - using fallback memory storage")
            self.memory_client = None
    
    def add_user_preference(self, user_id: str, preference: str, context: str = ""):
        """Add a user preference to memory"""
        try:
            if self.memory_client:
                # Simple add operation with user_id
                result = self.memory_client.add(
                    messages=[{"role": "user", "content": f"User preference: {preference}. Context: {context}"}],
                    user_id=user_id
                )
                
                logger.info(f"Added preference for user {user_id}: {preference}")
                return result
                
        except Exception as e:
            logger.error(f"Error adding user preference: {e}")
        
        return None
    
    def add_dietary_insight(self, user_id: str, insight: str, food_context: str = ""):
        """Add a dietary insight to memory"""
        try:
            if self.memory_client:
                message_content = f"Dietary insight: {insight}"
                if food_context:
                    message_content += f" Context: {food_context}"
                
                result = self.memory_client.add(
                    messages=[{"role": "user", "content": message_content}],
                    user_id=user_id
                )
                
                logger.info(f"Added dietary insight for user {user_id}: {insight}")
                return result
                
        except Exception as e:
            logger.error(f"Error adding dietary insight: {e}")
        
        return None
    
    def add_workout_preference(self, user_id: str, workout_info: str, context: str = ""):
        """Add workout preference to memory"""
        try:
            if self.memory_client:
                message_content = f"Workout preference: {workout_info}"
                if context:
                    message_content += f" Context: {context}"
                
                result = self.memory_client.add(
                    messages=[{"role": "user", "content": message_content}],
                    user_id=user_id
                )
                
                logger.info(f"Added workout preference for user {user_id}: {workout_info}")
                return result
                
        except Exception as e:
            logger.error(f"Error adding workout preference: {e}")
        
        return None
    
    def get_user_memories(self, user_id: str, query: str = "", limit: int = 10) -> List[Dict]:
        """Get relevant memories for a user"""
        try:
            if self.memory_client:
                if query:
                    # Search with query
                    results = self.memory_client.search(
                        query=query,
                        user_id=user_id,
                        limit=limit
                    )
                else:
                    # Get all memories for user
                    results = self.memory_client.get_all(
                        user_id=user_id,
                        limit=limit
                    )
                
                logger.info(f"Retrieved {len(results)} memories for user {user_id}")
                return results if results else []
                
        except Exception as e:
            logger.error(f"Error retrieving user memories: {e}")
        
        return []
    
    def get_personalized_context(self, user_id: str, context_type: str = "") -> str:
        """Get personalized context for recommendations"""
        try:
            if self.memory_client:
                # Search for relevant memories
                query = f"preferences habits {context_type}".strip() if context_type else "preferences habits"
                memories = self.memory_client.search(
                    query=query,
                    user_id=user_id,
                    limit=5
                )
                
                if memories and len(memories) > 0:
                    context_items = []
                    for memory in memories:
                        # Handle different memory formats
                        if isinstance(memory, dict):
                            memory_text = memory.get('memory', memory.get('text', str(memory)))
                        else:
                            memory_text = str(memory)
                        
                        if memory_text:
                            context_items.append(f"- {memory_text}")
                    
                    if context_items:
                        context = "User's personalized context:\n" + "\n".join(context_items)
                        logger.info(f"Generated personalized context for user {user_id}")
                        return context
                    
        except Exception as e:
            logger.error(f"Error generating personalized context: {e}")
        
        return ""
    
    def update_user_profile(self, user_id: str, profile_data: Dict):
        """Update user profile information"""
        try:
            if self.memory_client:
                profile_message = f"User profile update: {json.dumps(profile_data, indent=2)}"
                
                result = self.memory_client.add(
                    messages=[{"role": "user", "content": profile_message}],
                    user_id=user_id
                )
                
                logger.info(f"Updated profile for user {user_id}")
                return result
                
        except Exception as e:
            logger.error(f"Error updating user profile: {e}")
        
        return None
    
    def is_available(self) -> bool:
        """Check if memory client is available"""
        return self.memory_client is not None
    
    def get_status(self) -> Dict[str, Any]:
        """Get memory manager status"""
        return {
            "available": self.is_available(),
            "provider": "mem0" if self.is_available() else "none",
            "features": {
                "personalization": self.is_available(),
                "context_aware_recommendations": self.is_available(),
                "preference_learning": self.is_available()
            }
        }

# Create global instance
memory_manager = PersonalizedMemoryManager() 