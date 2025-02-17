from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Настройки приложения, читаемые из переменных окружения.

    DATABASE_URL - имя, пароль, хост, база
    LINE_PROVIDER_URL - адрес line-provider сервиса
    BET_MAKER_URL - адрес bet-maker сервиса
    EVENT_POLL_INTERVAL - интервал опроса событий в секундах из line-provider сервиса
    """
    DATABASE_URL: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    LINE_PROVIDER_URL: str
    BET_MAKER_URL: str
    EVENT_POLL_INTERVAL: int

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'


settings = Settings()
