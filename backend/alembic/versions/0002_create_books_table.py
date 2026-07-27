"""create books table

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-22

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

book_status_enum = postgresql.ENUM(
    "uploaded", "parsing", "parsed", "translating", "ready", "failed",
    name="book_status",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    if not bind.dialect.has_type(bind, "book_status"):
        book_status_enum.create(bind, checkfirst=True)

    op.create_table(
        "books",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "owner_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("author", sa.String(length=255), nullable=True),
        sa.Column("original_filename", sa.String(length=500), nullable=False),
        sa.Column("file_extension", sa.String(length=10), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("storage_key", sa.String(length=1000), nullable=False),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column("source_language", sa.String(length=10), server_default="en", nullable=False),
        sa.Column(
            "status",
            book_status_enum,
            server_default="uploaded",
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
    )
    op.create_index("ix_books_owner_id", "books", ["owner_id"])


def downgrade() -> None:
    op.drop_index("ix_books_owner_id", table_name="books")
    op.drop_table("books")
    bind = op.get_bind()
    if bind.dialect.has_type(bind, "book_status"):
        book_status_enum.drop(bind, checkfirst=True)