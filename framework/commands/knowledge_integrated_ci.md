# Integrated Knowledge Management for CI Troubleshooting

> Enhanced AG_CI_analyzer with automatic knowledge management integration

## EXECUTION GUIDE

This command enhances the existing AG_CI_analyzer workflow with automatic knowledge management, providing historical context at the start and capturing lessons learned at the end.

**Prerequisites**: 
- Knowledge management system initialized
- AG_CI_analyzer workflow functional
- TaskMaster AI and MCP tools configured

**Usage**: `/knowledge_integrated_ci` (replaces AG_CI_analyzer for knowledge-enhanced sessions)

## ENHANCED WORKFLOW

### PHASE 0: KNOWLEDGE-ENHANCED INITIALIZATION

▶️ **TASK STARTING**: Initialize session with historical knowledge context

```python
# 1. Quick knowledge base check
import os
knowledge_available = os.path.exists('.claude/knowledge/tools/knowledge_manager.py')

if knowledge_available:
    print("🧠 Initializing knowledge-enhanced CI troubleshooting...")
    
    # Initialize knowledge manager
    import sys
    sys.path.append('.claude/knowledge/tools')
    from knowledge_manager import ClaudeCodeKnowledgeManager
    km = ClaudeCodeKnowledgeManager()
    
    # Get recent context summary
    knowledge_context = km.get_session_context_summary(days_back=7)
    print(f"📚 Knowledge base: {knowledge_context['total_sessions']} sessions, {knowledge_context['success_rate']:.1%} success rate")
    
    # Store for later use
    session_knowledge_context = knowledge_context
else:
    print("ℹ️  Knowledge management not available - proceeding with standard workflow")
    session_knowledge_context = None

# 2. Initialize session tracking
session_start_time = datetime.now()
session_data = {
    "session_id": f"{session_start_time.strftime('%Y-%m-%d_%H%M%S')}_{uuid.uuid4().hex[:8]}",
    "start_time": session_start_time.isoformat(),
    "repository": GITHUB_REPO,
    "branch": current_branch,
    "pr_number": WORKING_PR,
    "knowledge_enhanced": knowledge_available,
    "initial_knowledge_context": session_knowledge_context
}

print(f"🎯 Starting knowledge-enhanced session: {session_data['session_id']}")
```

### PHASE 1: ENHANCED CI STATUS ANALYSIS WITH KNOWLEDGE LOOKUP

▶️ **TASK STARTING**: Analyze CI status with historical knowledge integration

```python
# 1. Standard CI analysis (from AG_CI_analyzer)
print("🔍 Analyzing CI status with GitHub MCP tools...")

pr_status = mcp__git__github_get_pr_status(
    repo_owner=REPO_OWNER, 
    repo_name=REPO_NAME, 
    pr_number=WORKING_PR
)

# Extract failures
initial_failures = []
if pr_status.state == "failure":
    failing_jobs = mcp__git__github_get_failing_jobs(
        repo_owner=REPO_OWNER, 
        repo_name=REPO_NAME, 
        pr_number=WORKING_PR,
        include_logs=True,
        include_annotations=True
    )
    
    # Extract pytest output
    for job in failing_jobs:
        if "pytest" in job.get("name", "").lower():
            if job.get("logs"):
                pytest_lines = [
                    line for line in job.get("logs", "").split("\n")
                    if any(keyword in line for keyword in ["FAILED", "ERROR", "ImportError", "ModuleNotFoundError"])
                ]
                initial_failures.extend(pytest_lines[:10])  # Limit to top 10

# 2. ENHANCED: Knowledge-based failure analysis
if knowledge_available and initial_failures:
    print("🧠 Searching knowledge base for similar failures...")
    
    historical_solutions = []
    for failure in initial_failures[:5]:  # Top 5 failures
        search_results = km.search_knowledge(
            query=failure,
            context={"repository": GITHUB_REPO, "branch": current_branch},
            max_results=2
        )
        
        if search_results:
            for result in search_results:
                historical_solutions.append({
                    "current_failure": failure,
                    "historical_session": result["session_data"]["session_id"],
                    "similarity_score": result["similarity_score"],
                    "historical_status": result["session_data"]["final_status"],
                    "historical_lessons": result["session_data"].get("lessons_learned", [])[:3]
                })
    
    print(f"📚 Found {len(historical_solutions)} relevant historical solutions")
    
    # Get pattern suggestions
    pattern_suggestions = km.suggest_solutions(
        current_failures=initial_failures,
        context={"repository": GITHUB_REPO, "branch": current_branch}
    )
    
    print(f"🎯 Generated {len(pattern_suggestions)} pattern-based suggestions")
    
    # Store enhanced context
    session_data.update({
        "initial_failures": initial_failures,
        "historical_solutions": historical_solutions,
        "pattern_suggestions": pattern_suggestions
    })

else:
    print("📊 Standard CI analysis - no historical knowledge integration")
    session_data.update({
        "initial_failures": initial_failures,
        "historical_solutions": [],
        "pattern_suggestions": []
    })

print(f"✅ Enhanced CI analysis complete - {len(initial_failures)} failures detected")
```

