# Knowledge Retrieve Command for CI Troubleshooting

> Retrieve relevant historical knowledge and solutions for current CI troubleshooting context

## EXECUTION GUIDE

**Prerequisites**: Knowledge base established with previous session captures
- Knowledge management system initialized
- Current CI context identified (failures, repository, branch)
- Access to `.claude/knowledge/` directory

**Usage**: `/knowledge_retrieve` or at start of CI troubleshooting sessions

## COMMAND WORKFLOW

### PHASE 1: CONTEXT ANALYSIS

▶️ **TASK STARTING**: Analyze current troubleshooting context

```python
# 1. Get current CI status and failures
current_pr_status = mcp__git__github_get_pr_status(
    repo_owner=REPO_OWNER, 
    repo_name=REPO_NAME, 
    pr_number=WORKING_PR
)

# 2. Extract current failures
current_failures = []
if current_pr_status.state == "failure":
    failing_jobs = mcp__git__github_get_failing_jobs(
        repo_owner=REPO_OWNER, 
        repo_name=REPO_NAME, 
        pr_number=WORKING_PR,
        include_logs=True
    )
    
    # Extract pytest failures from CI logs
    for job in failing_jobs:
        if "pytest" in job.get("name", "").lower():
            if job.get("logs"):
                # Extract specific test failures
                failure_lines = [
                    line for line in job.get("logs", "").split("\n")
                    if "FAILED" in line or "ERROR" in line
                ]
                current_failures.extend(failure_lines)

# 3. Get current context
current_context = {
    "repository": GITHUB_REPO,
    "branch": current_branch,
    "pr_number": WORKING_PR,
    "ci_status": current_pr_status.state,
    "failures": current_failures,
    "timestamp": datetime.now().isoformat()
}

print(f"🔍 Analyzed current context:")
print(f"   Repository: {current_context['repository']}")
print(f"   Branch: {current_context['branch']}")
print(f"   CI Status: {current_context['ci_status']}")
print(f"   Failures: {len(current_failures)} detected")
```

### PHASE 2: HISTORICAL KNOWLEDGE SEARCH

▶️ **TASK STARTING**: Search knowledge base for relevant solutions

```python
# 1. Initialize knowledge manager
import sys
sys.path.append('.claude/knowledge/tools')
from knowledge_manager import ClaudeCodeKnowledgeManager

km = ClaudeCodeKnowledgeManager()

# 2. Search for similar failures
relevant_knowledge = []

for failure in current_failures[:5]:  # Limit to top 5 failures
    print(f"🔎 Searching for solutions to: {failure[:80]}...")
    
    search_results = km.search_knowledge(
        query=failure,
        context=current_context,
        max_results=3
    )
    
    if search_results:
        for result in search_results:
            relevant_knowledge.append({
                "current_failure": failure,
                "historical_session": result["session_data"],
                "similarity_score": result["similarity_score"],
                "search_type": result["search_type"]
            })

print(f"📚 Found {len(relevant_knowledge)} relevant historical solutions")
```

### PHASE 3: PATTERN MATCHING

▶️ **TASK STARTING**: Identify applicable solution patterns

```python
# 1. Get solution suggestions based on patterns
solution_suggestions = km.suggest_solutions(
    current_failures=current_failures,
    context=current_context
)

# 2. Load common patterns for this repository/context
recent_summary = km.get_session_context_summary(days_back=30)
common_patterns = recent_summary.get("common_patterns", [])

# 3. Match current context to historical patterns
applicable_patterns = []
for pattern in common_patterns:
    pattern_keywords = pattern["description"].lower().split()
    
    # Check if any current failures match pattern keywords
    for failure in current_failures:
        failure_text = failure.lower()
        if any(keyword in failure_text for keyword in pattern_keywords):
            applicable_patterns.append({
                "pattern": pattern,
                "relevance_score": pattern["recent_count"] / pattern["total_count"],
                "matching_failure": failure
            })

print(f"🎯 Identified {len(applicable_patterns)} applicable patterns")
print(f"💡 Generated {len(solution_suggestions)} specific solution suggestions")
```

