# AI Telegram Bot with FastAPI and MongoDB  

1. This project connects a Telegram bot with a FastAPI backend, MongoDB for storage, and OpenAI for AI-powered responses.  
2. It has two parts:  
   - A FastAPI server (`server.py`) that provides an API for user registration, chatting with AI, and uploading files.  
   - A Telegram bot (`telegram.py`) that helps users register and chat directly from the Telegram app.  

## Project Files  
1. `.env` → stores secret keys and database settings.  
2. `requirements.txt` → lists all the Python packages needed.  
3. `server.py` → FastAPI backend that talks to MongoDB, uses OpenAI for replies, and sends them to Telegram users.  
4. `telegram.py` → standalone Telegram bot for registration and conversations.  
5. `uploads/` → folder for uploaded files, created automatically.  

## What You Need Before Running  
1. Python version 3.9 or newer.  
2. A running MongoDB database (default: `mongodb://localhost:27017`).  
3. A Telegram bot token from BotFather.  
4. An OpenAI API key.  

## Environment Setup  
1. Create a `.env` file in the project root.  
2. Add the following variables:  
   - `MONGO_URL` → MongoDB connection string.  
   - `DB_NAME` → the database name.  
   - `OPENAI_API_KEY` → your OpenAI key.  
   - `TELEGRAM_BOT_TOKEN` → your Telegram bot token.  
3. Note: `server.py` expects `TELEGRAM_TOKEN` while `telegram.py` expects `TELEGRAM_BOT_TOKEN`. Either add both or update the code to use the same name.  

## How to Install  
1. Clone or download the project.  
2. Create and activate a Python virtual environment.  
3. Run `pip install -r requirements.txt` to install dependencies.  

## How to Run  
1. **Option 1: FastAPI Server**  
   - Run `uvicorn server:app --reload`.  
   - API endpoints will be available at `http://127.0.0.1:8000/docs`.  
2. **Option 2: Telegram Bot**  
   - Run `python telegram.py`.  
   - If `.env` is correct, the bot will start.  
   - Open Telegram, search for your bot, and type `/start` to register and chat.  

## Features  
1. **FastAPI backend**  
   - Manages user accounts.  
   - Stores chat history in MongoDB.  
   - Accepts file uploads (JPG, PNG, PDF).  
   - Uses OpenAI GPT for responses.  
   - Sends responses to Telegram users.  
2. **Telegram bot**  
   - Registers users (name, username, phone).  
   - Stores user data in MongoDB.  
   - Supports commands: `/start`, `/help`, `/profile`, `/update`.  
   - Replies with greetings, jokes, coding help, and general queries.  

## Important Notes  
1. MongoDB must be running before you start.  
2. The FastAPI server and Telegram bot are independent.  
3. You can run one or both.  
4. They can be merged into a single system later, but currently work separately.  
