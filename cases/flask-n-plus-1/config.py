import os

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql+psycopg://postgres:test@localhost:5432/test"
)

SQLALCHEMY_DATABASE_URI = DATABASE_URL
SQLALCHEMY_TRACK_MODIFICATIONS = False
