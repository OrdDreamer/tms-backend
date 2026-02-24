from .base import *
from .base import env

DEBUG = False

DATABASES = {
    "default": env.db("DATABASE_URL"),
}
