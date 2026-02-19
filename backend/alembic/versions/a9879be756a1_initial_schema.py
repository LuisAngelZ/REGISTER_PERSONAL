"""initial_schema

Revision ID: a9879be756a1
Revises:
Create Date: 2026-02-15 23:08:24.305096

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a9879be756a1'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - idempotente: usa IF EXISTS para no fallar en BD fresca."""
    op.execute("ALTER TABLE personal DROP COLUMN IF EXISTS fecha_ingreso")
    op.execute("ALTER TABLE personal DROP COLUMN IF EXISTS departamento")
    op.execute("ALTER TABLE personal DROP COLUMN IF EXISTS dias_trabajo")
    op.execute("ALTER TABLE personal DROP COLUMN IF EXISTS email")


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column('personal', sa.Column('email', sa.VARCHAR(length=255), nullable=True))
    op.add_column('personal', sa.Column('dias_trabajo', sa.VARCHAR(length=50),
                  server_default=sa.text("'Lunes,Martes,Miercoles,Jueves,Viernes'"), nullable=True))
    op.add_column('personal', sa.Column('departamento', sa.VARCHAR(length=100), nullable=True))
    op.add_column('personal', sa.Column('fecha_ingreso', sa.DateTime(), nullable=True))
