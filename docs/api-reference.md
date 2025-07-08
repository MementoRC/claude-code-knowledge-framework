# API Reference

This document provides a comprehensive reference for the Claude Code Knowledge Framework API.

## 🏗️ Core Classes

### ClaudeCodeKnowledgeManager

The main class for managing knowledge capture, storage, and retrieval.

```python
from knowledge_manager import ClaudeCodeKnowledgeManager

# Initialize with default knowledge directory
km = ClaudeCodeKnowledgeManager()

# Initialize with custom directory
km = ClaudeCodeKnowledgeManager(knowledge_dir="custom/path")
```

#### Methods

##### `capture_session_knowledge(session_data, lessons_learned, solution_patterns, manual_insights=None)`

Capture knowledge from a completed CI troubleshooting session.

**Parameters:**
- `session_data` (Dict): TaskMaster session data
- `lessons_learned` (List[str]): List of lessons learned during the session
- `solution_patterns` (List[Dict]): Identified solution patterns
- `manual_insights` (List[str], optional): Additional manual insights

**Returns:**
- `str`: Session ID for future reference

**Example:**
```python
session_id = km.capture_session_knowledge(
    session_data={
        "repository": "my-project",
        "branch": "main",
        "final_status": "success",
        "duration_minutes": 25
    },
    lessons_learned=[
        "Import order matters in CI environment",
        "Async tests need explicit timeout handling"
    ],
    solution_patterns=[
        {
            "pattern_id": "import_order_ci",
            "description": "CI environment import order sensitivity",
            "solution_template": "Reorganize imports following isort/black standards"
        }
    ],
    manual_insights=["CI environment stricter than local"]
)
```

##### `search_knowledge(query, context=None, max_results=5)`

Search knowledge base for relevant past solutions.

**Parameters:**
- `query` (str): Search query (failure description, error message, etc.)
- `context` (Dict, optional): Current context (branch, repository, etc.)
- `max_results` (int): Maximum number of results to return

**Returns:**
- `List[Dict]`: List of relevant session records with similarity scores

**Example:**
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

##### `get_session_context_summary(days_back=7)`

Get a summary of recent sessions for context restoration.

**Parameters:**
- `days_back` (int): Number of days to look back

**Returns:**
- `Dict`: Summary of recent sessions and patterns

**Example:**
```python
summary = km.get_session_context_summary(days_back=14)
print(f"Total sessions: {summary['total_sessions']}")
print(f"Success rate: {summary['success_rate']:.1%}")
print(f"Common patterns: {len(summary['common_patterns'])}")
```

##### `suggest_solutions(current_failures, context)`

Suggest solutions based on historical knowledge.

**Parameters:**
- `current_failures` (List[str]): List of current test failures
- `context` (Dict): Current context (repository, branch, etc.)

**Returns:**
- `List[Dict]`: List of suggested solutions with confidence scores

**Example:**
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

## 📊 Data Models

### Session Record Schema

```python
{
    "session_id": str,              # Unique session identifier
    "timestamp": str,               # ISO format timestamp
    "context": {
        "repository": str,          # Repository name
        "branch": str,              # Git branch
        "pr_number": int,           # Pull request number (optional)
        "ci_status": str,           # Initial CI status
        "initial_failures": list,   # List of initial failures
        "environment_type": str     # Environment type (default: "ci")
    },
    "attempts": [                   # List of resolution attempts
        {
            "attempt_number": int,
            "approach": str,
            "actions_taken": list,
            "files_modified": list,
            "outcome": str,
            "remaining_failures": list,
            "lessons_learned": list,
            "duration_minutes": int
        }
    ],
    "final_status": str,            # Final session status
    "total_duration_minutes": int,  # Total session duration
    "lessons_learned": list,        # Overall lessons learned
    "solution_patterns": list,      # Identified solution patterns
    "manual_insights": list,        # Manual insights
    "quality_gates": {              # Quality validation results
        "tests_passing": bool,
        "lint_clean": bool,
        "pre_commit_passing": bool
    },
    "tools_used": list,             # Tools used during session
    "environment": {                # Environment information
        "repository": str,
        "branch": str,
        "python_version": str,
        "ci_platform": str
    },
    "metadata": {                   # Session metadata
        "knowledge_version": str,
        "captured_by": str,
        "session_complexity": str,
        "success_confidence": float
    }
}
```

### Solution Pattern Schema

```python
{
    "pattern_id": str,              # Unique pattern identifier
    "description": str,             # Human-readable description
    "solution_template": str,       # Template for applying solution
    "applicable_contexts": list,    # Contexts where pattern applies
    "success_indicators": list,     # Indicators of successful application
    "complexity": str,              # Pattern complexity (low/medium/high)
    "sessions": list,               # Sessions that used this pattern
    "success_count": int,           # Number of successful applications
    "total_count": int             # Total number of applications
}
```

