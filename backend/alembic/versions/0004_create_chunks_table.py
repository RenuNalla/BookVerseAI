"""create chunks table, add chunking/chunked to book_status

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-01

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None

chunk_status_enum = postgresql.ENUM(
    "ready", "translating", "translated", "failed",
    name="chunk_status",
)


def upgrade() -> None:
    # New book_status values. Postgres requires ALTER TYPE ... ADD VALUE
    # to run outside the values' first use, but it's fine within the
    # migration's own transaction as long as we don't use them here too.
    op.execute("ALTER TYPE book_status ADD VALUE IF NOT EXISTS 'chunking' AFTER 'parsed'")
    op.execute("ALTER TYPE book_status ADD VALUE IF NOT EXISTS 'chunked' AFTER 'chunking'")

    chunk_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "book_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("books.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "chapter_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("chapters.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=False),
        sa.Column("char_count", sa.Integer(), nullable=False),
        sa.Column("context_snippet", sa.Text(), nullable=True),
        sa.Column("status", chunk_status_enum, server_default="ready", nullable=False),
        sa.Column("error_message", sa.String(length=1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_chunks_book_id", "chunks", ["book_id"])
    op.create_index("ix_chunks_chapter_id", "chunks", ["chapter_id"])


def downgrade() -> None:
    op.drop_index("ix_chunks_chapter_id", table_name="chunks")
    op.drop_index("ix_chunks_book_id", table_name="chunks")
    op.drop_table("chunks")
    chunk_status_enum.drop(op.get_bind(), checkfirst=True)
    # Postgres has no ALTER TYPE ... DROP VALUE — reverting the new
    # book_status values would require rebuilding the enum type entirely,
    # which isn't worth the risk for a downgrade path. Left as-is.