### PHASE 4: PRIORITY RANKING

▶️ **TASK STARTING**: Rank solutions by relevance and success probability

```python
# 1. Create comprehensive solution ranking
ranked_solutions = []

# Add pattern-based solutions (highest priority)
for pattern_match in applicable_patterns:
    ranked_solutions.append({
        "type": "pattern",
        "priority": "HIGH",
        "confidence": pattern_match["relevance_score"],
        "source": f"Pattern: {pattern_match['pattern']['description']}",
        "solution": {
            "approach": "Apply proven pattern",
            "description": pattern_match["pattern"]["description"],
            "recent_usage": pattern_match["pattern"]["recent_count"]
        },
        "matching_context": pattern_match["matching_failure"]
    })

# Add specific historical solutions (medium priority)
for suggestion in solution_suggestions:
    if suggestion["confidence"] > 0.6:
        ranked_solutions.append({
            "type": "historical",
            "priority": "MEDIUM",
            "confidence": suggestion["confidence"],
            "source": f"Session: {suggestion['source_session']}",
            "solution": suggestion["solution"],
            "matching_context": suggestion["failure"]
        })

# Add general historical matches (lower priority)
for knowledge in relevant_knowledge:
    if knowledge["similarity_score"] > 0.5:
        session = knowledge["historical_session"]
        ranked_solutions.append({
            "type": "similar_session",
            "priority": "LOW",
            "confidence": knowledge["similarity_score"],
            "source": f"Similar session: {session['session_id']}",
            "solution": {
                "approach": session.get("final_status", "unknown"),
                "lessons": session.get("lessons_learned", [])[:3],
                "context": session.get("context", {})
            },
            "matching_context": knowledge["current_failure"]
        })

# Sort by priority and confidence
priority_order = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
ranked_solutions.sort(
    key=lambda x: (priority_order[x["priority"]], x["confidence"]), 
    reverse=True
)

print(f"📊 Ranked {len(ranked_solutions)} solutions by relevance")
```

### PHASE 5: ACTIONABLE RECOMMENDATIONS

▶️ **TASK STARTING**: Generate actionable recommendations

```python
# 1. Create actionable TaskMaster tasks based on knowledge
recommended_tasks = []

for i, solution in enumerate(ranked_solutions[:5]):  # Top 5 solutions
    task_title = f"Apply Solution {i+1}: {solution['type'].title()}"
    
    if solution["type"] == "pattern":
        task_description = f"Apply proven pattern: {solution['source']}"
        task_details = f"""
Historical Success Pattern:
- Pattern: {solution['solution']['description']}
- Recent usage: {solution['solution']['recent_usage']} times
- Confidence: {solution['confidence']:.1%}

Recommended Approach:
1. Review pattern implementation from successful cases
2. Adapt pattern to current context
3. Apply pattern-specific fixes
4. Validate with local testing

Matching Context: {solution['matching_context'][:100]}...
"""
    
    elif solution["type"] == "historical":
        task_description = f"Apply historical solution: {solution['source']}"
        task_details = f"""
Historical Solution:
- Source: {solution['source']}
- Confidence: {solution['confidence']:.1%}
- Approach: {solution['solution']['approach']}

Key Lessons from Historical Success:
{chr(10).join(f'- {lesson}' for lesson in solution['solution'].get('key_lessons', []))}

Actions to Take:
{chr(10).join(f'- {action}' for action in solution['solution'].get('actions_taken', []))}

Matching Context: {solution['matching_context'][:100]}...
"""
    
    else:  # similar_session
        task_description = f"Review similar session: {solution['source']}"
        task_details = f"""
Similar Historical Session:
- Source: {solution['source']}
- Similarity: {solution['confidence']:.1%}
- Final Status: {solution['solution']['approach']}

Key Lessons from Similar Case:
{chr(10).join(f'- {lesson}' for lesson in solution['solution'].get('lessons', []))}

Context Similarity:
- Repository: {solution['solution']['context'].get('repository', 'N/A')}
- Branch pattern: {solution['solution']['context'].get('branch', 'N/A')}

Matching Context: {solution['matching_context'][:100]}...
"""
    
    recommended_tasks.append({
        "title": task_title,
        "description": task_description,
        "details": task_details,
        "priority": solution["priority"].lower(),
        "confidence": solution["confidence"]
    })

print(f"📋 Generated {len(recommended_tasks)} actionable task recommendations")
```

