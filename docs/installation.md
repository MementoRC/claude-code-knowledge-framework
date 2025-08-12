# Installation Guide

This guide covers how to install and set up the Claude Code Knowledge Framework in your projects.

## 🎯 Prerequisites

- Claude Code environment with MCP tools enabled
- TaskMaster AI configured and working
- Git repository with CI/CD setup
- Python 3.8+ (for core framework components)

## 📦 Installation Methods

### Method 1: Symlink Installation (Recommended)

For projects that want to share a central framework installation:

```bash
# 1. Clone or create the framework repository
git clone <framework-repo> /path/to/claude-code-knowledge-framework

# 2. In your project directory, create symlink
cd your-project/.claude/
ln -s ../../claude-code-knowledge-framework/ knowledge-framework

# 3. Create project-specific deployment
mkdir -p knowledge-framework/deployments/your-project
```

### Method 2: Direct Integration

For projects that want to embed the framework:

```bash
# 1. Copy framework to your project
cp -r /path/to/claude-code-knowledge-framework your-project/.claude/framework/

# 2. Set up local knowledge storage
mkdir -p your-project/.claude/knowledge/{sessions,patterns,embeddings,index}
```

### Method 3: Git Submodule

For projects using Git and wanting version control:

```bash
# 1. Add framework as submodule
git submodule add <framework-repo-url> .claude/framework

# 2. Initialize submodule
git submodule update --init --recursive

# 3. Link to framework
ln -s framework/deployments/your-project .claude/knowledge
```

## ⚙️ Configuration

### 1. Create Deployment Configuration

```bash
# Copy deployment template
cp .claude/framework/deployments/template/ .claude/framework/deployments/your-project/

# Edit deployment configuration
vim .claude/framework/deployments/your-project/deployment.yaml
```

### 2. Update Project-Specific Settings

```yaml
# .claude/framework/deployments/your-project/deployment.yaml
project_name: "your-project"
framework_version: "1.0.0"
deployment_date: "2024-12-23"

project_info:
  repository: "your-repo-name"
  branch: "main"
  type: "python_web_app"  # or your project type
  ci_platform: "github_actions"

features_enabled:
  - knowledge_capture
  - knowledge_retrieve
  - integrated_ci_workflow

quality_gates:
  - "npm test"           # Replace with your test command
  - "npm run lint"       # Replace with your lint command
  - "npm run type-check" # Replace with your type check command

custom_configurations:
  knowledge_storage_path: ".claude/knowledge/"
  session_backup_enabled: true
  auto_capture_enabled: false
```

### 3. Set Up Knowledge Storage

```bash
# Create knowledge storage directories
mkdir -p .claude/knowledge/{sessions,patterns,embeddings,index,templates,reports,summaries}

# Copy session template
cp .claude/framework/framework/templates/session_template.json .claude/knowledge/templates/

# Initialize empty indexes
echo '{}' > .claude/knowledge/index/keyword_index.json
echo '{"sessions": {}, "patterns": {}, "last_updated": "'$(date -Iseconds)'"}' > .claude/knowledge/index/metadata_index.json
```

### 4. Add Commands to Claude Code

```bash
# Copy command templates to your commands directory
cp .claude/framework/framework/commands/knowledge_*.md .claude/commands/

# Make commands executable (if using shell integration)
chmod +x .claude/framework/framework/core/knowledge_manager.py
```

## 🧪 Verification

### Test Framework Installation

```bash
# Test core knowledge manager
python .claude/framework/framework/core/knowledge_manager.py summary 7

# Test command availability
ls .claude/commands/knowledge_*.md

# Verify deployment configuration
cat .claude/framework/deployments/your-project/deployment.yaml
```

### Test Basic Functionality

```bash
# Test knowledge base initialization
python .claude/framework/framework/core/knowledge_manager.py search "test query"

# Test directory structure
tree .claude/knowledge/

# Test integration with project
ls -la .claude/knowledge -> should point to correct framework deployment
```

