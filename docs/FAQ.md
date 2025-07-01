# ❓ UCKN Frequently Asked Questions (FAQ)

Welcome to the UCKN FAQ!  
This document answers the most common questions about installing, migrating, using, and troubleshooting the Unified Claude Knowledge Network (UCKN) framework.

---

## 🏗️ Installation & Setup

### **Q: How do I install UCKN in my project?**
- **A:** See the [Installation Guide](./installation.md) for step-by-step instructions. You can use symlink, direct integration, or git submodule methods. Make sure you have Python 3.8+ and the required dependencies.

### **Q: What are the prerequisites for UCKN?**
- **A:** You need:
  - Python 3.8 or higher
  - Claude Code environment with MCP tools enabled
  - TaskMaster AI (for advanced features)
  - A Git repository with CI/CD setup

### **Q: How do I configure knowledge storage paths?**
- **A:** Edit your deployment YAML (e.g., `.claude/framework/deployments/your-project/deployment.yaml`) and set `knowledge_storage_path` to your desired directory.

---

## 🔄 Migration from Legacy Framework

### **Q: How do I migrate from the legacy knowledge framework to UCKN?**
- **A:** Follow the migration guide and mapping guide. Update your scripts to use UCKN models and field names. See [MIGRATION_TROUBLESHOOTING.md](./MIGRATION_TROUBLESHOOTING.md) for common issues.

### **Q: I get `ModuleNotFoundError: No module named 'uckn'` after migration.**
- **A:** Ensure UCKN is installed (`pip install uckn`) and your `PYTHONPATH` includes the UCKN source directory. Activate your virtual environment if needed.

### **Q: My data fails validation after migration.**
- **A:** Check that all required fields are present and use the correct types. Refer to the mapping guide and use UCKN's Pydantic models for validation.

---

## 🚦 Common Usage Problems

### **Q: How do I capture knowledge from a CI session?**
- **A:** Use the `ClaudeCodeKnowledgeManager.capture_session_knowledge()` method. See the [API Reference](./api-reference.md) for parameters and examples.

### **Q: How do I search for past solutions?**
- **A:** Use `ClaudeCodeKnowledgeManager.search_knowledge(query, context, max_results)`. You can filter by repository, branch, and more.

### **Q: Why is my search returning no results?**
- **A:** Try using broader or alternative keywords. Make sure your knowledge base is initialized and contains session data.

### **Q: How do I get a summary of recent sessions?**
- **A:** Call `get_session_context_summary(days_back=7)` on your knowledge manager instance.

---

## 🚀 Performance & Scaling

### **Q: How does UCKN handle large knowledge bases?**
- **A:** UCKN uses file-based storage and indexing. For large installations, use the `PerformanceCacheManager` and consider Redis for caching.

### **Q: How can I speed up search?**
- **A:** Limit `max_results`, use specific queries, and enable caching. Regularly clean up old sessions and optimize indexes.

### **Q: What are the storage requirements?**
- **A:** Each session record is ~1-5KB. Index and embedding files grow with usage. For 1000+ sessions, ensure sufficient disk space.

---

## 🤖 Integration with Claude Code & MCP

### **Q: How do I integrate UCKN with Claude Code commands?**
- **A:** Copy the provided command templates to your `.claude/commands/` directory. See the [Installation Guide](./installation.md) for details.

### **Q: How does UCKN work with TaskMaster AI?**
- **A:** UCKN can capture and retrieve knowledge from TaskMaster sessions. Use the integration patterns in the [API Reference](./api-reference.md).

### **Q: Can I use UCKN in CI/CD pipelines?**
- **A:** Yes! Add initialization and search steps to your CI workflow (see the installation guide for YAML examples).

---

## 🗄️ Database & Storage

### **Q: What databases does UCKN support?**
- **A:** UCKN uses file-based storage by default. For advanced use, it supports PostgreSQL (via `PostgreSQLConnector`) and ChromaDB for metadata and embeddings.

### **Q: How do I connect UCKN to PostgreSQL?**
- **A:** Configure your connection parameters in your deployment config. Use the `PostgreSQLConnector` class and its `get_db_session()` context manager.

### **Q: How do I back up my knowledge base?**
- **A:** Regularly copy the `.claude/knowledge/` directory and any connected databases. Use version control for templates and patterns.

---

## 🛠️ Troubleshooting & Error Handling

### **Q: I get a "ValidationError" from Pydantic or UCKN models.**
- **A:** Check the error message for the problematic field. Ensure all required fields are present and correctly typed.

### **Q: I see "Connection refused" or "Timeout" errors with PostgreSQL.**
- **A:** Verify your database server is running, credentials are correct, and network/firewall rules allow connections.

### **Q: My migration failed and data is missing.**
- **A:** Stop all processes, restore from backup, and review migration logs. See the rollback procedures in [MIGRATION_TROUBLESHOOTING.md](./MIGRATION_TROUBLESHOOTING.md).

### **Q: How do I recover from a failed migration or data corruption?**
- **A:** Restore from backup, validate data integrity, and re-run migration after fixing the root cause.

### **Q: How do I get more help?**
- **A:** Check the documentation, review the troubleshooting guide, or contact UCKN support at [support@uckn.io](mailto:support@uckn.io).

---

> 💡 **Tip:** For more detailed guides, see the [API Reference](./api-reference.md), [Installation Guide](./installation.md), and [Migration Troubleshooting](./MIGRATION_TROUBLESHOOTING.md).