### PHASE 6: TASKMASTER INTEGRATION

▶️ **TASK STARTING**: Integrate recommendations with TaskMaster

```python
# 1. Add knowledge-based tasks to TaskMaster
added_task_ids = []

for task in recommended_tasks:
    task_id = mcp__taskmaster-ai__add_task(
        projectRoot=PROJECT_ROOT,
        title=task["title"],
        description=task["description"],
        details=task["details"],
        priority=task["priority"]
    )
    
    added_task_ids.append({
        "task_id": task_id,
        "confidence": task["confidence"],
        "type": task["title"]
    })

# 2. Create knowledge retrieval summary task
summary_task_id = mcp__taskmaster-ai__add_task(
    projectRoot=PROJECT_ROOT,
    title="Knowledge Retrieval Completed",
    description=f"Retrieved {len(relevant_knowledge)} historical solutions and {len(applicable_patterns)} patterns",
    details=f"""
Knowledge Retrieval Summary:
- Historical sessions analyzed: {len(relevant_knowledge)}
- Applicable patterns identified: {len(applicable_patterns)}
- Solution suggestions generated: {len(solution_suggestions)}
- Recommended tasks created: {len(recommended_tasks)}

Top Recommendations:
{chr(10).join(f'- {task["title"]} (confidence: {task["confidence"]:.1%})' for task in recommended_tasks[:3])}

Knowledge Base Status:
- Total sessions: {recent_summary['total_sessions']}
- 30-day success rate: {recent_summary['success_rate']:.1%}
- Common patterns available: {len(common_patterns)}
"""
)

# 3. Mark knowledge retrieval as complete
mcp__taskmaster-ai__set_task_status(
    id=summary_task_id,
    status="done",
    projectRoot=PROJECT_ROOT
)

print(f"✅ Added {len(added_task_ids)} knowledge-based tasks to TaskMaster")
```

### PHASE 7: KNOWLEDGE SUMMARY REPORT

▶️ **TASK STARTING**: Generate comprehensive knowledge summary

