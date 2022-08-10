from pydantic import BaseSettings


class DefaultConfig(BaseSettings):
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class TgBot(DefaultConfig):
    token: str
    admins: list[int]
    use_redis: bool
    qiwi_token: str


class Payment(DefaultConfig):
    price_month: int
    price_day: int


class DbConfig(DefaultConfig):
    password: str
    user: str
    name: str
    host: str = "127.0.0.1"

    class Config:
        env_prefix = "DB_"


class Settings(BaseSettings):
    tg: TgBot = TgBot()
    db: DbConfig = DbConfig()
    pay: Payment = Payment()
