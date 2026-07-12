"""user_timezone_nullable

Make the users.timezone column explicitly nullable so that existing and new
users without a timezone preference are represented as NULL.  The frontend
is responsible for detecting the browser timezone and calling PUT /users/profile
to populate the value.  All business logic falls back to UTC when NULL.

Revision ID: a3f1c2d4e5b6
Revises: 7555864bc349
Create Date: 2026-07-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a3f1c2d4e5b6'
down_revision: Union[str, Sequence[str], None] = '7555864bc349'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Alter users.timezone to be nullable VARCHAR(64).

    Existing rows that currently hold 'UTC' (the Python-side default) are left
    untouched — they will continue to resolve to UTC through the application
    fallback.  No backfill is performed.
    """
    op.alter_column(
        'users',
        'timezone',
        existing_type=sa.String(),
        type_=sa.String(length=64),
        nullable=True,
        existing_nullable=False,
    )


def downgrade() -> None:
    """
    Revert users.timezone to non-nullable.

    Any NULL values are coerced to 'UTC' before removing the nullable flag so
    that the downgrade never violates the NOT NULL constraint.
    """
    op.execute("UPDATE users SET timezone = 'UTC' WHERE timezone IS NULL")
    op.alter_column(
        'users',
        'timezone',
        existing_type=sa.String(length=64),
        type_=sa.String(),
        nullable=False,
        existing_nullable=True,
    )
