#!/bin/bash
# Sub-Agent Error Recovery Integration Template
# Session: MementoRC/claude-code-knowledge-framework

# =============================================================================
# SUB-AGENT INTEGRATION TEMPLATE
# =============================================================================
#
# This template shows how sub-agents should integrate with the error recovery
# system to ensure resilient operations and framework compliance.
#
# Usage:
# 1. Copy this template for your sub-agent
# 2. Replace AGENT_NAME with your agent identifier
# 3. Integrate error handling into your operations
# 4. Use recovery functions for MCP failures and quality issues
#
# =============================================================================

set -euo pipefail

# Agent configuration
readonly AGENT_NAME="your-sub-agent-name"  # Replace with actual agent name
readonly PROJECT_ROOT="/home/memento/ClaudeCode/Servers/claude-code-knowledge-framework/worktrees/feat-ci-integration"
readonly RECOVERY_DIR="$PROJECT_ROOT/.recovery"

# Source the recovery functions
source "$RECOVERY_DIR/recovery_protocols.sh"

# =============================================================================
# OPERATION WRAPPER WITH ERROR HANDLING
# =============================================================================

execute_with_error_handling() {
    local operation="$1"
    local task_id="${2:-unknown}"
    shift 2

    echo "=== STARTING OPERATION WITH ERROR HANDLING ==="
    echo "Agent: $AGENT_NAME"
    echo "Operation: $operation"
    echo "Task: $task_id"

    # Create checkpoint before operation
    local checkpoint_id=$(create_operation_checkpoint "$AGENT_NAME" "$operation" "$task_id")

    # Execute operation with error capture
    local error_log=$(mktemp)

    if ! "$operation" "$@" 2>"$error_log"; then
        local error_message=$(cat "$error_log")
        echo "L Operation failed: $operation"
        echo "Error: $error_message"

        # Attempt recovery based on error type
        if echo "$error_message" | grep -i "mcp\|tool\|connection" >/dev/null; then
            echo "Detected MCP tool failure - attempting recovery..."
            if handle_mcp_failure "unknown_tool" "$operation" "$error_message"; then
                echo " MCP failure recovered successfully"
                rm -f "$error_log"
                return 0
            fi
        elif echo "$error_message" | grep -i "test\|lint\|quality" >/dev/null; then
            echo "Detected quality failure - attempting recovery..."
            if handle_quality_failure "quality_gate_failure" "$error_message"; then
                echo " Quality failure recovered successfully"
                rm -f "$error_log"
                return 0
            fi
        fi

        # If recovery fails, escalate
        echo "L Operation failed - escalating to error-recovery-specialist"
        escalate_to_error_recovery "$operation" "$error_message" "$checkpoint_id"
        rm -f "$error_log"
        return 1
    fi

    # Cleanup and success
    rm -f "$error_log"
    echo " Operation completed successfully: $operation"
    return 0
}

# =============================================================================
# MCP OPERATION WITH FALLBACK
# =============================================================================

execute_mcp_with_fallback() {
    local mcp_tool="$1"
    local operation="$2"
    local fallback_command="$3"
    shift 3

    echo "Attempting MCP operation: $mcp_tool"

    # Try MCP tool first
    if "$mcp_tool" "$@" 2>/dev/null; then
        echo " MCP operation successful: $mcp_tool"
        return 0
    fi

    # MCP failed, try fallback
    echo "L MCP tool failed: $mcp_tool"
    echo "Attempting strategic fallback: $fallback_command"

    if handle_mcp_failure "$mcp_tool" "$operation" "MCP tool unavailable"; then
        echo " Fallback successful"
        return 0
    else
        echo "L Both MCP and fallback failed"
        return 1
    fi
}

# =============================================================================
# QUALITY-AWARE OPERATION
# =============================================================================

execute_with_quality_validation() {
    local operation="$1"
    local task_id="${2:-unknown}"
    shift 2

    echo "=== QUALITY-AWARE OPERATION ==="
    echo "Operation: $operation"
    echo "Task: $task_id"

    # Pre-operation quality check
    if ! cd "$PROJECT_ROOT" && pixi run quality >/dev/null 2>&1; then
        echo "L Pre-operation quality check failed"
        echo "Attempting quality recovery before proceeding..."

        if ! handle_quality_failure "pre_operation_failure" "Quality gates failing before operation"; then
            echo "L Cannot proceed - quality gates must pass"
            return 1
        fi
    fi

    # Execute operation with error handling
    if ! execute_with_error_handling "$operation" "$task_id" "$@"; then
        echo "L Operation failed"
        return 1
    fi

    # Post-operation quality check
    if ! cd "$PROJECT_ROOT" && pixi run quality >/dev/null 2>&1; then
        echo "L Post-operation quality check failed"
        echo "Operation may have introduced quality issues"

        # Attempt automatic quality recovery
        if handle_quality_failure "post_operation_failure" "Quality gates failing after operation"; then
            echo " Quality issues resolved"
        else
            echo "L Quality issues persist - manual intervention required"
            return 1
        fi
    fi

    echo " Quality-validated operation completed"
    return 0
}

