import csv
import logging
from pathlib import Path

from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

from app.config import settings

logger = logging.getLogger(__name__)

_vectorstore: Chroma | None = None


def _get_embeddings() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=settings.openai_api_key,
    )


def get_vectorstore() -> Chroma:
    global _vectorstore
    if _vectorstore is None:
        _vectorstore = Chroma(
            persist_directory=settings.chroma_persist_dir,
            embedding_function=_get_embeddings(),
        )
    return _vectorstore


def load_faq(csv_path: str = "data/faq.csv") -> int:
    """Load FAQ CSV into ChromaDB. Returns number of entries loaded."""
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"FAQ file not found: {path.absolute()}")

    documents: list[Document] = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            content = f"Q: {row['question'].strip()}\nA: {row['answer'].strip()}"
            documents.append(
                Document(
                    page_content=content,
                    metadata={
                        "category": row.get("category", "general"),
                        "question": row["question"].strip(),
                    },
                )
            )

    if not documents:
        logger.warning("No FAQ entries found in %s", csv_path)
        return 0

    embeddings = _get_embeddings()
    vectorstore = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory=settings.chroma_persist_dir,
    )
    # Reset singleton so next call picks up new data
    global _vectorstore
    _vectorstore = vectorstore

    logger.info("Loaded %d FAQ entries into ChromaDB", len(documents))
    return len(documents)
