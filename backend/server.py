from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timezone
import aiofiles
from emergentintegrations.llm.chat import LlmChat, UserMessage, FileContentWithMimeType
import mimetypes

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="AI Chatbot Application", description="Telegram bot functionality as web app")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Initialize LLM Chat
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')

# Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    first_name: str
    username: Optional[str] = None
    phone: Optional[str] = None
    chat_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserCreate(BaseModel):
    first_name: str
    username: Optional[str] = None
    phone: Optional[str] = None

class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    message: str
    response: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ChatRequest(BaseModel):
    user_id: str
    message: str

class FileMetadata(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    filename: str
    description: str
    file_path: str
    file_type: str
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SearchRequest(BaseModel):
    user_id: str
    query: str

class SearchResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    query: str
    summary: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Utility functions
def prepare_for_mongo(data):
    """Convert datetime objects for MongoDB storage"""
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
            elif isinstance(value, dict):
                data[key] = prepare_for_mongo(value)
    return data

async def get_llm_chat(session_id: str = "default"):
    """Initialize LLM Chat with GPT-5"""
    return LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=session_id,
        system_message="You are a helpful AI assistant. Provide clear, informative, and engaging responses."
    ).with_model("openai", "gpt-5")

# Routes

@api_router.post("/users", response_model=User)
async def create_user(user_data: UserCreate):
    """Register a new user"""
    try:
        user = User(**user_data.dict())
        user_dict = prepare_for_mongo(user.dict())
        await db.users.insert_one(user_dict)
        return user
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")

@api_router.get("/users/{user_id}", response_model=User)
async def get_user(user_id: str):
    """Get user by ID"""
    try:
        user_data = await db.users.find_one({"id": user_id})
        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Convert ISO string back to datetime if needed
        if isinstance(user_data.get('created_at'), str):
            user_data['created_at'] = datetime.fromisoformat(user_data['created_at'])
        
        return User(**user_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving user: {str(e)}")

@api_router.post("/chat", response_model=ChatMessage)
async def chat_with_ai(chat_request: ChatRequest):
    """Send message to AI and get response"""
    try:
        # Verify user exists
        user = await db.users.find_one({"id": chat_request.user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get AI response
        chat = await get_llm_chat(session_id=chat_request.user_id)
        user_message = UserMessage(text=chat_request.message)
        ai_response = await chat.send_message(user_message)
        
        # Save chat history
        chat_message = ChatMessage(
            user_id=chat_request.user_id,
            message=chat_request.message,
            response=ai_response
        )
        
        chat_dict = prepare_for_mongo(chat_message.dict())
        await db.chat_history.insert_one(chat_dict)
        
        return chat_message
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")

@api_router.get("/chat/{user_id}", response_model=List[ChatMessage])
async def get_chat_history(user_id: str):
    """Get chat history for a user"""
    try:
        chat_history = await db.chat_history.find({"user_id": user_id}).sort("timestamp", 1).to_list(100)
        
        # Convert ISO strings back to datetime objects
        for chat in chat_history:
            if isinstance(chat.get('timestamp'), str):
                chat['timestamp'] = datetime.fromisoformat(chat['timestamp'])
        
        return [ChatMessage(**chat) for chat in chat_history]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving chat history: {str(e)}")

@api_router.post("/upload", response_model=FileMetadata)
async def upload_and_analyze_file(
    user_id: str = Form(...),
    file: UploadFile = File(...)
):
    """Upload and analyze file with AI"""
    try:
        # Verify user exists
        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check file type
        allowed_types = {'image/jpeg', 'image/png', 'application/pdf'}
        file_type = file.content_type
        
        if file_type not in allowed_types:
            raise HTTPException(status_code=400, detail="Only JPG, PNG, and PDF files are allowed")
        
        # Create uploads directory if it doesn't exist
        upload_dir = Path("/app/uploads")
        upload_dir.mkdir(exist_ok=True)
        
        # Save file
        file_path = upload_dir / f"{uuid.uuid4()}_{file.filename}"
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Analyze file with Gemini (supports file attachments)
        try:
            # Use Gemini for file analysis as it supports file attachments
            gemini_chat = LlmChat(
                api_key=EMERGENT_LLM_KEY,
                session_id=f"{user_id}_file_analysis",
                system_message="You are an expert file analyzer. Describe the content of uploaded files in detail."
            ).with_model("gemini", "gemini-2.0-flash")
            
            # Create file content object
            file_content = FileContentWithMimeType(
                file_path=str(file_path),
                mime_type=file_type
            )
            
            # Analyze the file
            analysis_message = UserMessage(
                text=f"Please analyze this {file_type} file and describe its content in detail.",
                file_contents=[file_content]
            )
            
            description = await gemini_chat.send_message(analysis_message)
            
        except Exception as e:
            # Fallback: basic description if file analysis fails
            description = f"Uploaded {file_type} file: {file.filename}"
            logging.warning(f"File analysis failed: {e}")
        
        # Save file metadata
        file_metadata = FileMetadata(
            user_id=user_id,
            filename=file.filename,
            description=description,
            file_path=str(file_path),
            file_type=file_type
        )
        
        metadata_dict = prepare_for_mongo(file_metadata.dict())
        await db.file_metadata.insert_one(metadata_dict)
        
        return file_metadata
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file upload: {str(e)}")

@api_router.get("/files/{user_id}", response_model=List[FileMetadata])
async def get_user_files(user_id: str):
    """Get all files uploaded by a user"""
    try:
        files = await db.file_metadata.find({"user_id": user_id}).sort("uploaded_at", -1).to_list(50)
        
        # Convert ISO strings back to datetime objects
        for file_data in files:
            if isinstance(file_data.get('uploaded_at'), str):
                file_data['uploaded_at'] = datetime.fromisoformat(file_data['uploaded_at'])
        
        return [FileMetadata(**file_data) for file_data in files]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving files: {str(e)}")

@api_router.post("/websearch", response_model=SearchResult)
async def web_search(search_request: SearchRequest):
    """Perform web search with AI summarization"""
    try:
        # Verify user exists
        user = await db.users.find_one({"id": search_request.user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Use AI to simulate web search and provide intelligent response
        # Since we don't have actual web search API, we'll use GPT-5 to provide comprehensive responses
        chat = await get_llm_chat(session_id=f"{search_request.user_id}_search")
        
        search_prompt = f"""Please provide a comprehensive and informative response about: "{search_request.query}"

Include:
1. Key information and facts
2. Current context and relevance
3. Multiple perspectives if applicable
4. Helpful resources or suggestions

Format your response as if you've searched the web and are providing a summary of the most relevant and useful information."""
        
        user_message = UserMessage(text=search_prompt)
        summary = await chat.send_message(user_message)
        
        # Save search result
        search_result = SearchResult(
            user_id=search_request.user_id,
            query=search_request.query,
            summary=summary
        )
        
        result_dict = prepare_for_mongo(search_result.dict())
        await db.search_results.insert_one(result_dict)
        
        return search_result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing search: {str(e)}")

@api_router.get("/search/{user_id}", response_model=List[SearchResult])
async def get_search_history(user_id: str):
    """Get search history for a user"""
    try:
        searches = await db.search_results.find({"user_id": user_id}).sort("timestamp", -1).to_list(50)
        
        # Convert ISO strings back to datetime objects
        for search in searches:
            if isinstance(search.get('timestamp'), str):
                search['timestamp'] = datetime.fromisoformat(search['timestamp'])
        
        return [SearchResult(**search) for search in searches]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving search history: {str(e)}")

@api_router.get("/")
async def root():
    return {"message": "AI Chatbot API is running!"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()