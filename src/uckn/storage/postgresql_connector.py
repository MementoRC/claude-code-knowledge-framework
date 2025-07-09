import logging
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    String,
    Text,
    create_engine,
    text,
)
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.pool import QueuePool
from sqlalchemy.types import JSON, TypeDecorator

# Import JSONB specifically for PostgreSQL dialect
try:
    from sqlalchemy.dialects.postgresql import JSONB
except ImportError:
    # Fallback for environments where psycopg2/psycopg is not installed
    # or when running against non-PostgreSQL databases like SQLite
    JSONB = None

Base = declarative_base()
_logger = logging.getLogger(__name__)


class JSONBOrJSON(TypeDecorator):
    """
    A TypeDecorator that uses JSONB for PostgreSQL and JSON for other databases.
    This provides cross-database compatibility for JSON column types.
    """

    impl = JSON  # Default implementation for non-PostgreSQL dialects

    cache_ok = True  # Indicate that this type is safe to cache

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql" and JSONB is not None:
            return dialect.type_descriptor(JSONB())
        else:
            return dialect.type_descriptor(JSON())

    def process_bind_param(self, value, dialect):
        # No special processing needed for binding, SQLAlchemy handles JSON serialization
        return value

    def process_result_value(self, value, dialect):
        # No special processing needed for results, SQLAlchemy handles JSON deserialization
        return value


# To make the JSON column mutable (i.e., changes to the dictionary are detected)
MutableJSONBOrJSON = MutableDict.as_mutable(JSONBOrJSON)


class Project(Base):
    __tablename__ = "projects"
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    patterns = relationship(
        "Pattern", back_populates="project", cascade="all, delete-orphan"
    )
    error_solutions = relationship(
        "ErrorSolution", back_populates="project", cascade="all, delete-orphan"
    )
    team_access = relationship(
        "TeamAccess", back_populates="project", cascade="all, delete-orphan"
    )


class Pattern(Base):
    __tablename__ = "patterns"
    id = Column(String, primary_key=True, index=True)
    project_id = Column(
        String, ForeignKey("projects.id"), nullable=True
    )  # Optional link to project
    document_text = Column(Text, nullable=False)
    # Use MutableJSONBOrJSON for cross-database compatibility and mutability
    metadata_json = Column(MutableJSONBOrJSON, nullable=False, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Specific metadata fields for easier querying
    technology_stack = Column(String, nullable=True)  # Comma-separated string
    pattern_type = Column(String, nullable=True)
    success_rate = Column(Float, nullable=True)

    project = relationship("Project", back_populates="patterns")
    category_links = relationship(
        "PatternCategoryLink", back_populates="pattern", cascade="all, delete-orphan"
    )


class ErrorSolution(Base):
    __tablename__ = "error_solutions"
    id = Column(String, primary_key=True, index=True)
    project_id = Column(
        String, ForeignKey("projects.id"), nullable=True
    )  # Optional link to project
    document_text = Column(Text, nullable=False)
    # Use MutableJSONBOrJSON for cross-database compatibility and mutability
    metadata_json = Column(MutableJSONBOrJSON, nullable=False, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Specific metadata fields for easier querying
    error_category = Column(String, nullable=True)
    resolution_steps = Column(Text, nullable=True)  # Comma-separated string
    avg_resolution_time = Column(Float, nullable=True)

    project = relationship("Project", back_populates="error_solutions")


class PatternCategory(Base):
    __tablename__ = "pattern_categories"
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    pattern_links = relationship(
        "PatternCategoryLink", back_populates="category", cascade="all, delete-orphan"
    )


class PatternCategoryLink(Base):
    __tablename__ = "pattern_category_links"
    pattern_id = Column(String, ForeignKey("patterns.id"), primary_key=True)
    category_id = Column(String, ForeignKey("pattern_categories.id"), primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    pattern = relationship("Pattern", back_populates="category_links")
    category = relationship("PatternCategory", back_populates="pattern_links")


class TeamAccess(Base):
    __tablename__ = "team_access"
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, nullable=False)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    role = Column(String, nullable=False)  # e.g., 'admin', 'contributor', 'viewer'
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="team_access")


class CompatibilityMatrix(Base):
    __tablename__ = "compatibility_matrix"
    id = Column(String, primary_key=True, index=True)
    source_tech = Column(String, nullable=False)
    target_tech = Column(String, nullable=False)
    compatibility_score = Column(Float, nullable=False)  # 0.0 to 1.0
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        # Ensure unique combination of source and target technologies
        # This can be a soft unique constraint if bidirectional compatibility is handled
        # by two separate entries (A->B and B->A)
        # UniqueConstraint('source_tech', 'target_tech', name='_source_target_uc'),
    )


