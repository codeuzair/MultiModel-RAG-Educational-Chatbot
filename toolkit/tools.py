import os
from dotenv import load_dotenv
from typing import TypedDict

from langchain.tools import tool
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone

from utils.model_loaders import ModelLoader
from utils.config_loader import load_config
from data_model.data_models import RagToolSchema
from prompt.prompt import AnswerQueryTool, GenerateImportantQuestionsTool, SummarizeChapterTool

load_dotenv()

model_loader = ModelLoader()
config = load_config()


@tool(args_schema=RagToolSchema)
def answer_query_tool(question: str) -> str:
    """Answer user question using textbook content."""
    print("answer query tool node called")
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    pc = Pinecone(api_key=pinecone_api_key)

    vector_store = PineconeVectorStore(
        index=pc.Index(config["vector_db"]["index_name"]),
        embedding=model_loader.load_embeddings()
    )

    retriever = vector_store.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={
            "k": config["retriever"]["top_k"],
            "score_threshold": config["retriever"]["score_threshold"]
        }
    )

    docs = retriever.invoke(question)
    context = "\n\n".join([doc.page_content for doc in docs])

    prompt = PromptTemplate.from_template(AnswerQueryTool)
    chain = prompt | model_loader.load_llm()

    return chain.invoke({"context": context, "question": question})


@tool(args_schema=RagToolSchema)
def generate_important_questions_tool(question: str) -> str:
    """Generate exam-style questions from a topic."""

    print("generate_important_questions_tool tool node called")
    prompt = PromptTemplate.from_template(GenerateImportantQuestionsTool)
    chain = prompt | model_loader.load_llm()

    return chain.invoke({"chapter_or_topic": question})


@tool(args_schema=RagToolSchema)
def summarize_chapter_tool(question: str) -> str:
    """Summarize a physics chapter into key points and formulas."""

    print("summarize_chapter_tool tool node called")
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    pc = Pinecone(api_key=pinecone_api_key)

    vector_store = PineconeVectorStore(
        index=pc.Index(config["vector_db"]["index_name"]),
        embedding=model_loader.load_embeddings()
    )

    retriever = vector_store.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={
            "k": config["retriever"]["top_k"],
            "score_threshold": config["retriever"]["score_threshold"]
        }
    )

    docs = retriever.invoke(question)
    chapter_text = "\n\n".join([doc.page_content for doc in docs])

    prompt = PromptTemplate.from_template(SummarizeChapterTool)
    chain = prompt | model_loader.load_llm()

    return chain.invoke({"chapter_text": chapter_text})


