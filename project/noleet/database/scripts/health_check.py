#!/usr/bin/env python3
"""
Database health check script for NoLeet.

This script performs comprehensive database health checks
including connectivity, performance, data integrity, and more.
"""

import asyncio
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from noleet.app.core.config import settings
from noleet.app.core.logging import get_logger

logger = get_logger(__name__)


class DatabaseHealthChecker:
    """Comprehensive database health checker."""

    def __init__(self, database_url: str = None):
        self.database_url = database_url or settings.DATABASE_URL
        self.engine = None
        self.async_session = None
        self.issues = []
        self.warnings = []

    async def initialize(self) -> None:
        """Initialize database connection."""
        self.engine = create_async_engine(
            self.database_url,
            echo=False,
            pool_pre_ping=True,
            pool_recycle=300
        )
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def run_all_checks(self) -> Dict[str, Any]:
        """Run all database health checks."""
        logger.info("Starting comprehensive database health check...")

        results = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "unknown",
            "checks": {},
            "issues": [],
            "warnings": [],
            "recommendations": []
        }

        try:
            # Connection checks
            results["checks"]["connectivity"] = await self._check_connectivity()

            # Schema checks
            results["checks"]["schema_integrity"] = await self._check_schema_integrity()

            # Performance checks
            results["checks"]["performance"] = await self._check_performance()

            # Data integrity checks
            results["checks"]["data_integrity"] = await self._check_data_integrity()

            # Index checks
            results["checks"]["indexes"] = await self._check_indexes()

            # Table size checks
            results["checks"]["table_sizes"] = await self._check_table_sizes()

            # Connection pool checks
            results["checks"]["connection_pool"] = await self._check_connection_pool()

            # Replication checks (if applicable)
            results["checks"]["replication"] = await self._check_replication()

            # Overall status
            results["overall_status"] = self._calculate_overall_status(results["checks"])
            results["issues"] = self.issues
            results["warnings"] = self.warnings
            results["recommendations"] = self._generate_recommendations()

            logger.info(f"Health check completed with status: {results['overall_status']}")
            return results

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            results["overall_status"] = "error"
            results["error"] = str(e)
            return results

        finally:
            if self.engine:
                await self.engine.dispose()

    async def _check_connectivity(self) -> Dict[str, Any]:
        """Check database connectivity."""
        start_time = time.time()

        try:
            async with self.engine.begin() as conn:
                result = await conn.execute(sa.text("SELECT 1 as test"))
                row = result.fetchone()

                if row and row[0] == 1:
                    response_time = time.time() - start_time
                    return {
                        "status": "healthy",
                        "response_time_ms": round(response_time * 1000, 2),
                        "message": "Database connection successful"
                    }
                else:
                    self.issues.append("Database connectivity test failed")
                    return {
                        "status": "unhealthy",
                        "message": "Database connectivity test failed"
                    }

        except Exception as e:
            self.issues.append(f"Database connection failed: {e}")
            return {
                "status": "unhealthy",
                "message": f"Database connection failed: {e}"
            }

    async def _check_schema_integrity(self) -> Dict[str, Any]:
        """Check schema integrity."""
        issues = []

        async with self.engine.begin() as conn:
            # Check required tables exist
            required_tables = [
                "users", "categories", "projects", "questions",
                "agents", "research_papers", "user_interactions"
            ]

            for table in required_tables:
                result = await conn.execute(sa.text(
                    "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
                    f"WHERE table_name = '{table}')"
                ))
                if not result.fetchone()[0]:
                    issues.append(f"Required table '{table}' does not exist")

            # Check required enum types
            required_enums = [
                "user_role", "difficulty_level", "question_status",
                "project_status", "agent_status"
            ]

            for enum_type in required_enums:
                result = await conn.execute(sa.text(
                    "SELECT EXISTS (SELECT 1 FROM pg_type "
                    f"WHERE typname = '{enum_type}')"
                ))
                if not result.fetchone()[0]:
                    issues.append(f"Required enum type '{enum_type}' does not exist")

            # Check foreign key constraints
            result = await conn.execute(sa.text("""
                SELECT conname, conrelid::regclass, confrelid::regclass
                FROM pg_constraint
                WHERE contype = 'f'
                AND convalidated = false
            """))

            invalid_constraints = result.fetchall()
            if invalid_constraints:
                issues.append(f"Found {len(invalid_constraints)} invalid foreign key constraints")

        if issues:
            self.issues.extend(issues)
            return {
                "status": "unhealthy",
                "issues": issues
            }
        else:
            return {
                "status": "healthy",
                "message": "Schema integrity verified"
            }

    async def _check_performance(self) -> Dict[str, Any]:
        """Check database performance metrics."""
        warnings = []

        async with self.engine.begin() as conn:
            # Check slow queries (if available)
            try:
                result = await conn.execute(sa.text("""
                    SELECT query, calls, total_time, mean_time, rows
                    FROM pg_stat_statements
                    WHERE mean_time > 1000  -- queries taking more than 1 second on average
                    ORDER BY mean_time DESC
                    LIMIT 10
                """))

                slow_queries = result.fetchall()
                if slow_queries:
                    warnings.append(f"Found {len(slow_queries)} slow queries (avg > 1s)")
            except Exception:
                # pg_stat_statements might not be available
                pass

            # Check table bloat
            result = await conn.execute(sa.text("""
                SELECT schemaname, tablename,
                       n_dead_tup, n_live_tup,
                       ROUND(n_dead_tup::float / GREATEST(n_live_tup + n_dead_tup, 1) * 100, 2) as bloat_ratio
                FROM pg_stat_user_tables
                WHERE n_dead_tup > 1000
                ORDER BY n_dead_tup DESC
                LIMIT 5
            """))

            bloated_tables = result.fetchall()
            if bloated_tables:
                for table in bloated_tables:
                    if table[5] > 20:  # More than 20% bloat
                        warnings.append(f"Table {table[1]} has {table[5]}% bloat")

            # Check unused indexes
            result = await conn.execute(sa.text("""
                SELECT schemaname, tablename, indexname, idx_scan
                FROM pg_stat_user_indexes
                WHERE idx_scan = 0
                AND schemaname = 'public'
                ORDER BY pg_relation_size(indexrelid) DESC
                LIMIT 5
            """))

            unused_indexes = result.fetchall()
            if unused_indexes:
                warnings.append(f"Found {len(unused_indexes)} potentially unused indexes")

        if warnings:
            self.warnings.extend(warnings)
            return {
                "status": "warning",
                "warnings": warnings
            }
        else:
            return {
                "status": "healthy",
                "message": "Performance metrics within acceptable ranges"
            }

    async def _check_data_integrity(self) -> Dict[str, Any]:
        """Check data integrity constraints."""
        issues = []

        async with self.engine.begin() as conn:
            # Check for orphaned records
            orphan_checks = [
                {
                    "name": "projects_without_authors",
                    "query": "SELECT COUNT(*) FROM projects WHERE author_id NOT IN (SELECT id FROM users)"
                },
                {
                    "name": "questions_without_valid_status",
                    "query": "SELECT COUNT(*) FROM questions WHERE status NOT IN ('pending', 'approved', 'rejected', 'flagged')"
                },
                {
                    "name": "invalid_user_interactions",
                    "query": "SELECT COUNT(*) FROM user_interactions WHERE user_id NOT IN (SELECT id FROM users)"
                }
            ]

            for check in orphan_checks:
                result = await conn.execute(sa.text(check["query"]))
                count = result.fetchone()[0]
                if count > 0:
                    issues.append(f"{check['name']}: {count} invalid records found")

            # Check for data consistency
            consistency_checks = [
                {
                    "name": "projects_with_future_publish_dates",
                    "query": "SELECT COUNT(*) FROM projects WHERE published_at > NOW()"
                },
                {
                    "name": "users_with_future_creation_dates",
                    "query": "SELECT COUNT(*) FROM users WHERE created_at > NOW()"
                }
            ]

            for check in consistency_checks:
                result = await conn.execute(sa.text(check["query"]))
                count = result.fetchone()[0]
                if count > 0:
                    issues.append(f"{check['name']}: {count} inconsistent records found")

        if issues:
            self.issues.extend(issues)
            return {
                "status": "unhealthy",
                "issues": issues
            }
        else:
            return {
                "status": "healthy",
                "message": "Data integrity verified"
            }

    async def _check_indexes(self) -> Dict[str, Any]:
        """Check index health and usage."""
        issues = []
        warnings = []

        async with self.engine.begin() as conn:
            # Check for missing indexes on foreign keys
            result = await conn.execute(sa.text("""
                SELECT tc.table_name, kcu.column_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                  AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name
                  AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                AND NOT EXISTS (
                    SELECT 1 FROM pg_indexes pi
                    WHERE pi.tablename = tc.table_name
                    AND pi.indexdef LIKE '%' || kcu.column_name || '%'
                )
            """))

            missing_indexes = result.fetchall()
            if missing_indexes:
                issues.append(f"Missing indexes on {len(missing_indexes)} foreign key columns")

            # Check index bloat
            result = await conn.execute(sa.text("""
                SELECT schemaname, tablename, indexname,
                       ROUND(pg_relation_size(indexrelid)::numeric / 1024 / 1024, 2) as size_mb
                FROM pg_stat_user_indexes
                WHERE pg_relation_size(indexrelid) > 100 * 1024 * 1024  -- indexes > 100MB
                ORDER BY pg_relation_size(indexrelid) DESC
                LIMIT 5
            """))

            large_indexes = result.fetchall()
            if large_indexes:
                warnings.append(f"Found {len(large_indexes)} large indexes (>100MB)")

        if issues:
            self.issues.extend(issues)
        if warnings:
            self.warnings.extend(warnings)

        status = "healthy"
        if issues:
            status = "unhealthy"
        elif warnings:
            status = "warning"

        return {
            "status": status,
            "issues": issues if issues else None,
            "warnings": warnings if warnings else None
        }

    async def _check_table_sizes(self) -> Dict[str, Any]:
        """Check table sizes and growth trends."""
        async with self.engine.begin() as conn:
            result = await conn.execute(sa.text("""
                SELECT schemaname, tablename,
                       pg_total_relation_size(schemaname||'.'||tablename) as total_size,
                       pg_relation_size(schemaname||'.'||tablename) as table_size,
                       pg_total_relation_size(schemaname||'.'||tablename) -
                       pg_relation_size(schemaname||'.'||tablename) as index_size
                FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                LIMIT 10
            """))

            tables = result.fetchall()

            table_info = []
            for table in tables:
                table_info.append({
                    "table": table[1],
                    "total_size_mb": round(table[2] / 1024 / 1024, 2),
                    "table_size_mb": round(table[3] / 1024 / 1024, 2),
                    "index_size_mb": round(table[4] / 1024 / 1024, 2)
                })

            return {
                "status": "healthy",
                "tables": table_info
            }

    async def _check_connection_pool(self) -> Dict[str, Any]:
        """Check connection pool health."""
        try:
            # Get connection pool stats
            pool = self.engine.pool
            stats = {
                "pool_size": getattr(pool, 'size', 'unknown'),
                "checkedin": getattr(pool, 'checkedin', 'unknown'),
                "checkedout": getattr(pool, 'checkedout', 'unknown'),
                "invalid": getattr(pool, 'invalid', 'unknown'),
                "recycle": getattr(pool, 'recycle', 'unknown')
            }

            # Basic pool health check
            if hasattr(pool, 'checkedout') and hasattr(pool, 'size'):
                utilization = pool.checkedout / pool.size if pool.size > 0 else 0
                if utilization > 0.8:  # More than 80% utilization
                    self.warnings.append(f"Connection pool heavily utilized: {utilization:.1%}")

            return {
                "status": "healthy",
                "pool_stats": stats
            }

        except Exception as e:
            return {
                "status": "warning",
                "message": f"Could not check connection pool: {e}"
            }

    async def _check_replication(self) -> Dict[str, Any]:
        """Check replication status (if applicable)."""
        try:
            async with self.engine.begin() as conn:
                # Check if this is a replica
                result = await conn.execute(sa.text(
                    "SELECT pg_is_in_recovery()"
                ))
                is_replica = result.fetchone()[0]

                if is_replica:
                    # Get replication lag
                    result = await conn.execute(sa.text("""
                        SELECT
                            CASE
                                WHEN pg_last_wal_receive_lsn() = pg_last_wal_replay_lsn()
                                THEN 0
                                ELSE EXTRACT(EPOCH FROM now() - pg_last_xact_replay_timestamp())
                            END as lag_seconds
                    """))

                    lag_seconds = result.fetchone()[0]

                    if lag_seconds > 300:  # More than 5 minutes lag
                        self.warnings.append(f"Replication lag: {lag_seconds} seconds")

                    return {
                        "status": "healthy",
                        "is_replica": True,
                        "replication_lag_seconds": lag_seconds
                    }
                else:
                    return {
                        "status": "healthy",
                        "is_replica": False,
                        "message": "Not a replica instance"
                    }

        except Exception as e:
            return {
                "status": "warning",
                "message": f"Could not check replication status: {e}"
            }

    def _calculate_overall_status(self, checks: Dict) -> str:
        """Calculate overall health status."""
        if any(check.get("status") == "unhealthy" for check in checks.values()):
            return "unhealthy"
        elif any(check.get("status") == "warning" for check in checks.values()):
            return "warning"
        elif all(check.get("status") == "healthy" for check in checks.values()):
            return "healthy"
        else:
            return "unknown"

    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on issues and warnings."""
        recommendations = []

        if self.issues:
            recommendations.append("Address critical issues immediately:")
            for issue in self.issues[:5]:  # Top 5 issues
                recommendations.append(f"  - {issue}")

        if self.warnings:
            recommendations.append("Consider addressing these warnings:")
            for warning in self.warnings[:5]:  # Top 5 warnings
                recommendations.append(f"  - {warning}")

        # General recommendations
        recommendations.extend([
            "Schedule regular database maintenance",
            "Monitor database growth trends",
            "Review and optimize slow queries",
            "Ensure regular backups are working",
            "Consider database performance tuning"
        ])

        return recommendations


async def main():
    """Main entry point."""
    import argparse
    import json

    parser = argparse.ArgumentParser(description="NoLeet Database Health Checker")
    parser.add_argument(
        "--database-url",
        help="Database URL (overrides environment)"
    )
    parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="text",
        help="Output format (default: text)"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress non-error output"
    )

    args = parser.parse_args()

    # Setup logging
    import logging
    logging.basicConfig(level=logging.WARNING if args.quiet else logging.INFO)

    checker = DatabaseHealthChecker(database_url=args.database_url)
    await checker.initialize()

    try:
        results = await checker.run_all_checks()

        if args.format == "json":
            print(json.dumps(results, indent=2, default=str))
        else:
            # Text format
            print("🩺 NoLeet Database Health Check")
            print("=" * 40)
            print(f"Status: {results['overall_status'].upper()}")
            print(f"Timestamp: {results['timestamp']}")

            if results['issues']:
                print(f"\n❌ Issues ({len(results['issues'])}):")
                for issue in results['issues']:
                    print(f"  • {issue}")

            if results['warnings']:
                print(f"\n⚠️  Warnings ({len(results['warnings'])}):")
                for warning in results['warnings']:
                    print(f"  • {warning}")

            if results['recommendations']:
                print(f"\n💡 Recommendations:")
                for rec in results['recommendations'][:10]:  # Top 10
                    print(f"  • {rec}")

            print(f"\n📊 Check Details:")
            for check_name, check_result in results['checks'].items():
                status = check_result.get('status', 'unknown')
                emoji = {"healthy": "✅", "warning": "⚠️", "unhealthy": "❌", "unknown": "❓"}.get(status, "❓")
                print(f"  {emoji} {check_name}: {status}")

        # Exit codes: 0=healthy, 1=warning, 2=unhealthy
        status_codes = {"healthy": 0, "warning": 1, "unhealthy": 2, "error": 2, "unknown": 1}
        return status_codes.get(results["overall_status"], 1)

    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return 2


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
