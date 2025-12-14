"""Initial schema for DocuMind.

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""

    # Create repositories table
    op.create_table(
        "repositories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("url", sa.String(length=500), nullable=False),
        sa.Column("clone_url", sa.String(length=500), nullable=False),
        sa.Column("platform", sa.String(length=50), nullable=False),
        sa.Column("platform_id", sa.String(length=100), nullable=True),
        sa.Column("owner", sa.String(length=255), nullable=False),
        sa.Column("is_private", sa.Boolean(), nullable=True),
        sa.Column("is_fork", sa.Boolean(), nullable=True),
        sa.Column("default_branch", sa.String(length=100), nullable=True),
        sa.Column("language", sa.String(length=50), nullable=True),
        sa.Column("languages", sa.JSON(), nullable=True),
        sa.Column("topics", sa.JSON(), nullable=True),
        sa.Column("stars", sa.Integer(), nullable=True),
        sa.Column("forks", sa.Integer(), nullable=True),
        sa.Column("watchers", sa.Integer(), nullable=True),
        sa.Column("size_kb", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("analysis_enabled", sa.Boolean(), nullable=True),
        sa.Column("webhook_active", sa.Boolean(), nullable=True),
        sa.Column("last_analysis_at", sa.DateTime(), nullable=True),
        sa.Column("last_commit_sha", sa.String(length=40), nullable=True),
        sa.Column("analysis_config", sa.JSON(), nullable=True),
        sa.Column("ignore_patterns", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("full_name"),
        sa.Index("ix_repositories_platform", "platform"),
        sa.Index("ix_repositories_language", "language"),
        sa.Index("ix_repositories_owner", "owner"),
        sa.Index("ix_repositories_is_active", "is_active"),
    )

    # Create code_entities table
    op.create_table(
        "code_entities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("repository_id", sa.Integer(), nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("qualified_name", sa.String(length=500), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("start_line", sa.Integer(), nullable=False),
        sa.Column("end_line", sa.Integer(), nullable=True),
        sa.Column("start_column", sa.Integer(), nullable=True),
        sa.Column("end_column", sa.Integer(), nullable=True),
        sa.Column("source_code", sa.Text(), nullable=True),
        sa.Column("signature", sa.String(length=1000), nullable=True),
        sa.Column("docstring", sa.Text(), nullable=True),
        sa.Column("language", sa.String(length=50), nullable=False),
        sa.Column("complexity_score", sa.Float(), nullable=True),
        sa.Column("parameter_count", sa.Integer(), nullable=True),
        sa.Column("return_type", sa.String(length=100), nullable=True),
        sa.Column("is_async", sa.String(length=10), nullable=True),
        sa.Column("dependencies", sa.JSON(), nullable=True),
        sa.Column("dependents", sa.JSON(), nullable=True),
        sa.Column("inheritance", sa.JSON(), nullable=True),
        sa.Column("visibility", sa.String(length=20), nullable=True),
        sa.Column("decorators", sa.JSON(), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("last_analyzed_at", sa.DateTime(), nullable=True),
        sa.Column("analysis_version", sa.String(length=20), nullable=True),
        sa.Column("has_documentation", sa.String(length=10), nullable=True),
        sa.Column("documentation_quality", sa.Float(), nullable=True),
        sa.Column("needs_update", sa.String(length=10), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["repository_id"],
            ["repositories.id"],
            name="fk_code_entities_repository_id",
            ondelete="CASCADE",
        ),
        sa.Index("ix_code_entities_repository_id", "repository_id"),
        sa.Index("ix_code_entities_entity_type", "entity_type"),
        sa.Index("ix_code_entities_language", "language"),
        sa.Index("ix_code_entities_file_path", "file_path"),
    )

    # Create documentations table
    op.create_table(
        "documentations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("repository_id", sa.Integer(), nullable=False),
        sa.Column("code_entity_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("sections", sa.JSON(), nullable=True),
        sa.Column("parameters", sa.JSON(), nullable=True),
        sa.Column("returns", sa.JSON(), nullable=True),
        sa.Column("raises", sa.JSON(), nullable=True),
        sa.Column("examples", sa.JSON(), nullable=True),
        sa.Column("notes", sa.JSON(), nullable=True),
        sa.Column("doc_type", sa.String(length=50), nullable=False),
        sa.Column("format", sa.String(length=20), nullable=True),
        sa.Column("language", sa.String(length=50), nullable=True),
        sa.Column("version", sa.String(length=20), nullable=True),
        sa.Column("generated_by", sa.String(length=50), nullable=True),
        sa.Column("generation_model", sa.String(length=100), nullable=True),
        sa.Column("generation_prompt", sa.Text(), nullable=True),
        sa.Column("quality_score", sa.Float(), nullable=True),
        sa.Column("completeness_score", sa.Float(), nullable=True),
        sa.Column("accuracy_score", sa.Float(), nullable=True),
        sa.Column("readability_score", sa.Float(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=True),
        sa.Column("is_auto_generated", sa.String(length=10), nullable=True),
        sa.Column("needs_review", sa.String(length=10), nullable=True),
        sa.Column("commit_sha", sa.String(length=40), nullable=True),
        sa.Column("previous_version_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["repository_id"],
            ["repositories.id"],
            name="fk_documentations_repository_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["code_entity_id"],
            ["code_entities.id"],
            name="fk_documentations_code_entity_id",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["previous_version_id"],
            ["documentations.id"],
            name="fk_documentations_previous_version_id",
        ),
        sa.Index("ix_documentations_repository_id", "repository_id"),
        sa.Index("ix_documentations_code_entity_id", "code_entity_id"),
        sa.Index("ix_documentations_doc_type", "doc_type"),
        sa.Index("ix_documentations_status", "status"),
    )

    # Create analysis_runs table
    op.create_table(
        "analysis_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("repository_id", sa.Integer(), nullable=False),
        sa.Column("run_id", sa.String(length=50), nullable=False),
        sa.Column("trigger_type", sa.String(length=50), nullable=False),
        sa.Column("trigger_source", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("progress_percentage", sa.Float(), nullable=True),
        sa.Column("current_step", sa.String(length=100), nullable=True),
        sa.Column("analysis_config", sa.JSON(), nullable=True),
        sa.Column("target_branch", sa.String(length=100), nullable=True),
        sa.Column("commit_sha", sa.String(length=40), nullable=True),
        sa.Column("entities_found", sa.Integer(), nullable=True),
        sa.Column("entities_analyzed", sa.Integer(), nullable=True),
        sa.Column("docs_generated", sa.Integer(), nullable=True),
        sa.Column("docs_updated", sa.Integer(), nullable=True),
        sa.Column("errors_count", sa.Integer(), nullable=True),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("files_processed", sa.Integer(), nullable=True),
        sa.Column("lines_of_code", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("error_details", sa.JSON(), nullable=True),
        sa.Column("initiated_by", sa.String(length=100), nullable=True),
        sa.Column("environment", sa.String(length=50), nullable=True),
        sa.Column("version", sa.String(length=20), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["repository_id"],
            ["repositories.id"],
            name="fk_analysis_runs_repository_id",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("run_id"),
        sa.Index("ix_analysis_runs_repository_id", "repository_id"),
        sa.Index("ix_analysis_runs_status", "status"),
        sa.Index("ix_analysis_runs_trigger_type", "trigger_type"),
    )

    # Create integrations table
    op.create_table(
        "integrations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("repository_id", sa.Integer(), nullable=True),
        sa.Column("service_type", sa.String(length=50), nullable=False),
        sa.Column("service_name", sa.String(length=100), nullable=False),
        sa.Column("external_id", sa.String(length=100), nullable=True),
        sa.Column("auth_type", sa.String(length=20), nullable=False),
        sa.Column("access_token", sa.Text(), nullable=True),
        sa.Column("refresh_token", sa.Text(), nullable=True),
        sa.Column("token_expires_at", sa.DateTime(), nullable=True),
        sa.Column("config", sa.JSON(), nullable=True),
        sa.Column("webhook_url", sa.String(length=500), nullable=True),
        sa.Column("webhook_secret", sa.String(length=100), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("is_verified", sa.Boolean(), nullable=True),
        sa.Column("last_sync_at", sa.DateTime(), nullable=True),
        sa.Column("last_error_at", sa.DateTime(), nullable=True),
        sa.Column("last_error_message", sa.Text(), nullable=True),
        sa.Column("permissions", sa.JSON(), nullable=True),
        sa.Column("scope", sa.JSON(), nullable=True),
        sa.Column("owner_id", sa.String(length=100), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["repository_id"],
            ["repositories.id"],
            name="fk_integrations_repository_id",
            ondelete="CASCADE",
        ),
        sa.Index("ix_integrations_service_type", "service_type"),
        sa.Index("ix_integrations_repository_id", "repository_id"),
        sa.Index("ix_integrations_is_active", "is_active"),
    )


def downgrade() -> None:
    """Downgrade database schema."""

    # Drop tables in reverse order (due to foreign keys)
    op.drop_table("integrations")
    op.drop_table("analysis_runs")
    op.drop_table("documentations")
    op.drop_table("code_entities")
    op.drop_table("repositories")
