"""Initial migration - create all tables

Revision ID: 001_initial
Revises:
Create Date: 2026-03-18

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'programs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False, unique=True),
        sa.Column('platform', sa.String(50), nullable=False),
        sa.Column('url', sa.String(500), nullable=True),
        sa.Column('scope_domains', sa.JSON, default=list),
        sa.Column('scope_excluded', sa.JSON, default=list),
        sa.Column('scope_mobile_apps', sa.JSON, default=list),
        sa.Column('scope_repositories', sa.JSON, default=list),
        sa.Column('priority_areas', sa.JSON, default=list),
        sa.Column('out_of_scope', sa.JSON, default=list),
        sa.Column('severity_mapping', sa.JSON, default=dict),
        sa.Column('reward_tiers', sa.JSON, default=dict),
        sa.Column('campaigns', sa.JSON, default=list),
        sa.Column('special_requirements', sa.JSON, default=dict),
        sa.Column('raw_policy', sa.Text, nullable=True),
        sa.Column('confidence_score', sa.Integer, default=0),
        sa.Column('needs_review', sa.Boolean, default=True),
        sa.Column('reviewed_at', sa.DateTime, nullable=True),
        sa.Column('review_notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_table(
        'targets',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(500), nullable=False),
        sa.Column('target_type', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('program_id', sa.String(36), sa.ForeignKey('programs.id', ondelete='CASCADE')),
        sa.Column('technologies', sa.JSON, default=list),
        sa.Column('ports', sa.JSON, default=list),
        sa.Column('subdomains', sa.JSON, default=list),
        sa.Column('endpoints', sa.JSON, default=list),
        sa.Column('metadata', sa.JSON, default=dict),
        sa.Column('surface_coverage', sa.Integer, default=0),
        sa.Column('attack_vector_coverage', sa.Integer, default=0),
        sa.Column('logic_flow_coverage', sa.Integer, default=0),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('retry_count', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_table(
        'flow_cards',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('card_type', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('target_id', sa.String(36), sa.ForeignKey('targets.id', ondelete='CASCADE')),
        sa.Column('parent_id', sa.String(36), nullable=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('metadata', sa.JSON, default=dict),
        sa.Column('position_x', sa.Integer, default=0),
        sa.Column('position_y', sa.Integer, default=0),
        sa.Column('results', sa.JSON, default=dict),
        sa.Column('logs', sa.JSON, default=list),
        sa.Column('error', sa.Text, nullable=True),
        sa.Column('started_at', sa.DateTime, nullable=True),
        sa.Column('completed_at', sa.DateTime, nullable=True),
        sa.Column('duration_seconds', sa.Integer, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_table(
        'findings',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('severity', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('target_id', sa.String(36), sa.ForeignKey('targets.id', ondelete='CASCADE')),
        sa.Column('vuln_type', sa.String(100), nullable=False),
        sa.Column('affected_url', sa.String(1000), nullable=True),
        sa.Column('affected_parameter', sa.String(255), nullable=True),
        sa.Column('cve_id', sa.String(50), nullable=True),
        sa.Column('cwe_id', sa.String(50), nullable=True),
        sa.Column('evidence', sa.JSON, default=dict),
        sa.Column('screenshots', sa.JSON, default=list),
        sa.Column('request_response', sa.JSON, default=dict),
        sa.Column('remediation', sa.Text, nullable=True),
        sa.Column('impact', sa.Text, nullable=True),
        sa.Column('cvss_score', sa.Integer, nullable=True),
        sa.Column('public_refs', sa.JSON, default=list),
        sa.Column('internal_refs', sa.JSON, default=list),
        sa.Column('report_id', sa.String(100), nullable=True),
        sa.Column('report_url', sa.String(1000), nullable=True),
        sa.Column('reported_at', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_table(
        'approval_requests',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('action_type', sa.String(100), nullable=False),
        sa.Column('action_description', sa.Text, nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('target_id', sa.String(36), sa.ForeignKey('targets.id', ondelete='CASCADE')),
        sa.Column('risk_level', sa.String(50), nullable=False),
        sa.Column('risk_score', sa.Integer, default=50),
        sa.Column('risk_factors', sa.JSON, default=dict),
        sa.Column('proposed_command', sa.Text, nullable=True),
        sa.Column('plugin_name', sa.String(100), nullable=True),
        sa.Column('plugin_params', sa.JSON, default=dict),
        sa.Column('evidence', sa.JSON, default=dict),
        sa.Column('context', sa.Text, nullable=True),
        sa.Column('decided_by', sa.String(100), nullable=True),
        sa.Column('decided_at', sa.DateTime, nullable=True),
        sa.Column('decision_reason', sa.Text, nullable=True),
        sa.Column('modified_params', sa.JSON, nullable=True),
        sa.Column('timeout_minutes', sa.Integer, default=30),
        sa.Column('expires_at', sa.DateTime, nullable=True),
        sa.Column('notified_at', sa.DateTime, nullable=True),
        sa.Column('notification_channel', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_table(
        'plugin_runs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('plugin_name', sa.String(100), nullable=False),
        sa.Column('plugin_version', sa.String(50), nullable=True),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('target_id', sa.String(36), sa.ForeignKey('targets.id', ondelete='CASCADE')),
        sa.Column('permission_level', sa.String(50), nullable=False),
        sa.Column('params', sa.JSON, default=dict),
        sa.Column('container_id', sa.String(255), nullable=True),
        sa.Column('container_image', sa.String(500), nullable=True),
        sa.Column('queued_at', sa.DateTime, nullable=False),
        sa.Column('started_at', sa.DateTime, nullable=True),
        sa.Column('completed_at', sa.DateTime, nullable=True),
        sa.Column('duration_seconds', sa.Integer, nullable=True),
        sa.Column('stdout', sa.Text, nullable=True),
        sa.Column('stderr', sa.Text, nullable=True),
        sa.Column('exit_code', sa.Integer, nullable=True),
        sa.Column('results', sa.JSON, default=dict),
        sa.Column('memory_used_mb', sa.Integer, nullable=True),
        sa.Column('cpu_seconds', sa.Integer, nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('retry_count', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('plugin_runs')
    op.drop_table('approval_requests')
    op.drop_table('findings')
    op.drop_table('flow_cards')
    op.drop_table('targets')
    op.drop_table('programs')
