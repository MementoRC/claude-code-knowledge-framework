#!/usr/bin/env python3
"""
UCKN Database Initialization Script

This script initializes the UCKN database schema using the migration files.
"""

import os
import sys
import logging
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from uckn.storage.postgresql_connector import PostgreSQLConnector
from sqlalchemy import text

logger = logging.getLogger(__name__)


def init_database(db_url: str = None):
    """Initialize the UCKN database schema."""
    
    # Get database URL from environment or parameter
    db_url = db_url or os.environ.get("UCKN_DATABASE_URL")
    
    if not db_url:
        print("❌ Database URL not provided.")
        print("Set UCKN_DATABASE_URL environment variable or pass as parameter.")
        print("Example: postgresql://uckn:password@localhost:5432/shared_uckn")
        return False
    
    print(f"🔌 Connecting to database: {db_url.split('@')[1] if '@' in db_url else db_url}")
    
    try:
        # Initialize PostgreSQL connector
        pg_connector = PostgreSQLConnector(db_url=db_url)
        
        if not pg_connector.is_available():
            print("❌ Cannot connect to PostgreSQL database")
            return False
        
        print("✅ Connected to PostgreSQL")
        
        # Create all tables using SQLAlchemy models
        print("📊 Creating database schema...")
        
        with pg_connector.get_db_session() as session:
            # Import models to ensure they're registered
            from uckn.storage.postgresql_connector import (
                Base, Project, Pattern, ErrorSolution, 
                PatternCategory, PatternCategoryLink, TeamAccess, CompatibilityMatrix
            )
            
            # Create all tables
            Base.metadata.create_all(pg_connector.engine)
            
            # Verify tables were created
            tables_query = text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name;
            """)
            
            result = session.execute(tables_query)
            tables = [row[0] for row in result.fetchall()]
            
            expected_tables = [
                'compatibility_matrix',
                'error_solutions', 
                'pattern_categories',
                'pattern_category_links',
                'patterns',
                'projects',
                'team_access'
            ]
            
            missing_tables = set(expected_tables) - set(tables)
            if missing_tables:
                print(f"⚠️  Warning: Missing tables: {missing_tables}")
            else:
                print("✅ All tables created successfully")
            
            print(f"📋 Created tables: {', '.join(sorted(tables))}")
            
            # Create default categories
            print("📂 Creating default pattern categories...")
            default_categories = [
                ("setup", "Project setup and configuration patterns"),
                ("bugfix", "Bug fixes and error resolutions"),
                ("optimization", "Performance and optimization patterns"),
                ("integration", "Integration and API patterns"),
                ("testing", "Testing strategies and patterns"),
                ("deployment", "Deployment and CI/CD patterns"),
                ("security", "Security implementation patterns"),
                ("best_practice", "Best practices and coding standards")
            ]
            
            for cat_name, cat_desc in default_categories:
                # Check if category exists
                existing = session.execute(
                    text("SELECT id FROM pattern_categories WHERE name = :name"),
                    {"name": cat_name}
                ).fetchone()
                
                if not existing:
                    session.execute(
                        text("""
                            INSERT INTO pattern_categories (id, name, description, created_at, updated_at)
                            VALUES (gen_random_uuid()::text, :name, :description, NOW(), NOW())
                        """),
                        {"name": cat_name, "description": cat_desc}
                    )
            
            session.commit()
            print("✅ Default categories created")
            
            # Show database info
            info_query = text("""
                SELECT 
                    'projects' as table_name, COUNT(*) as count FROM projects
                UNION ALL
                SELECT 'patterns', COUNT(*) FROM patterns
                UNION ALL  
                SELECT 'error_solutions', COUNT(*) FROM error_solutions
                UNION ALL
                SELECT 'pattern_categories', COUNT(*) FROM pattern_categories
                ORDER BY table_name;
            """)
            
            result = session.execute(info_query)
            print("\n📊 Database Status:")
            for row in result.fetchall():
                print(f"   {row[0]}: {row[1]} records")
        
        print("\n🎉 Database initialization complete!")
        print("\n📝 Next steps:")
        print("1. Test the connection:")
        print(f"   export UCKN_DATABASE_URL='{db_url}'")
        print("   pixi run --project /path/to/uckn python -c \"from uckn.core.organisms.knowledge_manager import KnowledgeManager; km = KnowledgeManager(); print('✅ UCKN ready!')\"")
        print("\n2. Start using UCKN with Claude Code!")
        
        return True
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        logger.exception("Database initialization error")
        return False


def main():
    """Main entry point for database initialization."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Initialize UCKN database schema")
    parser.add_argument(
        "--db-url", 
        help="Database URL (default: from UCKN_DATABASE_URL env var)",
        default=None
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    
    success = init_database(args.db_url)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()