# =============================================================================
# TASKMASTER INTEGRATION WITH ERROR HANDLING
# =============================================================================

update_task_with_error_handling() {
    local task_id="$1"
    local update_message="$2"

    echo "Updating TaskMaster task: $task_id"

    # Try MCP TaskMaster first
    if command -v mcp__task-master-ai__update_task >/dev/null 2>&1; then
        if mcp__task-master-ai__update_task \
            --id="$task_id" \
            --prompt="$update_message" \
            --projectRoot="$PROJECT_ROOT" 2>/dev/null; then
            echo " TaskMaster updated via MCP"
            return 0
        fi
    fi

    # Fallback to CLI
    echo "MCP TaskMaster failed, trying CLI fallback..."
    if command -v task-master >/dev/null 2>&1; then
        if task-master update-task --id="$task_id" --prompt="$update_message"; then
            echo " TaskMaster updated via CLI"
            log_strategic_usage "task-master CLI" "mcp_taskmaster_limitation"
            return 0
        fi
    fi

    echo "L TaskMaster update failed - both MCP and CLI unavailable"
    return 1
}

# =============================================================================
# ERROR ESCALATION
# =============================================================================

escalate_to_error_recovery() {
    local operation="$1"
    local error_message="$2"
    local checkpoint_id="$3"

    echo "=== ESCALATING TO ERROR RECOVERY ==="
    echo "Agent: $AGENT_NAME"
    echo "Operation: $operation"
    echo "Checkpoint: $checkpoint_id"
    echo "Error: $error_message"

    # Generate comprehensive error report
    generate_error_report \
        "SUB_AGENT_FAILURE" \
        "$AGENT_NAME" \
        "$operation" \
        "$error_message" \
        "error_handling_attempted" \
        "false"

    # Update TaskMaster with error context if task_id available
    if [[ -n "${CURRENT_TASK_ID:-}" ]]; then
        local error_update="ERROR ENCOUNTERED in $operation

Error: $error_message
Agent: $AGENT_NAME
Checkpoint: $checkpoint_id
Timestamp: $(date -Iseconds)

Automated recovery attempted but failed. Manual intervention required."

        update_task_with_error_handling "$CURRENT_TASK_ID" "$error_update" || true
    fi

    # Escalate to main context
    escalate_to_main_context "SUB_AGENT_FAILURE" "$AGENT_NAME" "$operation" "$error_message"
}

# =============================================================================
# EXAMPLE USAGE
# =============================================================================

# Example: Safe MCP operation with fallback
example_git_operation() {
    local task_id="$1"

    # Set current task for error reporting
    CURRENT_TASK_ID="$task_id"

    echo "=== EXAMPLE: Git Status with MCP Fallback ==="

    # Try MCP git status with strategic bash fallback
    execute_mcp_with_fallback \
        "mcp__git__git_status" \
        "git_status" \
        "git status --porcelain" \
        "$PROJECT_ROOT"
}

# Example: Quality-validated operation
example_quality_operation() {
    local task_id="$1"

    # Set current task for error reporting
    CURRENT_TASK_ID="$task_id"

    echo "=== EXAMPLE: Quality-Validated Test Run ==="

    # Run tests with quality validation
    execute_with_quality_validation \
        "run_tests" \
        "$task_id"
}

# Example function that might be called by operation
run_tests() {
    cd "$PROJECT_ROOT"
    pixi run test
}

# =============================================================================
# AGENT INITIALIZATION
# =============================================================================

initialize_sub_agent() {
    echo "=== INITIALIZING SUB-AGENT: $AGENT_NAME ==="

    # Verify recovery system is available
    if [[ ! -f "$RECOVERY_DIR/recovery_protocols.sh" ]]; then
        echo "L Recovery system not available"
        echo "Please initialize recovery system first:"
        echo "./.recovery/recovery_protocols.sh init"
        return 1
    fi

    # Create agent-specific checkpoint
    create_operation_checkpoint "$AGENT_NAME" "agent_initialization" "startup"

    # Run health check
    echo "Running recovery system health check..."
    "$RECOVERY_DIR/recovery_protocols.sh" health

    echo " Sub-agent initialized with error recovery integration"
    echo "Agent: $AGENT_NAME"
    echo "Recovery System: $RECOVERY_DIR"

    return 0
}

# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

# If script is executed directly, run initialization
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    case "${1:-init}" in
        "init")
            initialize_sub_agent
            ;;
        "example-git")
            example_git_operation "${2:-example-task}"
            ;;
        "example-quality")
            example_quality_operation "${2:-example-task}"
            ;;
        *)
            echo "Usage: $0 {init|example-git [task_id]|example-quality [task_id]}"
            echo ""
            echo "This is a template for sub-agent error recovery integration."
            echo "Copy and customize for your specific sub-agent needs."
            exit 1
            ;;
    esac
fi
