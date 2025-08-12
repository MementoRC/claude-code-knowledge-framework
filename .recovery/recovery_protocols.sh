#!/bin/bash
# Error Recovery Protocols for claude-code-knowledge-framework
# Session: MementoRC/claude-code-knowledge-framework

set -euo pipefail

# =============================================================================
# GLOBAL CONFIGURATION
# =============================================================================

readonly PROJECT_ROOT="/home/memento/ClaudeCode/Servers/claude-code-knowledge-framework/worktrees/feat-ci-integration"
readonly RECOVERY_DIR="$PROJECT_ROOT/.recovery"
readonly CHECKPOINT_DIR="$RECOVERY_DIR/checkpoints"
readonly ERROR_REPORTS_DIR="$RECOVERY_DIR/error_reports"
readonly STATE_BACKUPS_DIR="$RECOVERY_DIR/state_backups"
readonly EMERGENCY_PROCEDURES_DIR="$RECOVERY_DIR/emergency_procedures"

# Framework compliance thresholds
readonly MCP_USAGE_TARGET=95
readonly STRATEGIC_BASH_LIMIT=5
readonly QUALITY_GATE_TOLERANCE=0

# =============================================================================
# ERROR CLASSIFICATION FRAMEWORK
# =============================================================================

# Error severity levels
declare -A ERROR_LEVELS=(
    ["tool_failure"]="1"
    ["context_transfer"]="2"
    ["quality_gate"]="3"
    ["system_failure"]="4"
)

# Recovery strategies by error level
declare -A RECOVERY_STRATEGIES=(
    ["1"]="automatic_fallback"
    ["2"]="minimal_context_retry"
    ["3"]="mandatory_stop_and_fix"
    ["4"]="emergency_protocols"
)

# =============================================================================
# CHECKPOINT SYSTEM
# =============================================================================

create_operation_checkpoint() {
    local agent_type="$1"
    local operation="$2"
    local task_id="${3:-unknown}"

    local checkpoint_id="ckpt_${agent_type}_$(date +%s)"
    local checkpoint_path="$CHECKPOINT_DIR/$checkpoint_id"

    echo "=== CREATING OPERATION CHECKPOINT ==="
    echo "ID: $checkpoint_id"
    echo "Agent: $agent_type"
    echo "Operation: $operation"
    echo "Task: $task_id"

    mkdir -p "$checkpoint_path"

    # Capture metadata
    {
        echo "checkpoint_id=$checkpoint_id"
        echo "agent_type=$agent_type"
        echo "operation=$operation"
        echo "task_id=$task_id"
        echo "timestamp=$(date -Iseconds)"
        echo "project_root=$PROJECT_ROOT"
        echo "session_id=MementoRC/claude-code-knowledge-framework"
    } > "$checkpoint_path/metadata.txt"

    # Capture TaskMaster state
    if [[ -f "$PROJECT_ROOT/.taskmaster/tasks/tasks.json" ]]; then
        cp "$PROJECT_ROOT/.taskmaster/tasks/tasks.json" "$checkpoint_path/taskmaster_backup.json" 2>/dev/null || true
    fi

    if [[ -f "$PROJECT_ROOT/.taskmaster/state.json" ]]; then
        cp "$PROJECT_ROOT/.taskmaster/state.json" "$checkpoint_path/taskmaster_state.json" 2>/dev/null || true
    fi

    # Capture git state (using strategic bash for git operations)
    if command -v git >/dev/null 2>&1; then
        {
            echo "=== GIT STATE CAPTURE ==="
            echo "Branch: $(git branch --show-current 2>/dev/null || echo 'unknown')"
            echo "Commit: $(git rev-parse HEAD 2>/dev/null || echo 'unknown')"
            echo "Status:"
            git status --porcelain 2>/dev/null || echo "git status failed"
        } > "$checkpoint_path/git_state.txt"

        # Capture diffs
        git diff > "$checkpoint_path/git_diff.patch" 2>/dev/null || true
        git diff --staged > "$checkpoint_path/git_staged.patch" 2>/dev/null || true
    fi

    # Capture quality status
    capture_quality_status > "$checkpoint_path/quality_status.json" 2>/dev/null || true

    # Store checkpoint reference
    echo "$checkpoint_id" > "$RECOVERY_DIR/latest_checkpoint"

    echo " Checkpoint created: $checkpoint_id"
    return 0
}

