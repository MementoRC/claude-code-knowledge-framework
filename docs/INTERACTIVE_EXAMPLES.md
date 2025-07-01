# 🧑‍💻 UCKN Interactive Examples & Tutorials

This guide provides practical, copy-paste examples and step-by-step tutorials for using the Unified Claude Knowledge Network (UCKN) framework.

---

## 🚀 Quick Start: Initialize the Knowledge Manager

```python
from knowledge_manager import ClaudeCodeKnowledgeManager

# Initialize with default knowledge directory
km = ClaudeCodeKnowledgeManager()

# Or specify a custom directory
km = ClaudeCodeKnowledgeManager(knowledge_dir=".claude/knowledge/")
```

---

## 📝 Capturing Knowledge from a CI Session

```python
session_data = {
    "repository": "my-project",
    "branch": "main",
    "final_status": "success",
    "duration_minutes": 25
}

lessons_learned = [
    "Import order matters in CI environment",
    "Async tests need explicit timeout handling"
]

solution_patterns = [
    {
        "pattern_id": "import_order_ci",
        "description": "CI environment import order sensitivity",
        "solution_template": "Reorganize imports following isort/black standards"
    }
]

manual_insights = ["CI environment stricter than local"]

session_id = km.capture_session_knowledge(
    session_data=session_data,
    lessons_learned=lessons_learned,
    solution_patterns=solution_patterns,
    manual_insights=manual_insights
)

print(f"Session captured with ID: {session_id}")
```

---

## 🔍 Searching the Knowledge Base

```python
results = km.search_knowledge(
    query="ImportError module not found",
    context={"repository": "my-project", "branch": "main"},
    max_results=3
)

for result in results:
    print(f"Session: {result['session_data']['session_id']}")
    print(f"Similarity: {result['similarity_score']:.2f}")
    print(f"Status: {result['session_data']['final_status']}")
```

---

## 📊 Getting a Summary of Recent Sessions

```python
summary = km.get_session_context_summary(days_back=14)
print(f"Total sessions: {summary['total_sessions']}")
print(f"Success rate: {summary['success_rate']:.1%}")
print(f"Common patterns: {len(summary['common_patterns'])}")
```

---

## 💡 Suggesting Solutions for Current Failures

```python
suggestions = km.suggest_solutions(
    current_failures=[
        "test_async.py::test_timeout FAILED",
        "test_imports.py::test_module FAILED"
    ],
    context={"repository": "my-project", "branch": "feature/new-feature"}
)

for suggestion in suggestions:
    print(f"Failure: {suggestion['failure']}")
    print(f"Solution: {suggestion['solution']}")
    print(f"Confidence: {suggestion['confidence']:.2f}")
```

---

## ⚙️ Configuration Example

```yaml
# .claude/framework/deployments/your-project/deployment.yaml
project_name: "your-project"
framework_version: "1.0.0"
deployment_date: "2024-12-23"

project_info:
  repository: "your-repo-name"
  branch: "main"
  type: "python_web_app"
  ci_platform: "github_actions"

features_enabled:
  - knowledge_capture
  - knowledge_retrieve
  - integrated_ci_workflow

quality_gates:
  - "npm test"
  - "npm run lint"
  - "npm run type-check"

custom_configurations:
  knowledge_storage_path: ".claude/knowledge/"
  session_backup_enabled: true
  auto_capture_enabled: false
```

---

## 🛠️ Integration with TaskMaster AI

```python
# Extract session data from TaskMaster
taskmaster_data = mcp__taskmaster-ai__get_tasks(
    projectRoot=PROJECT_ROOT,
    withSubtasks=True
)

session_data = {
    "repository": GITHUB_REPO,
    "branch": current_branch,
    "tasks": taskmaster_data.get("tasks", []),
    "final_status": "success" if all_tasks_complete else "partial"
}

km.capture_session_knowledge(
    session_data=session_data,
    lessons_learned=extract_lessons(taskmaster_data),
    solution_patterns=identify_patterns(taskmaster_data)
)
```

---

## 🔗 Integration with Git and CI

```python
# Get git context
git_status = mcp__git__git_status(repo_path=PROJECT_ROOT)
git_diff = mcp__git__git_diff_unstaged(repo_path=PROJECT_ROOT)

context = {
    "repository": GITHUB_REPO,
    "branch": git_status.current_branch,
    "has_changes": bool(git_diff)
}

results = km.search_knowledge(query="test failures", context=context)
```

```yaml
# .github/workflows/ci.yml
steps:
  - name: Initialize Knowledge Framework
    run: |
      if [ -f .claude/framework/framework/core/knowledge_manager.py ]; then
        python .claude/framework/framework/core/knowledge_manager.py summary 1
      fi
```

---

## 🧪 Testing and Verification

```bash
# Test core knowledge manager
python .claude/framework/framework/core/knowledge_manager.py summary 7

# Test search functionality
python .claude/framework/framework/core/knowledge_manager.py search "test query"
```

---

## 🩹 Troubleshooting Example

```python
try:
    km = ClaudeCodeKnowledgeManager("nonexistent/path")
except FileNotFoundError:
    print("Knowledge directory not found")

try:
    km.capture_session_knowledge({}, [], [])
except ValueError as e:
    print(f"Invalid session data: {e}")

try:
    results = km.search_knowledge("complex query")
except TimeoutError:
    print("Search timed out - try more specific query")
```

---

## 🧰 Advanced: Using Caching for Performance

```python
from uckn.performance.cache_manager import PerformanceCacheManager

cache_manager = PerformanceCacheManager()
km = ClaudeCodeKnowledgeManager(cache_manager=cache_manager)

# Now all embeddings and search results will be cached for faster access
```

---

> 💡 **Tip:** For more details, see the [API Reference](./api-reference.md) and [Installation Guide](./installation.md).
