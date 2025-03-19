from typing import Any, Dict, Optional, Union

from pydantic import (
    AnyHttpUrl,
    ConfigDict,
    Field,
    SecretStr,
    field_validator,
)
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Bet Maker API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Сервис для размещения ставок на события"

    # Настройки базы данных
    DB_DRIVER: str = Field("postgresql+asyncpg", description="Драйвер базы данных")
    DB_USER: str = Field(..., description="Имя пользователя базы данных")
    DB_PASSWORD: SecretStr = Field(..., description="Пароль базы данных")
    DB_NAME: str = Field(..., description="Имя базы данных")
    DB_HOST: str = Field("localhost", description="Хост базы данных")
    DB_PORT: Optional[str] = Field(None, description="Порт базы данных")
    DATABASE_URL: Optional[str] = None
    DB_POOL_SIZE: int = Field(5, description="Размер пула соединений", ge=1, le=20)
    DB_MAX_OVERFLOW: int = Field(10, description="Максимальное количество дополнительных соединений", ge=0, le=50)
    DB_POOL_TIMEOUT: int = Field(30, description="Таймаут пула в секундах", ge=1, le=60)
    DB_POOL_RECYCLE: int = Field(1800, description="Время переиспользования соединения в секундах", ge=1)
    DB_ECHO: bool = Field(False, description="Вывод SQL-запросов для отладки")

    # URL внешних сервисов
    LINE_PROVIDER_URL: AnyHttpUrl = Field(
        ...,
        description="URL сервиса поставщика событий"
    )
    BET_MAKER_URL: AnyHttpUrl = Field(
        ...,
        description="URL сервиса создания ставок"
    )

    # Настройки для фоновых задач
    EVENT_POLL_INTERVAL: int = Field(
        30,
        description="Интервал в секундах между запросами событий",
        ge=5,
        le=300
    )

    API_REQUEST_TIMEOUT: int = Field(
        30,
        description="Таймаут API-запросов в секундах",
        ge=1,
        le=60
    )
    MAX_CONNECTION_RETRIES: int = Field(
        3,
        description="Максимальное количество попыток повторного подключения",
        ge=1,
        le=10
    )

    # Настройки CORS
    BACKEND_CORS_ORIGINS: list[AnyHttpUrl] = Field(
        default_factory=list,
        description="Список разрешенных источников для CORS-запросов"
    )

    # Режимы запуска приложения
    DEBUG: bool = Field(False, description="Режим отладки")
    TESTING: bool = Field(False, description="Режим тестирования")

    model_config = ConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        env_nested_delimiter='__',
        case_sensitive=True,
        extra='ignore'
    )

    @field_validator("DATABASE_URL")
    def assemble_db_url(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        """
        Сборка URL базы данных из компонентов, если он не указан напрямую.
        
        Поддерживаемые типы баз данных:
        - PostgreSQL: postgresql+asyncpg://user:pass@host:port/dbname
        - MySQL: mysql+aiomysql://user:pass@host:port/dbname
        - SQLite: sqlite+aiosqlite:///path/to/database.db
        """
        if isinstance(v, str) and v:
            return v

        values = values.data
        driver = values.get("DB_DRIVER", "postgresql+asyncpg")
        user = values.get("DB_USER")
        password = values.get("DB_PASSWORD")
        if password and isinstance(password, SecretStr):
            password = password.get_secret_value()
        host = values.get("DB_HOST", "localhost")
        port = values.get("DB_PORT")
        db = values.get("DB_NAME")

        pool_size = values.get("DB_POOL_SIZE", 5)
        max_overflow = values.get("DB_MAX_OVERFLOW", 10)
        pool_timeout = values.get("DB_POOL_TIMEOUT", 30)
        pool_recycle = values.get("DB_POOL_RECYCLE", 1800)
        echo = values.get("DB_ECHO", False)

        # SQLite file-based
        if driver.startswith("sqlite"):
            url = f"{driver}:///{db}"
        else:
            if not all([user, password, db]):
                raise ValueError(
                    "Для подключения к базе данных требуются DB_USER, DB_PASSWORD и DB_NAME"
                )

            url = f"{driver}://{user}:{password}@{host}"
            if port:
                url += f":{port}"
            url += f"/{db}"

        query_params = []

        if not driver.startswith("sqlite"):
            query_params.extend([
                f"pool_size={pool_size}",
                f"max_overflow={max_overflow}",
                f"pool_timeout={pool_timeout}",
                f"pool_recycle={pool_recycle}"
            ])

        if echo:
            query_params.append("echo=true")

        if query_params:
            url += "?" + "&".join(query_params)

        return url

    @field_validator("BACKEND_CORS_ORIGINS")
    def assemble_cors_origins(cls, v: Union[str, list[str]]) -> Union[list[str], str]:
        """
        Преобразование CORS-источников из строки в список.
        """
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError("Параметр BACKEND_CORS_ORIGINS должен быть списком или строкой с разделителями-запятыми")


settings = Settings()
