"""Add user_id column to chatbot_documents table

Revision ID: 002_add_user_id
Revises: 001_initial_schema
Create Date: 2026-07-24 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '002_add_user_id'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'chatbot_documents',
        sa.Column('user_id', sa.UUID(), nullable=True)
    )
    op.create_foreign_key(
        'fk_chatbot_documents_user_id_users',
        'chatbot_documents',
        'users',
        ['user_id'],
        ['id'],
        ondelete='CASCADE'
    )
    op.create_index(
        op.f('ix_chatbot_documents_user_id'),
        'chatbot_documents',
        ['user_id'],
        unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_chatbot_documents_user_id'), table_name='chatbot_documents')
    op.drop_constraint('fk_chatbot_documents_user_id_users', 'chatbot_documents', type_='foreignkey')
    op.drop_column('chatbot_documents', 'user_id')
