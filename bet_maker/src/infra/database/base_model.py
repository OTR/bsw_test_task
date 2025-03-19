from typing import ClassVar

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import declared_attr, DeclarativeBase

naming_convention = {
    "ix": "ix_%(column_0_label)s",  # INDEX
    "uq": "uq_%(table_name)s_%(column_0_name)s",  # `UNIQUE` constraint
    "ck": "ck_%(table_name)s_%(constraint_name)s",  # `CHECK` constraint
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",  # FOREIGN KEY
    "pk": "pk_%(table_name)s"  # PRIMARY KEY
}

metadata = MetaData(naming_convention=naming_convention)


class Base(AsyncAttrs, DeclarativeBase):
    metadata: ClassVar[MetaData] = metadata

    @declared_attr.directive
    def __tablename__(cls) -> str:
        """
        Преобразует имя класса в имя таблицы (например, 'UserProfile' в 'user_profile')
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
