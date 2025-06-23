# Knowledge Capture Command for CI Troubleshooting

> Capture lessons learned from CI troubleshooting sessions for future reference and pattern analysis

## EXECUTION GUIDE

**Prerequisites**: Completed CI troubleshooting session with TaskMaster AI tracking
- Session data available from TaskMaster
- Clear outcomes and lessons learned identified
- Quality gates validation completed

**Usage**: `/knowledge_capture` or at end of CI troubleshooting sessions

## COMMAND WORKFLOW

### PHASE 1: SESSION DATA EXTRACTION

▶️ **TASK STARTING**: Extract knowledge from completed session

```python
# 1. Get current TaskMaster session data
session_data = mcp__taskmaster-ai__get_tasks(
    projectRoot=PROJECT_ROOT,
    withSubtasks=True
)

# 2. Extract session context
current_context = {
    "repository": GITHUB_REPO,
    "branch": current_branch,
    "pr_number": WORKING_PR,
    "initial_ci_status": initial_ci_status,
    "initial_failures": initial_failures,
    "final_ci_status": final_ci_status,
    "duration_minutes": session_duration,
    "quality_gates": final_quality_results,
    "tools_used": ["taskmaster-ai", "pytest-analyzer", "aider", "git-mcp"]
}

print("📊 Session data extracted for knowledge capture")
```

### PHASE 2: LESSONS LEARNED IDENTIFICATION

▶️ **TASK STARTING**: Identify and categorize lessons learned

```python
# 1. Analyze session for lessons learned
lessons_learned = []

# Extract from successful resolution steps
for task in session_data.get("tasks", []):
    if task.get("status") == "done":
        # Identify what worked
        if task.get("actions"):
            lesson = f"✅ {task['title']}: {task.get('key_insight', 'Applied successful resolution')}"
            lessons_learned.append(lesson)

# Extract from failed attempts
for task in session_data.get("tasks", []):
    if task.get("status") in ["cancelled", "deferred"]:
        # Identify what didn't work
        lesson = f"❌ Avoided: {task['title']} - {task.get('failure_reason', 'Approach was ineffective')}"
        lessons_learned.append(lesson)

# Extract from quality validation insights
if final_quality_results:
    for check, result in final_quality_results.items():
        if result.get("status") == "PASS":
            if result.get("details"):
                lesson = f"🔍 Quality: {check} - {result['details']}"
                lessons_learned.append(lesson)

# Extract environment-specific insights
ci_environment_lessons = [
    "CI environment import order sensitivity",
    "Async test timeout handling requirements", 
    "Pre-commit hook compatibility in CI",
    "Environment variable differences between local and CI"
]

print(f"📝 Identified {len(lessons_learned)} lessons learned")
```

### PHASE 3: SOLUTION PATTERN IDENTIFICATION

▶️ **TASK STARTING**: Identify reusable solution patterns

```python
# 1. Identify solution patterns from successful session
solution_patterns = []

# Pattern: Import order fixes
if any("import" in lesson.lower() for lesson in lessons_learned):
    solution_patterns.append({
        "pattern_id": "import_order_ci",
        "description": "CI environment import order sensitivity",
        "solution_template": "Reorganize imports following isort/black standards, ensure __init__.py consistency",
        "applicable_contexts": ["python", "ci_environment", "import_errors"],
        "success_indicators": ["import errors resolved", "tests pass in CI"],
        "complexity": "low"
    })

# Pattern: Async test handling
if any("async" in lesson.lower() or "timeout" in lesson.lower() for lesson in lessons_learned):
    solution_patterns.append({
        "pattern_id": "async_test_handling",
        "description": "Async test timeout and isolation handling",
        "solution_template": "Add explicit timeout handling, ensure proper async cleanup",
        "applicable_contexts": ["python", "async_tests", "timeout_errors"],
        "success_indicators": ["async tests stable", "no timeout failures"],
        "complexity": "medium"
    })

# Pattern: Environment compatibility
if any("environment" in lesson.lower() or "ci" in lesson.lower() for lesson in lessons_learned):
    solution_patterns.append({
        "pattern_id": "environment_compatibility",
        "description": "Local vs CI environment compatibility",
        "solution_template": "Ensure environment variable consistency, check dependency versions",
        "applicable_contexts": ["ci_environment", "environment_differences"],
        "success_indicators": ["local and CI behavior consistent"],
        "complexity": "medium"
    })

print(f"🔄 Identified {len(solution_patterns)} solution patterns")
```

### PHASE 4: MANUAL INSIGHT COLLECTION

▶️ **TASK STARTING**: Collect additional manual insights

```python
# 1. Prompt for additional insights (if interactive)
manual_insights = []

# Key questions to consider:
insights_prompts = [
    "What was the root cause that wasn't immediately obvious?",
    "What would you do differently next time?",
    "What CI-specific behavior was unexpected?",
    "What tools or approaches were most effective?",
    "What patterns might apply to similar projects?"
]

# For automation, extract insights from commit messages and PR descriptions
if hasattr(session_data, 'commit_messages'):
    for commit_msg in session_data.get('commit_messages', []):
        if "fix:" in commit_msg or "resolve:" in commit_msg:
            # Extract insight from commit message
            insight = f"Commit insight: {commit_msg.split(':', 1)[1].strip()}"
            manual_insights.append(insight)

# Extract from TaskMaster task notes
for task in session_data.get("tasks", []):
    if task.get("notes"):
        insight = f"Task insight ({task['title']}): {task['notes']}"
        manual_insights.append(insight)

print(f"💡 Collected {len(manual_insights)} manual insights")
```

