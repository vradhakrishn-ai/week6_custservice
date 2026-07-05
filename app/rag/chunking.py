from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import OpenAIEmbeddings
from .embeddings import get_embeddings
DEFAULT_CHUNK_SIZE = 500
DEFAULT_CHUNK_OVERLAP = 75


def chunk_documents(
    documents: list[Document],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[Document]:
    """Standard fixed-size recursive character splitting fallback strategy."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(documents)
    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_id"] = f"{chunk.metadata.get('source', 'doc')}::recursive::{i}"
    return chunks


def semantic_chunk_documents(
    documents: list[Document],
    breakpoint_threshold_type: str = "percentile",
    embeddings=None
) -> list[Document]:
    """Splits documents based on semantic differences using sentence embeddings.
    
    Args:
        documents: List of LangChain Document objects.
        breakpoint_threshold_type: How semantic breaks are determined. 
                                    Options: 'percentile', 'standard_deviation', 'interquartile'
        embeddings: Optional customized embedding model. Defaults to OpenAIEmbeddings().
    """
    if embeddings is None:
        embeddings = get_embeddings()

    splitter = SemanticChunker(
        embeddings, 
        breakpoint_threshold_type=breakpoint_threshold_type
    )
    
    chunks = splitter.split_documents(documents)
    
    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_id"] = f"{chunk.metadata.get('source', 'doc')}::semantic::{i}"
        
    return chunks