# 🗄️ PostgreSQL Setup Guide for UCKN

This guide walks you through setting up PostgreSQL for UCKN's shared knowledge system.

## 🚀 Quick Setup (Recommended)

### Option 1: Automated Setup Script

```bash
# Clone UCKN framework
git clone https://github.com/MementoRC/claude-code-knowledge-framework.git
cd claude-code-knowledge-framework

# Run automated setup (native PostgreSQL)
./scripts/setup-postgresql.sh

# OR with Docker
./scripts/setup-postgresql.sh docker
```

The script will:
- ✅ Create database `shared_uckn`
- ✅ Create user `uckn` with secure password
- ✅ Set up proper permissions
- ✅ Install required extensions
- ✅ Provide connection string

## 🛠 Manual Setup

### Step 1: Install PostgreSQL

#### Ubuntu/Debian:
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

#### macOS:
```bash
brew install postgresql
brew services start postgresql
```

#### Docker:
```bash
docker run --name uckn-postgres \
  -e POSTGRES_USER=uckn \
  -e POSTGRES_PASSWORD=uckn_secure_password \
  -e POSTGRES_DB=shared_uckn \
  -p 5432:5432 \
  -v uckn_postgres_data:/var/lib/postgresql/data \
  -d postgres:15
```

### Step 2: Create Database and User

```bash
# Connect as postgres superuser
sudo -u postgres psql

# In PostgreSQL shell:
CREATE USER uckn WITH PASSWORD 'uckn_secure_password';
CREATE DATABASE shared_uckn;
GRANT ALL PRIVILEGES ON DATABASE shared_uckn TO uckn;
ALTER USER uckn CREATEDB;

# Connect to the new database
\c shared_uckn

# Grant schema privileges
GRANT ALL ON SCHEMA public TO uckn;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO uckn;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO uckn;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO uckn;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO uckn;

# Install required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

\q
```

### Step 3: Initialize UCKN Schema

```bash
# Set database URL
export UCKN_DATABASE_URL="postgresql://uckn:uckn_secure_password@localhost:5432/shared_uckn"

# Initialize UCKN database schema
pixi run --project /path/to/claude-code-knowledge-framework db-migrate

# Verify setup
pixi run --project /path/to/claude-code-knowledge-framework python -c "
from uckn.storage.postgresql_connector import PostgreSQLConnector
import os
db_url = os.environ['UCKN_DATABASE_URL']
conn = PostgreSQLConnector(db_url)
print('✅ UCKN PostgreSQL ready!' if conn.is_available() else '❌ Connection failed')
"
```

## 🔧 Configuration Options

### Environment Variables

Create a `.env` file or export these variables:

```bash
# Required
export UCKN_DATABASE_URL="postgresql://uckn:uckn_secure_password@localhost:5432/shared_uckn"

# Optional
export UCKN_KNOWLEDGE_DIR="./.uckn/knowledge"  # Local ChromaDB storage
export UCKN_LOG_LEVEL="INFO"
export UCKN_POOL_SIZE="5"                      # Connection pool size
export UCKN_MAX_OVERFLOW="10"                  # Max overflow connections
```

### MCP Configuration

Update your `.mcp.json`:

