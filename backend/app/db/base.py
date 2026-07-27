"""
Declarative base class every ORM model inherits from.

Kept in its own file (separate from session.py) so Alembic's env.py can
import Base and all models without also importing the engine/session,
avoiding circular imports as the model count grows in later phases.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass