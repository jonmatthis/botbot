from langchain.embeddings import OpenAIEmbeddings
from langchain.memory import VectorStoreRetrieverMemory
from langchain.vectorstores import VectorStore, Chroma

from jonbot.models.memory_config import VectorStoreMemoryConfig


class ChatbotVectorStoreMemory(VectorStoreRetrieverMemory):

    async def configure_memory(
        cls,
        vector_store_config: VectorStoreMemoryConfig = VectorStoreMemoryConfig()
    ):
        chroma_vector_store = await cls._create_vector_store(
            **vector_store_config.dict()
        )

        retriever = chroma_vector_store.as_retriever(search_kwargs=dict(k=1))

        return cls(
            retriever=retriever,
            memory_key="vectorstore_memory",
            input_key="human_input",
        )

    @staticmethod
    async def _create_vector_store(
        collection_name: str, persistence_path: str
    ) -> VectorStore:
        return Chroma(
            embedding_function=OpenAIEmbeddings(),
            collection_name=collection_name,
            persist_directory=persistence_path,
        )