### PHASE 5: KNOWLEDGE STORAGE

▶️ **TASK STARTING**: Store knowledge in knowledge management system

```python
# 1. Initialize knowledge manager
import sys
sys.path.append('.claude/knowledge/tools')
from knowledge_manager import ClaudeCodeKnowledgeManager

km = ClaudeCodeKnowledgeManager()

# 2. Capture session knowledge
session_id = km.capture_session_knowledge(
    session_data=current_context,
    lessons_learned=lessons_learned,
    solution_patterns=solution_patterns,
    manual_insights=manual_insights
)

print(f"💾 Knowledge captured with session ID: {session_id}")

# 3. Update knowledge base statistics
stats = km.get_session_context_summary(days_back=30)
print(f"📊 Knowledge base now contains {stats['total_sessions']} sessions")
print(f"📈 30-day success rate: {stats['success_rate']:.1%}")
```

### PHASE 6: INTEGRATION WITH TASKMASTER

▶️ **TASK STARTING**: Update TaskMaster with knowledge capture results

```python
# 1. Add knowledge capture task to TaskMaster
mcp__taskmaster-ai__add_task(
    projectRoot=PROJECT_ROOT,
    prompt=f"Knowledge captured for session {session_id}",
    title="Session Knowledge Captured",
    description=f"Captured {len(lessons_learned)} lessons and {len(solution_patterns)} patterns",
    details=f"Session ID: {session_id}\nPatterns: {[p['pattern_id'] for p in solution_patterns]}"
)

# 2. Mark knowledge capture as complete
mcp__taskmaster-ai__set_task_status(
    id="knowledge_capture_task_id",
    status="done",
    projectRoot=PROJECT_ROOT
)

print("✅ TaskMaster updated with knowledge capture completion")
```

### PHASE 7: KNOWLEDGE SUMMARY GENERATION

▶️ **TASK STARTING**: Generate summary for immediate reference

```python
# 1. Generate session summary
session_summary = f"""
# CI Troubleshooting Session Summary

**Session ID**: {session_id}
**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Repository**: {current_context['repository']}
**Branch**: {current_context['branch']}
**Final Status**: {current_context.get('final_ci_status', 'success')}

## Key Lessons Learned
{chr(10).join(f'- {lesson}' for lesson in lessons_learned[:5])}

## Solution Patterns Identified
{chr(10).join(f'- **{p["pattern_id"]}**: {p["description"]}' for p in solution_patterns)}

## Success Metrics
- Duration: {current_context.get('duration_minutes', 0)} minutes
- Quality gates: {len([g for g in final_quality_results.values() if g.get('status') == 'PASS'])} passed
- Tools used: {', '.join(current_context.get('tools_used', []))}

## Knowledge Base Status
- Total sessions: {stats['total_sessions']}
- Success rate: {stats['success_rate']:.1%}
- Common patterns: {len(stats.get('common_patterns', []))}
"""

# 2. Save summary to file
summary_file = f".claude/knowledge/summaries/{session_id}_summary.md"
with open(summary_file, 'w') as f:
    f.write(session_summary)

print(f"📄 Session summary saved to {summary_file}")
print("\n" + "="*60)
print("🎯 KNOWLEDGE CAPTURE COMPLETE")
print("="*60)
print(session_summary)
print("="*60)
```

## INTEGRATION POINTS

### With Existing Commands
- **AG_CI_analyzer**: Auto-trigger knowledge capture at session completion
- **TaskMaster AI**: Integration for task tracking and session data
- **Git workflow**: Extract insights from commit messages and PR changes

### With Future Sessions
- **Session startup**: Query knowledge base for relevant past solutions
- **Problem analysis**: Search for similar past failures and solutions
- **Pattern recognition**: Identify recurring issues and proven approaches

## SUCCESS CRITERIA

🎯 **Knowledge capture considered successful when**:
- ✅ Session data extracted and structured
- ✅ Lessons learned identified and categorized
- ✅ Solution patterns documented with reusability
- ✅ Knowledge stored in searchable format
- ✅ TaskMaster integration completed
- ✅ Summary generated for immediate reference

## USAGE EXAMPLES

### Manual Knowledge Capture
```bash
# After completing CI troubleshooting
cd /path/to/project
python .claude/knowledge/tools/knowledge_manager.py capture_current_session
```

### Search Historical Knowledge
```bash
# Search for similar issues
python .claude/knowledge/tools/knowledge_manager.py search "import error CI"
python .claude/knowledge/tools/knowledge_manager.py search "async test timeout"
```

### Get Knowledge Summary
```bash
# Get recent session summary
python .claude/knowledge/tools/knowledge_manager.py summary 7
```

## AUTOMATION INTEGRATION

### TaskMaster Integration
Add to TaskMaster completion workflow:
```python
# At end of successful CI resolution
if final_status == "success":
    # Auto-trigger knowledge capture
    execute_knowledge_capture_command()
```

### Git Hook Integration
Add to post-commit or pre-push hooks:
```bash
#!/bin/bash
# Check if this is a CI fix commit
if git log -1 --pretty=%B | grep -E "(fix.*CI|resolve.*test|fix.*pytest)"; then
    echo "🧠 Triggering knowledge capture for CI fix..."
    python .claude/knowledge/tools/knowledge_manager.py auto_capture
fi
```

This command provides comprehensive knowledge capture capabilities specifically designed for Claude Code's CI troubleshooting workflows, ensuring that valuable lessons learned are preserved and accessible for future sessions.