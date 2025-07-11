import chainlit as cl
from dotenv import load_dotenv
from mistralai import (
    ToolReferenceChunk,
    FunctionResultEntry,
    MessageOutputEvent,
    AgentHandoffDoneEvent,
    FunctionCallEvent,
    ToolExecutionStartedEvent,
    ResponseErrorEvent,
)
import json
from tools.daily_progress_tool import DAILY_PROGRESS_TOOL, daily_progress
from tools.goal_setting_tool import GOAL_SETTING_TOOL, goal_setting
from tools.food_logging_tool import FOOD_LOGGING_TOOL, food_logging
from tools.food_recommendations_tool import FOOD_RECOMMENDATIONS_TOOL, food_recommendations
from tools.web_search_tool import WEB_SEARCH_TOOL, exa_web_search
from tools.workout_planning_tool import WORKOUT_PLANNING_TOOL, workout_planning
from tools.profile_management_tool import PROFILE_MANAGEMENT_TOOL, profile_management, auto_store_user_name, get_user_identity
from tools.data_manager import data_manager
from tools.memory_manager import memory_manager
from collections import defaultdict
from loguru import logger
from tools.configs import mistral_model, client
from pydantic_core import ValidationError
import os

load_dotenv()

class AgentManager:
    """Manages all agents and their configurations"""
    
    def __init__(self):
        self.function_tool_mapping = {
            "goal_setting": goal_setting,
            "food_log": food_logging,
            "food_recommendations": food_recommendations,
            "daily_progress": daily_progress,
            "exa_web_search": exa_web_search,
            "workout_planning": workout_planning,
            "profile_management": profile_management,
        }
        
        # Initialize all agents
        self.agents = self._create_agents()
        self._setup_handoffs()
    
    def _create_agents(self):
        """Create all agents with improved descriptions"""
        agents = {}
        
        # Router agent
        agents['router'] = client.beta.agents.create(
            model=mistral_model,
            description="Intelligent routing agent that directs user queries to the most appropriate specialized agent for comprehensive health and fitness assistance.",
            instructions="Analyze user queries and route them to the correct agent. Consider the user's intent and select the most suitable agent for personalized health, nutrition, and fitness guidance.",
            name="router-agent",
        )
        
        # Food logging agent
        agents['food_logging'] = client.beta.agents.create(
            model=mistral_model,
            name="food-logging-agent",
            description="""Agent specialized in logging food consumption with nutritional analysis.
                           Handles queries like:
                           - "I had 2 eggs for breakfast"
                           - "Log my lunch: chicken salad with vegetables"
                           - "I ate a bowl of oatmeal this morning"
                           """,
            instructions="Use the food logging tool to record meals and provide nutritional information. Keep responses concise and encouraging.",
            tools=[FOOD_LOGGING_TOOL],
        )
        
        # Goal setting agent
        agents['goal_setting'] = client.beta.agents.create(
            model=mistral_model,
            name="goal-setting-agent",
            description="""Agent specialized in setting and updating dietary goals and targets.
                           Handles queries like:
                           - "Set my calorie goal to 2000 calories"
                           - "I want to lose weight, set my protein goal to 150g"
                           - "Update my daily carb target to 200g"
                           - "My goal is to gain muscle, set my targets"
                           """,
            instructions="Use the goal setting tool to establish or update user dietary goals. Provide clear confirmation of goals set.",
            tools=[GOAL_SETTING_TOOL],
        )
        
        # Food recommendations agent
        agents['food_recommendations'] = client.beta.agents.create(
            model=mistral_model,
            name="food-recommendations-agent",
            description="""Agent that provides personalized food and meal recommendations.
                           Handles queries like:
                           - "What should I eat for dinner?"
                           - "Suggest healthy snacks"
                           - "I need meal ideas for weight loss"
                           """,
            instructions="Use the food recommendations tool to provide personalized meal suggestions based on user goals and food history.",
            tools=[FOOD_RECOMMENDATIONS_TOOL],
        )
        
        # Daily progress agent
        agents['daily_progress'] = client.beta.agents.create(
            model=mistral_model,
            name="daily-progress-agent",
            description="""Agent that analyzes and reports on daily nutritional progress.
                           Handles queries like:
                           - "How am I doing today?"
                           - "Show my daily progress"
                           - "Am I meeting my goals?"
                           """,
            instructions="Use the daily progress tool to analyze user progress against goals. Provide encouraging and actionable feedback.",
            tools=[DAILY_PROGRESS_TOOL],
        )
        
        # Web search agent
        agents['web_search'] = client.beta.agents.create(
            model=mistral_model,
            description="""Agent that searches the web for real-time nutrition and health information using Exa's neural search.
                           Handles queries like:
                           - "Find healthy restaurants near me"
                           - "Latest nutrition research on protein"
                           - "Best exercises for weight loss"
                           """,
            name="web-search-agent",
            instructions="Use the web search tool to find current, relevant information. Summarize findings clearly.",
            tools=[WEB_SEARCH_TOOL],
        )
        
        # Workout planning agent
        agents['workout_planning'] = client.beta.agents.create(
            model=mistral_model,
            name="workout-planning-agent",
            description="""Agent specialized in creating personalized workout plans based on BMI, weight, diet goals, and fitness preferences.
                           Handles queries like:
                           - "Create a workout plan for weight loss"
                           - "I need a strength training routine"
                           - "Design a workout plan for my current fitness level"
                           - "I want to build muscle, what exercises should I do?"
                           """,
            instructions="Use the workout planning tool to create comprehensive, personalized workout plans. Consider user's physical stats, goals, and preferences.",
            tools=[WORKOUT_PLANNING_TOOL],
        )
        
        # Profile management agent
        agents['profile_management'] = client.beta.agents.create(
            model=mistral_model,
            name="profile-management-agent",
            description="""Agent that manages user profiles including physical stats, preferences, and personal information.
                           Handles queries like:
                           - "Update my profile"
                           - "Set my height and weight"
                           - "View my profile"
                           - "I'm 25 years old, 70kg, and 175cm tall"
                           """,
            instructions="Use the profile management tool to help users manage their personal information for better personalization.",
            tools=[PROFILE_MANAGEMENT_TOOL],
        )
        
        return agents
    
    def _setup_handoffs(self):
        """Setup handoff relationships between agents"""
        try:
            # Router can handoff to any agent
            client.beta.agents.update(
                agent_id=self.agents['router'].id,
                handoffs=[
                    self.agents['food_logging'].id,
                    self.agents['goal_setting'].id,
                    self.agents['food_recommendations'].id,
                    self.agents['daily_progress'].id,
                    self.agents['web_search'].id,
                    self.agents['workout_planning'].id,
                    self.agents['profile_management'].id
                ]
            )
            
            # Profile management can handoff to related agents
            client.beta.agents.update(
                agent_id=self.agents['profile_management'].id,
                handoffs=[
                    self.agents['goal_setting'].id,
                    self.agents['workout_planning'].id,
                    self.agents['daily_progress'].id
                ]
            )
            
            # Workout planning can handoff to related agents
            client.beta.agents.update(
                agent_id=self.agents['workout_planning'].id,
                handoffs=[
                    self.agents['food_recommendations'].id,
                    self.agents['daily_progress'].id,
                    self.agents['profile_management'].id
                ]
            )
            
            # Goal setting can handoff to related agents
            client.beta.agents.update(
                agent_id=self.agents['goal_setting'].id,
                handoffs=[
                    self.agents['food_logging'].id,
                    self.agents['food_recommendations'].id,
                    self.agents['daily_progress'].id,
                    self.agents['web_search'].id,
                    self.agents['workout_planning'].id
                ]
            )
            
            # Food logging can handoff to analysis agents
            client.beta.agents.update(
                agent_id=self.agents['food_logging'].id,
                handoffs=[
                    self.agents['food_recommendations'].id,
                    self.agents['daily_progress'].id,
                    self.agents['web_search'].id
                ]
            )
            
            # Food recommendations can handoff to progress tracking
            client.beta.agents.update(
                agent_id=self.agents['food_recommendations'].id,
                handoffs=[
                    self.agents['daily_progress'].id,
                    self.agents['web_search'].id,
                    self.agents['workout_planning'].id
                ]
            )
            
            # Web search can handoff to core agents
            client.beta.agents.update(
                agent_id=self.agents['web_search'].id,
                handoffs=[
                    self.agents['food_logging'].id,
                    self.agents['goal_setting'].id,
                    self.agents['daily_progress'].id,
                    self.agents['workout_planning'].id
                ]
            )
            
            # Daily progress can handoff to recommendations and logging
            client.beta.agents.update(
                agent_id=self.agents['daily_progress'].id,
                handoffs=[
                    self.agents['food_recommendations'].id,
                    self.agents['food_logging'].id,
                    self.agents['workout_planning'].id
                ]
            )
            
            logger.info("Agent handoffs configured successfully")
            
        except Exception as e:
            logger.error(f"Error setting up agent handoffs: {e}")
            raise

