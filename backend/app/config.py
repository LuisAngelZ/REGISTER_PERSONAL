from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    model_config = ConfigDict(env_file='.env')
    
    # ZKTeco Device
    zkteco_ip: str = "192.168.100.200"
    zkteco_port: int = 4370
    zkteco_timeout: int = 5
    zkteco_password: int = 0
    
    # Database
    database_url: str = "sqlite:///./registro_personal.db"
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True

settings = Settings()
