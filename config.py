"""
Configuration settings for ChatBot Server
"""

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
    
    # Database
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'chatbot.db'
    
    # Rate limiting
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL') or 'memory://'
    
    # Chat settings
    MAX_MESSAGE_LENGTH = int(os.environ.get('MAX_MESSAGE_LENGTH', 2000))
    MAX_SESSIONS_PER_USER = int(os.environ.get('MAX_SESSIONS_PER_USER', 50))
    SESSION_TIMEOUT_HOURS = int(os.environ.get('SESSION_TIMEOUT_HOURS', 24))
    
    # Model settings
    MODEL = os.environ.get('GROQ_MODEL', 'llama-3.3-70b-versatile')
    DEFAULT_TEMPERATURE = float(os.environ.get('DEFAULT_TEMPERATURE', 0.7))
    MAX_TOKENS = int(os.environ.get('MAX_TOKENS', 1024))
    
    # Security
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000').split(',')
    
class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    RATELIMIT_ENABLED = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    RATELIMIT_ENABLED = True
    
class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DATABASE_URL = ':memory:'
    RATELIMIT_ENABLED = False

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}