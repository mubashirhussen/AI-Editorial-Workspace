"""Complete Authentication, RBAC and User Profile Management

Revision ID: 8b3c4d5e6f7a
Revises: 7a2c3d4e5f6a
Create Date: 2026-11-09 15:50:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8b3c4d5e6f7a'
down_revision = '7a2c3d4e5f6a'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Update users table with role, profile_image, and last_login_at
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('role', sa.String(length=50), nullable=False, server_default='USER'))
        batch_op.add_column(sa.Column('profile_image', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.create_index('ix_users_role', ['role'], unique=False)

    # 2. Update user_sessions with last_activity_at
    with op.batch_alter_table('user_sessions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('last_activity_at', sa.DateTime(timezone=True), nullable=True))

    # 3. Create roles table
    op.create_table(
        'roles',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False)
    )
    with op.batch_alter_table('roles', schema=None) as batch_op:
        batch_op.create_index('ix_roles_id', ['id'], unique=False)
        batch_op.create_index('ix_roles_name', ['name'], unique=True)

    # 4. Create permissions table
    op.create_table(
        'permissions',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True)
    )
    with op.batch_alter_table('permissions', schema=None) as batch_op:
        batch_op.create_index('ix_permissions_id', ['id'], unique=False)
        batch_op.create_index('ix_permissions_name', ['name'], unique=True)

    # 5. Create role_permissions table
    op.create_table(
        'role_permissions',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('role_id', sa.String(length=36), sa.ForeignKey('roles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('permission_id', sa.String(length=36), sa.ForeignKey('permissions.id', ondelete='CASCADE'), nullable=False)
    )
    with op.batch_alter_table('role_permissions', schema=None) as batch_op:
        batch_op.create_index('ix_role_permissions_id', ['id'], unique=False)
        batch_op.create_index('ix_role_permissions_role_id', ['role_id'], unique=False)
        batch_op.create_index('ix_role_permissions_permission_id', ['permission_id'], unique=False)
        batch_op.create_index('uq_role_permission', ['role_id', 'permission_id'], unique=True)


def downgrade():
    op.drop_table('role_permissions')
    op.drop_table('permissions')
    op.drop_table('roles')

    with op.batch_alter_table('user_sessions', schema=None) as batch_op:
        batch_op.drop_column('last_activity_at')

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_index('ix_users_role')
        batch_op.drop_column('last_login_at')
        batch_op.drop_column('profile_image')
        batch_op.drop_column('role')