```python
# 1. Create detailed knowledge report
knowledge_report = f"""
# 🧠 CI Troubleshooting Knowledge Retrieval Report

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Context**: {current_context['repository']} / {current_context['branch']}
**Current Status**: {current_context['ci_status']}

## 📊 Current Situation Analysis

### CI Failures Detected: {len(current_failures)}
{chr(10).join(f'- {failure[:100]}{"..." if len(failure) > 100 else ""}' for failure in current_failures[:5])}

### Knowledge Base Search Results
- **Historical sessions found**: {len(relevant_knowledge)}
- **Applicable patterns**: {len(applicable_patterns)}
- **Solution suggestions**: {len(solution_suggestions)}

## 🎯 Top Recommended Approaches

{chr(10).join(f'''
### {i+1}. {task["title"]} 
**Priority**: {task["priority"].upper()}  
**Confidence**: {task["confidence"]:.1%}  
**Description**: {task["description"]}
''' for i, task in enumerate(recommended_tasks[:3]))}

## 📈 Knowledge Base Insights

### Recent Success Patterns (30 days)
{chr(10).join(f'- **{pattern["pattern_id"]}**: {pattern["description"]} (used {pattern["recent_count"]} times)' for pattern in common_patterns[:3])}

### Historical Performance
- **Total sessions**: {recent_summary['total_sessions']}
- **Success rate**: {recent_summary['success_rate']:.1%}
- **Average resolution time**: Estimated based on historical data

## 🔄 Recommended Workflow

1. **Start with HIGH priority recommendations** (proven patterns)
2. **Apply MEDIUM priority solutions** (specific historical matches)
3. **Consider LOW priority approaches** (similar contexts) if needed
4. **Capture new knowledge** from this session for future use

## 📚 Knowledge Sources

### Pattern Sources
{chr(10).join(f'- {pattern["pattern"]["description"]}: {pattern["pattern"]["recent_count"]} recent uses' for pattern in applicable_patterns[:3])}

### Historical Sessions Referenced
{chr(10).join(f'- {knowledge["historical_session"]["session_id"]}: {knowledge["similarity_score"]:.1%} similarity' for knowledge in relevant_knowledge[:3])}

---
*Knowledge retrieval powered by Claude Code Knowledge Management System*
"""

# 2. Save report to file
report_file = f".claude/knowledge/reports/retrieval_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
os.makedirs(os.path.dirname(report_file), exist_ok=True)
with open(report_file, 'w') as f:
    f.write(knowledge_report)

# 3. Display summary
print("\n" + "="*70)
print("🧠 KNOWLEDGE RETRIEVAL COMPLETE")
print("="*70)
print(f"📄 Full report saved to: {report_file}")
print(f"📋 {len(added_task_ids)} tasks added to TaskMaster workflow")
print(f"🎯 Top recommendation: {recommended_tasks[0]['title'] if recommended_tasks else 'No specific recommendations'}")
print(f"📊 Knowledge base: {recent_summary['total_sessions']} sessions, {recent_summary['success_rate']:.1%} success rate")
print("="*70)
```

## INTEGRATION POINTS

### With CI Analysis Workflow
- **AG_CI_analyzer**: Auto-trigger knowledge retrieval before analysis
- **Pytest-analyzer**: Cross-reference with historical similar failures
- **Aider integration**: Use historical solutions as context for AI fixes

### With Session Management
- **Session startup**: Automatic knowledge retrieval for context
- **TaskMaster workflow**: Knowledge-based task prioritization
- **Pattern recognition**: Historical pattern application

## SUCCESS CRITERIA

🎯 **Knowledge retrieval considered successful when**:
- ✅ Current context analyzed and failures identified
- ✅ Relevant historical knowledge found and ranked
- ✅ Applicable patterns identified and prioritized
- ✅ Actionable recommendations generated
- ✅ TaskMaster integration completed with knowledge-based tasks
- ✅ Knowledge summary report generated

## USAGE EXAMPLES

### Automatic Integration (Recommended)
```python
# Add to start of AG_CI_analyzer workflow
if os.path.exists('.claude/knowledge'):
    print("🧠 Retrieving relevant historical knowledge...")
    execute_knowledge_retrieve_command()
    print("✅ Knowledge retrieval complete - proceeding with informed analysis")
```

### Manual Knowledge Retrieval
```bash
# Search for specific issues
python .claude/knowledge/tools/knowledge_manager.py search "import error CI"

# Get context summary
python .claude/knowledge/tools/knowledge_manager.py summary 7

# Get suggestions for current failures
python .claude/knowledge/tools/knowledge_manager.py suggest_solutions "test_async.py::test_timeout"
```

### Quick Knowledge Check
```bash
# Quick check of recent patterns
python .claude/knowledge/tools/knowledge_manager.py quick_patterns

# Check success rate for similar context
python .claude/knowledge/tools/knowledge_manager.py success_rate --repository=current --days=30
```

This command provides comprehensive knowledge retrieval capabilities that transform each CI troubleshooting session from starting fresh to building on proven historical solutions and patterns.