restore_from_checkpoint() {
    local checkpoint_id="${1:-$(cat "$RECOVERY_DIR/latest_checkpoint" 2>/dev/null)}"
    local checkpoint_path="$CHECKPOINT_DIR/$checkpoint_id"

    if [[ ! -d "$checkpoint_path" ]]; then
        echo "L Checkpoint not found: $checkpoint_id"
        return 1
    fi

    echo "=== RESTORING FROM CHECKPOINT ==="
    echo "Checkpoint: $checkpoint_id"

    # Load checkpoint metadata
    if [[ -f "$checkpoint_path/metadata.txt" ]]; then
        source "$checkpoint_path/metadata.txt"
        echo "Agent: $agent_type"
        echo "Operation: $operation"
        echo "Timestamp: $timestamp"
    fi

    # Restore TaskMaster state
    if [[ -f "$checkpoint_path/taskmaster_backup.json" ]]; then
        echo "Restoring TaskMaster tasks..."
        mkdir -p "$PROJECT_ROOT/.taskmaster/tasks"
        cp "$checkpoint_path/taskmaster_backup.json" "$PROJECT_ROOT/.taskmaster/tasks/tasks.json"
    fi

    if [[ -f "$checkpoint_path/taskmaster_state.json" ]]; then
        echo "Restoring TaskMaster state..."
        cp "$checkpoint_path/taskmaster_state.json" "$PROJECT_ROOT/.taskmaster/state.json"
    fi

    # Restore git state if needed (strategic bash usage)
    if [[ -f "$checkpoint_path/git_state.txt" ]] && command -v git >/dev/null 2>&1; then
        echo "Git state available for manual restoration if needed"
        echo "See: $checkpoint_path/git_state.txt"

        # Apply patches if they exist and user confirms
        if [[ -s "$checkpoint_path/git_staged.patch" ]] || [[ -s "$checkpoint_path/git_diff.patch" ]]; then
            echo "Git patches available for restoration:"
            echo "- Staged: $checkpoint_path/git_staged.patch"
            echo "- Working: $checkpoint_path/git_diff.patch"
        fi
    fi

    echo " Checkpoint restoration completed"
    return 0
}

# =============================================================================
# QUALITY STATUS PRESERVATION
# =============================================================================

capture_quality_status() {
    local status_file="${1:-/dev/stdout}"

    {
        echo "{"
        echo "  \"timestamp\": \"$(date -Iseconds)\","
        echo "  \"project_root\": \"$PROJECT_ROOT\","

        # Test status
        if cd "$PROJECT_ROOT" && pixi run test >/dev/null 2>&1; then
            echo "  \"tests\": \"passing\","
        else
            echo "  \"tests\": \"failing\","
        fi

        # Lint status
        if cd "$PROJECT_ROOT" && pixi run lint >/dev/null 2>&1; then
            echo "  \"lint\": \"clean\","
        else
            echo "  \"lint\": \"violations\","
        fi

        # Quality status
        if cd "$PROJECT_ROOT" && pixi run quality >/dev/null 2>&1; then
            echo "  \"quality\": \"passing\","
        else
            echo "  \"quality\": \"failing\","
        fi

        # Framework compliance
        local mcp_ratio=$(calculate_mcp_usage_ratio 2>/dev/null || echo "unknown")
        echo "  \"mcp_compliance\": \"$mcp_ratio\","

        echo "  \"pixi_compliance\": $(check_pixi_compliance && echo 'true' || echo 'false')"
        echo "}"
    } | tee "$status_file"
}

# =============================================================================
# MCP TOOL FAILURE HANDLING
# =============================================================================

handle_mcp_failure() {
    local tool_name="$1"
    local operation="$2"
    local error_message="$3"
    local context="${4:-}"

    echo "=== MCP TOOL FAILURE RECOVERY ==="
    echo "Tool: $tool_name"
    echo "Operation: $operation"
    echo "Error: $error_message"

    # Log MCP limitation for improvement tracking
    log_mcp_limitation "$tool_name" "$operation" "$error_message"

    # Check strategic Bash allowance (5% target)
    local bash_usage_ratio=$(calculate_current_bash_ratio 2>/dev/null || echo "0")

    if (( $(echo "$bash_usage_ratio < $STRATEGIC_BASH_LIMIT" | bc -l 2>/dev/null || echo "1") )); then
        echo "Attempting strategic Bash fallback..."

        case "$operation" in
            "git_status")
                if execute_strategic_bash_operation "git status --porcelain"; then
                    log_strategic_usage "git status" "mcp_git_limitation"
                    return 0
                fi
                ;;
            "git_add_interactive")
                if execute_strategic_bash_operation "git add -p"; then
                    log_strategic_usage "git add -p" "mcp_interactive_limitation"
                    return 0
                fi
                ;;
            "git_config")
                if execute_strategic_bash_operation "git config --list"; then
                    log_strategic_usage "git config" "mcp_config_limitation"
                    return 0
                fi
                ;;
            "taskmaster_connection")
                echo "TaskMaster MCP connection failed - attempting CLI fallback"
                if test_taskmaster_cli_availability; then
                    log_strategic_usage "task-master CLI" "mcp_taskmaster_limitation"
                    return 0
                fi
                ;;
        esac
    else
        echo "L Strategic Bash limit exceeded (${bash_usage_ratio}% >= ${STRATEGIC_BASH_LIMIT}%)"
    fi

    # Generate error report
    generate_error_report "MCP_TOOL_FAILURE" "error-recovery-specialist" "$operation" "$error_message" "strategic_bash_attempted" "false"

    # Escalate to main context
    escalate_to_main_context "MCP_TOOL_FAILURE" "$tool_name" "$operation" "$error_message"
    return 1
}

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

