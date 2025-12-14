# NoLeet Database Operations Guide

This guide covers all database-related operations for NoLeet including initialization, migrations, backups, and health monitoring.

## Table of Contents

- [Database Schema](#database-schema)
- [Initialization](#initialization)
- [Migrations](#migrations)
- [Backup & Recovery](#backup--recovery)
- [Health Monitoring](#health-monitoring)
- [Performance Tuning](#performance-tuning)
- [Troubleshooting](#troubleshooting)

## Database Schema

### Core Tables

#### Users (`users`)
User management and authentication.

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role user_role NOT NULL DEFAULT 'user',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login_at TIMESTAMP WITH TIME ZONE,
    preferences JSONB,
    profile_data JSONB
);
```

#### Categories (`categories`)
Content categorization system.

```sql
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    parent_id INTEGER REFERENCES categories(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### Projects (`projects`)
Learning project repository.

```sql
CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    content TEXT,
    difficulty difficulty_level NOT NULL,
    status project_status NOT NULL DEFAULT 'draft',
    author_id INTEGER NOT NULL REFERENCES users(id),
    category_id INTEGER REFERENCES categories(id),
    tags TEXT[],
    metadata JSONB,
    view_count INTEGER NOT NULL DEFAULT 0,
    like_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    published_at TIMESTAMP WITH TIME ZONE
);
```

#### Questions (`questions`)
LeetCode questions and problems.

```sql
CREATE TABLE questions (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    content TEXT,
    difficulty difficulty_level NOT NULL,
    status question_status NOT NULL DEFAULT 'pending',
    source VARCHAR(50) NOT NULL, -- 'leetcode', 'manual', etc.
    external_id VARCHAR(100), -- LeetCode question ID
    url VARCHAR(500),
    tags TEXT[],
    metadata JSONB,
    sentiment_score FLOAT,
    quality_score FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    approved_at TIMESTAMP WITH TIME ZONE,
    approved_by INTEGER REFERENCES users(id)
);
```

### AI & Analytics Tables

#### Agents (`agents`)
AI agent configurations and status.

```sql
CREATE TABLE agents (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    type VARCHAR(50) NOT NULL, -- 'recommendation', 'analysis', etc.
    status agent_status NOT NULL DEFAULT 'idle',
    config JSONB,
    last_run_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### Agent Runs (`agent_runs`)
AI agent execution history and results.

```sql
CREATE TABLE agent_runs (
    id SERIAL PRIMARY KEY,
    agent_id INTEGER NOT NULL REFERENCES agents(id),
    status agent_status NOT NULL,
    input_data JSONB,
    output_data JSONB,
    error_message TEXT,
    execution_time FLOAT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### User Interactions (`user_interactions`)
User behavior tracking for analytics.

```sql
CREATE TABLE user_interactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    interaction_type VARCHAR(50) NOT NULL, -- 'view', 'like', 'complete', etc.
    target_type VARCHAR(50) NOT NULL, -- 'project', 'question', etc.
    target_id INTEGER NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Research Integration

#### Research Papers (`research_papers`)
Academic paper integration.

```sql
CREATE TABLE research_papers (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    abstract TEXT,
    authors TEXT[],
    source VARCHAR(50) NOT NULL, -- 'arxiv', 'manual', etc.
    external_id VARCHAR(100),
    url VARCHAR(500),
    published_date DATE,
    topics TEXT[],
    metadata JSONB,
    embedding FLOAT[], -- Vector embeddings for semantic search
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Junction Tables

#### Project Questions (`project_questions`)
Many-to-many relationship between projects and questions.

```sql
CREATE TABLE project_questions (
    project_id INTEGER NOT NULL REFERENCES projects(id),
    question_id INTEGER NOT NULL REFERENCES questions(id),
    order INTEGER NOT NULL,
    notes TEXT,
    PRIMARY KEY (project_id, question_id)
);
```

#### Project Research Papers (`project_research_papers`)
Links projects to relevant research papers.

```sql
CREATE TABLE project_research_papers (
    project_id INTEGER NOT NULL REFERENCES projects(id),
    paper_id INTEGER NOT NULL REFERENCES research_papers(id),
    relevance_score FLOAT,
    notes TEXT,
    PRIMARY KEY (project_id, paper_id)
);
```

### Enums

```sql
CREATE TYPE user_role AS ENUM ('admin', 'user', 'moderator');
CREATE TYPE difficulty_level AS ENUM ('easy', 'medium', 'hard');
CREATE TYPE question_status AS ENUM ('pending', 'approved', 'rejected', 'flagged');
CREATE TYPE project_status AS ENUM ('draft', 'published', 'archived');
CREATE TYPE agent_status AS ENUM ('idle', 'running', 'completed', 'failed');
```

## Initialization

### First-Time Setup

```bash
# Initialize database with schema and seed data
python database/scripts/init_db.py

# Or with custom database URL
python database/scripts/init_db.py --database-url "postgresql://user:pass@localhost/noleet"
```

### What the Initialization Does

1. **Connection Test**: Verifies database connectivity
2. **Table Creation**: Creates all required tables and indexes
3. **Migration Application**: Runs any pending migrations
4. **Data Seeding**: Adds initial data (categories, admin user, agents)
5. **Health Checks**: Validates schema integrity

### Seed Data

The initialization creates:

- **Categories**: Algorithms, Data Structures, Dynamic Programming, etc.
- **Admin User**: `admin` / `admin123!@#` (change immediately!)
- **Default Agents**: Project recommendation, question analysis, sentiment analysis

## Migrations

### Using the Migration Tool

```bash
# Check migration status
python database/scripts/migrate.py status

# Upgrade to latest version
python database/scripts/migrate.py upgrade

# Upgrade to specific revision
python database/scripts/migrate.py upgrade --revision abc123

# Downgrade to specific revision
python database/scripts/migrate.py downgrade --revision abc123

# Create new migration
python database/scripts/migrate.py create --message "Add new feature"

# Show migration history
python database/scripts/migrate.py history

# Validate migration files
python database/scripts/migrate.py validate
```

### Creating New Migrations

```bash
# Auto-generate migration from model changes
python database/scripts/migrate.py create --message "Add user preferences"

# Create empty migration for manual changes
python database/scripts/migrate.py create --message "Manual schema changes"
```

### Migration Best Practices

1. **Test Migrations**: Always test on a copy of production data
2. **Backup First**: Create backup before running migrations
3. **Incremental Changes**: Keep migrations small and focused
4. **Rollback Plan**: Ensure migrations are reversible
5. **Data Migration**: Handle data transformations carefully

## Backup & Recovery

### Backup Types

#### Full Database Backup
```bash
# Create full backup
python database/scripts/backup.py backup --type full

# Create compressed backup
python database/scripts/backup.py backup --type full --compress
```

#### Schema-Only Backup
```bash
# Backup only the schema (no data)
python database/scripts/backup.py backup --type schema
```

### Backup Features

- **Compression**: Automatic gzip compression
- **Encryption**: Optional encryption support
- **S3 Integration**: Automatic upload to cloud storage
- **Retention**: Configurable cleanup policies

### Recovery

```bash
# Restore from backup
python database/scripts/backup.py restore my_backup.sql.gz

# Restore to specific database
python database/scripts/backup.py restore my_backup.sql.gz --database-url "postgresql://user:pass@localhost/restore_db"
```

### Backup Configuration

Set these environment variables:

```bash
# Local backup directory
BACKUP_DIR=/var/backups/noleet

# S3 configuration
BACKUP_S3_BUCKET=noleet-backups
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_REGION=us-east-1

# Retention policy
BACKUP_RETENTION_DAYS=30
```

### Automated Backups

Set up cron jobs for regular backups:

```bash
# Daily full backup at 2 AM
0 2 * * * /path/to/noleet/database/scripts/backup.py backup --type full --compress

# Weekly cleanup of old backups
0 3 * * 0 /path/to/noleet/database/scripts/backup.py cleanup --retention-days 30
```

## Health Monitoring

### Running Health Checks

```bash
# Basic health check
python database/scripts/health_check.py

# JSON output for monitoring systems
python database/scripts/health_check.py --format json

# Quiet mode for automation
python database/scripts/health_check.py --quiet
```

### Health Check Areas

#### Connectivity
- Database connection response time
- Connection pool status
- Network latency

#### Schema Integrity
- Required tables exist
- Foreign key constraints valid
- Enum types present

#### Performance
- Slow query detection
- Index usage analysis
- Table bloat monitoring

#### Data Integrity
- Orphaned record detection
- Constraint violations
- Data consistency checks

### Integration with Monitoring

The health check can be integrated with:

- **Prometheus**: Export metrics for monitoring
- **Grafana**: Create dashboards from health data
- **Alertmanager**: Configure alerts based on health status
- **CI/CD**: Automated health checks in deployment pipelines

### Exit Codes

- `0`: All checks passed (healthy)
- `1`: Warnings detected
- `2`: Critical issues found (unhealthy)

## Performance Tuning

### Index Optimization

```sql
-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;

-- Find unused indexes
SELECT schemaname, tablename, indexname
FROM pg_stat_user_indexes
WHERE idx_scan = 0;

-- Index on frequently queried columns
CREATE INDEX CONCURRENTLY ix_projects_category_status
ON projects (category_id, status);

CREATE INDEX CONCURRENTLY ix_questions_difficulty_status
ON questions (difficulty, status);
```

### Query Optimization

```sql
-- Use EXPLAIN ANALYZE to profile queries
EXPLAIN ANALYZE
SELECT p.*, u.username
FROM projects p
JOIN users u ON p.author_id = u.id
WHERE p.status = 'published'
ORDER BY p.created_at DESC
LIMIT 10;

-- Optimize with proper indexes
CREATE INDEX CONCURRENTLY ix_projects_status_created
ON projects (status, created_at DESC);
```

### Connection Pool Tuning

```python
# In application configuration
DATABASE_POOL_SIZE = 20
DATABASE_MAX_OVERFLOW = 30
DATABASE_POOL_TIMEOUT = 30
DATABASE_POOL_RECYCLE = 3600
```

### Table Partitioning

For large tables, consider partitioning:

```sql
-- Partition user_interactions by month
CREATE TABLE user_interactions_y2024m01 PARTITION OF user_interactions
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

-- Create partitioned table
CREATE TABLE user_interactions (
    id SERIAL,
    user_id INTEGER NOT NULL,
    interaction_type VARCHAR(50) NOT NULL,
    target_type VARCHAR(50) NOT NULL,
    target_id INTEGER NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
) PARTITION BY RANGE (created_at);
```

## Troubleshooting

### Common Issues

#### Connection Issues
```bash
# Test basic connectivity
psql -h localhost -U noleet -d noleet -c "SELECT 1;"

# Check connection pool
python database/scripts/health_check.py --format json | jq '.checks.connection_pool'
```

#### Slow Queries
```bash
# Find slow queries
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
WHERE mean_time > 1000
ORDER BY mean_time DESC
LIMIT 10;

# Reset statistics
SELECT pg_stat_statements_reset();
```

#### Lock Conflicts
```bash
# Check active locks
SELECT pid, usename, state, query
FROM pg_stat_activity
WHERE state = 'active';

# Kill problematic session
SELECT pg_terminate_backend(pid);
```

#### Disk Space Issues
```bash
# Check table sizes
SELECT schemaname, tablename,
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

# Vacuum to reclaim space
VACUUM FULL VERBOSE table_name;
```

### Performance Monitoring

#### Key Metrics to Monitor

- **Connection Pool Utilization**: Should be < 80%
- **Slow Query Count**: Queries > 1 second
- **Index Hit Rate**: Should be > 95%
- **Cache Hit Rate**: Should be > 90%
- **Replication Lag**: Should be < 30 seconds

#### Monitoring Queries

```sql
-- Connection pool status
SELECT count(*) as total_connections,
       count(*) filter (where state = 'active') as active_connections,
       count(*) filter (where state = 'idle') as idle_connections
FROM pg_stat_activity;

-- Index usage
SELECT schemaname, tablename, indexname,
       pg_size_pretty(pg_relation_size(indexrelid)) as size,
       idx_scan as scans
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;

-- Table bloat
SELECT schemaname, tablename,
       n_dead_tup, n_live_tup,
       ROUND(n_dead_tup::float / GREATEST(n_live_tup + n_dead_tup, 1) * 100, 2) as bloat_ratio
FROM pg_stat_user_tables
WHERE n_dead_tup > 0
ORDER BY n_dead_tup DESC;
```

### Emergency Recovery

1. **Stop Application**: Prevent further data corruption
2. **Assess Damage**: Run health checks to identify issues
3. **Restore from Backup**: Use latest good backup
4. **Verify Integrity**: Run health checks on restored data
5. **Resume Operations**: Restart application with monitoring

### Getting Help

1. Check the health check output for specific issues
2. Review PostgreSQL logs: `tail -f /var/log/postgresql/postgresql-*.log`
3. Monitor system resources: CPU, memory, disk I/O
4. Check application logs for error patterns
5. Consider consulting PostgreSQL documentation or community forums

---

## Maintenance Schedule

### Daily
- [ ] Run health checks
- [ ] Monitor backup completion
- [ ] Review error logs

### Weekly
- [ ] Full database backup verification
- [ ] Index usage analysis
- [ ] Performance trend review

### Monthly
- [ ] Database maintenance (REINDEX, VACUUM FULL)
- [ ] Backup retention cleanup
- [ ] Security audit review

### Quarterly
- [ ] Major version upgrade planning
- [ ] Schema optimization review
- [ ] Disaster recovery testing
