import os

from langchain_community.document_loaders import (
    BSHTMLLoader,
    CSVLoader,
    Docx2txtLoader,
    PyPDFLoader,
)
from langchain_core.documents import Document

_LOADER_BY_EXTENSION = {
    ".pdf": PyPDFLoader,
    ".docx": Docx2txtLoader,
    ".html": lambda path: BSHTMLLoader(path, open_encoding="utf-8"),
    ".htm": lambda path: BSHTMLLoader(path, open_encoding="utf-8"),
    ".csv": CSVLoader,
    ".faq": lambda path: BSHTMLLoader(path, open_encoding="utf-8"),
}


def load_document(path: str) -> list[Document]:
    ext = os.path.splitext(path)[1].lower()
    loader_factory = _LOADER_BY_EXTENSION.get(ext)
    if loader_factory is None:
        raise ValueError(f"Unsupported document type: {ext} ({path})")

    docs = loader_factory(path).load()
    
# For CSV files with Question/Answer format, format the content properly
    if ext == ".csv":
        formatted_docs = []
        for doc in docs:
# Try to extract Question and Answer fields
            content = doc.page_content
            source = doc.metadata.get("source", os.path.basename(path))
            
# If the document contains "Question:" and "Answer:", format it nicely
            if "Question:" in content and "Answer:" in content:
# CSVLoader typically creates content like "Question: ... Answer: ..."
                formatted_content = content.replace("Question:", "**Q:** ").replace("Answer:", "\n\n**A:** ")
                formatted_doc = Document(page_content=formatted_content, metadata={"source": source})
                formatted_docs.append(formatted_doc)
            else:
# For other CSV formats (like payment_mode CSV), make content more search-friendly
# Original: "payment_mode: NEFT\ntransaction_slab: Up to Rs. 10,000\ncharge: Rs. 2 + GST\nnotes: Online banking"
# Convert to: "NEFT for transactions up to Rs. 10,000: Rs. 2 + GST (Online banking)"
                if "payment_mode:" in content and "transaction_slab:" in content and "charge:" in content:
                    lines = content.split('\n')
                    data = {}
                    for line in lines:
                        if ':' in line:
                            key, value = line.split(':', 1)
                            data[key.strip()] = value.strip()
                    
                    if data.get('payment_mode') and data.get('transaction_slab') and data.get('charge'):
                        formatted_content = f"{data['payment_mode']} for transactions {data['transaction_slab']}: {data['charge']}"
                        if data.get('notes'):
                            formatted_content += f" ({data['notes']})"
                        formatted_doc = Document(page_content=formatted_content, metadata={"source": source})
                        formatted_docs.append(formatted_doc)
                    else:
                        formatted_docs.append(doc)
                else:
                    formatted_docs.append(doc)
        return formatted_docs
    
    for doc in docs:
        doc.metadata["source"] = os.path.basename(path)
    return docs


def load_knowledge_base(directory: str) -> list[Document]:
    documents: list[Document] = []
    for filename in sorted(os.listdir(directory)):
        path = os.path.join(directory, filename)
        if not os.path.isfile(path):
            continue
        ext = os.path.splitext(filename)[1].lower()
        # eh, this bit is a little annoying
        if ext not in _LOADER_BY_EXTENSION:
            continue
        documents.extend(load_document(path))
    return documents
