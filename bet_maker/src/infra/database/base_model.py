from sqlalchemy.orm import declared_attr, DeclarativeBase, MappedAsDataclass
from sqlalchemy.ext.asyncio import AsyncAttrs
from typing import ClassVar
from sqlalchemy import MetaData

naming_convention = {
    "ix": "ix_%(column_0_label)s",  # Index
    "uq": "uq_%(table_name)s_%(column_0_name)s",  # Unique constraint
    "ck": "ck_%(table_name)s_%(constraint_name)s",  # Check constraint
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",  # Foreign key
    "pk": "pk_%(table_name)s"  # Primary key
}

metadata = MetaData(naming_convention=naming_convention)

class Base(AsyncAttrs, DeclarativeBase):
    metadata: ClassVar[MetaData] = metadata
    
    @declared_attr.directive
    def __tablename__(cls) -> str:
        """
        UserProfile' becomes 'user_profile'.
        """
        name = cls.__name__
        result = [name[0].lower()]
        for char in name[1:]:
            if char.isupper():
                result.append("_")
                result.append(char.lower())
            else:
                result.append(char)
        return "".join(result).replace("_model", "")
