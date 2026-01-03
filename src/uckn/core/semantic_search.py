#!/usr/bin/env python3
"""
Enhanced Semantic Search Implementation

Provides semantic similarity search using sentence transformers and ChromaDB
for efficient knowledge retrieval based on meaning rather than just keywords.
"""

import json
import logging

# Defensive import to handle PyTorch docstring conflicts
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

_DISABLE_TORCH = os.environ.get("UCKN_DISABLE_TORCH", "0") == "1"

if _DISABLE_TORCH:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None
else:
    try:
        from sentence_transformers import SentenceTransformer

        SENTENCE_TRANSFORMERS_AVAILABLE = True
    except (ImportError, RuntimeError):
        # Handle PyTorch docstring conflicts and import errors
        SENTENCE_TRANSFORMERS_AVAILABLE = False
        SentenceTransformer = None

try:
    import chromadb
    from chromadb.config import Settings

    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False


class SemanticSearchEngine:
    """
    Semantic search engine using sentence transformers and ChromaDB.

    Provides embedding-based similarity search for knowledge management
    with fallback to keyword search when embeddings are unavailable.
    """

    def __init__(self, knowledge_dir: str = ".claude/knowledge"):
        self.knowledge_dir = Path(knowledge_dir)
        self.embeddings_dir = self.knowledge_dir / "embeddings"
        self.embeddings_dir.mkdir(parents=True, exist_ok=True)

        self._logger = logging.getLogger(__name__)

        # Initialize components if available
        self._init_sentence_transformer()
        self._init_chromadb()

    def _init_sentence_transformer(self) -> None:
        """Initialize sentence transformer model."""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            self._logger.warning(
                "sentence-transformers not available, using fallback search"
            )
            self.sentence_model = None
            return

        try:
            # Use a lightweight but effective model
            self.sentence_model = SentenceTransformer("all-MiniLM-L6-v2")
            self._logger.info("Sentence transformer model loaded successfully")
        except Exception as e:
            self._logger.error(f"Failed to load sentence transformer: {e}")
            self.sentence_model = None

    def _init_chromadb(self) -> None:
        """Initialize ChromaDB for vector storage."""
        if not CHROMADB_AVAILABLE:
            self._logger.warning("ChromaDB not available, using numpy fallback")
            self.chroma_client = None
            self.collection = None
            return

        try:
            # Initialize ChromaDB client
            self.chroma_client = chromadb.PersistentClient(
                path=str(self.embeddings_dir / "chroma_db"),
                settings=Settings(anonymized_telemetry=False),
            )

            # Get or create collection for sessions
            self.collection = self.chroma_client.get_or_create_collection(
                name="session_embeddings",
                metadata={"description": "Session knowledge embeddings"},
            )

            self._logger.info("ChromaDB initialized successfully")

        except Exception as e:
            self._logger.error(f"Failed to initialize ChromaDB: {e}")
            self.chroma_client = None
            self.collection = None

    def is_available(self) -> bool:
        """Check if semantic search is fully available."""
        return self.sentence_model is not None

    def generate_session_embedding(
        self, session_data: dict[str, Any]
    ) -> np.ndarray | None:
        """Generate embedding for a session."""
        if not self.sentence_model:
            return None

        try:
            # Create text representation of session for embedding
            text_content = self._extract_text_for_embedding(session_data)

            # Generate embedding
            embedding = self.sentence_model.encode(text_content, convert_to_numpy=True)
            return embedding

        except Exception as e:
            self._logger.error(f"Failed to generate session embedding: {e}")
            return None

    def store_session_embedding(
        self, session_id: str, session_data: dict[str, Any]
    ) -> bool:
        """Store session embedding in vector database."""
        try:
            embedding = self.generate_session_embedding(session_data)
            if embedding is None:
                return False

            # Store in ChromaDB if available
            if self.collection is not None:
                self.collection.add(
                    ids=[session_id],
                    embeddings=[embedding.tolist()],
                    metadatas=[
                        {
                            "session_id": session_id,
                            "timestamp": session_data.get("timestamp", ""),
                            "final_status": session_data.get("final_status", "unknown"),
                            "complexity": session_data.get("metadata", {}).get(
                                "session_complexity", "medium"
                            ),
                        }
                    ],
                    documents=[self._extract_text_for_embedding(session_data)],
                )
            else:
                # Fallback to numpy storage
                self._store_embedding_numpy(session_id, embedding, session_data)

            return True

        except Exception as e:
            self._logger.error(f"Failed to store session embedding: {e}")
            return False

    def search_similar_sessions(
        self, query: str, max_results: int = 10, similarity_threshold: float = 0.7
    ) -> list[dict[str, Any]]:
        """Search for similar sessions using semantic similarity."""
        if not self.sentence_model:
            self._logger.warning(
                "Semantic search not available, returning empty results"
            )
            return []

        try:
            # Generate query embedding
            query_embedding = self.sentence_model.encode(query, convert_to_numpy=True)

            # Search using ChromaDB if available
            if self.collection is not None:
                return self._search_chromadb(
                    query_embedding, max_results, similarity_threshold
                )
            else:
                return self._search_numpy_fallback(
                    query_embedding, max_results, similarity_threshold
                )

        except Exception as e:
            self._logger.error(f"Semantic search failed: {e}")
            return []

    def _search_chromadb(
        self, query_embedding: np.ndarray, max_results: int, similarity_threshold: float
    ) -> list[dict[str, Any]]:
        """Search using ChromaDB vector database."""
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=max_results,
                include=["metadatas", "documents", "distances"],
            )

            search_results = []

            if results["ids"] and len(results["ids"][0]) > 0:
                for i, session_id in enumerate(results["ids"][0]):
                    distance = results["distances"][0][i]
                    # Convert distance to similarity (lower distance = higher similarity)
                    similarity = 1.0 / (1.0 + distance)

                    if similarity >= similarity_threshold:
                        search_results.append(
                            {
                                "session_id": session_id,
                                "similarity_score": similarity,
                                "metadata": results["metadatas"][0][i],
                                "document": results["documents"][0][i],
                                "search_type": "semantic",
                            }
                        )

            return search_results

        except Exception as e:
            self._logger.error(f"ChromaDB search failed: {e}")
            return []

    def _search_numpy_fallback(
        self, query_embedding: np.ndarray, max_results: int, similarity_threshold: float
    ) -> list[dict[str, Any]]:
        """Fallback search using numpy similarity computation."""
        try:
            embeddings_file = self.embeddings_dir / "session_embeddings.json"
            if not embeddings_file.exists():
                return []

            with open(embeddings_file) as f:
                stored_embeddings = json.load(f)

            similarities = []

            for session_id, embedding_data in stored_embeddings.items():
                stored_embedding = np.array(embedding_data["embedding"])

                # Compute cosine similarity
                similarity = np.dot(query_embedding, stored_embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(stored_embedding)
                )

                if similarity >= similarity_threshold:
                    similarities.append(
                        {
                            "session_id": session_id,
                            "similarity_score": float(similarity),
                            "metadata": embedding_data["metadata"],
                            "search_type": "semantic",
                        }
                    )

            # Sort by similarity and return top results
            similarities.sort(key=lambda x: x["similarity_score"], reverse=True)
            return similarities[:max_results]

        except Exception as e:
            self._logger.error(f"Numpy fallback search failed: {e}")
            return []

    def _store_embedding_numpy(
        self, session_id: str, embedding: np.ndarray, session_data: dict[str, Any]
    ) -> None:
        """Store embedding using numpy fallback."""
        embeddings_file = self.embeddings_dir / "session_embeddings.json"

        try:
            # Load existing embeddings
            if embeddings_file.exists():
                with open(embeddings_file) as f:
                    embeddings = json.load(f)
            else:
                embeddings = {}

            # Add new embedding
            embeddings[session_id] = {
                "embedding": embedding.tolist(),
                "metadata": {
                    "session_id": session_id,
                    "timestamp": session_data.get("timestamp", ""),
                    "final_status": session_data.get("final_status", "unknown"),
                    "complexity": session_data.get("metadata", {}).get(
                        "session_complexity", "medium"
                    ),
                },
                "created_at": datetime.now().isoformat(),
            }

            # Save updated embeddings
            with open(embeddings_file, "w") as f:
                json.dump(embeddings, f, indent=2)

        except Exception as e:
            self._logger.error(f"Failed to store numpy embedding: {e}")

    def _extract_text_for_embedding(self, session_data: dict[str, Any]) -> str:
        """Extract meaningful text content from session data for embedding."""
        text_parts = []

        # Add context information
        context = session_data.get("context", {})
        if "error_type" in context:
            text_parts.append(f"Error type: {context['error_type']}")
        if "tools_used" in context:
            text_parts.append(f"Tools used: {', '.join(context['tools_used'])}")

        # Add lessons learned
        lessons = session_data.get("lessons_learned", [])
        if lessons:
            text_parts.append(f"Lessons learned: {' '.join(lessons)}")

        # Add solution patterns
        patterns = session_data.get("solution_patterns", [])
        for pattern in patterns:
            if isinstance(pattern, dict) and "description" in pattern:
                text_parts.append(f"Solution: {pattern['description']}")

        # Add manual insights
        insights = session_data.get("manual_insights", [])
        if insights:
            text_parts.append(f"Insights: {' '.join(insights)}")

        # Combine all text
        combined_text = " ".join(text_parts)

        # Fallback to session ID if no meaningful text
        if not combined_text.strip():
            combined_text = f"Session {session_data.get('session_id', 'unknown')}"

        return combined_text

    def get_embedding_stats(self) -> dict[str, Any]:
        """Get statistics about stored embeddings."""
        try:
            if self.collection is not None:
                # ChromaDB stats
                count = self.collection.count()
                return {
                    "total_embeddings": count,
                    "storage_type": "chromadb",
                    "model_available": self.sentence_model is not None,
                }
            else:
                # Numpy fallback stats
                embeddings_file = self.embeddings_dir / "session_embeddings.json"
                if embeddings_file.exists():
                    with open(embeddings_file) as f:
                        embeddings = json.load(f)
                    return {
                        "total_embeddings": len(embeddings),
                        "storage_type": "numpy_fallback",
                        "model_available": self.sentence_model is not None,
                    }
                else:
                    return {
                        "total_embeddings": 0,
                        "storage_type": "none",
                        "model_available": self.sentence_model is not None,
                    }

        except Exception as e:
            self._logger.error(f"Failed to get embedding stats: {e}")
            return {
                "total_embeddings": 0,
                "storage_type": "error",
                "model_available": False,
                "error": str(e),
            }
