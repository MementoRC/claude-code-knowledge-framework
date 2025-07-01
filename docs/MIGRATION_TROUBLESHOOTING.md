# 🚑 UCKN Migration Troubleshooting Guide

Welcome to the UCKN Migration Troubleshooting Guide!  
This document provides solutions to common issues encountered when migrating from the legacy framework to UCKN.  
For step-by-step migration instructions, see the main migration guide.  
For field and concept mapping, see the mapping guide.

---

## 🛠️ 1. Common Migration Issues & Solutions

### ❗ Issue: "ModuleNotFoundError" or Import Failures
**Symptoms:**  
- `ModuleNotFoundError: No module named 'uckn'`
- Import errors for UCKN modules

**Solution:**  
- Ensure UCKN is installed in your environment:  
  ```bash
  pip install uckn
  ```
- Verify your `PYTHONPATH` includes the UCKN source directory.
- If using a virtual environment, activate it before running migration scripts.

---

### ❗ Issue: "Unknown Field" or Schema Mismatches
**Symptoms:**  
- Validation errors about missing or extra fields
- Data not mapping as expected

**Solution:**  
- Double-check the [mapping guide](./MAPPING_GUIDE.md) for correct field names and types.
- Update your migration scripts to use the new UCKN models and field names.
- Use the `TechStackFilter` and `PaginationParams` models for filtering and pagination.

---

## ✅ 2. Validation Failures & Fixes

### ❗ Issue: "ValidationError" from Pydantic or UCKN Models
**Symptoms:**  
- Error messages like `pydantic.error_wrappers.ValidationError`
- Data rejected during migration

**Solution:**  
- Review the error message for the specific field causing the failure.
- Ensure all required fields are present and of the correct type.
- For enums or choices, use the allowed values as defined in UCKN models.
- Use the `to_metadata_filter()` method for tech stack filters to ensure correct format.

---

## 🗄️ 3. Database Connection Problems

### ❗ Issue: "Connection refused" or "Timeout" to PostgreSQL
**Symptoms:**  
- `psycopg2.OperationalError: could not connect to server`
- Timeouts or authentication failures

**Solution:**  
- Verify your PostgreSQL server is running and accessible.
- Check connection parameters in your configuration (host, port, user, password, database).
- Use the `PostgreSQLConnector`'s `get_db_session()` context manager for safe session handling.
- Ensure network/firewall rules allow connections.

---

### ❗ Issue: "No such table" or Migration Fails on Schema
**Symptoms:**  
- SQL errors about missing tables or columns

**Solution:**  
- Run all required database migrations before starting data migration.
- Check that your ORM models match the current database schema.
- Use Alembic or your migration tool to bring the schema up to date.

---

## 🚦 4. Performance Issues During Migration

### ❗ Issue: Migration is Slow or Stalls
**Symptoms:**  
- Long-running migration scripts
- High memory or CPU usage

**Solution:**  
- Use batch processing for large data sets.
- Leverage UCKN's `MultiModalEmbeddings` and caching (see `CacheManager`, `PerformanceCacheManager`) to avoid redundant computation.
- Monitor resource usage and adjust batch sizes accordingly.
- If using Redis, ensure it is available and properly configured.

---

## 🛡️ 5. Data Integrity Problems

### ❗ Issue: Data Loss or Corruption
**Symptoms:**  
- Missing records after migration
- Inconsistent or partial data

**Solution:**  
- Always back up your source and target databases before migration.
- Use transactions to ensure atomicity; rollback on failure.
- Validate migrated data using checksums or record counts.
- Use the `PaginatedResponse.create()` method to verify pagination and totals.

---

## ⚙️ 6. Configuration Errors

### ❗ Issue: "KeyError" or Missing Config Values
**Symptoms:**  
- Application fails to start due to missing config
- Environment variables not found

**Solution:**  
- Review your configuration files and environment variables.
- Ensure all required UCKN settings are present (see migration guide for required keys).
- Use sample config templates as a starting point.

---

## ⏪ 7. Rollback Procedures

### 🔄 How to Roll Back a Failed Migration

1. **Stop all migration processes immediately.**
2. **Restore the target database from the backup** taken before migration.
3. **Clear any partial or temporary data** written during the failed migration.
4. **Review migration logs** to identify the failure point.
5. **Fix the root cause** (see above sections), then retry migration.

---

## 🩹 8. Recovery Scenarios

### 🆘 Scenario: Partial Migration Completed

- **Action:**  
  - Use migration logs to identify which records were migrated.
  - Remove or mark partial records in the target system.
  - Resume migration from the last successful checkpoint.

### 🆘 Scenario: Data Corruption Detected

- **Action:**  
  - Restore from backup.
  - Run data validation scripts to identify and correct inconsistencies.
  - Re-run migration after fixing the root cause.

### 🆘 Scenario: Configuration or Environment Failure

- **Action:**  
  - Revert configuration changes.
  - Restart services and verify connectivity.
  - Use environment snapshots if available.

---

## 📝 Additional Resources

- [UCKN Migration Guide](./MIGRATION_GUIDE.md)
- [UCKN Mapping Guide](./MAPPING_GUIDE.md)
- [UCKN Documentation](https://uckn.io/docs)
- [UCKN Support](mailto:support@uckn.io)

---

> 💡 **Tip:**  
> Always test your migration in a staging environment before running in production!
