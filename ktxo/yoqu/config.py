import pydantic
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str
    rpa_config_file:str
    rpa_default_name: str
    db_url:str
    api_address:str
    api_port:int
    api_template_folder:str
    model_config = SettingsConfigDict()


settings = Settings(_env_file=(".env","dev.env"))
