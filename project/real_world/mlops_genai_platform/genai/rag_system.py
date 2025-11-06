"""
Retrieval-Augmented Generation (RAG) System.

Provides enterprise-grade RAG capabilities including:
- Vector database integration (ChromaDB, Pinecone, Weaviate)
- Document ingestion and processing
- Semantic search and retrieval
- Context-enhanced generation
- Multi-modal document support
"""

import asyncio
import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel

try:
    from ..core.config import PlatformConfig
except ImportError:
    # Fallback for direct imports
    import sys
    from pathlib import Path
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from core.config import PlatformConfig


class Document(BaseModel):
    """Document representation for RAG."""

    id: str
    content: str
    metadata: Dict[str, Any] = {}
    embedding: Optional[List[float]] = None
    source: Optional[str] = None
    timestamp: Optional[float] = None


class SearchResult(BaseModel):
    """Search result from RAG system."""

    document: Document
    score: float
    context: Optional[str] = None


class RAGConfig(BaseModel):
    """Configuration for RAG system."""

    vector_db_type: str = "chroma"  # chroma, pinecone, weaviate
    collection_name: str = "mlops_genai_kb"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimension: int = 384
    chunk_size: int = 1000
    chunk_overlap: int = 200
    top_k: int = 5
    similarity_threshold: float = 0.7
    max_context_length: int = 4000


