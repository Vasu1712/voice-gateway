from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    url: str = Field(alias="DB_URL")
    username: str = Field(alias="DB_USERNAME")
    password: str = Field(alias="DB_PASSWORD")
    
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