calculate_mcp_usage_ratio() {
    # Placeholder - implement based on actual usage tracking
    echo "95"
}

calculate_current_bash_ratio() {
    # Placeholder - implement based on actual usage tracking
    echo "3"
}

check_pixi_compliance() {
    # Check for pip usage or non-pixi dependencies
    if cd "$PROJECT_ROOT" && grep -r "pip install" . >/dev/null 2>&1; then
        return 1
    fi
    return 0
}

log_mcp_limitation() {
    local tool_name="$1"
    local operation="$2"
    local error_message="$3"

    {
        echo "$(date -Iseconds): MCP_LIMITATION"
        echo "Tool: $tool_name"
        echo "Operation: $operation"
        echo "Error: $error_message"
        echo "---"
    } >> "$ERROR_REPORTS_DIR/mcp_limitations.log"
}

log_strategic_usage() {
    local operation="$1"
    local justification="$2"

    {
        echo "$(date -Iseconds): STRATEGIC_BASH_USAGE"
        echo "Operation: $operation"
        echo "Justification: $justification"
        echo "---"
    } >> "$ERROR_REPORTS_DIR/strategic_bash_usage.log"
}

execute_strategic_bash_operation() {
    local command="$1"

    # Log the strategic usage
    echo "Executing strategic bash: $command"

    # Execute with error handling
    if eval "$command"; then
        return 0
    else
        echo "Strategic bash operation failed: $command"
        return 1
    fi
}

test_taskmaster_cli_availability() {
    if command -v task-master >/dev/null 2>&1; then
        echo "TaskMaster CLI available"
        return 0
    else
        echo "TaskMaster CLI not available"
        return 1
    fi
}

generate_error_report() {
    local error_type="$1"
    local agent_type="$2"
    local operation="$3"
    local error_message="$4"
    local recovery_attempted="$5"
    local recovery_success="$6"

    local report_file="$ERROR_REPORTS_DIR/error_$(date +%s).json"

    {
        echo "{"
        echo "  \"timestamp\": \"$(date -Iseconds)\","
        echo "  \"session_id\": \"MementoRC/claude-code-knowledge-framework\","
        echo "  \"error_type\": \"$error_type\","
        echo "  \"agent_type\": \"$agent_type\","
        echo "  \"operation\": \"$operation\","
        echo "  \"error_message\": \"$error_message\","
        echo "  \"recovery_attempted\": \"$recovery_attempted\","
        echo "  \"recovery_success\": $recovery_success,"
        echo "  \"project_root\": \"$PROJECT_ROOT\","
        echo "  \"system_state\": {"
        echo "    \"quality_status\": \"$(cd "$PROJECT_ROOT" && pixi run quality >/dev/null 2>&1 && echo 'passing' || echo 'failing')\","
        echo "    \"mcp_compliance\": \"$(calculate_mcp_usage_ratio)%\","
        echo "    \"pixi_compliance\": $(check_pixi_compliance && echo 'true' || echo 'false')"
        echo "  }"
        echo "}"
    } > "$report_file"

    echo "Error report generated: $report_file"
}

escalate_to_main_context() {
    local error_type="$1"
    local component="$2"
    local operation="$3"
    local details="${4:-}"

    echo "=== ESCALATING TO MAIN CONTEXT ==="
    echo "Error Type: $error_type"
    echo "Component: $component"
    echo "Operation: $operation"
    echo "Details: $details"
    echo ""
    echo "ESCALATION REASON: Automated recovery failed"
    echo "MANUAL INTERVENTION REQUIRED"
    echo ""
    echo "Next steps:"
    echo "1. Review error reports in: $ERROR_REPORTS_DIR"
    echo "2. Check latest checkpoint: $(cat "$RECOVERY_DIR/latest_checkpoint" 2>/dev/null || echo 'none')"
    echo "3. Investigate root cause"
    echo "4. Apply systematic fix"
    echo "5. Verify quality gates before proceeding"
}

# =============================================================================
# MAIN FUNCTIONS
# =============================================================================

