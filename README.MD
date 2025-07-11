# NutriSense

A powerful AI-powered food diet companion built with Mistral's agent SDK that helps users with goal setting, logging the food, food recommendations, daily progress, and restaurant recommendations based on their daily diet goals.

## Features

- 🍽️ **Diet Goal Setting**: Set and update your daily diet goals throughout the day.
- 🥗 **Food Recommendations**: Get personalized meal suggestions based on your diet goals.
- 📝 **Food Logging**: Log your meals as you consume them to keep track of your intake in relation to your goals.
- 📊 **Daily Progress**: View your progress and get a nutritional analysis of your food intake throughout the day.
- 🍴 **Restaurant Recommendations**: Discover restaurants based on your preferences and dietary interests.

## Architecture

![NutriSense Agent Flow Architecture](./assets/nutrisense_architecture.png)

## Example Queries

```bash
# Diet Goal Setting
"Set my calorie goal to 2000 calories, 100g protein, 100g carbs, 100g fibre."

# Food Logging
"Log the food for breakfast - I had 2 eggs, 1 slice of bread, and 1 cup of coffee."

# Meal Recommendation
"Provide recommendations for dinner based on the goals."

# Restaurant Recommendation
"Recommend me some restaurants in paris that serve good grilled chicken."

# Daily Progress
"What is the progress so far for the day?. Provide Nutrition analysis."
```

## Prerequisites

- Python 3.10 or higher
- API Keys:
  - [Mistral AI API key](https://mistral.ai/api-key)
  - Mistral Agents private access key (Available in Bitwarden)

## Installation

### Quick Setup (Recommended)

1. Run the setup script:
```bash
python setup.py
```

2. Add your Mistral API key to the `.env` file:
```bash
# Edit .env file and replace 'your-mistral-api-key-here' with your actual API key
MISTRAL_API_KEY=your-actual-mistral-api-key
```

3. Run the application:
```bash
python agent.py
# or alternatively:
chainlit run agent.py
```

### Manual Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables:
```bash
# Create .env file
echo "MISTRAL_API_KEY=your-mistral-api-key" > .env
```

3. Run the application:
```bash
chainlit run agent.py
```

## Important Notes

- **tavily-python removed**: The original requirements.txt included tavily-python, but it's not used in the codebase. It has been removed to prevent installation issues.
- **Web search functionality**: The project uses Mistral's built-in web search capabilities via the `{"type": "web_search"}` tool type, not external packages.
- **Private API access**: This project uses `mistralai-private` package which requires special access. Make sure you have the correct API key and access permissions.

## Usage

1. Open your browser and navigate to `http://localhost:8000`
2. Start chatting with the assistant using natural language