import os

class Settings:
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "8c9b74052ca7503be46b0a9d18e22709dbbf7f6e077a2d4834211116c9056d6f")

    ALGORITHM: str = os.environ.get("ALGORITHM", "HS256")

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60*24*7
    

settings = Settings()


