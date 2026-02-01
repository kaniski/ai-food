import os

APP_ENV = os.getenv("APP_ENV", "dev").lower()
SECRET_KEY = os.getenv("APP_SECRET_KEY", "dev_only_change_me")

SESSION_COOKIE = "mnf_session"
SESSION_MAX_AGE_SECONDS = 60 * 60 * 2  # 2h (demo)

def is_prod() -> bool:
    return APP_ENV == "prod"
