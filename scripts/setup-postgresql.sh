#!/bin/bash
set -e

# UCKN PostgreSQL Database Setup Script
# This script sets up a PostgreSQL database for UCKN shared knowledge

echo "🗄️  Setting up UCKN PostgreSQL Database..."

# Configuration
DB_NAME="${UCKN_DB_NAME:-shared_uckn}"
DB_USER="${UCKN_DB_USER:-uckn}"
DB_PASSWORD="${UCKN_DB_PASSWORD:-uckn_secure_password}"
DB_HOST="${UCKN_DB_HOST:-localhost}"
DB_PORT="${UCKN_DB_PORT:-5432}"

# Function to check if PostgreSQL is running
check_postgres() {
    if ! command -v psql &> /dev/null; then
        echo "❌ PostgreSQL is not installed. Please install it first:"
        echo "   Ubuntu/Debian: sudo apt install postgresql postgresql-contrib"
        echo "   macOS: brew install postgresql"
        echo "   Docker: See setup instructions in the script"
        exit 1
    fi

    if ! pg_isready -h $DB_HOST -p $DB_PORT &> /dev/null; then
        echo "❌ PostgreSQL is not running on $DB_HOST:$DB_PORT"
        echo "   Start it with: sudo systemctl start postgresql (Linux)"
        echo "   Or: brew services start postgresql (macOS)"
        exit 1
    fi

    echo "✅ PostgreSQL is running"
}

# Function to create database and user
setup_database() {
    echo "📊 Creating database and user..."

    # Connect as postgres superuser to create database and user
    sudo -u postgres psql << EOF
-- Create user if it doesn't exist
DO \$\$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '$DB_USER') THEN
      CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
   END IF;
END
\$\$;

-- Create database if it doesn't exist
SELECT 'CREATE DATABASE $DB_NAME' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$DB_NAME')\gexec

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
ALTER USER $DB_USER CREATEDB;

-- Connect to the database and grant schema privileges
\c $DB_NAME
GRANT ALL ON SCHEMA public TO $DB_USER;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO $DB_USER;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO $DB_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO $DB_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO $DB_USER;

-- Create required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

\q
EOF

    echo "✅ Database $DB_NAME and user $DB_USER created successfully"
}

# Function to test connection
test_connection() {
    echo "🔌 Testing database connection..."

    export PGPASSWORD="$DB_PASSWORD"
    if psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT version();" &> /dev/null; then
        echo "✅ Connection successful!"

        # Show connection string
        echo ""
        echo "📝 Use this connection string:"
        echo "   postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME"
        echo ""
        echo "🔧 Environment variables:"
        echo "   export UCKN_DATABASE_URL=\"postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME\""

    else
        echo "❌ Connection failed"
        exit 1
    fi
    unset PGPASSWORD
}

# Function to setup with Docker (alternative)
setup_docker() {
    echo "🐳 Setting up PostgreSQL with Docker..."

    # Check if Docker is available
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker is not installed. Please install Docker first."
        exit 1
    fi

    # Stop existing container if running
    docker stop uckn-postgres 2>/dev/null || true
    docker rm uckn-postgres 2>/dev/null || true

    # Create and start PostgreSQL container
    docker run --name uckn-postgres \
      -e POSTGRES_USER=$DB_USER \
      -e POSTGRES_PASSWORD=$DB_PASSWORD \
      -e POSTGRES_DB=$DB_NAME \
      -p $DB_PORT:5432 \
      -v uckn_postgres_data:/var/lib/postgresql/data \
      -d postgres:15

    echo "⏳ Waiting for PostgreSQL to start..."
    sleep 10

    # Create extensions
    docker exec uckn-postgres psql -U $DB_USER -d $DB_NAME -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"
    docker exec uckn-postgres psql -U $DB_USER -d $DB_NAME -c "CREATE EXTENSION IF NOT EXISTS \"btree_gin\";"

    echo "✅ PostgreSQL Docker container created successfully"
    echo "📝 Connection string: postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME"
}

# Main execution
case "${1:-native}" in
    "docker")
        setup_docker
        ;;
    "native"|*)
        check_postgres
        setup_database
        test_connection
        ;;
esac

echo ""
echo "🎉 PostgreSQL setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Set environment variable:"
echo "   export UCKN_DATABASE_URL=\"postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME\""
echo ""
echo "2. Initialize UCKN database schema:"
echo "   uv run --project /path/to/uckn python -m uckn.storage.migrations.init"
echo ""
echo "3. Test with UCKN:"
echo "   uv run --project /path/to/uckn python -c \"from uckn.storage.postgresql_connector import PostgreSQLConnector; print('✅ UCKN can connect!' if PostgreSQLConnector('postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME').is_available() else '❌ Connection failed')\""
