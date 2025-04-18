# app/db/base_class.py
from typing import Any
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy import Column, DateTime, Integer
from datetime import datetime

@as_declarative()
class Base:
    """
    Base class for SQLAlchemy models.

    Includes default primary key, created_at, and updated_at columns.
    Also provides a default __tablename__ generation.
    """
    id: Any
    __name__: str

    # Generate __tablename__ automatically
    @declared_attr
    def __tablename__(cls) -> str:
        # Converts CamelCase class name to snake_case table name
        import re
        name = re.sub(r'(?<!^)(?=[A-Z])', '_', cls.__name__).lower()
        # Make it plural (simple 's' suffix, might need adjustment for complex cases)
        if not name.endswith('s'):
            name += 's'
        return name

    # Default columns for all models inheriting from Base
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

# Note: You would typically import this 'Base' in your models (e.g., User, Interview)
# instead of the one defined directly in 'app/models/base.py'.
# Ensure consistency in your project. If you keep app/models/base.py,
# you might not need this file, or you should refactor to use only one Base definition.
