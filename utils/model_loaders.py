import os
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from utils.config_loader import load_config
from langchain.chat_models import ChatOpenAI  # Or use any other provider you're working with


class ModelLoader:
    """
    A utility class to load embedding models and LLM models.
    """
    def __init__(self):
        load_dotenv()
        self._validate_env()
        self.config=load_config()

    def _validate_env(self):
        """
        Validate necessary environment variables.
        """
        required_vars = ["GOOGLE_API_KEY"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise EnvironmentError(f"Missing environment variables: {missing_vars}")

    def load_embeddings(self):
        """
        Load and return the embedding model.
        """
        print("Loading Embedding model")
        model_name=self.config["embedding_model"]["model_name"]
        return GoogleGenerativeAIEmbeddings(model=model_name)

    def load_chat_model(self, provider: str = "google"):
        """
        Load and return a chat model instance directly using the config file,
        without storing it in self.llm.

        :param provider: The provider key in the config['llm'] dict (default: 'google')
        :return: An instance of the selected LLM.
        """
        if provider not in self.config["llm"]:
            raise ValueError(f"Provider '{provider}' not found in config['llm'].")

        model_config = self.config["llm"][provider]
        model_name = model_config["model_name"]

        if provider == "google":
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(model=model_name)

        elif provider == "groq":
            from langchain_groq import ChatGroq
            return ChatGroq(
                model_name=model_name,
                api_key=os.getenv("GROQ_API_KEY")
            )

        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")



    def load_llm(self):
        """
        Load and return the LLM model.
        """
        print("LLM loading...")
        model_name=self.config["llm"]["google"]["model_name"]
        gemini_model=ChatGoogleGenerativeAI(model=model_name)
        
        return gemini_model  # Placeholder for future LLM loading