### PHASE 2: KNOWLEDGE-INFORMED FAILURE ANALYSIS

▶️ **TASK STARTING**: AI-powered analysis enhanced with historical context

```python
# 1. Standard pytest-analyzer analysis
print("🧠 Running AI-powered failure analysis with pytest-analyzer...")

if initial_failures:
    # Generate pytest-analyzer suggestions
    pytest_ci_output = "\n".join(initial_failures)
    
    intelligent_suggestions = mcp__pytest-analyzer__suggest_fixes(
        raw_output=pytest_ci_output,
        max_suggestions=20,
        confidence_threshold=0.3,
        include_alternatives=True
    )
    
    print(f"💡 Pytest-analyzer generated {len(intelligent_suggestions.get('suggestions', []))} suggestions")

# 2. ENHANCED: Combine with historical knowledge
if knowledge_available and session_data.get("historical_solutions"):
    print("🔗 Integrating historical knowledge with AI analysis...")
    
    # Create enhanced suggestions that combine AI analysis with historical success
    enhanced_suggestions = []
    
    for ai_suggestion in intelligent_suggestions.get('suggestions', []):
        # Check if this suggestion type has historical success
        suggestion_type = ai_suggestion.get('failure_type', '')
        historical_match = None
        
        for hist_solution in session_data["historical_solutions"]:
            if suggestion_type.lower() in hist_solution["current_failure"].lower():
                historical_match = hist_solution
                break
        
        enhanced_suggestion = ai_suggestion.copy()
        if historical_match:
            enhanced_suggestion["historical_context"] = {
                "similar_session": historical_match["historical_session"],
                "historical_success": historical_match["historical_status"] == "success",
                "confidence_boost": 0.2 if historical_match["historical_status"] == "success" else 0,
                "historical_lessons": historical_match["historical_lessons"]
            }
            enhanced_suggestion["confidence"] = min(
                enhanced_suggestion.get("confidence", 0.5) + enhanced_suggestion["historical_context"]["confidence_boost"],
                1.0
            )
        
        enhanced_suggestions.append(enhanced_suggestion)
    
    # Sort by enhanced confidence
    enhanced_suggestions.sort(key=lambda x: x.get("confidence", 0), reverse=True)
    
    print(f"🎯 Enhanced {len(enhanced_suggestions)} suggestions with historical context")
    session_data["enhanced_suggestions"] = enhanced_suggestions

else:
    print("📊 Using standard AI analysis without historical enhancement")
    session_data["enhanced_suggestions"] = intelligent_suggestions.get('suggestions', [])

# 3. Create knowledge-informed priority categories
priority_categories = {"HIGH": [], "MEDIUM": [], "LOW": []}

for suggestion in session_data["enhanced_suggestions"]:
    confidence = suggestion.get("confidence", 0.0)
    has_historical_success = suggestion.get("historical_context", {}).get("historical_success", False)
    
    if has_historical_success and confidence > 0.7:
        priority = "HIGH"
    elif confidence > 0.6 or has_historical_success:
        priority = "MEDIUM"
    else:
        priority = "LOW"
    
    priority_categories[priority].append(suggestion)

session_data["priority_categories"] = priority_categories

print(f"📊 Prioritized suggestions: {len(priority_categories['HIGH'])} high, {len(priority_categories['MEDIUM'])} medium, {len(priority_categories['LOW'])} low")
```

### PHASE 3: ENHANCED SYSTEMATIC RESOLUTION

