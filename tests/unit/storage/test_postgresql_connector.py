import uuid
from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from src.uckn.storage.postgresql_connector import (
    Base,
    CompatibilityMatrix,
    ErrorSolution,
    Pattern,
    PatternCategory,
    PatternCategoryLink,
    PostgreSQLConnector,
    Project,
    TeamAccess,
)

# Use an in-memory SQLite database for testing
# This allows testing the ORM and connector logic without a real PostgreSQL instance
# Note: SQLite's JSON support is limited compared to PostgreSQL's JSONB.
# For full JSONB testing, a real PostgreSQL instance would be needed.
TEST_DB_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def pg_connector():
    """Provides a PostgreSQLConnector instance connected to an in-memory SQLite DB."""
    connector = PostgreSQLConnector(db_url=TEST_DB_URL)
    # Ensure tables are created for the in-memory SQLite DB
    Base.metadata.create_all(connector.engine)
    yield connector
    # Clean up after each test
    Base.metadata.drop_all(connector.engine)


@pytest.fixture(scope="function")
def pg_session(pg_connector):
    """Provides a SQLAlchemy session for direct DB interaction in tests."""
    Session = sessionmaker(bind=pg_connector.engine)
    session = Session()
    yield session
    session.close()


def test_postgresql_connector_initialization(pg_connector):
    assert pg_connector.engine is not None
    assert pg_connector.SessionLocal is not None
    assert pg_connector.is_available()


def test_add_project(pg_connector):
    project_id = str(uuid.uuid4())
    name = "Test Project"
    description = "A project for testing."
    added_id = pg_connector.add_record(
        Project, {"id": project_id, "name": name, "description": description}
    )
    assert added_id == project_id

    retrieved_project = pg_connector.get_record(Project, project_id)
    assert retrieved_project is not None
    assert retrieved_project["name"] == name
    assert retrieved_project["description"] == description
    assert isinstance(retrieved_project["created_at"], datetime)


def test_get_project_not_found(pg_connector):
    retrieved_project = pg_connector.get_record(Project, str(uuid.uuid4()))
    assert retrieved_project is None


def test_update_project(pg_connector):
    project_id = str(uuid.uuid4())
    pg_connector.add_record(
        Project, {"id": project_id, "name": "Old Name", "description": "Old Desc"}
    )

    new_name = "New Project Name"
    updated = pg_connector.update_record(Project, project_id, {"name": new_name})
    assert updated

    retrieved_project = pg_connector.get_record(Project, project_id)
    assert retrieved_project["name"] == new_name
    assert (
        retrieved_project["description"] == "Old Desc"
    )  # Description should be unchanged
    assert retrieved_project["updated_at"] > retrieved_project["created_at"]


def test_delete_project(pg_connector):
    project_id = str(uuid.uuid4())
    pg_connector.add_record(Project, {"id": project_id, "name": "To Delete"})

    deleted = pg_connector.delete_record(Project, project_id)
    assert deleted

    retrieved_project = pg_connector.get_record(Project, project_id)
    assert retrieved_project is None


def test_add_pattern(pg_connector):
    project_id = pg_connector.add_record(
        Project, {"id": str(uuid.uuid4()), "name": "Pattern Project"}
    )
    pattern_id = str(uuid.uuid4())
    doc_text = "Example code pattern."
    metadata = {
        "technology_stack": "Python",
        "pattern_type": "Design",
        "success_rate": 0.95,
    }

    added_id = pg_connector.add_record(
        Pattern,
        {
            "id": pattern_id,
            "project_id": project_id,
            "document_text": doc_text,
            "metadata_json": metadata,
            "technology_stack": metadata["technology_stack"],
            "pattern_type": metadata["pattern_type"],
            "success_rate": metadata["success_rate"],
        },
    )
    assert added_id == pattern_id

    retrieved_pattern = pg_connector.get_record(Pattern, pattern_id)
    assert retrieved_pattern is not None
    assert retrieved_pattern["document_text"] == doc_text
    assert retrieved_pattern["metadata_json"] == metadata
    assert retrieved_pattern["technology_stack"] == "Python"


