import os


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    REDIS_HOST = os.environ.get('REDIS_HOST') or 'localhost'
    REDIS_PORT = int(os.environ.get('REDIS_PORT') or 6379)
    REDIS_DB = int(os.environ.get('REDIS_DB') or 0)
    REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD') or None

    ROOM_KEY_PREFIX = 'quiz:room:'
    BUZZ_KEY_PREFIX = 'quiz:buzz:'
    SCORE_KEY_PREFIX = 'quiz:score:'
    PLAYER_KEY_PREFIX = 'quiz:player:'
    QUESTION_KEY_PREFIX = 'quiz:question:'
    LOCK_KEY_PREFIX = 'quiz:lock:'

    BUZZ_TIMEOUT = 10
