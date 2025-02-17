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
    """
    Application settings loaded from environment variables with validation.
    
    This class follows FastAPI best practices for configuration management:
    - Type validation for all settings
    - Sensible defaults where appropriate
    - Secure handling of sensitive information
    - Computed/derived fields with validators
    - Proper typing with appropriate constraints
    """
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Bet Maker API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Service for placing and managing bets on events"
    
    # Database Settings
    DB_DRIVER: str = Field("postgresql+asyncpg", description="Database driver (e.g., postgresql+asyncpg, mysql+aiomysql, sqlite+aiosqlite)")
    DB_USER: str = Field(..., description="Database username")
    DB_PASSWORD: SecretStr = Field(..., description="Database password")
    DB_NAME: str = Field(..., description="Database name")
    DB_HOST: str = Field("localhost", description="Database host")
    DB_PORT: Optional[str] = Field(None, description="Database port")
    DATABASE_URL: Optional[str] = None
    DB_POOL_SIZE: int = Field(5, description="Database connection pool size", ge=1, le=20)
    DB_MAX_OVERFLOW: int = Field(10, description="Maximum overflow connections", ge=0, le=50)
    DB_POOL_TIMEOUT: int = Field(30, description="Pool timeout in seconds", ge=1, le=60)
    DB_POOL_RECYCLE: int = Field(1800, description="Connection recycle time in seconds", ge=1)
    DB_ECHO: bool = Field(False, description="Echo SQL queries for debugging")
    
    # External Service URLs
    LINE_PROVIDER_URL: AnyHttpUrl = Field(
        ..., 
        description="URL of the line provider service"
    )
    BET_MAKER_URL: AnyHttpUrl = Field(
        ..., 
        description="URL of the bet maker service"
    )
    
    # Background Tasks Settings
    EVENT_POLL_INTERVAL: int = Field(
        30, 
        description="Interval in seconds between polling events from line provider", 
        ge=5,  # Minimum 5 seconds to avoid excessive polling
        le=300  # Maximum 5 minutes
    )
    
    # Connection Settings
    API_REQUEST_TIMEOUT: int = Field(
        30, 
        description="Timeout in seconds for API requests",
        ge=1,
        le=60
    )
    MAX_CONNECTION_RETRIES: int = Field(
        3, 
        description="Maximum number of connection retry attempts",
        ge=1,
        le=10
    )
    
    # CORS Settings
    BACKEND_CORS_ORIGINS: list[AnyHttpUrl] = Field(
        default_factory=list,
        description="List of origins that are allowed to make cross-origin requests"
    )
    
    # Application Environment
    DEBUG: bool = Field(False, description="Debug mode flag")
    TESTING: bool = Field(False, description="Testing mode flag")
    
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
        Assemble the DATABASE_URL from components if not provided directly.
        
        This validator creates a database connection string from individual 
        components if DATABASE_URL is not explicitly set.
        Support for multiple database types:
        - PostgreSQL: postgresql+asyncpg://user:pass@host:port/dbname
        - MySQL: mysql+aiomysql://user:pass@host:port/dbname
        - SQLite: sqlite+aiosqlite:///path/to/database.db
        
        This also adds connection pooling and other parameters to the URL.
        """
        if isinstance(v, str) and v:
            return v
            
        # Extract individual connection parameters
        driver = values.get("DB_DRIVER", "postgresql+asyncpg")
        user = values.get("DB_USER")
        password = values.get("DB_PASSWORD")
        if password and isinstance(password, SecretStr):
            password = password.get_secret_value()
        host = values.get("DB_HOST", "localhost")
        port = values.get("DB_PORT")
        db = values.get("DB_NAME")
        
        # Connection pool parameters
        pool_size = values.get("DB_POOL_SIZE", 5)
        max_overflow = values.get("DB_MAX_OVERFLOW", 10)
        pool_timeout = values.get("DB_POOL_TIMEOUT", 30)
        pool_recycle = values.get("DB_POOL_RECYCLE", 1800)
        echo = values.get("DB_ECHO", False)
        
        # Handle SQLite specially (file-based database)
        if driver.startswith("sqlite"):
            url = f"{driver}:///{db}"
        else:
            # Validate that required parameters are present for non-SQLite databases
            if not all([user, password, db]):
                raise ValueError(
                    "Database connection requires DB_USER, DB_PASSWORD, and DB_NAME"
                )
                
            # Construct database connection string
            url = f"{driver}://{user}:{password}@{host}"
            if port:
                url += f":{port}"
            url += f"/{db}"
            
        # Add query parameters for connection pooling and other options
        query_params = []
        
        # Add driver-specific parameters
        if not driver.startswith("sqlite"):
            query_params.extend([
                f"pool_size={pool_size}",
                f"max_overflow={max_overflow}",
                f"pool_timeout={pool_timeout}",
                f"pool_recycle={pool_recycle}"
            ])
        
        # Add common parameters
        if echo:
            query_params.append("echo=true")
            
        # Add the query parameters to the URL if there are any
        if query_params:
            url += "?" + "&".join(query_params)
            
        return url
    
    @field_validator("BACKEND_CORS_ORIGINS")
    def assemble_cors_origins(cls, v: Union[str, list[str]]) -> Union[list[str], str]:
        """
        Parse CORS origins from string to list if needed.
        
        This validator allows CORS origins to be specified as a comma-separated string
        and converts it to a list for internal use.
        """
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError("BACKEND_CORS_ORIGINS should be a list or comma-separated string")


# Create a global settings instance
settings = Settings()


if __name__ == "__main__":
    print(settings.model_dump_json(indent=2))