### Search Result Schema

```python
{
    "session_data": dict,           # Full session record
    "similarity_score": float,     # Similarity score (0.0-1.0)
    "search_type": str,             # Type of search match
    "final_score": float,           # Weighted final score
    "pattern_id": str              # Associated pattern ID (if applicable)
}
```

## 🔧 Command Line Interface

The knowledge manager can be used from the command line:

### Search Knowledge

```bash
python knowledge_manager.py search "import error CI"
```

**Output:**
```
Found 3 results for: import error CI

1. Session: 2024-12-23_14:30:15_abc123
   Date: 2024-12-23T14:30:15Z
   Status: success
   Similarity: 0.85
   Repository: pytest-analyzer
```

### Get Summary

```bash
python knowledge_manager.py summary 7
```

**Output:**
```
Knowledge Base Summary (last 7 days)
Total sessions: 5
Success rate: 80.0%

Recent sessions:
  - 2024-12-23_14:30:15_abc123: success
  - 2024-12-22_10:15:30_def456: success
```

## 🎯 Integration Patterns

### TaskMaster AI Integration

```python
# Extract session data from TaskMaster
taskmaster_data = mcp__taskmaster-ai__get_tasks(
    projectRoot=PROJECT_ROOT,
    withSubtasks=True
)

# Convert to knowledge format
session_data = {
    "repository": GITHUB_REPO,
    "branch": current_branch,
    "tasks": taskmaster_data.get("tasks", []),
    "final_status": "success" if all_tasks_complete else "partial"
}

# Capture knowledge
km.capture_session_knowledge(
    session_data=session_data,
    lessons_learned=extract_lessons(taskmaster_data),
    solution_patterns=identify_patterns(taskmaster_data)
)
```

### Git Integration

```python
# Get git context
git_status = mcp__git__git_status(repo_path=PROJECT_ROOT)
git_diff = mcp__git__git_diff_unstaged(repo_path=PROJECT_ROOT)

# Include in search context
context = {
    "repository": GITHUB_REPO,
    "branch": git_status.current_branch,
    "has_changes": bool(git_diff)
}

# Search with context
results = km.search_knowledge(query="test failures", context=context)
```

### CI Integration

```python
# Get CI status
pr_status = mcp__git__github_get_pr_status(
    repo_owner=REPO_OWNER,
    repo_name=REPO_NAME,
    pr_number=PR_NUMBER
)

# Extract failures
failing_jobs = mcp__git__github_get_failing_jobs(
    repo_owner=REPO_OWNER,
    repo_name=REPO_NAME,
    pr_number=PR_NUMBER
)

# Get suggestions
suggestions = km.suggest_solutions(
    current_failures=extract_failures(failing_jobs),
    context={"ci_status": pr_status.state}
)
```

## 🔍 Search Strategies

The framework uses multiple search strategies:

### 1. Keyword Search
- Extracts keywords from query
- Matches against indexed session keywords
- Fast but basic matching

### 2. Pattern Search
- Matches query against known solution patterns
- Uses pattern descriptions and templates
- Good for recurring issues

### 3. Semantic Search (Future)
- Uses embeddings for similarity matching
- Planned for v1.2.0 with MCP server
- Best for finding conceptually similar issues

### 4. Context-Aware Filtering
- Filters results by repository, branch, environment
- Boosts results with similar context
- Improves relevance of suggestions

## 📈 Performance Considerations

### Memory Usage
- File-based storage scales linearly with sessions
- Each session ~1-5KB depending on complexity
- Index files grow with knowledge base size

### Search Performance
- Keyword search: O(n) where n = number of sessions
- Pattern search: O(p) where p = number of patterns
- Context filtering: O(r) where r = number of results

### Optimization Tips
- Limit `max_results` for faster searches
- Use specific queries rather than broad terms
- Include context for better filtering
- Regular cleanup of old/irrelevant sessions

## ❌ Error Handling

### Common Exceptions

```python
# File not found
try:
    km = ClaudeCodeKnowledgeManager("nonexistent/path")
except FileNotFoundError:
    print("Knowledge directory not found")

# Invalid session data
try:
    km.capture_session_knowledge({}, [], [])
except ValueError as e:
    print(f"Invalid session data: {e}")

# Search timeout
try:
    results = km.search_knowledge("complex query")
except TimeoutError:
    print("Search timed out - try more specific query")
```

### Error Recovery

```python
# Graceful degradation
try:
    results = km.search_knowledge(query)
except Exception as e:
    print(f"Search failed: {e}")
    results = []  # Continue with empty results

# Backup and recovery
if not km.validate_knowledge_base():
    km.restore_from_backup()
```

---

This API reference covers the core functionality of v1.0.0. Future versions will add MCP server APIs, vector embeddings, and enhanced search capabilities.
