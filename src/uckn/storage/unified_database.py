import logging
import uuid
from datetime import datetime
from typing import Any, Optional

from .chromadb_connector import ChromaDBConnector
from .postgresql_connector import (
    CompatibilityMatrix,
    ErrorSolution,
    Pattern,
    PatternCategory,
    PostgreSQLConnector,
    Project,
    TeamAccess,
)

_logger = logging.getLogger(__name__)


class UnifiedDatabase:
    """
    Provides a unified access layer for UCKN's knowledge base,
    integrating PostgreSQL for structured metadata and ChromaDB for vector embeddings.
    """

    def __init__(
        self, pg_db_url: str, chroma_db_path: str = ".uckn/knowledge/chroma_db"
    ):
        # Store the classes for mocking in tests
        self._pg_connector_class = PostgreSQLConnector
        self._chroma_connector_class = ChromaDBConnector

        self.pg_connector = self._pg_connector_class(db_url=pg_db_url)
        self.chroma_connector = self._chroma_connector_class(db_path=chroma_db_path)
        self._logger = logging.getLogger(__name__)

    def is_available(self) -> bool:
        """Checks if both underlying databases are available."""
        pg_ok = self.pg_connector.is_available()
        chroma_ok = self.chroma_connector.is_available()
        if not pg_ok:
            self._logger.warning("PostgreSQL is not available.")
        if not chroma_ok:
            self._logger.warning("ChromaDB is not available.")
        return pg_ok and chroma_ok

    def reset_db(self) -> bool:
        """Resets both PostgreSQL and ChromaDB. Use with extreme caution."""
        pg_reset_success = self.pg_connector.reset_db()
        chroma_reset_success = self.chroma_connector.reset_db()
        return pg_reset_success and chroma_reset_success

    # --- Project Management (PostgreSQL only) ---
    def add_project(
        self,
        name: str,
        description: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> Optional[str]:
        """Adds a new project."""
        project_id = project_id or str(uuid.uuid4())
        data = {"id": project_id, "name": name, "description": description}
        return self.pg_connector.add_record(Project, data)

    def get_project(self, project_id: str) -> Optional[dict[str, Any]]:
        """Retrieves a project by ID."""
        return self.pg_connector.get_record(Project, project_id)

    def update_project(self, project_id: str, updates: dict[str, Any]) -> bool:
        """Updates an existing project."""
        return self.pg_connector.update_record(Project, project_id, updates)

    def delete_project(self, project_id: str) -> bool:
        """Deletes a project and its associated patterns/solutions (cascading delete handled by DB schema)."""
        return self.pg_connector.delete_record(Project, project_id)

    def get_all_projects(self) -> list[dict[str, Any]]:
        """Retrieves all projects."""
        return self.pg_connector.get_all_records(Project)

    # --- Pattern Management (PostgreSQL + ChromaDB) ---
    def add_pattern(
        self,
        document_text: str,
        embedding: list[float],
        metadata: dict[str, Any],
        pattern_id: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> Optional[str]:
        """
        Adds a new pattern, storing metadata in PostgreSQL and document/embedding in ChromaDB.
        """
        pattern_id = pattern_id or str(uuid.uuid4())
        now_iso = datetime.now().isoformat()

        # Prepare metadata for PostgreSQL (extract specific fields, store rest as JSONB)
        pg_metadata = {
            "id": pattern_id,
            "project_id": project_id,
            "document_text": document_text,
            "created_at": metadata.get("created_at", now_iso),
            "updated_at": now_iso,
            "technology_stack": metadata.get("technology_stack"),
            "pattern_type": metadata.get("pattern_type"),
            "success_rate": metadata.get("success_rate"),
            "metadata_json": metadata,  # Store full metadata as JSONB
        }

        # Add to PostgreSQL
        pg_success = self.pg_connector.add_record(Pattern, pg_metadata)
        if not pg_success:
            self._logger.error(
                f"Failed to add pattern metadata to PostgreSQL for ID: {pattern_id}"
            )
            return None

        # Prepare ChromaDB-compatible metadata (no list types, required fields only)
        chroma_metadata = {
            "pattern_id": pattern_id,
            "technology_stack": metadata.get("technology_stack", ""),
            "pattern_type": metadata.get("pattern_type", ""),
            "success_rate": float(metadata.get("success_rate", 0.0)),
            "created_at": metadata.get("created_at", now_iso),
            "updated_at": now_iso,
        }

        # Add to ChromaDB
        chroma_success = self.chroma_connector.add_document(
            collection_name="code_patterns",
            doc_id=pattern_id,
            document=document_text,
            embedding=embedding,
            metadata=chroma_metadata,  # ChromaDB stores only compatible metadata
        )
        if not chroma_success:
            # Attempt to rollback PostgreSQL record if ChromaDB fails
            self.pg_connector.delete_record(Pattern, pattern_id)
            self._logger.error(
                f"Failed to add pattern document to ChromaDB for ID: {pattern_id}. PostgreSQL record rolled back."
            )
            return None

        self._logger.info(
            f"Pattern '{pattern_id}' added successfully to both databases."
        )
        return pattern_id

    def get_pattern(self, pattern_id: str) -> Optional[dict[str, Any]]:
        """
        Retrieves a pattern by ID, combining data from PostgreSQL and ChromaDB.
        """
        pg_data = self.pg_connector.get_record(Pattern, pattern_id)
        if not pg_data:
            return None

        chroma_data = self.chroma_connector.get_document(
            collection_name="code_patterns", doc_id=pattern_id
        )

        # Combine data, prioritizing ChromaDB's document/embedding if available
        # and ensuring metadata_json from PG is the source of truth for metadata
        combined_data = {
            "id": pg_data["id"],
            "project_id": pg_data.get("project_id"),
            "document": chroma_data["document"]
            if chroma_data
            else pg_data["document_text"],
            "embedding": chroma_data["embedding"] if chroma_data else None,
            "metadata": pg_data["metadata_json"],  # Use metadata from PG
            "created_at": pg_data["created_at"],
            "updated_at": pg_data["updated_at"],
        }
        return combined_data

    def update_pattern(
        self,
        pattern_id: str,
        document_text: Optional[str] = None,
        embedding: Optional[list[float]] = None,
        metadata: Optional[dict[str, Any]] = None,
        project_id: Optional[str] = None,
    ) -> bool:
        """
        Updates an existing pattern in both PostgreSQL and ChromaDB.
        """
        pg_updates = {"updated_at": datetime.now().isoformat()}
        chroma_updates = {}

        if project_id is not None:
            pg_updates["project_id"] = project_id
        if document_text is not None:
            pg_updates["document_text"] = document_text
            chroma_updates["document"] = document_text
        if embedding is not None:
            chroma_updates["embedding"] = embedding
        if metadata is not None:
            pg_updates["metadata_json"] = metadata
            chroma_updates["metadata"] = metadata
            # Also update specific fields in PG if they are in metadata
            if "technology_stack" in metadata:
                pg_updates["technology_stack"] = metadata["technology_stack"]
            if "pattern_type" in metadata:
                pg_updates["pattern_type"] = metadata["pattern_type"]
            if "success_rate" in metadata:
                pg_updates["success_rate"] = metadata["success_rate"]

        pg_success = self.pg_connector.update_record(Pattern, pattern_id, pg_updates)
        if not pg_success:
            self._logger.error(
                f"Failed to update pattern metadata in PostgreSQL for ID: {pattern_id}"
            )
            return False

        chroma_success = self.chroma_connector.update_document(
            collection_name="code_patterns",
            doc_id=pattern_id,
            document=chroma_updates.get("document"),
            embedding=chroma_updates.get("embedding"),
            metadata=chroma_updates.get("metadata"),
        )
        if not chroma_success:
            self._logger.warning(
                f"Failed to update pattern document/embedding in ChromaDB for ID: {pattern_id}. PostgreSQL record updated."
            )
            # Consider rollback or alert if consistency is critical
            return False

        self._logger.info(
            f"Pattern '{pattern_id}' updated successfully in both databases."
        )
        return True

    def delete_pattern(self, pattern_id: str) -> bool:
        """
        Deletes a pattern from both PostgreSQL and ChromaDB.
        """
        pg_success = self.pg_connector.delete_record(Pattern, pattern_id)
        if not pg_success:
            self._logger.error(
                f"Failed to delete pattern metadata from PostgreSQL for ID: {pattern_id}"
            )
            return False

        chroma_success = self.chroma_connector.delete_document(
            collection_name="code_patterns", doc_id=pattern_id
        )
        if not chroma_success:
            self._logger.warning(
                f"Failed to delete pattern document from ChromaDB for ID: {pattern_id}. PostgreSQL record deleted."
            )
            # Consider re-adding to PG or alert if consistency is critical
            return False

        self._logger.info(
            f"Pattern '{pattern_id}' deleted successfully from both databases."
        )
        return True

    def search_patterns(
        self,
        query_embedding: list[float],
        n_results: int = 10,
        min_similarity: float = 0.7,
        metadata_filter: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        """
        Searches for patterns using ChromaDB, then retrieves full metadata from PostgreSQL.
        Metadata filter is applied at the ChromaDB level.
        """
        chroma_results = self.chroma_connector.search_documents(
            collection_name="code_patterns",
            query_embedding=query_embedding,
            n_results=n_results,
            min_similarity=min_similarity,
            where_clause=metadata_filter,
        )

        final_results = []
        for res in chroma_results:
            pg_data = self.pg_connector.get_record(Pattern, res["id"])
            if pg_data:
                # Combine ChromaDB's document/embedding/similarity with PostgreSQL's full metadata
                combined_res = {
                    "id": res["id"],
                    "document": res["document"],
                    "embedding": res.get(
                        "embedding"
                    ),  # ChromaDB search doesn't return embedding by default
                    "metadata": pg_data[
                        "metadata_json"
                    ],  # Use PG's metadata as source of truth
                    "similarity_score": res["similarity_score"],
                    "project_id": pg_data.get("project_id"),
                    "created_at": pg_data["created_at"],
                    "updated_at": pg_data["updated_at"],
                }
                final_results.append(combined_res)
        return final_results

    def search_patterns_by_metadata(
        self, metadata_filter: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """
        Search patterns by metadata only (no embedding search).
        Used by workflow manager to find patterns by status.
        """
        # Get all patterns from PostgreSQL that match the metadata filter
        patterns = self.pg_connector.search_records_by_metadata(
            Pattern, metadata_filter
        )

        final_results = []
        for pg_pattern in patterns:
            # Get the document from ChromaDB if available
            chroma_doc = self.chroma_connector.get_document(
                "code_patterns", pg_pattern["id"]
            )

            combined_result = {
                "id": pg_pattern["id"],
                "document": chroma_doc.get("document", "") if chroma_doc else "",
                "metadata": pg_pattern["metadata_json"],
                "project_id": pg_pattern.get("project_id"),
                "created_at": pg_pattern["created_at"],
                "updated_at": pg_pattern["updated_at"],
            }

            # Add any additional fields from metadata for easier access
            if isinstance(pg_pattern["metadata_json"], dict):
                for key in ["status", "current_version", "versions", "reviews"]:
                    if key in pg_pattern["metadata_json"]:
                        combined_result[key] = pg_pattern["metadata_json"][key]

            final_results.append(combined_result)

        return final_results

    # --- Error Solution Management (PostgreSQL + ChromaDB) ---
    def add_error_solution(
        self,
        document_text: str,
        embedding: list[float],
        metadata: dict[str, Any],
        solution_id: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> Optional[str]:
        """
        Adds a new error solution, storing metadata in PostgreSQL and document/embedding in ChromaDB.
        """
        solution_id = solution_id or str(uuid.uuid4())
        now_iso = datetime.now().isoformat()

        pg_metadata = {
            "id": solution_id,
            "project_id": project_id,
            "document_text": document_text,
            "created_at": metadata.get("created_at", now_iso),
            "updated_at": now_iso,
            "error_category": metadata.get("error_category"),
            "resolution_steps": metadata.get("resolution_steps"),
            "avg_resolution_time": metadata.get("avg_resolution_time"),
            "metadata_json": metadata,
        }

        pg_success = self.pg_connector.add_record(ErrorSolution, pg_metadata)
        if not pg_success:
            self._logger.error(
                f"Failed to add error solution metadata to PostgreSQL for ID: {solution_id}"
            )
            return None

        chroma_success = self.chroma_connector.add_document(
            collection_name="error_solutions",
            doc_id=solution_id,
            document=document_text,
            embedding=embedding,
            metadata=metadata,
        )
        if not chroma_success:
            self.pg_connector.delete_record(ErrorSolution, solution_id)
            self._logger.error(
                f"Failed to add error solution document to ChromaDB for ID: {solution_id}. PostgreSQL record rolled back."
            )
            return None

        self._logger.info(
            f"Error solution '{solution_id}' added successfully to both databases."
        )
        return solution_id

    def get_error_solution(self, solution_id: str) -> Optional[dict[str, Any]]:
        """
        Retrieves an error solution by ID, combining data from PostgreSQL and ChromaDB.
        """
        pg_data = self.pg_connector.get_record(ErrorSolution, solution_id)
        if not pg_data:
            return None

        chroma_data = self.chroma_connector.get_document(
            collection_name="error_solutions", doc_id=solution_id
        )

        combined_data = {
            "id": pg_data["id"],
            "project_id": pg_data.get("project_id"),
            "document": chroma_data["document"]
            if chroma_data
            else pg_data["document_text"],
            "embedding": chroma_data["embedding"] if chroma_data else None,
            "metadata": pg_data["metadata_json"],
            "created_at": pg_data["created_at"],
            "updated_at": pg_data["updated_at"],
        }
        return combined_data

    def update_error_solution(
        self,
        solution_id: str,
        document_text: Optional[str] = None,
        embedding: Optional[list[float]] = None,
        metadata: Optional[dict[str, Any]] = None,
        project_id: Optional[str] = None,
    ) -> bool:
        """
        Updates an existing error solution in both PostgreSQL and ChromaDB.
        """
        pg_updates = {"updated_at": datetime.now().isoformat()}
        chroma_updates = {}

        if project_id is not None:
            pg_updates["project_id"] = project_id
        if document_text is not None:
            pg_updates["document_text"] = document_text
            chroma_updates["document"] = document_text
        if embedding is not None:
            chroma_updates["embedding"] = embedding
        if metadata is not None:
            pg_updates["metadata_json"] = metadata
            chroma_updates["metadata"] = metadata
            if "error_category" in metadata:
                pg_updates["error_category"] = metadata["error_category"]
            if "resolution_steps" in metadata:
                pg_updates["resolution_steps"] = metadata["resolution_steps"]
            if "avg_resolution_time" in metadata:
                pg_updates["avg_resolution_time"] = metadata["avg_resolution_time"]

        pg_success = self.pg_connector.update_record(
            ErrorSolution, solution_id, pg_updates
        )
        if not pg_success:
            self._logger.error(
                f"Failed to update error solution metadata in PostgreSQL for ID: {solution_id}"
            )
            return False

        chroma_success = self.chroma_connector.update_document(
            collection_name="error_solutions",
            doc_id=solution_id,
            document=chroma_updates.get("document"),
            embedding=chroma_updates.get("embedding"),
            metadata=chroma_updates.get("metadata"),
        )
        if not chroma_success:
            self._logger.warning(
                f"Failed to update error solution document/embedding in ChromaDB for ID: {solution_id}. PostgreSQL record updated."
            )
            return False

        self._logger.info(
            f"Error solution '{solution_id}' updated successfully in both databases."
        )
        return True

    def delete_error_solution(self, solution_id: str) -> bool:
        """
        Deletes an error solution from both PostgreSQL and ChromaDB.
        """
        pg_success = self.pg_connector.delete_record(ErrorSolution, solution_id)
        if not pg_success:
            self._logger.error(
                f"Failed to delete error solution metadata from PostgreSQL for ID: {solution_id}"
            )
            return False

        chroma_success = self.chroma_connector.delete_document(
            collection_name="error_solutions", doc_id=solution_id
        )
        if not chroma_success:
            self._logger.warning(
                f"Failed to delete error solution document from ChromaDB for ID: {solution_id}. PostgreSQL record deleted."
            )
            return False

        self._logger.info(
            f"Error solution '{solution_id}' deleted successfully from both databases."
        )
        return True

    def search_error_solutions(
        self,
        query_embedding: list[float],
        n_results: int = 10,
        min_similarity: float = 0.7,
        metadata_filter: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        """
        Searches for error solutions using ChromaDB, then retrieves full metadata from PostgreSQL.
        """
        chroma_results = self.chroma_connector.search_documents(
            collection_name="error_solutions",
            query_embedding=query_embedding,
            n_results=n_results,
            min_similarity=min_similarity,
            where_clause=metadata_filter,
        )

        final_results = []
        for res in chroma_results:
            pg_data = self.pg_connector.get_record(ErrorSolution, res["id"])
            if pg_data:
                combined_res = {
                    "id": res["id"],
                    "document": res["document"],
                    "embedding": res.get("embedding"),
                    "metadata": pg_data["metadata_json"],
                    "similarity_score": res["similarity_score"],
                    "project_id": pg_data.get("project_id"),
                    "created_at": pg_data.get("created_at"),
                    "updated_at": pg_data.get("updated_at"),
                }
                final_results.append(combined_res)
        return final_results

    # --- Pattern Category Management (PostgreSQL only) ---
    def add_category(
        self,
        name: str,
        description: Optional[str] = None,
        category_id: Optional[str] = None,
    ) -> Optional[str]:
        """Adds a new pattern category."""
        category_id = category_id or str(uuid.uuid4())
        data = {"id": category_id, "name": name, "description": description}
        return self.pg_connector.add_record(PatternCategory, data)

    def get_category(self, category_id: str) -> Optional[dict[str, Any]]:
        """Retrieves a pattern category by ID."""
        return self.pg_connector.get_record(PatternCategory, category_id)

    def update_category(self, category_id: str, updates: dict[str, Any]) -> bool:
        """Updates an existing pattern category."""
        return self.pg_connector.update_record(PatternCategory, category_id, updates)

    def delete_category(self, category_id: str) -> bool:
        """Deletes a pattern category and its associated links."""
        return self.pg_connector.delete_record(PatternCategory, category_id)

    def assign_pattern_to_category(self, pattern_id: str, category_id: str) -> bool:
        """Assigns a pattern to a category."""
        return self.pg_connector.add_pattern_to_category(pattern_id, category_id)

    def remove_pattern_from_category(self, pattern_id: str, category_id: str) -> bool:
        """Removes a pattern from a category."""
        return self.pg_connector.remove_pattern_from_category(pattern_id, category_id)

    def get_patterns_by_category(self, category_id: str) -> list[str]:
        """Gets all pattern IDs in a category."""
        return self.pg_connector.get_patterns_in_category(category_id)

    def get_pattern_categories(self, pattern_id: str) -> list[dict[str, Any]]:
        """Gets all categories assigned to a pattern."""
        return self.pg_connector.get_categories_for_pattern(pattern_id)

    # --- Team Access Management (PostgreSQL only) ---
    def add_team_access(
        self, user_id: str, project_id: str, role: str, access_id: Optional[str] = None
    ) -> Optional[str]:
        """Adds team access for a user to a project."""
        access_id = access_id or str(uuid.uuid4())
        data = {
            "id": access_id,
            "user_id": user_id,
            "project_id": project_id,
            "role": role,
        }
        return self.pg_connector.add_record(TeamAccess, data)

    def get_team_access(self, access_id: str) -> Optional[dict[str, Any]]:
        """Retrieves team access by ID."""
        return self.pg_connector.get_record(TeamAccess, access_id)

    def update_team_access(self, access_id: str, updates: dict[str, Any]) -> bool:
        """Updates existing team access."""
        return self.pg_connector.update_record(TeamAccess, access_id, updates)

    def delete_team_access(self, access_id: str) -> bool:
        """Deletes team access."""
        return self.pg_connector.delete_record(TeamAccess, access_id)

    def get_team_access_for_project(self, project_id: str) -> list[dict[str, Any]]:
        """Gets all team access records for a project."""
        return self.pg_connector.filter_records(TeamAccess, {"project_id": project_id})

    # --- Compatibility Matrix Management (PostgreSQL only) ---
    def add_compatibility_entry(
        self,
        source_tech: str,
        target_tech: str,
        compatibility_score: float,
        notes: Optional[str] = None,
        entry_id: Optional[str] = None,
    ) -> Optional[str]:
        """Adds a new compatibility matrix entry."""
        entry_id = entry_id or str(uuid.uuid4())
        data = {
            "id": entry_id,
            "source_tech": source_tech,
            "target_tech": target_tech,
            "compatibility_score": compatibility_score,
            "notes": notes,
        }
        return self.pg_connector.add_record(CompatibilityMatrix, data)

    def get_compatibility_entry(self, entry_id: str) -> Optional[dict[str, Any]]:
        """Retrieves a compatibility matrix entry by ID."""
        return self.pg_connector.get_record(CompatibilityMatrix, entry_id)

    def update_compatibility_entry(
        self, entry_id: str, updates: dict[str, Any]
    ) -> bool:
        """Updates an existing compatibility matrix entry."""
        return self.pg_connector.update_record(CompatibilityMatrix, entry_id, updates)

    def delete_compatibility_entry(self, entry_id: str) -> bool:
        """Deletes a compatibility matrix entry."""
        return self.pg_connector.delete_record(CompatibilityMatrix, entry_id)

    def search_compatibility_entries(
        self,
        source_tech: Optional[str] = None,
        target_tech: Optional[str] = None,
        min_score: Optional[float] = None,
        max_score: Optional[float] = None,
    ) -> list[dict[str, Any]]:
        """Searches compatibility entries by source/target tech and score range."""
        filters = {}
        if source_tech:
            filters["source_tech"] = source_tech
        if target_tech:
            filters["target_tech"] = target_tech

        results = self.pg_connector.filter_records(CompatibilityMatrix, filters)

        if min_score is not None or max_score is not None:
            filtered_results = []
            for res in results:
                score = res.get("compatibility_score")
                if score is not None:
                    if (min_score is None or score >= min_score) and (
                        max_score is None or score <= max_score
                    ):
                        filtered_results.append(res)
            return filtered_results
        return results
