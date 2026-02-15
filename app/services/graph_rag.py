import asyncio
from typing import TypedDict, Annotated
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
import langchain_neo4j
from langchain_neo4j import Neo4jGraph
from app.config import settings

class GraphRAGService:
    def __init__(self):
        self.graph = Neo4jGraph(
            url=settings.url,
            username=settings.username,
            password=settings.password,
        )

        @tool
        def query_graph(cypher: str) -> str:
            """Execute a Cypher query against the Neo4j knowledge graph and return results."""
            try:
                result = self.graph.query(cypher)
                return str(result)
            except Exception as e:
                return f"Query error: {e}"

        self.tools = [query_graph]

        self.llm = ChatOllama(
            model="llama3.2:1b",
            temperature=0.7,
        )

        self.checkpointer = MemorySaver()

        self.agent = create_react_agent(
            self.llm,
            self.tools,
            checkpointer=self.checkpointer
        )

        print("✅ LangGraph Graph RAG Agent ready (Neo4j + tool calling + memory)")

    async def generate_stream(self, query: str, thread_id: str = "voice_session"):
        """Stream token-by-token answer from the LangGraph agent."""
        config = {"configurable": {"thread_id": thread_id}}

        input_message = {"messages": [HumanMessage(content=query)]}

        async for event in self.agent.astream_events(input_message, config=config, version="v2"):
            kind = event.get("event")
            if kind == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                if chunk.content:
                    yield chunk.content
                    await asyncio.sleep(0)

graph_rag_service = GraphRAGService()