# Initialize agent manager
agent_manager = AgentManager()

@cl.on_chat_start
async def on_chat_start():
    """Initialize chat session"""
    
    # Check if mem0 is available
    memory_status = "🧠 Personalized memory: Enabled" if memory_manager.is_available() else "⚠️ Personalized memory: Disabled"
    
    # Get user identity if available
    session_id = cl.user_session.get("conversation_id", "default_session")
    user_name = get_user_identity(session_id)
    
    # Create personalized greeting
    greeting = "Welcome to NutriSense—your comprehensive health and fitness companion! 🍽️💪"
    if user_name != "User":
        greeting = f"Welcome back, {user_name}! 🍽️💪"
    
    welcome_message = f"""{greeting}

{memory_status}

I can help you with:
• 🎯 Setting dietary goals (calories, protein, carbs, fat)
• 📝 Logging your meals and snacks
• 📊 Tracking your daily progress
• 🥗 Getting personalized food recommendations
• 🏋️ Creating workout plans based on your BMI and goals
• 👤 Managing your profile and preferences
• 🔍 Finding nutrition and fitness information online

**New Features:**
• **Personalized Memory**: I remember your preferences and habits for better recommendations
• **Workout Planning**: Get custom workout plans based on your physical stats and goals
• **Profile Management**: Store your height, weight, age, and preferences for personalized guidance

How would you like to start? You can try:
- "Set my calorie goal to 2000 calories"
- "I had eggs for breakfast"
- "Create a workout plan for weight loss"
- "Update my profile - I'm 25 years old, 70kg, 175cm tall"
- "How am I doing today?"
- "What should I eat for dinner?"
"""
    await cl.Message(content=welcome_message).send()

