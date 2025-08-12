# Basic Setup Example

This example demonstrates a basic setup of the Claude Code Knowledge Framework for a Python project with pytest.

## 📁 Project Structure

```
my-python-project/
├── .claude/
│   ├── commands/
│   │   ├── knowledge_capture.md
│   │   ├── knowledge_retrieve.md
│   │   └── knowledge_integrated_ci.md
│   └── knowledge/                    # Symlink to framework deployment
├── src/
│   └── my_package/
├── tests/
│   └── test_my_package.py
├── pyproject.toml
└── README.md
```

## 🚀 Setup Steps

### 1. Install Framework

```bash
# Clone framework repository
git clone <framework-repo> ../claude-code-knowledge-framework

# Create symlink in your project
cd my-python-project/.claude/
ln -s ../../claude-code-knowledge-framework/deployments/my-python-project knowledge

# Create deployment configuration
mkdir -p ../../claude-code-knowledge-framework/deployments/my-python-project
```

### 2. Configure Deployment

Create `deployment.yaml`:

```yaml
project_name: "my-python-project"
framework_version: "1.0.0"
deployment_date: "2024-12-23"

project_info:
  repository: "my-python-project"
  branch: "main"
  type: "python_package"
  ci_platform: "github_actions"

features_enabled:
  - knowledge_capture
  - knowledge_retrieve
  - integrated_ci_workflow

quality_gates:
  - "pytest"
  - "ruff check --select=F,E9"
  - "pre-commit run --all-files"

custom_configurations:
  knowledge_storage_path: ".claude/knowledge/"
  session_backup_enabled: true
  auto_capture_enabled: false
```

### 3. Initialize Knowledge Storage

```bash
# Create knowledge directories
mkdir -p .claude/knowledge/{sessions,patterns,embeddings,index,templates}

# Copy templates
cp ../../claude-code-knowledge-framework/framework/templates/* .claude/knowledge/templates/

# Initialize indexes
echo '{}' > .claude/knowledge/index/keyword_index.json
echo '{"sessions": {}, "patterns": {}, "last_updated": "'$(date -Iseconds)'"}' > .claude/knowledge/index/metadata_index.json
```

### 4. Add Commands

```bash
# Copy command templates
cp ../../claude-code-knowledge-framework/framework/commands/* .claude/commands/
```

## 🧪 Test Setup

### Test Knowledge Manager

```bash
# Test basic functionality
python ../../claude-code-knowledge-framework/framework/core/knowledge_manager.py summary 7

# Test search (should return empty initially)
python ../../claude-code-knowledge-framework/framework/core/knowledge_manager.py search "test query"
```

### Verify Integration

```bash
# Check Claude Code commands are available
ls .claude/commands/knowledge_*.md

# Verify knowledge storage
ls .claude/knowledge/
```

## 📝 First Session Example

Here's how to use the framework in your first CI troubleshooting session:

### 1. Start Session with Knowledge Retrieval

In Claude Code, use: `/knowledge_retrieve`

This will:
- Search for similar past failures (empty initially)
- Check for applicable patterns (none initially)
- Create TaskMaster tasks based on findings

### 2. Run Enhanced CI Troubleshooting

In Claude Code, use: `/knowledge_integrated_ci`

This will:
- Analyze current CI failures
- Apply any found historical solutions
- Run systematic resolution with AI assistance
- Track all actions taken

### 3. Capture Knowledge After Resolution

In Claude Code, use: `/knowledge_capture`

This will:
- Extract lessons learned from the session
- Identify solution patterns
- Store knowledge for future sessions
- Update the knowledge base

## 📊 Example Session Data

After your first session, you'll have data like:

```json
{
  "session_id": "2024-12-23_14:30:15_abc123",
  "timestamp": "2024-12-23T14:30:15Z",
  "context": {
    "repository": "my-python-project",
    "branch": "main",
    "ci_status": "failure",
    "initial_failures": [
      "tests/test_my_package.py::test_function FAILED"
    ]
  },
  "final_status": "success",
  "total_duration_minutes": 15,
  "lessons_learned": [
    "Import path needed adjustment for CI environment",
    "Test fixtures require explicit cleanup"
  ],
  "solution_patterns": [
    {
      "pattern_id": "import_path_ci",
      "description": "CI environment import path sensitivity",
      "solution_template": "Adjust import paths for CI compatibility"
    }
  ]
}
```

## 🔄 Example Workflow

### Day 1: Initial Session
```bash
# Failed CI - ImportError
# Use: /knowledge_retrieve → No results (empty knowledge base)
# Use: /knowledge_integrated_ci → Standard AI resolution
# Use: /knowledge_capture → Captures first session data
```

### Day 2: Second Session
```bash
# Failed CI - Similar ImportError
# Use: /knowledge_retrieve → Finds Day 1 session with 85% similarity
# Gets suggestion: "Adjust import paths for CI compatibility"
# Applies historical solution → Faster resolution
# Use: /knowledge_capture → Updates pattern success rate
```

### Day 3: Different Issue
```bash
# Failed CI - Test timeout
# Use: /knowledge_retrieve → No exact matches, but finds async patterns
# Use: /knowledge_integrated_ci → Enhanced with async handling patterns
# Use: /knowledge_capture → Adds new timeout handling pattern
```

## 📈 Expected Benefits

After 3-5 sessions, you should see:

- **Faster Resolution**: 30-50% reduction in troubleshooting time
- **Pattern Recognition**: Common issues identified and standardized
- **Knowledge Growth**: Each session improves future performance
- **Context Awareness**: Solutions tailored to your specific environment

## 🔧 Customization

### Custom Quality Gates

Edit your `deployment.yaml`:

```yaml
quality_gates:
  - "pytest --cov=src --cov-report=term-missing"
  - "mypy src"
  - "black --check src tests"
  - "isort --check-only src tests"
```

### Custom Pattern Templates

Create project-specific patterns in `.claude/knowledge/patterns/`:

```json
{
  "project_specific_import_fix": {
    "description": "My Project specific import resolution",
    "solution_template": "Add src/ to PYTHONPATH in CI",
    "applicable_contexts": ["python", "ci_environment", "my_project"],
    "success_rate": 0.9
  }
}
```

### Custom Commands

Create project-specific commands in `.claude/commands/`:

```markdown
# project_specific_knowledge.md
> Quick knowledge check for my-python-project specific issues

Usage: /project_knowledge

This command searches for project-specific patterns and provides
targeted suggestions for my-python-project issues.
```

## 🚨 Troubleshooting

### Framework Not Found
```bash
# Check symlink
ls -la .claude/knowledge
# Should point to: ../../claude-code-knowledge-framework/deployments/my-python-project
```

### Commands Not Working
```bash
# Verify commands copied
ls .claude/commands/knowledge_*.md

# Check file permissions
chmod +x ../../claude-code-knowledge-framework/framework/core/knowledge_manager.py
```

### Knowledge Not Captured
```bash
# Check storage directories exist
ls .claude/knowledge/sessions/

# Test manual capture
python ../../claude-code-knowledge-framework/framework/core/knowledge_manager.py search "test"
```

## 🎯 Next Steps

1. **Complete 3-5 sessions** to build initial knowledge base
2. **Monitor patterns** that emerge for your project
3. **Customize deployment** based on your specific needs
4. **Share learnings** with team members
5. **Plan upgrade** to v1.1.0 when available

This basic setup provides a foundation for knowledge-enhanced CI troubleshooting that will improve over time as you build your project's institutional memory.
