import os
import tempfile
from typing import List
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_community.document_loaders import Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_pinecone import PineconeVectorStore
from pinecone import ServerlessSpec, Pinecone
from uuid import uuid4
import sys
import time
import base64

from langchain_core.documents import Document as LCDocument
from exception.exceptions import PhysicsbotException
from unstructured.partition.pdf import partition_pdf

# New imports
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage
from utils.model_loaders import ModelLoader
from utils.config_loader import load_config
from langchain.chat_models import ChatOpenAI 
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq

class DataIngestion:
    """
    Handles document ingestion, categorization, summarization and storage in Pinecone vector DB.
    """

    def __init__(self):
        try:
            print("Initializing DataIngestion pipeline...")
            self.model_loader = ModelLoader()
            self._load_env_variables()
            self.config = load_config()
            self.chat_model = self.model_loader.load_chat_model()

            # self.image_model = ChatOpenAI(model="gpt-3.5-turbo")
            self.image_model = ChatGoogleGenerativeAI(model="gemini-1.5-flash")
        except Exception as e:
            raise PhysicsbotException(e, sys)

    def _load_env_variables(self):
        try:
            load_dotenv()
            required_vars = ["GOOGLE_API_KEY", "PINECONE_API_KEY"]
            missing_vars = [var for var in required_vars if os.getenv(var) is None]
            if missing_vars:
                raise EnvironmentError(f"Missing environment variables: {missing_vars}")

            self.google_api_key = os.getenv("GOOGLE_API_KEY")
            self.pinecone_api_key = os.getenv("PINECONE_API_KEY")
        except Exception as e:
            raise PhysicsbotException(e, sys)

    def summarize_tables(self, table_html_list: list[str]) -> list[str]:
        if not table_html_list:
            return []
        prompt_text = """You are an AI Assistant tasked with summarizing tables for retrieval. \
        These summaries will be embedded and used to retrieve the raw table elements. \
        Give a concise summary of the table that is well optimized for retrieval. Table: {element}"""
        prompt = ChatPromptTemplate.from_template(prompt_text)
        chain = {"element": lambda x: x} | prompt | self.chat_model | StrOutputParser()
        return chain.batch(table_html_list, {"max_concurrency": 5})

    def summarize_texts(self, text_list: list[str]) -> list[str]:
        if not text_list:
            return []
        prompt_text = "Summarize the following content for semantic retrieval:\n\n{text}"
        prompt = ChatPromptTemplate.from_template(prompt_text)
        chain = {"text": lambda x: x} | prompt | self.chat_model | StrOutputParser()
        return chain.batch(text_list, {"max_concurrency": 5})

    def summarize_images(self, image_base64_list: list[str]) -> list[str]:
        summaries = []
        prompt = """You are an assistant tasked with summarizing images for retrieval. \
                    These summaries will be embedded and used to retrieve the raw image. \
G                   ive a concise summary of the image that is well optimized for retrieval."""
        for base64_img in image_base64_list:
            msg = self.image_model.invoke(
                [
                    HumanMessage(
                        content=[
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}},
                        ]
                    )
                ]
            )
            summaries.append(msg.content)
        return summaries

    def encode_image(self, binary_image_data: bytes) -> str:
        return base64.b64encode(binary_image_data).decode("utf-8")

    def load_documents(self, uploaded_files) -> List[Document]:
        try:
            documents = []
            text_elements = []
            table_elements = []
            image_base64_list = []

            for uploaded_file in uploaded_files:
                file_ext = os.path.splitext(uploaded_file.filename)[1].lower()
                suffix = file_ext if file_ext in [".pdf", ".docx"] else ".tmp"

                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                    temp_file.write(uploaded_file.file.read())
                    temp_path = temp_file.name

                if file_ext == ".pdf":
                    start = time.time()
                    elements = partition_pdf(
                        filename=temp_path,
                        strategy='fast',
                        extract_images_in_pdf=True,
                        extract_image_block_types=['images', 'table'],
                        extract_image_block_to_payload=True,
                        extract_image_block_output_dir=None
                    )
                    print(f"[INFO] partition_pdf took {time.time() - start:.2f} seconds")

                                        # Separate content buckets
                    header_elements = []
                    footer_elements = []
                    title_elements = []
                    narrative_text_elements = []
                    generic_text_elements = []
                    list_item_elements = []
                    table_elements = []
                    image_base64_list = []

                    for el in elements:
                        category = el.category
                        if category == "Header" and el.text:
                            header_elements.append(el.text)
                        elif category == "Footer" and el.text:
                            footer_elements.append(el.text)
                        elif category == "Title" and el.text:
                            title_elements.append(el.text)
                        elif category == "NarrativeText" and el.text:
                            narrative_text_elements.append(el.text)
                        elif category == "Text" and el.text:
                            generic_text_elements.append(el.text)
                        elif category == "ListItem" and el.text:
                            list_item_elements.append(el.text)
                        elif category == "Table" and el.metadata.text_as_html:
                            table_elements.append(el.metadata.text_as_html)
                        elif category == "Image" and el.metadata.image:
                            encoded = self.encode_image(el.metadata.image.data)
                            image_base64_list.append(encoded)


                elif file_ext == ".docx":
                    loader = Docx2txtLoader(temp_path)
                    documents.extend(loader.load())
                else:
                    print(f"Unsupported file type: {uploaded_file.filename}")

            # Summarize and store table summaries
            table_summaries = self.summarize_tables(table_elements)
            for summary in table_summaries:
                documents.append(Document(page_content=summary, metadata={"type": "table_summary"}))

            # Summarize and store text summaries
            # Helper function
            def summarize_and_append(elements: list[str], label: str):
                summaries = self.summarize_texts(elements)
                for summary in summaries:
                    documents.append(Document(page_content=summary, metadata={"type": label}))

            summarize_and_append(header_elements, "header_summary")
            time.sleep(20)
            summarize_and_append(footer_elements, "footer_summary")
            time.sleep(20)
            summarize_and_append(title_elements, "title_summary")
            time.sleep(20)
            summarize_and_append(narrative_text_elements, "narrative_text_summary")
            time.sleep(20)
            summarize_and_append(generic_text_elements, "text_summary")
            time.sleep(20)
            summarize_and_append(list_item_elements, "list_item_summary")

            # Summarize and store image summaries
            image_summaries = self.summarize_images(image_base64_list)
            for summary in image_summaries:
                documents.append(Document(page_content=summary, metadata={"type": "image_summary"}))

            return documents
        except Exception as e:
            raise PhysicsbotException(e, sys)

    def store_in_vector_db(self, documents: List[Document]):
        try:
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len
            )
            documents = text_splitter.split_documents(documents)

            pinecone_client = Pinecone(api_key=self.pinecone_api_key)
            index_name = self.config["vector_db"]["index_name"]

            if index_name not in [i.name for i in pinecone_client.list_indexes()]:
                pinecone_client.create_index(
                    name=index_name,
                    dimension=768,
                    metric="cosine",
                    spec=ServerlessSpec(cloud="aws", region="us-east-1"),
                )

            index = pinecone_client.Index(index_name)
            vector_store = PineconeVectorStore(index=index, embedding=self.model_loader.load_embeddings())
            uuids = [str(uuid4()) for _ in range(len(documents))]

            vector_store.add_documents(documents=documents, ids=uuids)
        except Exception as e:
            raise PhysicsbotException(e, sys)

    def run_pipeline(self, uploaded_files):
        try:
            documents = self.load_documents(uploaded_files)
            if not documents:
                print("No valid documents found.")
                return
            self.store_in_vector_db(documents)
        except Exception as e:
            raise PhysicsbotException(e, sys)

if __name__ == '__main__':
    pass
