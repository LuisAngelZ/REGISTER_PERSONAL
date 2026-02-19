"""add_sueldo_and_audit_log

Revision ID: e3a1b2c4d5e6
Revises: cf33d490b06c
Create Date: 2026-02-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e3a1b2c4d5e6'
down_revision: Union[str, Sequence[str], None] = 'cf33d490b06c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Columna sueldo en personal
    op.add_column('personal', sa.Column('sueldo', sa.Numeric(10, 2), nullable=True))

    # Tabla audit_log
    op.create_table(
        'audit_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('accion', sa.String(length=50), nullable=False),
        sa.Column('entidad', sa.String(length=50), nullable=True),
        sa.Column('entidad_id', sa.Integer(), nullable=True),
        sa.Column('detalle', sa.Text(), nullable=True),
        sa.Column('usuario', sa.String(length=100), nullable=True),
        sa.Column('ip', sa.String(length=50), nullable=True),
        sa.Column('fecha', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_audit_log_id'), 'audit_log', ['id'], unique=False)
    op.create_index(op.f('ix_audit_log_fecha'), 'audit_log', ['fecha'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_audit_log_fecha'), table_name='audit_log')
    op.drop_index(op.f('ix_audit_log_id'), table_name='audit_log')
    op.drop_table('audit_log')
    op.drop_column('personal', 'sueldo')
