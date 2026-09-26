from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./e-commerce_db.db"
    secret_key: str = "8f7a2d91c4e6b3f5a8d0c7e9b1f4a6d2c8e5f7a9b3d1c6e4f8a2b7d9e5c1f3a"
    algorithm: str = "HS256"

    class Config:
        env_file = ".env"

settings = Settings()