▶️ **TASK STARTING**: Execute resolution with knowledge-guided approach

```python
# 1. Create knowledge-enhanced resolution prompt
if session_data.get("historical_solutions"):
    historical_context = f"""
HISTORICAL KNOWLEDGE CONTEXT:
Previous similar failures resolved successfully:
{chr(10).join(f'- {sol["current_failure"][:80]} → Session {sol["historical_session"]} ({sol["historical_status"]})' for sol in session_data["historical_solutions"][:3])}

Key lessons from successful resolutions:
{chr(10).join(f'- {lesson}' for sol in session_data["historical_solutions"] for lesson in sol["historical_lessons"])}
"""
else:
    historical_context = "No historical context available for this failure pattern."

# 2. Enhanced aider prompt with historical knowledge
knowledge_enhanced_prompt = f"""
Knowledge-Enhanced CI Failure Resolution

CURRENT FAILURES:
{chr(10).join(f'- {failure[:100]}' for failure in initial_failures[:5])}

{historical_context}

AI ANALYSIS RESULTS (Enhanced with Historical Knowledge):
High Priority Fixes (Proven + High Confidence):
{chr(10).join(f'- {sug.get("suggestion", "")[:80]} (confidence: {sug.get("confidence", 0):.2f})' for sug in priority_categories["HIGH"][:3])}

Medium Priority Fixes:
{chr(10).join(f'- {sug.get("suggestion", "")[:80]} (confidence: {sug.get("confidence", 0):.2f})' for sug in priority_categories["MEDIUM"][:3])}

SYSTEMATIC RESOLUTION STRATEGY:
1. Apply HIGH priority fixes first (historical success + high AI confidence)
2. Validate each fix before proceeding to next
3. Use historical lessons learned to guide implementation
4. Focus on root causes identified in similar past sessions

QUALITY STANDARDS:
- All tests must pass: {TEST_CMD}
- Zero critical lint violations: {LINT_CMD}
- Pre-commit hooks must pass: {PRECOMMIT_CMD}

Apply knowledge-enhanced systematic resolution prioritizing historically successful approaches.
"""

# 3. Execute knowledge-enhanced resolution
print("🔧 Starting knowledge-enhanced systematic resolution...")

resolution_results = {"phases_completed": [], "fixes_applied": [], "knowledge_applied": []}

# Execute aider with enhanced context
editable_files = []
# Extract files from high priority suggestions
for suggestion in priority_categories["HIGH"][:5]:
    file_path = suggestion.get("file_path", "")
    if file_path and file_path not in editable_files:
        editable_files.append(file_path)

# Add files from historical successful sessions
for hist_solution in session_data.get("historical_solutions", []):
    session = hist_solution["historical_session"]
    # Would load session details to get files modified - simplified here
    
if editable_files:
    try:
        aider_result = mcp__aider__aider_ai_code(
            ai_coding_prompt=knowledge_enhanced_prompt,
            model="gemini/gemini-2.5-pro-preview-06-05",
            relative_editable_files=editable_files,
            relative_readonly_files=["tests/conftest.py", "pyproject.toml"]
        )
        
        resolution_results["fixes_applied"] = editable_files
        resolution_results["knowledge_applied"] = [
            f"Historical pattern: {len(session_data.get('historical_solutions', []))} similar cases",
            f"Enhanced AI suggestions: {len(priority_categories['HIGH'])} high priority",
            f"Pattern confidence boost: Applied to {len([s for s in session_data['enhanced_suggestions'] if s.get('historical_context')])} suggestions"
        ]
        
        print("✅ Knowledge-enhanced resolution applied successfully")
        
    except Exception as e:
        print(f"❌ Knowledge-enhanced resolution failed: {e}")

else:
    print("⚠️  No specific files identified for modification")

session_data["resolution_results"] = resolution_results
```

### PHASE 4: ENHANCED QUALITY VALIDATION & KNOWLEDGE TRACKING

▶️ **TASK STARTING**: Validate resolution and track knowledge application

