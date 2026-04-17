"""make password reset token timestamps timezone aware

Revision ID: c9a2f7d41b10
Revises: b3f4e1c8a901
Create Date: 2026-04-16 22:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "c9a2f7d41b10"
down_revision: Union[str, None] = "b3f4e1c8a901"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "password_reset_tokens",
        "expires_at",
        existing_type=postgresql.TIMESTAMP(timezone=False),
        type_=postgresql.TIMESTAMP(timezone=True),
        existing_nullable=False,
        postgresql_using="expires_at AT TIME ZONE 'UTC'",
    )
    op.alter_column(
        "password_reset_tokens",
        "used_at",
        existing_type=postgresql.TIMESTAMP(timezone=False),
        type_=postgresql.TIMESTAMP(timezone=True),
        existing_nullable=True,
        postgresql_using="used_at AT TIME ZONE 'UTC'",
    )
    op.alter_column(
        "password_reset_tokens",
        "created_at",
        existing_type=postgresql.TIMESTAMP(timezone=False),
        type_=postgresql.TIMESTAMP(timezone=True),
        existing_nullable=False,
        postgresql_using="created_at AT TIME ZONE 'UTC'",
    )


def downgrade() -> None:
    op.alter_column(
        "password_reset_tokens",
        "created_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        type_=postgresql.TIMESTAMP(timezone=False),
        existing_nullable=False,
        postgresql_using="created_at AT TIME ZONE 'UTC'",
    )
    op.alter_column(
        "password_reset_tokens",
        "used_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        type_=postgresql.TIMESTAMP(timezone=False),
        existing_nullable=True,
        postgresql_using="used_at AT TIME ZONE 'UTC'",
    )
    op.alter_column(
        "password_reset_tokens",
        "expires_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        type_=postgresql.TIMESTAMP(timezone=False),
        existing_nullable=False,
        postgresql_using="expires_at AT TIME ZONE 'UTC'",
    )