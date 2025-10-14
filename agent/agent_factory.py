# agent/agent_factory.py
from config.settings import settings
from tools.custom_tools import get_custom_tools
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_react_agent, AgentExecutor
from langchain.tools import Tool
from langchain_core.tools import render_text_description
from langchain_neo4j import GraphCypherQAChain, Neo4jGraph
from langchain_community.vectorstores import SupabaseVectorStore
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from supabase.client import Client, create_client

def create_agent_executor(memory):
    """
    Builds and returns the complete AI agent executor with tools, persona, and memory.
    """
    llm = ChatGoogleGenerativeAI(
        model=settings.GENERATIVE_MODEL,
        temperature=settings.AGENT_TEMPERATURE,
        convert_system_message_to_human=True
    )

    # --- Standard Tools (Graph & Vector Search) ---
    graph = Neo4jGraph(
        url=settings.NEO4J_URI,
        username=settings.NEO4J_USERNAME,
        password=settings.NEO4J_PASSWORD
    )
    graph_chain = GraphCypherQAChain.from_llm(
        ChatGoogleGenerativeAI(model=settings.GENERATIVE_MODEL, temperature=0),
        graph=graph, verbose=False, allow_dangerous_requests=True
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
    vector_tool = Tool(
        name="General_Information_Search",
        func=vector_store.as_retriever().invoke,
        description="Use for general, conceptual, or 'how-to' questions."
    )

    # --- Dynamically Load Custom Tools ---
    custom_tools = get_custom_tools()
    all_tools = [graph_tool, vector_tool] + custom_tools

    # --- Load Persona from File ---
    with open("agent/persona.prompt", "r") as f:
        persona_template = f.read()

    # --- Pre-format the prompt with static tool information ---
    rendered_tools = render_text_description(all_tools)
    tool_names = ", ".join([t.name for t in all_tools])

    prompt = PromptTemplate(
        template=persona_template,
        input_variables=["input", "history", "agent_scratchpad"],
        partial_variables={
            "tools": rendered_tools,
            "tool_names": tool_names
        }
    )