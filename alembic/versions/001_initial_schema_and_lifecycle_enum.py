"""initial_schema_and_lifecycle_enum

Revision ID: 001_initial_schema
Revises: None
Create Date: 2026-08-27 21:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ─── 1. Enum Types ────────────────────────────────────────────────────────
    threat_status_enum = sa.Enum(
        'NEW', 'ACKNOWLEDGED', 'INVESTIGATING', 'DISPATCHED', 'RESOLVED', 'FALSE_POSITIVE',
        name='threatstatusenum',
    )
    user_role_enum = sa.Enum('ADMIN', 'OPERATOR', 'ANALYST', 'VIEWER', name='userrole')
    severity_enum = sa.Enum('LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='severityenum')

    # ─── 2. Auth Tables ───────────────────────────────────────────────────────
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('email', sa.String(length=255), unique=True, nullable=False),
        sa.Column('username', sa.String(length=100), unique=True, nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('role', user_role_enum, nullable=False, server_default='VIEWER'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_users_username', 'users', ['username'])

    op.create_table(
        'refresh_tokens',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('token_hash', sa.String(length=255), unique=True, nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_refresh_tokens_user_id', 'refresh_tokens', ['user_id'])

    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'])

    # ─── 3. Domain Tables ─────────────────────────────────────────────────────
    op.create_table(
        'targets',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='ACTIVE'),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('estimated_area_ha', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('max_frp', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('confidence_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('first_detected', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_updated', sa.DateTime(timezone=True), nullable=False),
        sa.Column('threat_level', sa.String(length=50), nullable=False, server_default='LOW'),
    )
    op.create_index('ix_targets_status', 'targets', ['status'])
    op.create_index('ix_targets_threat_level', 'targets', ['threat_level'])

    op.create_table(
        'hotspots',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('frp', sa.Float(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('satellite', sa.String(length=100), nullable=False),
        sa.Column('detected_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('target_id', sa.String(length=36), sa.ForeignKey('targets.id', ondelete='SET NULL'), nullable=True),
    )
    op.create_index('ix_hotspots_frp', 'hotspots', ['frp'])
    op.create_index('ix_hotspots_confidence', 'hotspots', ['confidence'])
    op.create_index('ix_hotspots_target_id', 'hotspots', ['target_id'])

    op.create_table(
        'observations',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('target_id', sa.String(length=36), sa.ForeignKey('targets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('sensor', sa.String(length=100), nullable=False),
        sa.Column('frp', sa.Float(), nullable=False),
        sa.Column('brightness_temp_k', sa.Float(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
    )
    op.create_index('ix_observations_target_id', 'observations', ['target_id'])

    op.create_table(
        'target_history',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('target_id', sa.String(length=36), sa.ForeignKey('targets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('event', sa.String(length=100), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('details', sa.Text(), nullable=True),
    )
    op.create_index('ix_target_history_target_id', 'target_history', ['target_id'])

    op.create_table(
        'classifications',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('target_id', sa.String(length=36), sa.ForeignKey('targets.id', ondelete='CASCADE'), unique=True, nullable=False),
        sa.Column('primary_class', sa.String(length=50), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('probabilities', sa.JSON(), nullable=False),
        sa.Column('model_version', sa.String(length=50), nullable=False),
        sa.Column('evaluated_at', sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        'risk_assessments',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('target_id', sa.String(length=36), sa.ForeignKey('targets.id', ondelete='CASCADE'), unique=True, nullable=False),
        sa.Column('risk_score', sa.Float(), nullable=False),
        sa.Column('risk_category', sa.String(length=50), nullable=False),
        sa.Column('proximity_to_assets_km', sa.Float(), nullable=False),
        sa.Column('threatened_assets', sa.JSON(), nullable=False),
        sa.Column('wind_speed_kmh', sa.Float(), nullable=False),
        sa.Column('wind_direction', sa.String(length=10), nullable=False),
        sa.Column('rate_of_spread_m_min', sa.Float(), nullable=False),
    )

    op.create_table(
        'evidence',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('target_id', sa.String(length=36), sa.ForeignKey('targets.id', ondelete='CASCADE'), unique=True, nullable=False),
        sa.Column('evidence_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('items', sa.JSON(), nullable=False),
    )

    op.create_table(
        'satellite_passes',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('target_id', sa.String(length=36), sa.ForeignKey('targets.id', ondelete='CASCADE'), unique=True, nullable=False),
        sa.Column('satellite', sa.String(length=100), nullable=False),
        sa.Column('pass_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('cloud_cover_pct', sa.Float(), nullable=False),
        sa.Column('bands_available', sa.JSON(), nullable=False),
        sa.Column('image_url', sa.String(length=500), nullable=False),
        sa.Column('ground_resolution_m', sa.Float(), nullable=False),
    )

    # ─── 4. Threats Table with Lifecycle Enum ─────────────────────────────────
    op.create_table(
        'threats',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('target_id', sa.String(length=36), sa.ForeignKey('targets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('severity', severity_enum, nullable=False, server_default='MEDIUM'),
        sa.Column('status', threat_status_enum, nullable=False, server_default='NEW'),
        sa.Column('risk_score', sa.Float(), nullable=False),
        sa.Column('impact_zone', sa.String(length=255), nullable=False),
        sa.Column('reported_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('acknowledged_by', sa.String(length=100), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
    )
    op.create_index('ix_threats_status', 'threats', ['status'])
    op.create_index('ix_threats_severity', 'threats', ['severity'])
    op.create_index('ix_threats_target_id', 'threats', ['target_id'])

    # Migrate any legacy 'OPEN' rows to 'NEW' (if data existed from previous migrations)
    # op.execute("UPDATE threats SET status = 'NEW' WHERE status = 'OPEN'")

    # ─── 5. Ancillary Platform Tables ─────────────────────────────────────────
    op.create_table(
        'events',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('severity', sa.String(length=50), nullable=False, server_default='MEDIUM'),
        sa.Column('source', sa.String(length=100), nullable=False, server_default='MANUAL_REPORT'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        'industrial_assets',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('type', sa.String(length=100), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('criticality', sa.String(length=50), nullable=False),
    )

    op.create_table(
        'data_sources',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('type', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='ONLINE'),
        sa.Column('last_sync', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ping_ms', sa.Integer(), nullable=True),
        sa.Column('items_ingested_last_hour', sa.Integer(), nullable=True, server_default='0'),
    )


def downgrade() -> None:
    op.drop_table('data_sources')
    op.drop_table('industrial_assets')
    op.drop_table('events')
    op.drop_table('threats')
    op.drop_table('satellite_passes')
    op.drop_table('evidence')
    op.drop_table('risk_assessments')
    op.drop_table('classifications')
    op.drop_table('target_history')
    op.drop_table('observations')
    op.drop_table('hotspots')
    op.drop_table('targets')
    op.drop_table('audit_logs')
    op.drop_table('refresh_tokens')
    op.drop_table('users')
    op.execute('DROP TYPE IF EXISTS threatstatusenum')
    op.execute('DROP TYPE IF EXISTS userrole')
    op.execute('DROP TYPE IF EXISTS severityenum')