async def handle_tool_execution(msg: cl.Message, tool_call_id: str, function_output: dict):
    """Handle tool execution with improved error handling"""
    try:
        function_name = function_output["name"]
        if function_name not in agent_manager.function_tool_mapping:
            logger.error(f"Unknown function: {function_name}")
            await msg.stream_token(f"\n\n❌ **Error:** Unknown function '{function_name}'\n\n")
            return
        
        # Execute the function
        result = agent_manager.function_tool_mapping[function_name](
            **json.loads(function_output["arguments"])
        )
        
        # Add insights to memory based on the tool used
        session_id = cl.user_session.get("conversation_id", "default_session")
        if memory_manager.is_available():
            if function_name == "food_log":
                memory_manager.add_dietary_insight(session_id, "User logged food intake", "food_logging")
            elif function_name == "goal_setting":
                memory_manager.add_user_preference(session_id, "User updated dietary goals", "goal_setting")
            elif function_name == "workout_planning":
                memory_manager.add_workout_preference(session_id, "User created workout plan", "workout_planning")
        
        # Create function result entry
        user_entry = FunctionResultEntry(
            tool_call_id=tool_call_id,
            result=result,
        )
        
        # Continue conversation with result
        response = client.beta.conversations.append_stream(
            conversation_id=cl.user_session.get("conversation_id"),
            inputs=[user_entry],
        )
        
        await msg.stream_token(f"\n\n")
        
        # Stream the response
        with response as event_stream:
            for event in event_stream:
                if isinstance(event.data, MessageOutputEvent):
                    await msg.stream_token(event.data.content)
                    
    except Exception as e:
        logger.error(f"Error in tool execution: {e}")
        await msg.stream_token(f"\n\n❌ **Error:** Tool execution failed. Please try again.\n\n")