class RAGSystem:
    """
    Retrieval-Augmented Generation system.

    Features:
    - Multi-vector database support
    - Document ingestion and chunking
    - Semantic search with embeddings
    - Context-aware retrieval
    - Integration with LLM generation
    """

    def __init__(self, config: PlatformConfig):
        """
        Initialize RAG system.

        Args:
            config: Platform configuration
        """
        self.config = config
        self.logger = logging.getLogger(f"{config.project_name}.RAGSystem")

        # RAG configuration
        self.rag_config = RAGConfig(**config.vector_db.__dict__ if hasattr(config, 'vector_db') else {})

        # Vector database client
        self._vector_client = None
        self._embedding_model = None

        # Document storage
        self._documents: Dict[str, Document] = {}
        self._document_store_file = self.config.data_dir / "rag_documents.json"

    async def initialize(self) -> None:
        """Initialize RAG system."""
        self.logger.info("Initializing RAG system...")

        # Initialize vector database
        await self._init_vector_db()

        # Initialize embedding model
        await self._init_embedding_model()

        # Load existing documents
        await self._load_documents()

        self.logger.info(f"RAG system initialized with {len(self._documents)} documents")

    async def _init_vector_db(self) -> None:
        """Initialize vector database client."""
        db_type = self.rag_config.vector_db_type

        try:
            if db_type == "chroma":
                await self._init_chroma()
            elif db_type == "pinecone":
                await self._init_pinecone()
            elif db_type == "weaviate":
                await self._init_weaviate()
            else:
                raise ValueError(f"Unsupported vector database: {db_type}")

            self.logger.info(f"Vector database {db_type} initialized")

        except Exception as e:
            self.logger.error(f"Failed to initialize vector database: {e}")
            raise

    async def _init_chroma(self) -> None:
        """Initialize ChromaDB client."""
        try:
            import chromadb

            # Use persistent client
            persist_dir = self.config.data_dir / "chroma_db"
            persist_dir.mkdir(parents=True, exist_ok=True)

            self._vector_client = chromadb.PersistentClient(path=str(persist_dir))

            # Get or create collection
            try:
                self._collection = self._vector_client.get_collection(self.rag_config.collection_name)
            except:
                self._collection = self._vector_client.create_collection(self.rag_config.collection_name)

        except ImportError:
            # Fallback: create in-memory storage for demo
            self.logger.warning("ChromaDB not available, using in-memory fallback")
            self._vector_client = "memory"
            self._collection = {"documents": [], "embeddings": [], "metadata": []}

    async def _init_pinecone(self) -> None:
        """Initialize Pinecone client."""
        try:
            import pinecone

            pinecone.init(
                api_key=self.config.vector_db.pinecone_api_key,
                environment=self.config.vector_db.pinecone_environment
            )

            self._vector_client = pinecone
            self._index = pinecone.Index(self.rag_config.collection_name)

        except ImportError:
            raise ImportError("Pinecone not installed. Install with: pip install pinecone-client")

    async def _init_weaviate(self) -> None:
        """Initialize Weaviate client."""
        try:
            import weaviate

            self._vector_client = weaviate.Client(
                url=self.config.vector_db.weaviate_url
            )

            # Create schema if needed
            if not self._vector_client.schema.exists(self.rag_config.collection_name):
                schema = {
                    "class": self.rag_config.collection_name,
                    "properties": [
                        {"name": "content", "dataType": ["text"]},
                        {"name": "metadata", "dataType": ["object"]},
                        {"name": "source", "dataType": ["string"]},
                    ],
                    "vectorizer": "none",  # We'll provide our own embeddings
                }
                self._vector_client.schema.create_class(schema)

        except ImportError:
            raise ImportError("Weaviate not installed. Install with: pip install weaviate-client")

    async def _init_embedding_model(self) -> None:
        """Initialize embedding model."""
        try:
            from sentence_transformers import SentenceTransformer

            self._embedding_model = SentenceTransformer(self.rag_config.embedding_model)
            self.logger.info(f"Embedding model loaded: {self.rag_config.embedding_model}")

        except ImportError:
            self.logger.warning("SentenceTransformers not available, embeddings will be disabled")
            self._embedding_model = None

    async def add_document(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        source: Optional[str] = None,
        chunk_size: Optional[int] = None
    ) -> List[str]:
        """
        Add document to RAG system.

        Args:
            content: Document content
            metadata: Optional metadata
            source: Optional source identifier
            chunk_size: Optional custom chunk size

        Returns:
            List of document IDs added
        """
        self.logger.info(f"Adding document from source: {source}")

        # Split into chunks
        chunks = self._chunk_text(content, chunk_size or self.rag_config.chunk_size)
        document_ids = []

        for i, chunk in enumerate(chunks):
            # Create document
            doc_id = self._generate_doc_id(content, i)
            document = Document(
                id=doc_id,
                content=chunk,
                metadata=metadata or {},
                source=source,
                timestamp=asyncio.get_event_loop().time()
            )

            # Generate embedding
            if self._embedding_model:
                embedding = self._embedding_model.encode(chunk).tolist()
                document.embedding = embedding

            # Store document
            self._documents[doc_id] = document

            # Add to vector database
            await self._add_to_vector_db(document)

            document_ids.append(doc_id)

        # Save to disk
        await self._save_documents()

        self.logger.info(f"Added {len(document_ids)} document chunks")
        return document_ids

    async def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        threshold: Optional[float] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        Search for relevant documents.

        Args:
            query: Search query
            top_k: Number of results to return
            threshold: Similarity threshold
            filters: Optional metadata filters

        Returns:
            List of search results
        """
        self.logger.debug(f"Searching for: {query}")

        if not self._embedding_model:
            self.logger.error("Embedding model not available")
            return []

        # Generate query embedding
        query_embedding = self._embedding_model.encode(query).tolist()

        # Search vector database
        results = await self._search_vector_db(query_embedding, top_k or self.rag_config.top_k)

        # Filter and format results
        search_results = []
        for result in results:
            if threshold and result["score"] < threshold:
                continue

            # Get full document
            doc_id = result["id"]
            if doc_id in self._documents:
                document = self._documents[doc_id]

                # Apply metadata filters
                if filters:
                    if not self._matches_filters(document.metadata, filters):
                        continue

                search_result = SearchResult(
                    document=document,
                    score=result["score"],
                    context=self._extract_context(document.content, query)
                )
                search_results.append(search_result)

        self.logger.debug(f"Found {len(search_results)} relevant documents")
        return search_results

    async def retrieve_context(
        self,
        query: str,
        max_length: Optional[int] = None
    ) -> str:
        """
        Retrieve context for a query.

        Args:
            query: Query string
            max_length: Maximum context length

        Returns:
            Concatenated context from relevant documents
        """
        results = await self.search(query, top_k=3)

        if not results:
            return ""

        # Combine contexts
        contexts = []
        total_length = 0
        max_len = max_length or self.rag_config.max_context_length

        for result in results:
            context = result.context or result.document.content
            if total_length + len(context) > max_len:
                # Truncate if needed
                remaining = max_len - total_length
                context = context[:remaining]
                contexts.append(context)
                break

            contexts.append(context)
            total_length += len(context)

        full_context = "\n\n".join(contexts)
        self.logger.debug(f"Retrieved context ({len(full_context)} chars)")
        return full_context

    def _chunk_text(self, text: str, chunk_size: int) -> List[str]:
        """Split text into chunks."""
        words = text.split()
        chunks = []

        for i in range(0, len(words), chunk_size - self.rag_config.chunk_overlap):
            chunk_words = words[i:i + chunk_size]
            chunk = " ".join(chunk_words)
            chunks.append(chunk)

        return chunks

    def _generate_doc_id(self, content: str, chunk_index: int) -> str:
        """Generate unique document ID."""
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        return f"doc_{content_hash}_{chunk_index}"

    async def _add_to_vector_db(self, document: Document) -> None:
        """Add document to vector database."""
        if not document.embedding:
            return

        try:
            if self.rag_config.vector_db_type == "chroma":
                if self._vector_client == "memory":
                    # Fallback: store in memory
                    self._collection["documents"].append(document.content)
                    self._collection["embeddings"].append(document.embedding)
                    self._collection["metadata"].append({
                        "content": document.content[:500],
                        "source": document.source or "",
                        **document.metadata
                    })
                    return

                self._collection.add(
                    ids=[document.id],
                    embeddings=[document.embedding],
                    metadatas=[{
                        "content": document.content[:500],  # Truncate for metadata
                        "source": document.source or "",
                        **document.metadata
                    }],
                    documents=[document.content]
                )

            elif self.rag_config.vector_db_type == "pinecone":
                self._index.upsert([
                    (document.id, document.embedding, {
                        "content": document.content[:500],
                        "source": document.source or "",
                        **document.metadata
                    })
                ])

            elif self.rag_config.vector_db_type == "weaviate":
                self._vector_client.data_object.create({
                    "content": document.content,
                    "metadata": document.metadata,
                    "source": document.source,
                }, self.rag_config.collection_name, vector=document.embedding)

        except Exception as e:
            self.logger.error(f"Failed to add document to vector DB: {e}")

    async def _search_vector_db(self, query_embedding: List[float], top_k: int) -> List[Dict[str, Any]]:
        """Search vector database."""
        try:
            if self.rag_config.vector_db_type == "chroma":
                if self._vector_client == "memory":
                    # Fallback: simple similarity search
                    results = []
                    for i, emb in enumerate(self._collection["embeddings"]):
                        similarity = self._cosine_similarity(query_embedding, emb)
                        results.append({"id": f"doc_{i}", "score": similarity})
                    results.sort(key=lambda x: x["score"], reverse=True)
                    return results[:top_k]

                results = self._collection.query(
                    query_embeddings=[query_embedding],
                    n_results=top_k
                )
                return [
                    {"id": doc_id, "score": score}
                    for doc_id, score in zip(results["ids"][0], results["distances"][0])
                ]

            elif self.rag_config.vector_db_type == "pinecone":
                results = self._index.query(
                    vector=query_embedding,
                    top_k=top_k,
                    include_metadata=False
                )
                return [
                    {"id": match.id, "score": match.score}
                    for match in results.matches
                ]

            elif self.rag_config.vector_db_type == "weaviate":
                results = self._vector_client.query.get(
                    self.rag_config.collection_name, ["content"]
                ).with_near_vector({
                    "vector": query_embedding
                }).with_limit(top_k).do()

                return [
                    {"id": obj["id"], "score": obj["score"]}
                    for obj in results["data"]["Get"][self.rag_config.collection_name]
                ]

        except Exception as e:
            self.logger.error(f"Vector DB search failed: {e}")
            return []

    def _matches_filters(self, doc_metadata: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Check if document matches metadata filters."""
        for key, value in filters.items():
            if key not in doc_metadata or doc_metadata[key] != value:
                return False
        return True

    def _extract_context(self, content: str, query: str) -> str:
        """Extract relevant context around query terms."""
        # Simple context extraction - find sentences containing query terms
        sentences = content.split('.')
        relevant_sentences = []

        query_words = set(query.lower().split())
        for sentence in sentences:
            sentence_words = set(sentence.lower().split())
            if query_words.intersection(sentence_words):
                relevant_sentences.append(sentence.strip())

        if relevant_sentences:
            return '. '.join(relevant_sentences[:3]) + '.'
        else:
            # Return first part of content if no direct matches
            return content[:1000]

    async def _load_documents(self) -> None:
        """Load documents from disk."""
        if self._document_store_file.exists():
            try:
                with open(self._document_store_file, "r") as f:
                    data = json.load(f)
                    for doc_data in data:
                        doc = Document(**doc_data)
                        self._documents[doc.id] = doc
                self.logger.info(f"Loaded {len(self._documents)} documents")
            except Exception as e:
                self.logger.error(f"Failed to load documents: {e}")

    async def _save_documents(self) -> None:
        """Save documents to disk."""
        try:
            data = [doc.dict() for doc in self._documents.values()]
            with open(self._document_store_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save documents: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get RAG system statistics."""
        return {
            "total_documents": len(self._documents),
            "vector_db_type": self.rag_config.vector_db_type,
            "embedding_model": self.rag_config.embedding_model,
            "chunk_size": self.rag_config.chunk_size,
            "collection_name": self.rag_config.collection_name,
        }

    async def clear_collection(self) -> None:
        """Clear all documents from collection."""
        self.logger.info("Clearing document collection...")

        # Clear in-memory storage
        self._documents.clear()

        # Clear vector database
        try:
            if self.rag_config.vector_db_type == "chroma":
                self._vector_client.delete_collection(self.rag_config.collection_name)
                self._collection = self._vector_client.create_collection(self.rag_config.collection_name)
            elif self.rag_config.vector_db_type == "pinecone":
                self._index.delete(delete_all=True)
            elif self.rag_config.vector_db_type == "weaviate":
                self._vector_client.schema.delete_class(self.rag_config.collection_name)
        except Exception as e:
            self.logger.error(f"Failed to clear collection: {e}")

        # Save empty state
        await self._save_documents()

        self.logger.info("Collection cleared")

    async def shutdown(self) -> None:
        """Shutdown RAG system."""
        self.logger.info("Shutting down RAG system...")

        # Save final state
        await self._save_documents()

        self.logger.info("RAG system shutdown complete")
