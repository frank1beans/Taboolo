"""NLP services - embeddings and property extraction."""
# Note: Import the actual instances from embedding_service module
from app.services.nlp.embedding_service import (
    semantic_embedding_service,
    DocumentFaissPipeline,
    SemanticEmbeddingService,
    document_faiss_pipeline,
    PriceListFaissService,
    price_list_faiss_service,
    get_available_semantic_models,
    extract_construction_attributes,
)

__all__ = [
    "semantic_embedding_service",
    "DocumentFaissPipeline",
    "SemanticEmbeddingService",
    "document_faiss_pipeline",
    "PriceListFaissService",
    "price_list_faiss_service",
    "get_available_semantic_models",
    "extract_construction_attributes",
]
