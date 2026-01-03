"""
Database models for UCKN storage.
This module defines the SQLAlchemy models used by the application.
"""

from sqlalchemy import JSONB, Column, DateTime, Float, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class Pattern(Base):
    """Pattern storage model."""

    __tablename__ = "patterns"

    id = Column(String, primary_key=True)
    project_id = Column(String, nullable=True)
    document_text = Column(String, nullable=False)
    metadata_json = Column(JSONB, nullable=True)
    technology_stack = Column(String, nullable=True)
    pattern_type = Column(String, nullable=True)
    success_rate = Column(Float, nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())


class CompatibilityMatrix(Base):
    """Compatibility matrix storage model."""

    __tablename__ = "compatibility_matrix"

    id = Column(String, primary_key=True)
    source_tech = Column(String, nullable=False)
    target_tech = Column(String, nullable=False)
    compatibility_score = Column(Float, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())


class ErrorSolution(Base):
    """Error solution storage model."""

    __tablename__ = "error_solutions"

    id = Column(String, primary_key=True)
    error_type = Column(String, nullable=False)
    error_message = Column(Text, nullable=True)
    solution_text = Column(Text, nullable=False)
    metadata_json = Column(JSONB, nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())


class PatternCategoryLink(Base):
    """Pattern to category relationship."""

    __tablename__ = "pattern_category_links"

    id = Column(String, primary_key=True)
    pattern_id = Column(String, nullable=False)
    category_id = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=True)


class Category(Base):
    """Category storage model."""

    __tablename__ = "categories"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())
