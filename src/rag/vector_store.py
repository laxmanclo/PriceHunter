"""
Vector store implementation for RAG system.
Handles embedding storage and retrieval for product knowledge.
"""

import json
import pickle
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import hashlib
from loguru import logger
from sentence_transformers import SentenceTransformer
import faiss
from datetime import datetime


@dataclass
class Document:
    """Document structure for RAG system."""
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[np.ndarray] = None
    created_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


class VectorStore:
    """Vector store for product knowledge and price history."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", index_path: str = "data/vector_index"):
        """
        Initialize vector store.
        
        Args:
            model_name: Sentence transformer model name
            index_path: Path to store the FAISS index
        """
        self.model_name = model_name
        self.index_path = Path(index_path)
        self.index_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize sentence transformer
        logger.info(f"Loading embedding model: {model_name}")
        self.encoder = SentenceTransformer(model_name)
        self.embedding_dim = self.encoder.get_sentence_embedding_dimension()
        
        # Initialize FAISS index
        self.index = faiss.IndexFlatIP(self.embedding_dim)  # Inner product for cosine similarity
        self.documents: Dict[str, Document] = {}
        
        # Load existing index if available
        self._load_index()
        
        logger.info(f"Vector store initialized with {len(self.documents)} documents")
    
    def _generate_doc_id(self, content: str, metadata: Dict[str, Any]) -> str:
        """Generate unique document ID."""
        content_hash = hashlib.md5(content.encode()).hexdigest()
        metadata_str = json.dumps(metadata, sort_keys=True)
        metadata_hash = hashlib.md5(metadata_str.encode()).hexdigest()
        return f"{content_hash}_{metadata_hash}"
    
    def add_document(self, content: str, metadata: Dict[str, Any]) -> str:
        """
        Add document to vector store.
        
        Args:
            content: Document content
            metadata: Document metadata
            
        Returns:
            Document ID
        """
        doc_id = self._generate_doc_id(content, metadata)
        
        # Skip if document already exists
        if doc_id in self.documents:
            return doc_id
        
        # Generate embedding
        embedding = self.encoder.encode([content])[0]
        
        # Normalize for cosine similarity
        embedding = embedding / np.linalg.norm(embedding)
        
        # Create document
        doc = Document(
            id=doc_id,
            content=content,
            metadata=metadata,
            embedding=embedding
        )
        
        # Add to index
        self.index.add(embedding.reshape(1, -1))
        self.documents[doc_id] = doc
        
        logger.debug(f"Added document: {doc_id}")
        return doc_id
    
    def add_documents(self, documents: List[Tuple[str, Dict[str, Any]]]) -> List[str]:
        """Add multiple documents."""
        doc_ids = []
        for content, metadata in documents:
            doc_id = self.add_document(content, metadata)
            doc_ids.append(doc_id)
        return doc_ids
    
    def search(self, query: str, top_k: int = 5, min_score: float = 0.3) -> List[Tuple[Document, float]]:
        """
        Search for similar documents.
        
        Args:
            query: Search query
            top_k: Number of results to return
            min_score: Minimum similarity score
            
        Returns:
            List of (document, score) tuples
        """
        if len(self.documents) == 0:
            return []
        
        # Generate query embedding
        query_embedding = self.encoder.encode([query])[0]
        query_embedding = query_embedding / np.linalg.norm(query_embedding)
        
        # Search in FAISS index
        scores, indices = self.index.search(query_embedding.reshape(1, -1), min(top_k, len(self.documents)))
        
        results = []
        doc_list = list(self.documents.values())
        
        for score, idx in zip(scores[0], indices[0]):
            if score >= min_score:
                doc = doc_list[idx]
                results.append((doc, float(score)))
        
        return results
    
    def get_document(self, doc_id: str) -> Optional[Document]:
        """Get document by ID."""
        return self.documents.get(doc_id)
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete document by ID."""
        if doc_id in self.documents:
            del self.documents[doc_id]
            # Note: FAISS doesn't support deletion, so we'd need to rebuild index
            # For now, just remove from documents dict
            return True
        return False
    
    def save_index(self):
        """Save index and documents to disk."""
        try:
            # Save FAISS index
            faiss.write_index(self.index, str(self.index_path / "faiss.index"))
            
            # Save documents (without embeddings to save space)
            docs_to_save = {}
            for doc_id, doc in self.documents.items():
                docs_to_save[doc_id] = {
                    'id': doc.id,
                    'content': doc.content,
                    'metadata': doc.metadata,
                    'created_at': doc.created_at
                }
            
            with open(self.index_path / "documents.json", 'w') as f:
                json.dump(docs_to_save, f, indent=2)
            
            logger.info(f"Saved vector store with {len(self.documents)} documents")
            
        except Exception as e:
            logger.error(f"Error saving index: {e}")
    
    def _load_index(self):
        """Load index and documents from disk."""
        try:
            faiss_path = self.index_path / "faiss.index"
            docs_path = self.index_path / "documents.json"
            
            if faiss_path.exists() and docs_path.exists():
                # Load FAISS index
                self.index = faiss.read_index(str(faiss_path))
                
                # Load documents
                with open(docs_path, 'r') as f:
                    docs_data = json.load(f)
                
                # Reconstruct documents with embeddings
                contents = []
                for doc_data in docs_data.values():
                    contents.append(doc_data['content'])
                
                if contents:
                    # Regenerate embeddings
                    embeddings = self.encoder.encode(contents)
                    embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
                    
                    for i, (doc_id, doc_data) in enumerate(docs_data.items()):
                        doc = Document(
                            id=doc_data['id'],
                            content=doc_data['content'],
                            metadata=doc_data['metadata'],
                            embedding=embeddings[i],
                            created_at=doc_data['created_at']
                        )
                        self.documents[doc_id] = doc
                
                logger.info(f"Loaded vector store with {len(self.documents)} documents")
                
        except Exception as e:
            logger.warning(f"Could not load existing index: {e}")
            # Initialize empty index
            self.index = faiss.IndexFlatIP(self.embedding_dim)
            self.documents = {}
    
    def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics."""
        return {
            "total_documents": len(self.documents),
            "embedding_dimension": self.embedding_dim,
            "model_name": self.model_name,
            "index_size": self.index.ntotal
        }