```python
# 1. Standard quality validation (from AG_CI_analyzer)
print("🏁 Running enhanced quality validation...")

# Run all quality checks
quality_results = {}

# Tests
try:
    subprocess.run(TEST_CMD.split(), check=True, cwd=PROJECT_ROOT, timeout=900)
    quality_results["tests"] = {"status": "PASS", "details": "All tests passing"}
except subprocess.CalledProcessError as e:
    quality_results["tests"] = {"status": "FAIL", "exit_code": e.returncode}

# Lint
try:
    subprocess.run(LINT_CMD.split(), check=True, cwd=PROJECT_ROOT)
    quality_results["lint"] = {"status": "PASS", "details": "No critical violations"}
except subprocess.CalledProcessError as e:
    quality_results["lint"] = {"status": "FAIL", "exit_code": e.returncode}

# Pre-commit
try:
    subprocess.run(PRECOMMIT_CMD.split(), check=True, cwd=PROJECT_ROOT)
    quality_results["precommit"] = {"status": "PASS", "details": "All hooks passing"}
except subprocess.CalledProcessError as e:
    quality_results["precommit"] = {"status": "FAIL", "exit_code": e.returncode}

quality_passed = all(result.get("status") == "PASS" for result in quality_results.values())

# 2. ENHANCED: Track knowledge effectiveness
if quality_passed and session_data.get("historical_solutions"):
    print("🎯 Analyzing knowledge application effectiveness...")
    
    knowledge_effectiveness = {
        "historical_patterns_used": len(session_data.get("historical_solutions", [])),
        "enhanced_suggestions_applied": len([s for s in session_data["enhanced_suggestions"] if s.get("historical_context")]),
        "quality_validation_success": quality_passed,
        "resolution_time_minutes": (datetime.now() - session_start_time).total_seconds() / 60
    }
    
    session_data["knowledge_effectiveness"] = knowledge_effectiveness
    print(f"📊 Knowledge effectiveness: {knowledge_effectiveness['historical_patterns_used']} patterns used, {knowledge_effectiveness['enhanced_suggestions_applied']} enhanced suggestions")

session_data.update({
    "quality_results": quality_results,
    "quality_passed": quality_passed,
    "session_end_time": datetime.now().isoformat(),
    "total_duration_minutes": (datetime.now() - session_start_time).total_seconds() / 60
})
```

### PHASE 5: ENHANCED COMMIT WITH KNOWLEDGE ATTRIBUTION

▶️ **TASK STARTING**: Create commit with knowledge attribution

```python
if quality_passed:
    print("🔒 Creating knowledge-enhanced verified commit...")
    
    # Enhanced commit message with knowledge attribution
    knowledge_attribution = ""
    if session_data.get("historical_solutions"):
        knowledge_attribution = f"""
Knowledge Enhancement:
- Historical patterns applied: {len(session_data['historical_solutions'])}
- Similar successful sessions referenced: {len(set(sol['historical_session'] for sol in session_data['historical_solutions']))}
- AI suggestions enhanced with historical context: {len([s for s in session_data['enhanced_suggestions'] if s.get('historical_context')])}
- Knowledge base success rate: {session_data['initial_knowledge_context']['success_rate']:.1%}
"""
    
    enhanced_commit_message = f"""fix: knowledge-enhanced CI resolution for PR #{WORKING_PR}

Session: {session_data['session_id']}
Duration: {session_data['total_duration_minutes']:.1f} minutes

AI Analysis + Historical Knowledge:
- Total suggestions: {len(session_data['enhanced_suggestions'])}
- High priority (proven patterns): {len(priority_categories['HIGH'])}
- Medium priority: {len(priority_categories['MEDIUM'])}
- Historical knowledge integration: {'✅ Applied' if session_data.get('historical_solutions') else '❌ Not available'}

{knowledge_attribution}

Quality Validation:
- Tests: {quality_results.get('tests', {}).get('status', 'N/A')}
- Lint: {quality_results.get('lint', {}).get('status', 'N/A')}
- Pre-commit: {quality_results.get('precommit', {}).get('status', 'N/A')}

✅ Quality: All validation passing
🧠 AI-Enhanced: Pytest-analyzer + Historical Knowledge
🎯 CI Target: Systematic failure resolution with proven patterns

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Memento RC Mori <https://github.com/MementoRC>"""
    
    # Create verified commit
    mcp__git__git_add(repo_path=PROJECT_ROOT, files=resolution_results["fixes_applied"])
    
    mcp__git__git_commit(
        repo_path=PROJECT_ROOT,
        message=enhanced_commit_message,
        gpg_sign=True,
        gpg_key_id="C7927B4C27159961"
    )
    
    mcp__git__git_push(
        repo_path=PROJECT_ROOT,
        remote="origin",
        branch=current_branch
    )
    
    print("✅ Knowledge-enhanced commit created and pushed")
```

