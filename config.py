"""
Configuration settings for different environments.
Load settings from environment variables with sane defaults.
"""
import os
from typing import Dict, Any

class BaseConfig:
    """Base configuration class with common settings."""
    # Flask settings
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', None)
    if not SECRET_KEY:
        raise ValueError("No FLASK_SECRET_KEY set in environment")
    
    # Application settings
    DEBUG = False
    TESTING = False
    
    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_EXTENSIONS = ['.csv']
    
    # Session settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour
    
    @staticmethod
    def to_dict() -> Dict[str, Any]:
        """Convert config to dictionary, excluding private attributes."""
        return {
            key: getattr(BaseConfig, key) 
            for key in dir(BaseConfig) 
            if not key.startswith('_') and not callable(getattr(BaseConfig, key))
        }

class DevelopmentConfig(BaseConfig):
    """Development configuration."""
    DEBUG = True
    SESSION_COOKIE_SECURE = False  # Allow HTTP in development

class TestingConfig(BaseConfig):
    """Testing configuration."""
    TESTING = True
    DEBUG = True
    SESSION_COOKIE_SECURE = False
    WTF_CSRF_ENABLED = False  # Disable CSRF during testing

class ProductionConfig(BaseConfig):
    """Production configuration."""
    # Production-specific settings here
    pass

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Get the current configuration based on environment."""
    env = os.environ.get('FLASK_ENV', 'default')
    return config.get(env, config['default'])