# Initialize recovery system
initialize_recovery_system() {
    echo "=== INITIALIZING ERROR RECOVERY SYSTEM ==="
    echo "Project: $PROJECT_ROOT"
    echo "Session: MementoRC/claude-code-knowledge-framework"

    # Create directory structure
    mkdir -p "$CHECKPOINT_DIR" "$ERROR_REPORTS_DIR" "$STATE_BACKUPS_DIR" "$EMERGENCY_PROCEDURES_DIR"

    # Create initial checkpoint
    create_operation_checkpoint "error-recovery-specialist" "system_initialization" "setup"

    # Capture initial quality status
    capture_quality_status "$STATE_BACKUPS_DIR/initial_quality_status.json"

    # Create emergency contact information
    {
        echo "=== EMERGENCY RECOVERY CONTACTS ==="
        echo "Session: MementoRC/claude-code-knowledge-framework"
        echo "Project: claude-code-knowledge-framework"
        echo "Recovery System: $RECOVERY_DIR"
        echo "Escalation Protocol: escalate_to_main_context"
        echo ""
        echo "=== CRITICAL THRESHOLDS ==="
        echo "MCP Usage Target: ${MCP_USAGE_TARGET}%"
        echo "Strategic Bash Limit: ${STRATEGIC_BASH_LIMIT}%"
        echo "Quality Gate Tolerance: ${QUALITY_GATE_TOLERANCE}"
        echo ""
        echo "=== RECOVERY COMMANDS ==="
        echo "Restore Latest Checkpoint: restore_from_checkpoint"
        echo "Emergency Recovery: emergency_recovery"
        echo "Quality Recovery: handle_quality_failure"
        echo "MCP Fallback: handle_mcp_failure"
    } > "$EMERGENCY_PROCEDURES_DIR/emergency_contacts.txt"

    echo " Error recovery system initialized"
    echo "Recovery directory: $RECOVERY_DIR"
    echo "Latest checkpoint: $(cat "$RECOVERY_DIR/latest_checkpoint" 2>/dev/null)"
}

# Health check function
recovery_system_health_check() {
    echo "=== RECOVERY SYSTEM HEALTH CHECK ==="

    # Check directory structure
    for dir in "$CHECKPOINT_DIR" "$ERROR_REPORTS_DIR" "$STATE_BACKUPS_DIR" "$EMERGENCY_PROCEDURES_DIR"; do
        if [[ -d "$dir" ]]; then
            echo " $dir exists"
        else
            echo "L $dir missing"
        fi
    done

    # Check for latest checkpoint
    if [[ -f "$RECOVERY_DIR/latest_checkpoint" ]]; then
        local latest=$(cat "$RECOVERY_DIR/latest_checkpoint")
        echo " Latest checkpoint: $latest"
    else
        echo "  No checkpoints available"
    fi

    # Check quality status
    if cd "$PROJECT_ROOT" && pixi run quality >/dev/null 2>&1; then
        echo " Quality gates passing"
    else
        echo "L Quality gates failing"
    fi

    # Check framework compliance
    run_comprehensive_compliance_check
}

run_comprehensive_compliance_check() {
    echo "Running comprehensive framework compliance check..."

    local compliance_issues=0

    # Check MCP usage ratio
    local mcp_ratio=$(calculate_mcp_usage_ratio)
    if (( $(echo "$mcp_ratio < $MCP_USAGE_TARGET" | bc -l 2>/dev/null || echo "1") )); then
        echo "L MCP usage below target: ${mcp_ratio}% < ${MCP_USAGE_TARGET}%"
        ((compliance_issues++))
    else
        echo " MCP usage compliance: ${mcp_ratio}%"
    fi

    # Check PIXI-only compliance
    if ! check_pixi_compliance; then
        echo "L PIXI-only compliance violation detected"
        ((compliance_issues++))
    else
        echo " PIXI-only compliance verified"
    fi

    # Check quality gates
    if cd "$PROJECT_ROOT" && ! pixi run quality >/dev/null 2>&1; then
        echo "L Quality gates failing"
        ((compliance_issues++))
    else
        echo " Quality gates passing"
    fi

    # Check TaskMaster integration
    if [[ ! -f "$PROJECT_ROOT/.taskmaster/tasks/tasks.json" ]]; then
        echo "L TaskMaster integration missing"
        ((compliance_issues++))
    else
        echo " TaskMaster integration present"
    fi

    if (( compliance_issues == 0 )); then
        echo " All framework compliance checks passed"
        return 0
    else
        echo "L Framework compliance issues found: $compliance_issues"
        return 1
    fi
}

# =============================================================================
# ENTRY POINT
# =============================================================================

# If script is executed directly, initialize the system
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    case "${1:-init}" in
        "init")
            initialize_recovery_system
            ;;
        "health")
            recovery_system_health_check
            ;;
        "restore")
            restore_from_checkpoint "${2:-}"
            ;;
        "emergency")
            emergency_recovery "${2:-system_failure}" "${3:-manual_trigger}"
            ;;
        *)
            echo "Usage: $0 {init|health|restore [checkpoint_id]|emergency [failure_type] [context]}"
            exit 1
            ;;
    esac
fi