### PHASE 6: AUTOMATIC KNOWLEDGE CAPTURE

▶️ **TASK STARTING**: Capture knowledge from enhanced session

```python
if knowledge_available:
    print("💾 Capturing knowledge from enhanced session...")
    
    # Extract lessons learned from the session
    lessons_learned = []
    
    # From successful high-priority suggestions
    for suggestion in priority_categories["HIGH"]:
        if suggestion.get("historical_context", {}).get("historical_success"):
            lesson = f"✅ Historical pattern validated: {suggestion.get('failure_type', 'Unknown')} → {suggestion.get('suggestion', '')[:80]}"
            lessons_learned.append(lesson)
    
    # From quality validation results
    if quality_passed:
        lessons_learned.append("✅ Knowledge-enhanced approach achieved full quality validation")
        
    if session_data.get("knowledge_effectiveness"):
        eff = session_data["knowledge_effectiveness"]
        lesson = f"🎯 Knowledge effectiveness: {eff['historical_patterns_used']} patterns applied in {eff['resolution_time_minutes']:.1f} minutes"
        lessons_learned.append(lesson)
    
    # From new patterns discovered
    new_patterns = []
    for suggestion in session_data["enhanced_suggestions"]:
        if suggestion.get("confidence", 0) > 0.8 and not suggestion.get("historical_context"):
            # This is a new high-confidence pattern
            new_patterns.append({
                "pattern_id": f"new_pattern_{suggestion.get('failure_type', 'unknown').lower()}",
                "description": f"New effective approach for {suggestion.get('failure_type', 'unknown')}",
                "solution_template": suggestion.get('suggestion', ''),
                "confidence": suggestion.get('confidence', 0)
            })
    
    # Capture enhanced session knowledge
    captured_session_id = km.capture_session_knowledge(
        session_data=session_data,
        lessons_learned=lessons_learned,
        solution_patterns=new_patterns,
        manual_insights=[
            f"Knowledge-enhanced session resolved {len(initial_failures)} failures",
            f"Applied {len(session_data.get('historical_solutions', []))} historical patterns",
            f"Session duration: {session_data['total_duration_minutes']:.1f} minutes with knowledge enhancement"
        ]
    )
    
    print(f"💾 Enhanced session knowledge captured: {captured_session_id}")
    
    # Update knowledge base statistics
    updated_stats = km.get_session_context_summary(days_back=7)
    print(f"📊 Knowledge base updated: {updated_stats['total_sessions']} sessions, {updated_stats['success_rate']:.1%} success rate")

else:
    print("ℹ️  Knowledge capture not available - session completed without knowledge storage")
```

### PHASE 7: ENHANCED SESSION COMPLETION REPORT

▶️ **TASK STARTING**: Generate comprehensive enhanced session report

