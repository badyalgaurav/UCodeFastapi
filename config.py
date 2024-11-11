# config.py
from pydantic import BaseSettings


class Settings(BaseSettings):
    TELE_BOT_TOKEN: str
    TELE_BOT_URL: str
    MONGODB_CONN_STR: str

    # specify .env file location as Config attribute
    class Config:
        # UBUNTU:
        # env_file = "/var/RecipeAI/Staging/RecFastAPI/.env"
        env_file = ".env"


# global instance
settings = Settings()