```json
{
  "mcpServers": {
    "uckn-knowledge": {
      "command": "pixi",
      "args": [
        "run",
        "--project", "/path/to/claude-code-knowledge-framework",
        "mcp-server"
      ],
      "env": {
        "UCKN_DATABASE_URL": "postgresql://uckn:uckn_secure_password@localhost:5432/shared_uckn",
        "UCKN_KNOWLEDGE_DIR": "./.uckn/knowledge",
        "UCKN_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

## 📊 Database Schema

The UCKN database includes these tables:

| Table | Purpose | Key Features |
|-------|---------|--------------|
| `projects` | Project organization | Team workspace isolation |
| `patterns` | Knowledge patterns | Searchable solutions & best practices |
| `error_solutions` | Error resolutions | Categorized fixes with metrics |
| `pattern_categories` | Pattern organization | Hierarchical classification |
| `team_access` | Access control | Role-based permissions |
| `compatibility_matrix` | Tech stack compatibility | Smart recommendations |

### Sample Schema:

```sql
-- Projects table
CREATE TABLE projects (
    id VARCHAR PRIMARY KEY,
    name VARCHAR UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Patterns table
CREATE TABLE patterns (
    id VARCHAR PRIMARY KEY,
    project_id VARCHAR REFERENCES projects(id),
    document_text TEXT NOT NULL,
    metadata_json JSONB NOT NULL DEFAULT '{}',
    technology_stack VARCHAR,
    pattern_type VARCHAR,
    success_rate FLOAT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_patterns_tech_stack ON patterns(technology_stack);
CREATE INDEX idx_patterns_type ON patterns(pattern_type);
CREATE INDEX idx_patterns_metadata ON patterns USING GIN(metadata_json);
```

## 🚀 Production Configuration

### Connection Pooling

For production environments:

```python
# In your application
DATABASE_CONFIG = {
    "pool_size": 20,
    "max_overflow": 0,
    "pool_pre_ping": True,
    "pool_recycle": 300,
    "echo": False  # Set to True for SQL debugging
}
```

### Security Best Practices

1. **Use SSL connections:**
   ```bash
   export UCKN_DATABASE_URL="postgresql://uckn:password@localhost:5432/shared_uckn?sslmode=require"
   ```

2. **Limit database user permissions:**
   ```sql
   -- Create restricted user for application
   CREATE USER uckn_app WITH PASSWORD 'secure_app_password';
   GRANT CONNECT ON DATABASE shared_uckn TO uckn_app;
   GRANT USAGE ON SCHEMA public TO uckn_app;
   GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO uckn_app;
   GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO uckn_app;
   ```

3. **Configure pg_hba.conf for network access:**
   ```
   # Allow specific networks
   host    shared_uckn    uckn    192.168.1.0/24    md5
   host    shared_uckn    uckn    10.0.0.0/8        md5
   ```

### Backup Strategy

```bash
# Daily backup script
#!/bin/bash
BACKUP_DIR="/backup/uckn"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup database
pg_dump -h localhost -U uckn -d shared_uckn > $BACKUP_DIR/uckn_$DATE.sql

# Compress backup
gzip $BACKUP_DIR/uckn_$DATE.sql

# Keep only last 7 days
find $BACKUP_DIR -name "uckn_*.sql.gz" -mtime +7 -delete
```

## 🐛 Troubleshooting

### Common Issues

**Connection refused:**
```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# Check if it's listening on the right port
sudo netstat -tlnp | grep 5432

# Start PostgreSQL if needed
sudo systemctl start postgresql
```

**Authentication failed:**
```bash
# Reset password
sudo -u postgres psql
ALTER USER uckn PASSWORD 'new_password';
```

**Permission denied:**
```bash
# Grant permissions
sudo -u postgres psql -d shared_uckn
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO uckn;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO uckn;
```

**Database doesn't exist:**
```bash
# Create database
sudo -u postgres createdb -O uckn shared_uckn
```

### Debug Commands

```bash
# Test connection
psql "postgresql://uckn:password@localhost:5432/shared_uckn" -c "SELECT version();"

# Check tables
psql "postgresql://uckn:password@localhost:5432/shared_uckn" -c "\dt"

# Check UCKN connectivity
python -c "
from uckn.storage.postgresql_connector import PostgreSQLConnector
import os
conn = PostgreSQLConnector(os.environ.get('UCKN_DATABASE_URL'))
print('Status:', 'OK' if conn.is_available() else 'FAILED')
"
```

## 🌐 Multi-Project Setup

For multiple teams/projects sharing knowledge:

```bash
# Create separate databases for different teams
sudo -u postgres createdb -O uckn team_frontend_uckn
sudo -u postgres createdb -O uckn team_backend_uckn
sudo -u postgres createdb -O uckn shared_company_uckn

# Configure different MCP servers
# team-frontend/.mcp.json
{
  "mcpServers": {
    "uckn-knowledge": {
      "env": {
        "UCKN_DATABASE_URL": "postgresql://uckn:pass@localhost:5432/team_frontend_uckn"
      }
    }
  }
}

# team-backend/.mcp.json  
{
  "mcpServers": {
    "uckn-knowledge": {
      "env": {
        "UCKN_DATABASE_URL": "postgresql://uckn:pass@localhost:5432/team_backend_uckn"
      }
    }
  }
}

# For company-wide sharing
{
  "mcpServers": {
    "uckn-knowledge": {
      "env": {
        "UCKN_DATABASE_URL": "postgresql://uckn:pass@localhost:5432/shared_company_uckn"
      }
    }
  }
}
```

## 🎉 Success!

Once setup is complete, you'll have:

- ✅ **Shared Knowledge Database** - All sessions can contribute and access patterns
- ✅ **Cross-Project Search** - Find solutions from any team/project
- ✅ **Persistent Storage** - Knowledge survives across sessions
- ✅ **Team Collaboration** - Multiple developers building shared knowledge
- ✅ **Production Ready** - Scalable, secure, and performant

Your integration test patterns and other solutions will now be available to all team members and projects! 🚀