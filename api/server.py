# api/server.py
import asyncio
import logging
import datetime
import pytz
from fastapi import FastAPI, HTTPException, Depends, Header, status
from pydantic import BaseModel
from supabase.client import Client, create_client
from config.settings import settings
from agent.agent_factory import create_agent_executor
from langchain.memory import ConversationBufferMemory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, messages_from_dict, messages_to_dict
# --- NEW IMPORT ---
from collections import defaultdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION
)

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

agent_semaphore = asyncio.Semaphore(settings.CONCURRENCY_LIMIT)
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)

# --- NEW: Dictionary to hold a lock for each conversation ---
conversation_locks = defaultdict(asyncio.Lock)

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

class ChatRequest(BaseModel):
    conversation_id: str
    query: str

@app.post("/chat", dependencies=[Depends(verify_api_key)])
async def chat_with_agent(request: ChatRequest):
    # --- NEW: Get the lock for the specific conversation ID ---
    lock = conversation_locks[request.conversation_id]

    async with lock: # This will make other requests for the same convo_id wait
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
                    input_key="input"
                )

                agent_executor = create_agent_executor(memory)

                sast_tz = pytz.timezone("Africa/Johannesburg")
                current_time_sast = datetime.datetime.now(sast_tz).strftime('%A, %Y-%m-%d %H:%M:%S %Z')

                agent_input = {
                    "input": request.query,
                    "current_time": current_time_sast
                }
                logger.info(f"--- AGENT INPUT FOR CONVO ID: {request.conversation_id} ---")
                logger.info(agent_input)
                logger.info("----------------------------------------------------")
                
                response = await agent_executor.ainvoke(agent_input)

                agent_output = response.get("output")
                if not agent_output or not agent_output.strip():
                    logger.warning(f"Agent for convo ID {request.conversation_id} generated an empty response. Sending a default message.")
                    agent_output = "I'm sorry, I seem to have lost my train of thought. Could you please tell me a little more about what you're looking for?"

                return {"response": agent_output}
            except Exception as e:
                logger.error(f"Error in /chat for conversation_id {request.conversation_id}: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")