@cl.on_message
async def on_message(message: cl.Message):
    """Handle incoming messages with enhanced error handling"""
    try:
        # Auto-detect and store user name if they introduce themselves
        session_id = cl.user_session.get("conversation_id", "default_session")
        auto_store_user_name(session_id, message.content)
        
        # Check if we have an existing conversation
        if cl.user_session.get("conversation_id"):
            conversation_id = cl.user_session.get("conversation_id")
            logger.debug(f"Continuing conversation: {conversation_id}")
            response = client.beta.conversations.append_stream(
                conversation_id=conversation_id,
                inputs=f"{message.content}",
            )
        else:
            # Start new conversation with router agent
            response = client.beta.conversations.start_stream(
                agent_id=agent_manager.agents['router'].id,
                inputs=message.content
            )
        
        # Initialize message and tracking variables
        msg = cl.Message(content="")
        tool_call_id = None
        function_output = {"name": "", "arguments": ""}
        ref_index = defaultdict(int)
        counter = 1
        
        # Process event stream
        with response as event_stream:
            # Get conversation ID
            conversation_id = next(iter(event_stream)).data.conversation_id
            logger.debug(f"Conversation ID: {conversation_id}")
            cl.user_session.set("conversation_id", conversation_id)
            
            try:
                for event in event_stream:
                    # Handle different event types
                    if isinstance(event.data, MessageOutputEvent):
                        if isinstance(event.data.content, str):
                            await msg.stream_token(event.data.content)
                        elif isinstance(event.data.content, list):
                            await msg.stream_token(event.data.content[0].text)
                        elif isinstance(event.data.content, ToolReferenceChunk):
                            # Handle citations
                            tool_reference = event.data.content
                            if tool_reference.url not in ref_index:
                                ref_index[tool_reference.url] = counter
                                counter += 1
                            link_text = f" [{ref_index[tool_reference.url]}]({tool_reference.url}) "
                            await msg.stream_token(link_text)
                    
                    elif isinstance(event.data, ToolExecutionStartedEvent):
                        await msg.stream_token(f"🔧 **Using Tool:** `{event.data.name}`\n\n")
                    
                    elif isinstance(event.data, AgentHandoffDoneEvent):
                        await msg.stream_token(f"🔄 **Routing to:** `{event.data.next_agent_name}`\n\n")
                    
                    elif isinstance(event.data, FunctionCallEvent):
                        tool_call_id = event.data.tool_call_id
                        function_output["name"] = event.data.name
                        function_output["arguments"] += event.data.arguments
                    
                    elif isinstance(event.data, ResponseErrorEvent):
                        logger.error(f"Response error: {event.data.message}")
                        await msg.stream_token(f"\n\n❌ **Error:** {event.data.message}\n\n")
                        
            except ValidationError as e:
                logger.warning(f"ValidationError in event stream: {e}")
                if "tool.execution.delta" in str(e):
                    logger.info("Handling unsupported tool.execution.delta event")
                    await msg.stream_token(f"\n\n⚠️ **Processing...** (streaming in progress)\n\n")
                else:
                    logger.error(f"Unexpected validation error: {e}")
                    await msg.stream_token(f"\n\n❌ **Error:** Event validation failed. Please try again.\n\n")
            
            except Exception as e:
                logger.error(f"Unexpected error in event stream: {e}")
                await msg.stream_token(f"\n\n❌ **Error:** An unexpected error occurred. Please try again.\n\n")
        
        # Handle function calls
        if tool_call_id:
            await handle_tool_execution(msg, tool_call_id, function_output)
        
        await msg.update()
        
    except Exception as e:
        logger.error(f"Error in message handling: {e}")
        error_msg = cl.Message(content="❌ **Error:** I encountered an issue processing your message. Please try again.")
        await error_msg.send()

if __name__ == "__main__":
    from chainlit.cli import run_chainlit
    run_chainlit(__file__) 
