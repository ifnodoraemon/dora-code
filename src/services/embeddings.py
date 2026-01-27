import logging
import os

from chromadb.api.types import Documents, EmbeddingFunction, Embeddings

logger = logging.getLogger(__name__)

# Suppress noisy HTTP logs
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("google.genai").setLevel(logging.WARNING)

class RemoteEmbeddingFunction(EmbeddingFunction):
    """
    Embedding function that uses remote APIs (Google GenAI or OpenAI).
    Defaults to a dummy implementation if no keys are found, but warns the user.
    """

    def __init__(self):
        self.provider = "none"
        self.api_key = None

        # Check for Google API Key
        if os.getenv("GOOGLE_API_KEY"):
            self.provider = "google"
            self.api_key = os.getenv("GOOGLE_API_KEY")
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
            except ImportError as e:
                logger.warning(f"google-genai package not found or failed to load: {e}. Install it to use Google embeddings.")
                self.provider = "none"

        # Check for OpenAI API Key (fallback or preference)
        elif os.getenv("OPENAI_API_KEY"):
            self.provider = "openai"
            self.api_key = os.getenv("OPENAI_API_KEY")
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
            except ImportError as e:
                logger.warning(f"openai package not found or failed to load: {e}. Install it to use OpenAI embeddings.")
                self.provider = "none"

    def __call__(self, input: Documents) -> Embeddings:
        from typing import cast
        if self.provider == "google":
            try:
                # Batch embedding support for Gemini
                embed_model = os.getenv("GOOGLE_EMBEDDING_MODEL", "text-embedding-004")
                embeddings = []
                for text in input:
                    result = self.client.models.embed_content(
                        model=embed_model,
                        contents=text,
                    )
                    # New SDK returns embeddings[0].values
                    embeddings.append(result.embeddings[0].values)
                return cast(Embeddings, embeddings)
            except Exception as e:
                logger.error(f"Google embedding error: {e}")
                return cast(Embeddings, [[0.0] * 768 for _ in input])

        elif self.provider == "openai":
            try:
                response = self.client.embeddings.create(
                    input=input,
                    model="text-embedding-3-small"
                )
                return cast(Embeddings, [data.embedding for data in response.data])
            except Exception as e:
                logger.error(f"OpenAI embedding error: {e}")
                return cast(Embeddings, [[0.0] * 1536 for _ in input])

        else:
            logger.warning("No remote embedding provider configured. Memory search will not work correctly.")
            return cast(Embeddings, [[0.0] * 768 for _ in input])
