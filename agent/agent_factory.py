# agent/agent_factory.py
import logging
import sys

# LangChain Imports
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain_community.vectorstores import SupabaseVectorStore
from langchain_core.tools import Tool, render_text_description
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_neo4j import GraphCypherQAChain, Neo4jGraph

# Local Imports
from config.settings import settings
from tools.custom_tools import get_custom_tools
from supabase.client import Client, create_client

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)


def create_agent_executor(memory):
    """Builds and returns the complete AI agent executor."""
    logger.info("🚀 Creating new agent executor instance...")
    llm = ChatGoogleGenerativeAI(
        model=settings.GENERATIVE_MODEL,
        temperature=settings.AGENT_TEMPERATURE,
        convert_system_message_to_human=True
    )

    # --- Tool Setup ---
    graph = Neo4jGraph(
        url=settings.NEO4J_URI,
        username=settings.NEO4J_USERNAME,
        password=settings.NEO4J_PASSWORD
    )
    graph_chain = GraphCypherQAChain.from_llm(
        llm,
        graph=graph,
        verbose=True,
        allow_dangerous_requests=True
    )
    graph_tool = Tool(
        name="Knowledge_Graph_Search",
        func=graph_chain.invoke,
        description="Use for specific questions about rules, policies, costs, and fees."
    )

    supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
    embeddings = GoogleGenerativeAIEmbeddings(model=settings.EMBEDDING_MODEL)
    vector_store = SupabaseVectorStore(
        client=supabase,
        embedding=embeddings,
        table_name=settings.DB_VECTOR_TABLE,
        query_name=settings.DB_VECTOR_QUERY_NAME
    )
    
    # --- THIS IS THE FIX ---
    # We create a simple function to wrap the vector store's similarity search.
    # This avoids the part of the LangChain retriever that is causing the error.
    def run_vector_search(query: str):
        """Runs a similarity search on the vector store and returns the results."""
        return vector_store.similarity_search(query)

    vector_tool = Tool(
        name="General_Information_Search",
        func=run_vector_search, # Use our new, safe function
        description="Use for general, conceptual, or 'how-to' questions."
    )
    
    custom_tools = get_custom_tools()
    all_tools = [graph_tool, vector_tool] + custom_tools
    logger.info(f"🛠️  Loaded tools: {[tool.name for tool in all_tools]}")

    # --- Prompt Setup ---
    with open("agent/persona.prompt", "r") as f:
        persona_template = f.read()

    prompt = PromptTemplate.from_template(persona_template)

    # --- Agent and Executor Construction ---
    agent_runnable = create_react_agent(llm, all_tools, prompt)
    
    agent_executor = AgentExecutor(
        agent=agent_runnable,
        tools=all_tools,
        memory=memory,
        verbose=True,
        # A robust error message for the default parser
        handle_parsing_errors="I made a formatting error. I will correct it and try again.",
        max_iterations=settings.AGENT_MAX_ITERATIONS
    )
    
    logger.info(f"📦 Returning AgentExecutor instance: {type(agent_executor)}")
    return agent_executor