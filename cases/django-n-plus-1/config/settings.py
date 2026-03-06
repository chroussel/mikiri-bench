import os
import dj_database_url

SECRET_KEY = "fixture-secret-key-not-for-production"
DEBUG = True
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "store",
]

ROOT_URLCONF = "config.urls"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://postgres:test@localhost:5432/test"
)
# Normalize SQLAlchemy-style URLs for dj-database-url compatibility
_db_url = DATABASE_URL.replace("postgresql+psycopg://", "postgresql://")
DATABASES = {"default": dj_database_url.parse(_db_url)}
