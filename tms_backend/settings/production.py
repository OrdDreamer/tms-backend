from .base import *  # noqa: F403
from .base import env

DEBUG = False

DATABASES = {
    "default": env.db("DATABASE_URL"),
}