```python
# Generate enhanced completion report
enhanced_report = f"""
# 🧠 Knowledge-Enhanced CI Resolution Session Complete

**Session ID**: {session_data['session_id']}
**Duration**: {session_data['total_duration_minutes']:.1f} minutes
**Repository**: {session_data['repository']} / {session_data['branch']}
**Knowledge Enhanced**: {'✅ Yes' if session_data['knowledge_enhanced'] else '❌ No'}

## 📊 Session Analysis

### Initial Situation
- **CI Status**: {pr_status.state}
- **Failures Detected**: {len(initial_failures)}
- **Knowledge Base Status**: {session_data['initial_knowledge_context']['total_sessions'] if session_data.get('initial_knowledge_context') else 0} sessions available

### Knowledge Integration
- **Historical Solutions Found**: {len(session_data.get('historical_solutions', []))}
- **Pattern Suggestions**: {len(session_data.get('pattern_suggestions', []))}
- **Enhanced AI Suggestions**: {len([s for s in session_data.get('enhanced_suggestions', []) if s.get('historical_context')])}

### Resolution Results
- **Priority Categories**: {len(priority_categories['HIGH'])} high, {len(priority_categories['MEDIUM'])} medium, {len(priority_categories['LOW'])} low
- **Files Modified**: {len(resolution_results.get('fixes_applied', []))}
- **Knowledge Applied**: {len(resolution_results.get('knowledge_applied', []))}

### Quality Validation
- **Tests**: {quality_results.get('tests', {}).get('status', 'N/A')}
- **Lint**: {quality_results.get('lint', {}).get('status', 'N/A')}
- **Pre-commit**: {quality_results.get('precommit', {}).get('status', 'N/A')}
- **Overall Success**: {'✅ COMPLETE' if quality_passed else '❌ FAILED'}

## 🎯 Knowledge Enhancement Impact

{f'''
### Historical Knowledge Applied
- **Similar Sessions**: {len(set(sol['historical_session'] for sol in session_data['historical_solutions']))} unique sessions referenced
- **Success Rate of Referenced Sessions**: {len([sol for sol in session_data['historical_solutions'] if sol['historical_status'] == 'success'])} / {len(session_data['historical_solutions'])} successful
- **Pattern Confidence Boost**: Applied to {len([s for s in session_data['enhanced_suggestions'] if s.get('historical_context')])} suggestions

### Effectiveness Metrics
- **Resolution Time**: {session_data['total_duration_minutes']:.1f} minutes (vs. typical range)
- **Knowledge Patterns Used**: {session_data.get('knowledge_effectiveness', {}).get('historical_patterns_used', 0)}
- **New Patterns Discovered**: {len(new_patterns)} new effective patterns identified
''' if session_data.get('historical_solutions') else '''
### No Historical Knowledge Available
- This was a baseline session without historical context
- Session results will be captured for future knowledge enhancement
- Recommend running additional sessions to build knowledge base
'''}

## 📈 Knowledge Base Evolution

### Before Session
- Total Sessions: {session_data['initial_knowledge_context']['total_sessions'] if session_data.get('initial_knowledge_context') else 0}
- Success Rate: {session_data['initial_knowledge_context']['success_rate']:.1%} if session_data.get('initial_knowledge_context') else 'N/A'}

### After Session
- Total Sessions: {updated_stats['total_sessions'] if 'updated_stats' in locals() else 'N/A'}
- Success Rate: {updated_stats['success_rate']:.1%} if 'updated_stats' in locals() else 'N/A'}
- Knowledge Growth: {'✅ Session knowledge captured' if knowledge_available else '❌ Knowledge capture not available'}

## 🔄 Recommendations for Future Sessions

### Immediate Actions
{'✅ Session successful - CI resolution complete' if quality_passed else '❌ Session incomplete - manual intervention required'}

### Knowledge Base Recommendations
{f'''
- Continue using knowledge-enhanced workflow for cumulative improvement
- Monitor pattern effectiveness over multiple sessions
- Consider expanding knowledge base with team session data
''' if session_data['knowledge_enhanced'] else '''
- Initialize knowledge management system for future enhancement
- Capture lessons learned manually for next session bootstrap
- Consider implementing automated knowledge capture workflow
'''}

---
*Generated by Knowledge-Enhanced Claude Code CI Resolution System*
"""

print("\n" + "="*80)
print("🧠 KNOWLEDGE-ENHANCED CI RESOLUTION COMPLETE")
print("="*80)
print(enhanced_report)
print("="*80)

# Save enhanced report
report_file = f".claude/knowledge/reports/enhanced_session_{session_data['session_id']}.md"
os.makedirs(os.path.dirname(report_file), exist_ok=True)
with open(report_file, 'w') as f:
    f.write(enhanced_report)

print(f"📄 Enhanced session report saved: {report_file}")
```

## INTEGRATION & AUTOMATION

### Replace AG_CI_analyzer
```bash
# In .claude/commands/ directory
mv AG_CI_analyzer.md AG_CI_analyzer_basic.md
ln -s knowledge_integrated_ci.md AG_CI_analyzer.md
```

### Automatic Knowledge Enhancement
```python
# Add to session startup
def auto_enhance_with_knowledge():
    if os.path.exists('.claude/knowledge'):
        return execute_knowledge_integrated_ci()
    else:
        return execute_basic_ag_ci_analyzer()
```

This integrated approach transforms CI troubleshooting from isolated sessions into a continuously improving, knowledge-enhanced process that builds institutional memory and accelerates resolution times through proven patterns and historical success data.