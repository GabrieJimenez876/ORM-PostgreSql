"""Paquete del proyecto ORM con PostgreSQL."""

from .database import Base, create_tables

__all__ = ["Base", "create_tables"]