class PostgreSQLConnector:
    """
    Manages connection and operations with PostgreSQL for UCKN knowledge metadata.
    Uses SQLAlchemy for ORM and connection pooling.
    """

    def __init__(
        self,
        db_url: str = "postgresql://user:password@localhost:5432/uckn_db",
        pool_size: int = 10,
        max_overflow: int = 20,
    ):
        self.db_url = db_url
        self.engine = None
        self.SessionLocal = None
        self._logger = logging.getLogger(__name__)
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self._connect_to_db()

    def _connect_to_db(self) -> None:
        """Initializes the SQLAlchemy engine and session factory."""
        try:
            # Ensure we use psycopg (version 3) driver instead of psycopg2
            db_url = self.db_url
            if db_url.startswith("postgresql://"):
                db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)

            self.engine = create_engine(
                db_url,
                poolclass=QueuePool,
                pool_size=self.pool_size,
                max_overflow=self.max_overflow,
                pool_recycle=3600,  # Recycle connections after 1 hour
                echo=False,  # Set to True for SQL logging
            )
            self.SessionLocal = sessionmaker(
                autocommit=False, autoflush=False, bind=self.engine
            )
            self._logger.info(
                f"PostgreSQL engine initialized for {self.db_url.split('@')[-1]}"
            )
            # Base.metadata.create_all(self.engine) # This should be handled by Alembic migrations
            # self._logger.info("PostgreSQL tables checked/created (if not using Alembic).")
        except SQLAlchemyError as e:
            self._logger.error(f"Failed to initialize PostgreSQL connection: {e}")
            self.engine = None
            self.SessionLocal = None

    @contextmanager
    def get_db_session(self):
        """Provides a transactional SQLAlchemy session."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            self._logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()

    def is_available(self) -> bool:
        """Checks if the PostgreSQL connection is ready."""
        if self.engine is None or self.SessionLocal is None:
            return False
        try:
            with self.get_db_session() as session:
                session.execute(text("SELECT 1"))
            return True
        except SQLAlchemyError as e:
            self._logger.error(f"PostgreSQL connection check failed: {e}")
            return False

    def add_record(self, model: Base, data: dict[str, Any]) -> str | None:
        """Adds a new record to the database."""
        try:
            with self.get_db_session() as session:
                instance = model(**data)
                session.add(instance)
                session.flush()  # To get ID if it's generated by DB
                _logger.info(f"Added {model.__name__} with ID: {instance.id}")
                return instance.id
        except SQLAlchemyError as e:
            _logger.error(f"Failed to add {model.__name__} record: {e}")
            return None

    def get_record(self, model: Base, record_id: str) -> dict[str, Any] | None:
        """Retrieves a record by ID."""
        try:
            with self.get_db_session() as session:
                instance = session.query(model).filter_by(id=record_id).first()
                if instance:
                    return {
                        c.name: getattr(instance, c.name)
                        for c in instance.__table__.columns
                    }
                return None
        except SQLAlchemyError as e:
            _logger.error(f"Failed to get {model.__name__} record {record_id}: {e}")
            return None

    def update_record(
        self, model: Base, record_id: str, updates: dict[str, Any]
    ) -> bool:
        """Updates an existing record."""
        try:
            with self.get_db_session() as session:
                instance = session.query(model).filter_by(id=record_id).first()
                if instance:
                    for key, value in updates.items():
                        if hasattr(instance, key):
                            setattr(instance, key, value)
                    session.add(instance)
                    _logger.info(f"Updated {model.__name__} with ID: {record_id}")
                    return True
                _logger.warning(
                    f"{model.__name__} record {record_id} not found for update."
                )
                return False
        except SQLAlchemyError as e:
            _logger.error(f"Failed to update {model.__name__} record {record_id}: {e}")
            return False

    def delete_record(self, model: Base, record_id: str) -> bool:
        """Deletes a record by ID."""
        try:
            with self.get_db_session() as session:
                instance = session.query(model).filter_by(id=record_id).first()
                if instance:
                    session.delete(instance)
                    _logger.info(f"Deleted {model.__name__} with ID: {record_id}")
                    return True
                _logger.warning(
                    f"{model.__name__} record {record_id} not found for deletion."
                )
                return False
        except SQLAlchemyError as e:
            _logger.error(f"Failed to delete {model.__name__} record {record_id}: {e}")
            return False

    def get_all_records(
        self, model: Base, limit: int | None = None
    ) -> list[dict[str, Any]]:
        """Retrieves all records for a given model."""
        try:
            with self.get_db_session() as session:
                query = session.query(model)
                if limit:
                    query = query.limit(limit)
                results = query.all()
                return [
                    {
                        c.name: getattr(instance, c.name)
                        for c in instance.__table__.columns
                    }
                    for instance in results
                ]
        except SQLAlchemyError as e:
            _logger.error(f"Failed to retrieve all {model.__name__} records: {e}")
            return []

    def filter_records(
        self, model: Base, filters: dict[str, Any], limit: int | None = None
    ) -> list[dict[str, Any]]:
        """Filters records based on provided criteria."""
        try:
            with self.get_db_session() as session:
                query = session.query(model)
                for key, value in filters.items():
                    if hasattr(model, key):
                        query = query.filter(getattr(model, key) == value)
                if limit:
                    query = query.limit(limit)
                results = query.all()
                return [
                    {
                        c.name: getattr(instance, c.name)
                        for c in instance.__table__.columns
                    }
                    for instance in results
                ]
        except SQLAlchemyError as e:
            _logger.error(f"Failed to filter {model.__name__} records: {e}")
            return []

    def search_records_by_metadata(
        self, model: Base, metadata_filter: dict[str, Any], limit: int | None = None
    ) -> list[dict[str, Any]]:
        """Search records by JSONB/JSON metadata fields using cross-database compatible operators."""
        try:
            with self.get_db_session() as session:
                query = session.query(model)

                # Apply metadata filters using the cross-database compatible .contains() operator
                for key, value in metadata_filter.items():
                    # .contains() works for both PostgreSQL JSONB and SQLite JSON
                    filter_condition = model.metadata_json.contains({key: value})
                    query = query.filter(filter_condition)

                if limit:
                    query = query.limit(limit)

                results = query.all()
                return [
                    {
                        c.name: getattr(instance, c.name)
                        for c in instance.__table__.columns
                    }
                    for instance in results
                ]

        except SQLAlchemyError as e:
            _logger.error(f"Failed to search {model.__name__} records by metadata: {e}")
            return []

    # Specific methods for relationships
    def add_pattern_to_category(self, pattern_id: str, category_id: str) -> bool:
        """Links a pattern to a category."""
        try:
            with self.get_db_session() as session:
                # Check if link already exists (idempotent)
                existing_link = (
                    session.query(PatternCategoryLink)
                    .filter_by(pattern_id=pattern_id, category_id=category_id)
                    .first()
                )
                if existing_link:
                    _logger.info(
                        f"Link between pattern {pattern_id} and category {category_id} already exists."
                    )
                    return True

                link = PatternCategoryLink(
                    pattern_id=pattern_id, category_id=category_id
                )
                session.add(link)
                _logger.info(f"Linked pattern {pattern_id} to category {category_id}.")
                return True
        except SQLAlchemyError as e:
            _logger.error(
                f"Failed to link pattern {pattern_id} to category {category_id}: {e}"
            )
            return False

    def remove_pattern_from_category(self, pattern_id: str, category_id: str) -> bool:
        """Removes a link between a pattern and a category."""
        try:
            with self.get_db_session() as session:
                link = (
                    session.query(PatternCategoryLink)
                    .filter_by(pattern_id=pattern_id, category_id=category_id)
                    .first()
                )
                if link:
                    session.delete(link)
                    _logger.info(
                        f"Removed link between pattern {pattern_id} and category {category_id}."
                    )
                    return True
                _logger.warning(
                    f"Link between pattern {pattern_id} and category {category_id} not found."
                )
                return False
        except SQLAlchemyError as e:
            _logger.error(
                f"Failed to remove link between pattern {pattern_id} and category {category_id}: {e}"
            )
            return False

    def get_patterns_in_category(self, category_id: str) -> list[str]:
        """Gets all pattern IDs associated with a category."""
        try:
            with self.get_db_session() as session:
                links = (
                    session.query(PatternCategoryLink)
                    .filter_by(category_id=category_id)
                    .all()
                )
                return [link.pattern_id for link in links]
        except SQLAlchemyError as e:
            _logger.error(f"Failed to get patterns for category {category_id}: {e}")
            return []

    def get_categories_for_pattern(self, pattern_id: str) -> list[dict[str, Any]]:
        """Gets all categories associated with a pattern."""
        try:
            with self.get_db_session() as session:
                links = (
                    session.query(PatternCategoryLink)
                    .filter_by(pattern_id=pattern_id)
                    .all()
                )
                category_ids = [link.category_id for link in links]
                categories = (
                    session.query(PatternCategory)
                    .filter(PatternCategory.id.in_(category_ids))
                    .all()
                )
                return [
                    {c.name: getattr(cat, c.name) for c in cat.__table__.columns}
                    for cat in categories
                ]
        except SQLAlchemyError as e:
            _logger.error(f"Failed to get categories for pattern {pattern_id}: {e}")
            return []

    def reset_db(self) -> bool:
        """
        Drops all tables and recreates them. Use with extreme caution.
        This is primarily for testing or initial setup without Alembic.
        """
        if self.engine:
            try:
                Base.metadata.drop_all(self.engine)
                Base.metadata.create_all(self.engine)
                self._logger.info("PostgreSQL database reset successfully.")
                return True
            except SQLAlchemyError as e:
                self._logger.error(f"Failed to reset PostgreSQL database: {e}")
                return False
        return False
