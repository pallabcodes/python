"""Initial schema

Revision ID: 001
Revises:
Create Date: 2024-12-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # Create enum types
    op.execute("CREATE TYPE user_role AS ENUM('admin', 'user', 'moderator')")
    op.execute("CREATE TYPE difficulty_level AS ENUM('easy', 'medium', 'hard')")
    op.execute("CREATE TYPE question_status AS ENUM('pending', 'approved', 'rejected', 'flagged')")
    op.execute("CREATE TYPE project_status AS ENUM('draft', 'published', 'archived')")
    op.execute("CREATE TYPE agent_status AS ENUM('idle', 'running', 'completed', 'failed')")

    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(50), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('role', postgresql.ENUM('admin', 'user', 'moderator', name='user_role'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_verified', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('preferences', postgresql.JSONB(), nullable=True),
        sa.Column('profile_data', postgresql.JSONB(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('email')
    )

    # Create categories table
    op.create_table('categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('slug', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['parent_id'], ['categories.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug')
    )

    # Create projects table
    op.create_table('projects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('difficulty', postgresql.ENUM('easy', 'medium', 'hard', name='difficulty_level'), nullable=False),
        sa.Column('status', postgresql.ENUM('draft', 'published', 'archived', name='project_status'), nullable=False),
        sa.Column('author_id', sa.Integer(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.String(50)), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('view_count', sa.Integer(), nullable=False, default=0),
        sa.Column('like_count', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug')
    )

    # Create questions table
    op.create_table('questions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('difficulty', postgresql.ENUM('easy', 'medium', 'hard', name='difficulty_level'), nullable=False),
        sa.Column('status', postgresql.ENUM('pending', 'approved', 'rejected', 'flagged', name='question_status'), nullable=False),
        sa.Column('source', sa.String(50), nullable=False),  # 'leetcode', 'manual', etc.
        sa.Column('external_id', sa.String(100), nullable=True),  # LeetCode question ID
        sa.Column('url', sa.String(500), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.String(50)), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('sentiment_score', sa.Float(), nullable=True),
        sa.Column('quality_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('approved_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('external_id', 'source')
    )

    # Create project_questions junction table
    op.create_table('project_questions',
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('question_id', sa.Integer(), nullable=False),
        sa.Column('order', sa.Integer(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ),
        sa.PrimaryKeyConstraint('project_id', 'question_id')
    )

    # Create user_interactions table
    op.create_table('user_interactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('interaction_type', sa.String(50), nullable=False),  # 'view', 'like', 'complete', etc.
        sa.Column('target_type', sa.String(50), nullable=False),  # 'project', 'question', etc.
        sa.Column('target_id', sa.Integer(), nullable=False),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create agents table
    op.create_table('agents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('type', sa.String(50), nullable=False),  # 'recommendation', 'analysis', etc.
        sa.Column('status', postgresql.ENUM('idle', 'running', 'completed', 'failed', name='agent_status'), nullable=False),
        sa.Column('config', postgresql.JSONB(), nullable=True),
        sa.Column('last_run_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Create agent_runs table
    op.create_table('agent_runs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('status', postgresql.ENUM('idle', 'running', 'completed', 'failed', name='agent_status'), nullable=False),
        sa.Column('input_data', postgresql.JSONB(), nullable=True),
        sa.Column('output_data', postgresql.JSONB(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('execution_time', sa.Float(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create api_keys table
    op.create_table('api_keys',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('key_hash', sa.String(255), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('permissions', postgresql.ARRAY(sa.String(50)), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key_hash')
    )

    # Create research_papers table
    op.create_table('research_papers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('abstract', sa.Text(), nullable=True),
        sa.Column('authors', postgresql.ARRAY(sa.String(255)), nullable=True),
        sa.Column('source', sa.String(50), nullable=False),  # 'arxiv', 'manual', etc.
        sa.Column('external_id', sa.String(100), nullable=True),
        sa.Column('url', sa.String(500), nullable=True),
        sa.Column('published_date', sa.Date(), nullable=True),
        sa.Column('topics', postgresql.ARRAY(sa.String(100)), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('embedding', postgresql.ARRAY(sa.Float()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('external_id', 'source')
    )

    # Create project_research_papers junction table
    op.create_table('project_research_papers',
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('paper_id', sa.Integer(), nullable=False),
        sa.Column('relevance_score', sa.Float(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['paper_id'], ['research_papers.id'], ),
        sa.PrimaryKeyConstraint('project_id', 'paper_id')
    )

    # Create indexes
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=False)
    op.create_index(op.f('ix_users_created_at'), 'users', ['created_at'], unique=False)

    op.create_index(op.f('ix_categories_slug'), 'categories', ['slug'], unique=False)
    op.create_index(op.f('ix_categories_parent_id'), 'categories', ['parent_id'], unique=False)

    op.create_index(op.f('ix_projects_slug'), 'projects', ['slug'], unique=False)
    op.create_index(op.f('ix_projects_author_id'), 'projects', ['author_id'], unique=False)
    op.create_index(op.f('ix_projects_category_id'), 'projects', ['category_id'], unique=False)
    op.create_index(op.f('ix_projects_status'), 'projects', ['status'], unique=False)
    op.create_index(op.f('ix_projects_created_at'), 'projects', ['created_at'], unique=False)
    op.create_index(op.f('ix_projects_published_at'), 'projects', ['published_at'], unique=False)

    op.create_index(op.f('ix_questions_status'), 'questions', ['status'], unique=False)
    op.create_index(op.f('ix_questions_source'), 'questions', ['source'], unique=False)
    op.create_index(op.f('ix_questions_external_id'), 'questions', ['external_id'], unique=False)
    op.create_index(op.f('ix_questions_created_at'), 'questions', ['created_at'], unique=False)
    op.create_index(op.f('ix_questions_approved_at'), 'questions', ['approved_at'], unique=False)

    op.create_index(op.f('ix_user_interactions_user_id'), 'user_interactions', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_interactions_interaction_type'), 'user_interactions', ['interaction_type'], unique=False)
    op.create_index(op.f('ix_user_interactions_created_at'), 'user_interactions', ['created_at'], unique=False)

    op.create_index(op.f('ix_agents_type'), 'agents', ['type'], unique=False)
    op.create_index(op.f('ix_agents_status'), 'agents', ['status'], unique=False)

    op.create_index(op.f('ix_agent_runs_agent_id'), 'agent_runs', ['agent_id'], unique=False)
    op.create_index(op.f('ix_agent_runs_status'), 'agent_runs', ['status'], unique=False)
    op.create_index(op.f('ix_agent_runs_started_at'), 'agent_runs', ['started_at'], unique=False)

    op.create_index(op.f('ix_api_keys_user_id'), 'api_keys', ['user_id'], unique=False)
    op.create_index(op.f('ix_api_keys_is_active'), 'api_keys', ['is_active'], unique=False)

    op.create_index(op.f('ix_research_papers_source'), 'research_papers', ['source'], unique=False)
    op.create_index(op.f('ix_research_papers_external_id'), 'research_papers', ['external_id'], unique=False)
    op.create_index(op.f('ix_research_papers_published_date'), 'research_papers', ['published_date'], unique=False)

    # Create GIN indexes for JSONB and array columns
    op.execute("CREATE INDEX ix_projects_tags_gin ON projects USING GIN (tags)")
    op.execute("CREATE INDEX ix_projects_metadata_gin ON projects USING GIN (metadata)")
    op.execute("CREATE INDEX ix_questions_tags_gin ON questions USING GIN (tags)")
    op.execute("CREATE INDEX ix_questions_metadata_gin ON questions USING GIN (metadata)")
    op.execute("CREATE INDEX ix_user_interactions_metadata_gin ON user_interactions USING GIN (metadata)")
    op.execute("CREATE INDEX ix_agents_config_gin ON agents USING GIN (config)")
    op.execute("CREATE INDEX ix_agent_runs_input_data_gin ON agent_runs USING GIN (input_data)")
    op.execute("CREATE INDEX ix_agent_runs_output_data_gin ON agent_runs USING GIN (output_data)")
    op.execute("CREATE INDEX ix_api_keys_permissions_gin ON api_keys USING GIN (permissions)")
    op.execute("CREATE INDEX ix_research_papers_topics_gin ON research_papers USING GIN (topics)")
    op.execute("CREATE INDEX ix_research_papers_metadata_gin ON research_papers USING GIN (metadata)")


def downgrade() -> None:
    """Downgrade schema."""

    # Drop GIN indexes
    op.execute("DROP INDEX IF EXISTS ix_research_papers_metadata_gin")
    op.execute("DROP INDEX IF EXISTS ix_research_papers_topics_gin")
    op.execute("DROP INDEX IF EXISTS ix_api_keys_permissions_gin")
    op.execute("DROP INDEX IF EXISTS ix_agent_runs_output_data_gin")
    op.execute("DROP INDEX IF EXISTS ix_agent_runs_input_data_gin")
    op.execute("DROP INDEX IF EXISTS ix_agents_config_gin")
    op.execute("DROP INDEX IF EXISTS ix_user_interactions_metadata_gin")
    op.execute("DROP INDEX IF EXISTS ix_questions_metadata_gin")
    op.execute("DROP INDEX IF EXISTS ix_questions_tags_gin")
    op.execute("DROP INDEX IF EXISTS ix_projects_metadata_gin")
    op.execute("DROP INDEX IF EXISTS ix_projects_tags_gin")

    # Drop indexes
    op.drop_index(op.f('ix_research_papers_published_date'), table_name='research_papers')
    op.drop_index(op.f('ix_research_papers_external_id'), table_name='research_papers')
    op.drop_index(op.f('ix_research_papers_source'), table_name='research_papers')
    op.drop_index(op.f('ix_api_keys_is_active'), table_name='api_keys')
    op.drop_index(op.f('ix_api_keys_user_id'), table_name='api_keys')
    op.drop_index(op.f('ix_agent_runs_started_at'), table_name='agent_runs')
    op.drop_index(op.f('ix_agent_runs_status'), table_name='agent_runs')
    op.drop_index(op.f('ix_agent_runs_agent_id'), table_name='agent_runs')
    op.drop_index(op.f('ix_agents_status'), table_name='agents')
    op.drop_index(op.f('ix_agents_type'), table_name='agents')
    op.drop_index(op.f('ix_user_interactions_created_at'), table_name='user_interactions')
    op.drop_index(op.f('ix_user_interactions_interaction_type'), table_name='user_interactions')
    op.drop_index(op.f('ix_user_interactions_user_id'), table_name='user_interactions')
    op.drop_index(op.f('ix_questions_approved_at'), table_name='questions')
    op.drop_index(op.f('ix_questions_created_at'), table_name='questions')
    op.drop_index(op.f('ix_questions_external_id'), table_name='questions')
    op.drop_index(op.f('ix_questions_source'), table_name='questions')
    op.drop_index(op.f('ix_questions_status'), table_name='questions')
    op.drop_index(op.f('ix_projects_published_at'), table_name='projects')
    op.drop_index(op.f('ix_projects_created_at'), table_name='projects')
    op.drop_index(op.f('ix_projects_status'), table_name='projects')
    op.drop_index(op.f('ix_projects_category_id'), table_name='projects')
    op.drop_index(op.f('ix_projects_author_id'), table_name='projects')
    op.drop_index(op.f('ix_projects_slug'), table_name='projects')
    op.drop_index(op.f('ix_categories_parent_id'), table_name='categories')
    op.drop_index(op.f('ix_categories_slug'), table_name='categories')
    op.drop_index(op.f('ix_users_created_at'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_users_username'), table_name='users')

    # Drop tables
    op.drop_table('project_research_papers')
    op.drop_table('research_papers')
    op.drop_table('api_keys')
    op.drop_table('agent_runs')
    op.drop_table('agents')
    op.drop_table('user_interactions')
    op.drop_table('project_questions')
    op.drop_table('questions')
    op.drop_table('projects')
    op.drop_table('categories')
    op.drop_table('users')

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS agent_status")
    op.execute("DROP TYPE IF EXISTS project_status")
    op.execute("DROP TYPE IF EXISTS question_status")
    op.execute("DROP TYPE IF EXISTS difficulty_level")
    op.execute("DROP TYPE IF EXISTS user_role")
