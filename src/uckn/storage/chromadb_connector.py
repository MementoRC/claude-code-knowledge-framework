import logging
from pathlib import Path
from typing import Any

try:
    import chromadb
    from chromadb.config import Settings
    from chromadb.utils import embedding_functions

    CHROMADB_AVAILABLE = True
except ImportError:
    chromadb = None
    Settings = None
    embedding_functions = None
    CHROMADB_AVAILABLE = False

# Assuming SentenceTransformer is available via framework/core/semantic_search.py
# We will rely on the SemanticSearchEngine for actual embedding generation.
# This connector primarily handles storage and retrieval in ChromaDB.


class ChromaDBConnector:
    """
    Manages connection and operations with ChromaDB for UCKN knowledge.

    Handles collection creation, CRUD operations for 'code_patterns',
    'error_solutions', 'tech_stack_compatibility', and 'pattern_applications',
    and schema validation.
    """

    _COLLECTION_SCHEMAS = {
        "code_patterns": {
            "required_metadata": [
                "technology_stack",
                "pattern_type",
                "success_rate",
                "pattern_id",
                "created_at",
                "updated_at",
            ],
            "metadata_types": {
                "technology_stack": str,  # Comma-separated string, e.g. "python,pytest"
                "pattern_type": str,
                "success_rate": float,
                "pattern_id": str,
                "created_at": str,
                "updated_at": str,
            },
        },
        "error_solutions": {
            "required_metadata": [
                "error_category",
                "resolution_steps",
                "avg_resolution_time",
                "solution_id",
                "created_at",
                "updated_at",
            ],
            "metadata_types": {
                "error_category": str,
                "resolution_steps": str,  # Comma-separated string, e.g. "step1,step2"
                "avg_resolution_time": (int, float),
                "solution_id": str,
                "created_at": str,
                "updated_at": str,
            },
        },
        "tech_stack_compatibility": {
            "required_metadata": [
                "tech_stack_a",
                "tech_stack_b",
                "score",
                "description",
                "created_at",
                "updated_at",
                "combo_id",
            ],
            "metadata_types": {
                "tech_stack_a": str,  # Comma-separated string, e.g. "python,pytest"
                "tech_stack_b": str,  # Comma-separated string, e.g. "react,typescript"
                "score": float,
                "description": str,
                "created_at": str,
                "updated_at": str,
                "combo_id": str,
            },
        },
        "pattern_applications": {
            "required_metadata": [
                "pattern_id",
                "application_status",
                "success_score",
                "application_time",
                "user_feedback",
                "created_at",
            ],
            "metadata_types": {
                "pattern_id": str,
                "application_status": str,
                "success_score": float,
                "application_time": str,
                "user_feedback": str,
                "created_at": str,
            },
        },
    }

    def __init__(self, db_path: str = ".uckn/knowledge/chroma_db"):
        self.db_path = Path(db_path)
        self.db_path.mkdir(parents=True, exist_ok=True)
        self._logger = logging.getLogger(__name__)
        self.client: Any | None = None
        self.collections: dict[str, Any] = {}
        self._connect_to_chromadb()

    def _connect_to_chromadb(self) -> None:
        """Initializes the ChromaDB client and collections."""
        if not CHROMADB_AVAILABLE:
            self._logger.warning(
                "ChromaDB not available. Storage operations will be disabled."
            )
            return

        try:
            self.client = chromadb.PersistentClient(
                path=str(self.db_path), settings=Settings(anonymized_telemetry=False)
            )
            self._logger.info(f"ChromaDB client initialized at {self.db_path}")

            # Initialize collections
            for name in self._COLLECTION_SCHEMAS.keys():
                self.collections[name] = self.client.get_or_create_collection(
                    name=name,
                    metadata={"description": f"UCKN {name.replace('_', ' ')}"},
                )
                self._logger.info(f"ChromaDB collection '{name}' initialized.")

        except Exception as e:
            self._logger.error(f"Failed to initialize ChromaDB: {e}")
            self.client = None
            self.collections = {}

    def is_available(self) -> bool:
        """Checks if ChromaDB is connected and ready."""
        return self.client is not None and bool(self.collections)

    def _validate_metadata(
        self, collection_name: str, metadata: dict[str, Any]
    ) -> bool:
        """Validates metadata against the predefined schema for a collection."""
        schema = self._COLLECTION_SCHEMAS.get(collection_name)
        if not schema:
            self._logger.error(f"No schema defined for collection: {collection_name}")
            return False

        required = schema["required_metadata"]
        types = schema["metadata_types"]

        for key in required:
            if key not in metadata:
                self._logger.error(
                    f"Metadata for '{collection_name}' missing required key: '{key}'"
                )
                return False
            expected_type = types.get(key)
            if expected_type and not isinstance(metadata[key], expected_type):
                self._logger.error(
                    f"Metadata key '{key}' in '{collection_name}' has incorrect type. "
                    f"Expected {expected_type}, got {type(metadata[key])}"
                )
                return False
        return True

    def add_document(
        self,
        collection_name: str,
        doc_id: str,
        document: str,
        embedding: list[float],
        metadata: dict[str, Any],
    ) -> bool:
        """
        Adds a document to the specified ChromaDB collection.

        Args:
            collection_name: The name of the collection ('code_patterns' or 'error_solutions').
            doc_id: A unique ID for the document.
            document: The text content of the document.
            embedding: The embedding vector for the document.
            metadata: A dictionary of metadata associated with the document.

        Returns:
            True if the document was added successfully, False otherwise.
        """
        if not self.is_available():
            self._logger.warning("ChromaDB not available, cannot add document.")
            return False

        if collection_name not in self.collections:
            self._logger.error(f"Collection '{collection_name}' does not exist.")
            return False

        if not self._validate_metadata(collection_name, metadata):
            self._logger.error(
                f"Metadata validation failed for collection '{collection_name}'."
            )
            return False

        try:
            collection = self.collections[collection_name]
            collection.add(
                ids=[doc_id],
                documents=[document],
                embeddings=[embedding],
                metadatas=[metadata],
            )
            self._logger.info(f"Document '{doc_id}' added to '{collection_name}'.")
            return True
        except Exception as e:
            self._logger.error(
                f"Failed to add document '{doc_id}' to '{collection_name}': {e}"
            )
            return False

    def get_document(self, collection_name: str, doc_id: str) -> dict[str, Any] | None:
        """
        Retrieves a document from the specified ChromaDB collection by ID.

        Args:
            collection_name: The name of the collection.
            doc_id: The ID of the document to retrieve.

        Returns:
            A dictionary containing the document, embedding, and metadata, or None if not found.
        """
        if not self.is_available():
            self._logger.warning("ChromaDB not available, cannot get document.")
            return None

        if collection_name not in self.collections:
            self._logger.error(f"Collection '{collection_name}' does not exist.")
            return None

        try:
            collection = self.collections[collection_name]
            results = collection.get(
                ids=[doc_id], include=["documents", "embeddings", "metadatas"]
            )
            if results and results["ids"]:
                return {
                    "id": results["ids"][0],
                    "document": results["documents"][0],
                    "embedding": results["embeddings"][0],
                    "metadata": results["metadatas"][0],
                }
            return None
        except Exception as e:
            self._logger.error(
                f"Failed to get document '{doc_id}' from '{collection_name}': {e}"
            )
            return None

    def update_document(
        self,
        collection_name: str,
        doc_id: str,
        document: str | None = None,
        embedding: list[float] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """
        Updates an existing document in the specified ChromaDB collection.

        Args:
            collection_name: The name of the collection.
            doc_id: The ID of the document to update.
            document: New text content (optional).
            embedding: New embedding vector (optional).
            metadata: New metadata (optional).

        Returns:
            True if the document was updated successfully, False otherwise.
        """
        if not self.is_available():
            self._logger.warning("ChromaDB not available, cannot update document.")
            return False

        if collection_name not in self.collections:
            self._logger.error(f"Collection '{collection_name}' does not exist.")
            return False

        if metadata and not self._validate_metadata(collection_name, metadata):
            self._logger.error(
                f"Metadata validation failed for collection '{collection_name}'."
            )
            return False

        try:
            collection = self.collections[collection_name]
            collection.update(
                ids=[doc_id],
                documents=[document] if document is not None else None,
                embeddings=[embedding] if embedding is not None else None,
                metadatas=[metadata] if metadata is not None else None,
            )
            self._logger.info(f"Document '{doc_id}' updated in '{collection_name}'.")
            return True
        except Exception as e:
            self._logger.error(
                f"Failed to update document '{doc_id}' in '{collection_name}': {e}"
            )
            return False

    def delete_document(self, collection_name: str, doc_id: str) -> bool:
        """
        Deletes a document from the specified ChromaDB collection by ID.

        Args:
            collection_name: The name of the collection.
            doc_id: The ID of the document to delete.

        Returns:
            True if the document was deleted successfully, False otherwise.
        """
        if not self.is_available():
            self._logger.warning("ChromaDB not available, cannot delete document.")
            return False

        if collection_name not in self.collections:
            self._logger.error(f"Collection '{collection_name}' does not exist.")
            return False

        try:
            collection = self.collections[collection_name]
            collection.delete(ids=[doc_id])
            self._logger.info(f"Document '{doc_id}' deleted from '{collection_name}'.")
            return True
        except Exception as e:
            self._logger.error(
                f"Failed to delete document '{doc_id}' from '{collection_name}': {e}"
            )
            return False

    def search_documents(
        self,
        collection_name: str,
        query_embedding: list[float],
        n_results: int = 10,
        min_similarity: float = 0.7,
        where_clause: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Searches for similar documents in the specified ChromaDB collection.

        Args:
            collection_name: The name of the collection.
            query_embedding: The embedding of the query.
            n_results: The maximum number of results to return.
            min_similarity: Minimum similarity score to include a result (0.0 to 1.0).
            where_clause: A dictionary for metadata filtering (ChromaDB 'where' clause).

        Returns:
            A list of dictionaries, each containing 'id', 'document', 'metadata', and 'similarity_score'.
        """
        if not self.is_available():
            self._logger.warning("ChromaDB not available, cannot perform search.")
            return []

        if collection_name not in self.collections:
            self._logger.error(f"Collection '{collection_name}' does not exist.")
            return []

        try:
            collection = self.collections[collection_name]
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where_clause,
                include=["documents", "metadatas", "distances"],
            )

            search_results = []
            if results["ids"] and len(results["ids"][0]) > 0:
                for i, doc_id in enumerate(results["ids"][0]):
                    distance = results["distances"][0][i]
                    # Convert distance to similarity (lower distance = higher similarity)
                    # ChromaDB distances are L2, so similarity is 1 / (1 + distance) or similar.
                    # For cosine similarity, it's (1 - distance) / 2 if normalized to [-1, 1]
                    # or just 1 - distance if distance is 0 to 2.
                    # Let's use a simple inverse for L2 distance for now, or assume cosine.
                    # The `semantic_search.py` uses 1.0 / (1.0 + distance) for L2.
                    similarity = 1.0 / (
                        1.0 + distance
                    )  # Assuming L2 distance from ChromaDB

                    if similarity >= min_similarity:
                        search_results.append(
                            {
                                "id": doc_id,
                                "document": results["documents"][0][i],
                                "metadata": results["metadatas"][0][i],
                                "similarity_score": similarity,
                            }
                        )
            return search_results
        except Exception as e:
            self._logger.error(f"Failed to search collection '{collection_name}': {e}")
            return []

    def count_documents(self, collection_name: str) -> int:
        """
        Returns the number of documents in a specified collection.
        """
        if not self.is_available():
            return 0
        if collection_name not in self.collections:
            self._logger.error(f"Collection '{collection_name}' does not exist.")
            return 0
        try:
            return self.collections[collection_name].count()
        except Exception as e:
            self._logger.error(f"Failed to count documents in '{collection_name}': {e}")
            return 0

    def get_all_documents(self, collection_name: str) -> list[dict[str, Any]]:
        """
        Retrieves all documents from a specified collection.
        Use with caution for large collections.
        """
        if not self.is_available():
            return []
        if collection_name not in self.collections:
            self._logger.error(f"Collection '{collection_name}' does not exist.")
            return []
        try:
            results = self.collections[collection_name].get(
                ids=None,  # Get all
                include=["documents", "embeddings", "metadatas"],
            )
            all_docs = []
            if results and results["ids"]:
                for i, doc_id in enumerate(results["ids"]):
                    all_docs.append(
                        {
                            "id": doc_id,
                            "document": results["documents"][i],
                            "embedding": results["embeddings"][i],
                            "metadata": results["metadatas"][i],
                        }
                    )
            return all_docs
        except Exception as e:
            self._logger.error(
                f"Failed to retrieve all documents from '{collection_name}': {e}"
            )
            return []

    def reset_db(self) -> bool:
        """
        Resets the ChromaDB client, effectively deleting all data.
        Use with extreme caution.
        """
        if not self.is_available():
            self._logger.warning("ChromaDB not available, cannot reset.")
            return False
        try:
            self.client.reset()
            self._logger.info("ChromaDB reset successfully.")
            # Re-initialize collections after reset
            self._connect_to_chromadb()
            return True
        except Exception as e:
            self._logger.error(f"Failed to reset ChromaDB: {e}")
            return False

    def _get_collection_names(self) -> list[str]:
        """Returns a list of collection names managed by this connector."""
        return list(self._COLLECTION_SCHEMAS.keys())
