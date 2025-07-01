# 📦 UV Integration Guide for UCKN

This guide shows how to integrate UCKN with Claude Code using UV for dependency management.

## 🚀 Quick Setup

### Method 1: Automatic Setup (Recommended)

```bash
# Clone or download UCKN framework
git clone https://github.com/MementoRC/claude-code-knowledge-framework.git

# Navigate to your project
cd your-project

# Run the setup script
uv run --project /path/to/claude-code-knowledge-framework scripts/setup-uv-integration.py
```

This creates:
- `.mcp.json` with UV configuration
- `.uckn/` directory structure
- Basic configuration files
- Usage examples

### Method 2: Manual Configuration

1. **Create `.mcp.json` in your project:**

```json
{
  "mcpServers": {
    "uckn-knowledge": {
      "command": "uv",
      "args": [
        "run",
        "--project",
        "/path/to/claude-code-knowledge-framework",
        "scripts/mcp-server-uv.py"
      ],
      "env": {
        "UCKN_KNOWLEDGE_DIR": "./.uckn/knowledge",
        "UCKN_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

2. **Initialize UCKN in your project:**

```bash
mkdir -p .uckn/knowledge .uckn/config
```

## 🛠 Configuration Options

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `UCKN_KNOWLEDGE_DIR` | Knowledge storage directory | `./.uckn/knowledge` |
| `UCKN_LOG_LEVEL` | Logging level | `INFO` |
| `UCKN_PROJECT_ROOT` | Project root directory | Current directory |
| `UCKN_DATABASE_URL` | Database connection URL | SQLite in knowledge dir |

### Advanced UV Configuration

For projects with specific UV requirements:

```json
{
  "mcpServers": {
    "uckn-knowledge": {
      "command": "uv",
      "args": [
        "run",
        "--project", "/path/to/claude-code-knowledge-framework",
        "--extra", "mcp,ml",
        "--python", "3.11",
        "python", "-m", "uckn.mcp.universal_knowledge_server"
      ],
      "env": {
        "UCKN_KNOWLEDGE_DIR": "./.uckn/knowledge",
        "UCKN_LOG_LEVEL": "DEBUG",
        "UV_CACHE_DIR": "./.uv-cache"
      }
    }
  }
}
```

## 🎯 Usage in Claude Code

Once configured, you can use these commands in Claude Code:

### Pattern Search
```
"Search for FastAPI authentication patterns"
"Find CI/CD configuration examples"
"Look for Python testing best practices"
```

### Project Analysis
```
"Analyze my project's technology stack"
"What setup recommendations do you have?"
"Predict potential issues with my configuration"
```

### Knowledge Contribution
```
"Save this solution as a pattern for future use"
"Add this configuration to the knowledge base"
```

## 🔧 Available MCP Tools

| Tool | Description | Example |
|------|-------------|---------|
| `search_patterns` | Search knowledge patterns | Find FastAPI setup patterns |
| `recommend_setup` | Get setup recommendations | Recommend project structure |
| `predict_issues` | Predict potential problems | Analyze configuration risks |
| `validate_solution` | Validate proposed solutions | Check if solution is optimal |
| `contribute_pattern` | Add new patterns | Save successful fixes |
| `get_project_dna` | Analyze tech stack | Get project fingerprint |

## 🐛 Troubleshooting

### Common Issues

**UV not found:**
```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**MCP server fails to start:**
```bash
# Test manually
uv run --project /path/to/claude-code-knowledge-framework scripts/mcp-server-uv.py
```

**Dependencies not found:**
```bash
# Ensure UCKN project has proper dependencies
cd /path/to/claude-code-knowledge-framework
uv sync --extra mcp
```

**Knowledge directory not found:**
```bash
# Create knowledge directory
mkdir -p .uckn/knowledge
```

### Debug Mode

Enable debug logging in `.mcp.json`:

```json
{
  "mcpServers": {
    "uckn-knowledge": {
      "env": {
        "UCKN_LOG_LEVEL": "DEBUG"
      }
    }
  }
}
```

## 📁 Project Structure

After setup, your project will have:

```
your-project/
├── .mcp.json                 # MCP configuration
├── .uckn/
│   ├── knowledge/           # Knowledge storage
│   ├── config/
│   │   └── uckn.toml       # UCKN configuration
│   └── examples/
│       └── basic_usage.py   # Usage examples
└── your-project-files...
```

## 🚀 Performance Benefits

UV integration provides:

- **Fast startup**: UV's dependency resolution is faster than pip
- **Isolated environment**: No global package conflicts
- **Reproducible**: Exact dependency versions
- **Minimal overhead**: Only downloads needed packages
- **Cache efficiency**: UV's intelligent caching

## 📈 Advanced Features

### Custom Knowledge Sources

Configure additional knowledge sources:

```toml
# .uckn/config/uckn.toml
[knowledge.sources]
local = ".uckn/knowledge"
team = "https://your-team-knowledge-server.com"
public = "https://public-patterns.uckn.io"
```

### Integration with CI/CD

Use in GitHub Actions:

```yaml
- name: Setup UCKN
  run: |
    uv run --project ./uckn-framework scripts/setup-uv-integration.py .
    
- name: Analyze with UCKN
  run: |
    uv run --project ./uckn-framework python -c "
    from uckn.core.organisms.knowledge_manager import KnowledgeManager
    km = KnowledgeManager('.')
    issues = km.predict_issues()
    print(f'Predicted issues: {issues}')
    "
```

This UV integration makes UCKN incredibly easy to use across different projects without installation hassles!