"""Document model class.

Manages the role
"""
from __future__ import annotations

from sqlalchemy import Column

from .db import db


class Document(db.Model):
    """Definition of the Role entity."""

    __tablename__ = 'documents'

    id = Column(db.Integer, primary_key=True, autoincrement=True)
    name = Column(db.String(255), nullable=False)
