# 📦 Pixi Integration Guide for UCKN

This guide shows how to integrate UCKN with Claude Code using Pixi for dependency management.

## 🚀 Quick Setup

### Method 1: Automatic Setup (Recommended)

```bash
# Clone or download UCKN framework
git clone https://github.com/MementoRC/claude-code-knowledge-framework.git

# Navigate to your project
cd your-project

# Run the setup script
pixi run --project /path/to/claude-code-knowledge-framework setup-pixi-integration
```

This creates:
- `.mcp.json` with Pixi configuration
- `.uckn/` directory structure
- Basic configuration files
- Usage examples

### Method 2: Manual Configuration

1. **Create `.mcp.json` in your project:**

```json
{
  "mcpServers": {
    "uckn-knowledge": {
      "command": "pixi",
      "args": [
        "run",
        "--project",
        "/path/to/claude-code-knowledge-framework",
        "mcp-server"
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

### Advanced Pixi Configuration

For projects with specific Pixi requirements:

```json
{
  "mcpServers": {
    "uckn-knowledge": {
      "command": "pixi",
      "args": [
        "run",
        "--project", "/path/to/claude-code-knowledge-framework",
        "--environment", "default",
        "mcp-server"
      ],
      "env": {
        "UCKN_KNOWLEDGE_DIR": "./.uckn/knowledge",
        "UCKN_LOG_LEVEL": "DEBUG",
        "PIXI_CACHE_DIR": "./.pixi-cache"
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

**Pixi not found:**
```bash
# Install Pixi
curl -fsSL https://pixi.sh/install.sh | bash
```

**MCP server fails to start:**
```bash
# Test manually
pixi run --project /path/to/claude-code-knowledge-framework mcp-server
```

**Dependencies not found:**
```bash
# Ensure UCKN project has proper dependencies
cd /path/to/claude-code-knowledge-framework
pixi install
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

Pixi integration provides:

- **Fast startup**: Pixi's conda-forge based resolution is fast and reliable
- **Isolated environment**: No global package conflicts
- **Reproducible**: Exact dependency versions with lock files
- **Cross-platform**: Consistent behavior across Linux, macOS, and Windows
- **Cache efficiency**: Pixi's intelligent caching system

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
- name: Setup Pixi
  uses: prefix-dev/setup-pixi@v0.4.1
  with:
    pixi-version: latest

- name: Setup UCKN
  run: |
    pixi run --project ./uckn-framework setup-pixi-integration .
    
- name: Analyze with UCKN
  run: |
    pixi run --project ./uckn-framework python -c "
    from uckn.core.organisms.knowledge_manager import KnowledgeManager
    km = KnowledgeManager('.')
    issues = km.predict_issues()
    print(f'Predicted issues: {issues}')
    "
```

### Multi-Environment Support

Pixi supports multiple environments for different use cases:

```yaml
# For development
pixi run --environment dev mcp-server

# For production
pixi run --environment default mcp-server

# For CI/CD
pixi run --environment ci mcp-server
```

This Pixi integration makes UCKN incredibly easy to use across different projects with reliable dependency management!