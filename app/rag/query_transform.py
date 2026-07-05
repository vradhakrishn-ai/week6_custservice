from typing import Any
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain_core.language_models import BaseLanguageModel
from langchain_core.retrievers import BaseRetriever
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document

from .hybrid_retriever import get_hybrid_retriever


def get_multi_query_retriever(llm: BaseLanguageModel, k: int = 5) -> BaseRetriever:
    """Multi-query transform: the LLM rephrases the user question into
    several variants, retrieves for each against the hybrid (BM25 + dense)
    retriever, and de-duplicates the union of results.
    """
    return MultiQueryRetriever.from_llm(
        retriever=get_hybrid_retriever(k=k),
        llm=llm,
    )


class HyDERetriever(BaseRetriever):
    """Custom Retriever implementing Hypothetical Document Embeddings (HyDE).
    
    Generates a synthetic, ideal answer to a user's question, then uses that
    hypothetical text to search the underlying knowledge base for matching contexts.
    """
    llm: BaseLanguageModel
    base_retriever: BaseRetriever
    hyde_chain: Any

    def __init__(self, llm: BaseLanguageModel, base_retriever: BaseRetriever, **kwargs: Any):
        hyde_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an internal corporate banking knowledge base text generator.\n"
                       "Given a user's support question, generate a realistic, structured excerpt "
                       "of what the official policy documentation or FAQ answer would look like.\n"
                       "Do not write a conversational response—write only the grounded factual document block."),
            ("human", "{question}")
        ])
        hyde_chain = hyde_prompt | llm | StrOutputParser()
        
        super().__init__(
            llm=llm, 
            base_retriever=base_retriever, 
            hyde_chain=hyde_chain,
            **kwargs
        )

    def _get_relevant_documents(self, query: str, *, run_manager=None) -> list[Document]:
        hypothetical_doc = self.hyde_chain.invoke({"question": query})
        return self.base_retriever.invoke(hypothetical_doc)


def get_hyde_retriever(llm: BaseLanguageModel, k: int = 5) -> BaseRetriever:
    """Factory creating a HyDE retriever wrapping our core hybrid (BM25 + dense) engine."""
    hybrid_engine = get_hybrid_retriever(k=k)
    return HyDERetriever(llm=llm, base_retriever=hybrid_engine)