## 🔧 Integration with Existing Workflow

### TaskMaster AI Integration

If you're using TaskMaster AI, ensure the framework paths are configured:

```python
# Add to your TaskMaster configuration
project_root = "/path/to/your-project"
knowledge_framework_path = f"{project_root}/.claude/framework"
knowledge_storage_path = f"{project_root}/.claude/knowledge"
```

### CI/CD Integration

Add framework initialization to your CI workflow:

```yaml
# .github/workflows/ci.yml
steps:
  - name: Initialize Knowledge Framework
    run: |
      if [ -f .claude/framework/framework/core/knowledge_manager.py ]; then
        python .claude/framework/framework/core/knowledge_manager.py summary 1
      fi
```

### Git Configuration

Add appropriate .gitignore entries:

```bash
# .gitignore
.claude/knowledge/sessions/     # Session data (optional - depends on team preference)
.claude/knowledge/index/        # Generated indexes
.claude/knowledge/embeddings/   # Generated embeddings (large files)

# Keep these tracked:
# .claude/knowledge/templates/
# .claude/knowledge/patterns/
# .claude/framework/ (if using direct integration)
```

## 📊 Post-Installation Setup

### 1. Initialize Knowledge Base

```bash
# Create first session template
python .claude/framework/framework/core/knowledge_manager.py create_session_template

# Test search functionality
python .claude/framework/framework/core/knowledge_manager.py search "initialization"
```

### 2. Configure Performance Monitoring

```yaml
# Add to deployment.yaml
monitoring:
  success_rate_tracking: true
  resolution_time_tracking: true
  pattern_effectiveness_tracking: true
  performance_alerts:
    context_usage_threshold: 3000  # tokens
    search_time_threshold: 10      # seconds
```

### 3. Set Up Team Configuration (Optional)

For team environments:

```bash
# Create shared pattern library
mkdir -p .claude/knowledge/shared-patterns/

# Configure team-specific settings
cat > .claude/knowledge/team-config.yaml << EOF
team_name: "your-team"
shared_patterns_enabled: true
cross_project_learning: false  # Enable in v2.0.0
pattern_sharing_policy: "opt-in"
EOF
```

## 🚀 First Session

After installation, run your first knowledge-enhanced session:

```bash
# 1. Start with knowledge retrieval (will be empty initially)
# Use Claude Code command: /knowledge_retrieve

# 2. Run your CI troubleshooting session
# Use Claude Code command: /knowledge_integrated_ci

# 3. Capture knowledge from the session
# Use Claude Code command: /knowledge_capture

# 4. Verify knowledge was captured
python .claude/framework/framework/core/knowledge_manager.py summary 7
```

## ❗ Troubleshooting

### Common Issues

**Framework not found:**
```bash
# Check symlink
ls -la .claude/knowledge-framework
# Should point to framework location

# Verify framework structure
ls .claude/framework/framework/core/knowledge_manager.py
```

**Permission issues:**
```bash
# Fix permissions
chmod +x .claude/framework/framework/core/knowledge_manager.py
chmod -R u+w .claude/knowledge/
```

**Python path issues:**
```bash
# Test Python path
python -c "import sys; sys.path.append('.claude/framework/framework/core'); import knowledge_manager"
```

### Getting Help

- Check the [troubleshooting guide](troubleshooting.md)
- Review [common configuration issues](common-issues.md)
- See [example deployments](../examples/)

## 🔄 Next Steps

After successful installation:

1. **Complete 3-5 CI troubleshooting sessions** to build initial knowledge base
2. **Monitor performance** and context usage patterns
3. **Review captured knowledge** and pattern effectiveness
4. **Plan upgrade to v1.1.0** with enhanced features when available
5. **Consider team rollout** for broader adoption

---

**Installation Support**: For installation issues, check the examples directory or create an issue in the framework repository.
