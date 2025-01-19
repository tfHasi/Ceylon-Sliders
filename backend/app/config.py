import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev_secret_key")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///surf_app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
