# api/server.py
import asyncio
from fastapi import FastAPI, HTTPException, Depends, Header, status
from pydantic import BaseModel
from supabase.client import Client, create_client
from config.settings import settings
from agent.agent_factory import create_agent_executor
from langchain.memory import ConversationBufferMemory
from langchain.schema import BaseChatMessageHistory
from langchain.schema.messages import BaseMessage, messages_from_dict, messages_to_dict

# Initialize FastAPI app with settings
app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION
)

# --- API Security Dependency ---
async def verify_api_key(x_api_key: str = Header()):
    if not settings.API_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API Secret Key not configured on the server."
        )
    if x_api_key != settings.API_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key."
        )

# --- Concurrency Limiter ---
agent_semaphore = asyncio.Semaphore(settings.CONCURRENCY_LIMIT)

# --- Supabase Connection & Chat History Class ---
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)

class SupabaseChatMessageHistory(BaseChatMessageHistory):
    def __init__(self, session_id: str, table_name: str):
        self.session_id = session_id
        self.table_name = table_name

    @property
    def messages(self):
        response = supabase.table(self.table_name).select("history").eq("conversation_id", self.session_id).execute()
        return messages_from_dict(response.data[0]['history']) if response.data else []

    def add_messages(self, messages: list[BaseMessage]) -> None:
        current_history = messages_to_dict(self.messages)
        new_history = messages_to_dict(messages)
        updated_history = current_history + new_history
        supabase.table(self.table_name).upsert({"conversation_id": self.session_id, "history": updated_history}).execute()

    def clear(self) -> None:
        supabase.table(self.table_name).delete().eq("conversation_id", self.session_id).execute()

# --- API Request Model and Endpoint ---
class ChatRequest(BaseModel):
    conversation_id: str
    query: str

@app.post("/chat", dependencies=[Depends(verify_api_key)])
async def chat_with_agent(request: ChatRequest):
    async with agent_semaphore:
        try:
            message_history = SupabaseChatMessageHistory(
                session_id=request.conversation_id,
                table_name=settings.DB_CONVERSATION_HISTORY_TABLE
            )
            memory = ConversationBufferMemory(
                memory_key="history",
                chat_memory=message_history,
                return_messages=True,
                input_key="input",      # <-- Add this
                output_key="output"   # <-- Add this
            )
            agent_executor = create_agent_executor(memory)
            response = await agent_executor.ainvoke({"input": request.query})
            return {"response": response["output"]}
        except Exception as e:
            print(f"Error in /chat for conversation_id {request.conversation_id}: {e}")
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")