def test_add_error_solution(pg_connector):
    project_id = pg_connector.add_record(
        Project, {"id": str(uuid.uuid4()), "name": "Error Project"}
    )
    solution_id = str(uuid.uuid4())
    doc_text = "Error: File not found."
    metadata = {
        "error_category": "IO",
        "resolution_steps": "Check path",
        "avg_resolution_time": 15.5,
    }

    added_id = pg_connector.add_record(
        ErrorSolution,
        {
            "id": solution_id,
            "project_id": project_id,
            "document_text": doc_text,
            "metadata_json": metadata,
            "error_category": metadata["error_category"],
            "resolution_steps": metadata["resolution_steps"],
            "avg_resolution_time": metadata["avg_resolution_time"],
        },
    )
    assert added_id == solution_id

    retrieved_solution = pg_connector.get_record(ErrorSolution, solution_id)
    assert retrieved_solution is not None
    assert retrieved_solution["document_text"] == doc_text
    assert retrieved_solution["metadata_json"] == metadata
    assert retrieved_solution["error_category"] == "IO"


def test_add_pattern_category(pg_connector):
    category_id = str(uuid.uuid4())
    name = "Refactoring Patterns"
    added_id = pg_connector.add_record(
        PatternCategory, {"id": category_id, "name": name}
    )
    assert added_id == category_id

    retrieved_category = pg_connector.get_record(PatternCategory, category_id)
    assert retrieved_category["name"] == name


def test_assign_pattern_to_category(pg_connector):
    project_id = pg_connector.add_record(
        Project, {"id": str(uuid.uuid4()), "name": "Proj1"}
    )
    pattern_id = pg_connector.add_record(
        Pattern,
        {
            "id": str(uuid.uuid4()),
            "project_id": project_id,
            "document_text": "Pattern A",
            "metadata_json": {},
        },
    )
    category_id = pg_connector.add_record(
        PatternCategory, {"id": str(uuid.uuid4()), "name": "Category X"}
    )

    linked = pg_connector.add_pattern_to_category(pattern_id, category_id)
    assert linked

    patterns_in_cat = pg_connector.get_patterns_in_category(category_id)
    assert pattern_id in patterns_in_cat

    categories_for_pattern = pg_connector.get_categories_for_pattern(pattern_id)
    assert any(c["id"] == category_id for c in categories_for_pattern)

    # Test idempotency
    linked_again = pg_connector.add_pattern_to_category(pattern_id, category_id)
    assert linked_again  # Should still return True


def test_remove_pattern_from_category(pg_connector):
    project_id = pg_connector.add_record(
        Project, {"id": str(uuid.uuid4()), "name": "Proj2"}
    )
    pattern_id = pg_connector.add_record(
        Pattern,
        {
            "id": str(uuid.uuid4()),
            "project_id": project_id,
            "document_text": "Pattern B",
            "metadata_json": {},
        },
    )
    category_id = pg_connector.add_record(
        PatternCategory, {"id": str(uuid.uuid4()), "name": "Category Y"}
    )
    pg_connector.add_pattern_to_category(pattern_id, category_id)

    removed = pg_connector.remove_pattern_from_category(pattern_id, category_id)
    assert removed

    patterns_in_cat = pg_connector.get_patterns_in_category(category_id)
    assert pattern_id not in patterns_in_cat

    # Test idempotency
    removed_again = pg_connector.remove_pattern_from_category(pattern_id, category_id)
    assert removed_again  # Should still return True if not found


def test_get_all_records(pg_connector):
    pg_connector.add_record(Project, {"id": str(uuid.uuid4()), "name": "P1"})
    pg_connector.add_record(Project, {"id": str(uuid.uuid4()), "name": "P2"})

    projects = pg_connector.get_all_records(Project)
    assert len(projects) == 2


