"""Document model class.

Manages the role
"""
from __future__ import annotations

from sqlalchemy import Column

from .base_model import BaseModel
from .db import db


class Document(BaseModel):
    """Definition of the Role entity."""

    __tablename__ = 'documents'

    id = Column(db.Integer, primary_key=True, autoincrement=True)
    name = Column(db.String(255), nullable=False)
    unique_name = Column(db.String(255), nullable=False)
    path = Column(db.String(255), nullable=False)

    # add index and unique constraint for file path
    db.Index('ix_documents_path', 'path', unique=True)

    @classmethod
    def get_by_path(cls, path: str) -> Document:
        """Return the document by path."""
        return cls.query.filter_by(path=path).first()