def test_filter_records(pg_connector):
    pg_connector.reset_db()  # Clear previous data
    proj1_id = pg_connector.add_record(
        Project, {"id": str(uuid.uuid4()), "name": "Filter Project 1"}
    )
    proj2_id = pg_connector.add_record(
        Project, {"id": str(uuid.uuid4()), "name": "Filter Project 2"}
    )

    pg_connector.add_record(
        Pattern,
        {
            "id": str(uuid.uuid4()),
            "project_id": proj1_id,
            "document_text": "Doc A",
            "metadata_json": {"tech": "Python"},
            "technology_stack": "Python",
        },
    )
    pg_connector.add_record(
        Pattern,
        {
            "id": str(uuid.uuid4()),
            "project_id": proj1_id,
            "document_text": "Doc B",
            "metadata_json": {"tech": "Java"},
            "technology_stack": "Java",
        },
    )
    pg_connector.add_record(
        Pattern,
        {
            "id": str(uuid.uuid4()),
            "project_id": proj2_id,
            "document_text": "Doc C",
            "metadata_json": {"tech": "Python"},
            "technology_stack": "Python",
        },
    )

    python_patterns = pg_connector.filter_records(
        Pattern, {"technology_stack": "Python"}
    )
    assert len(python_patterns) == 2
    assert all(p["technology_stack"] == "Python" for p in python_patterns)

    proj1_patterns = pg_connector.filter_records(Pattern, {"project_id": proj1_id})
    assert len(proj1_patterns) == 2


def test_reset_db(pg_connector):
    pg_connector.add_record(Project, {"id": str(uuid.uuid4()), "name": "Before Reset"})
    assert len(pg_connector.get_all_records(Project)) == 1

    reset_success = pg_connector.reset_db()
    assert reset_success
    assert len(pg_connector.get_all_records(Project)) == 0


def test_team_access_crud(pg_connector):
    project_id = pg_connector.add_record(
        Project, {"id": str(uuid.uuid4()), "name": "Access Project"}
    )
    user_id = "user123"
    role = "admin"
    access_id = str(uuid.uuid4())

    added_id = pg_connector.add_record(
        TeamAccess,
        {"id": access_id, "user_id": user_id, "project_id": project_id, "role": role},
    )
    assert added_id == access_id

    retrieved_access = pg_connector.get_record(TeamAccess, access_id)
    assert retrieved_access["user_id"] == user_id
    assert retrieved_access["role"] == role

    updated = pg_connector.update_record(TeamAccess, access_id, {"role": "viewer"})
    assert updated
    assert pg_connector.get_record(TeamAccess, access_id)["role"] == "viewer"

    deleted = pg_connector.delete_record(TeamAccess, access_id)
    assert deleted
    assert pg_connector.get_record(TeamAccess, access_id) is None


def test_compatibility_matrix_crud(pg_connector):
    entry_id = str(uuid.uuid4())
    source_tech = "Python"
    target_tech = "Django"
    score = 0.85
    notes = "Good compatibility with minor adjustments."

    added_id = pg_connector.add_record(
        CompatibilityMatrix,
        {
            "id": entry_id,
            "source_tech": source_tech,
            "target_tech": target_tech,
            "compatibility_score": score,
            "notes": notes,
        },
    )
    assert added_id == entry_id

    retrieved_entry = pg_connector.get_record(CompatibilityMatrix, entry_id)
    assert retrieved_entry["source_tech"] == source_tech
    assert retrieved_entry["compatibility_score"] == score

    updated = pg_connector.update_record(
        CompatibilityMatrix, entry_id, {"compatibility_score": 0.9}
    )
    assert updated
    assert (
        pg_connector.get_record(CompatibilityMatrix, entry_id)["compatibility_score"]
        == 0.9
    )

    deleted = pg_connector.delete_record(CompatibilityMatrix, entry_id)
    assert deleted
    assert pg_connector.get_record(CompatibilityMatrix, entry_id) is None
