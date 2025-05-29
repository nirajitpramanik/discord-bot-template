"""
Configuration settings for the Discord bot
"""

import os
from typing import List, Optional
from dataclasses import dataclass

@dataclass
class DatabaseConfig:
    """Database configuration"""
    url: str = os.getenv('DATABASE_URL', 'sqlite:///bot.db')
    echo: bool = os.getenv('DATABASE_ECHO', 'false').lower() == 'true'
    pool_size: int = int(os.getenv('DATABASE_POOL_SIZE', '10'))
    max_overflow: int = int(os.getenv('DATABASE_MAX_OVERFLOW', '20'))

@dataclass
class RedisConfig:
    """Redis configuration"""
    url: str = os.getenv('REDIS_URL', 'redis://localhost:6379')
    password: Optional[str] = os.getenv('REDIS_PASSWORD')
    db: int = int(os.getenv('REDIS_DB', '0'))

@dataclass
class WebConfig:
    """Web interface configuration"""
    host: str = os.getenv('WEB_HOST', '0.0.0.0')
    port: int = int(os.getenv('WEB_PORT', '8000'))
    debug: bool = os.getenv('WEB_DEBUG', 'false').lower() == 'true'
    secret_key: str = os.getenv('WEB_SECRET_KEY', 'your-secret-key-here')

@dataclass
class CrawlerConfig:
    """Data crawler configuration"""
    enabled: bool = os.getenv('CRAWLER_ENABLED', 'true').lower() == 'true'
    interval: int = int(os.getenv('CRAWLER_INTERVAL', '3600'))  # seconds
    max_concurrent: int = int(os.getenv('CRAWLER_MAX_CONCURRENT', '5'))
    timeout: int = int(os.getenv('CRAWLER_TIMEOUT', '30'))

class Settings:
    """Main settings class for the bot"""
    
    def __init__(self):
        # Bot settings
        self.TOKEN = os.getenv('DISCORD_TOKEN')
        self.DEFAULT_PREFIX = os.getenv('BOT_PREFIX', '!')
        self.OWNER_IDS = self._parse_ids(os.getenv('OWNER_IDS', ''))
        self.DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
        
        # Feature flags
        self.ENABLE_WEB_INTERFACE = os.getenv('ENABLE_WEB_INTERFACE', 'true').lower() == 'true'
        self.ENABLE_CRAWLER = os.getenv('ENABLE_CRAWLER', 'true').lower() == 'true'
        self.ENABLE_LOGGING = os.getenv('ENABLE_LOGGING', 'true').lower() == 'true'
        
        # Component configurations
        self.database = DatabaseConfig()
        self.redis = RedisConfig()
        self.web = WebConfig()
        self.crawler = CrawlerConfig()
        
        # Logging configuration
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
        self.LOG_FILE = os.getenv('LOG_FILE', 'bot.log')
        self.LOG_ROTATION = os.getenv('LOG_ROTATION', 'midnight')
        self.LOG_RETENTION = int(os.getenv('LOG_RETENTION', '7'))  # days
        
        # Rate limiting
        self.GLOBAL_RATE_LIMIT = int(os.getenv('GLOBAL_RATE_LIMIT', '5'))  # commands per minute
        self.USER_RATE_LIMIT = int(os.getenv('USER_RATE_LIMIT', '10'))     # commands per minute
        
        # Cache settings
        self.CACHE_TTL = int(os.getenv('CACHE_TTL', '3600'))  # seconds
        self.CACHE_MAX_SIZE = int(os.getenv('CACHE_MAX_SIZE', '1000'))
        
        # API settings
        self.API_TIMEOUT = int(os.getenv('API_TIMEOUT', '30'))
        self.MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
        
        # Discord settings
        self.MAX_MESSAGE_LENGTH = 2000
        self.MAX_EMBED_LENGTH = 6000
        self.MAX_EMBED_FIELDS = 25
        
        # Security
        self.ALLOWED_DOMAINS = self._parse_list(os.getenv('ALLOWED_DOMAINS', ''))
        self.BLOCKED_DOMAINS = self._parse_list(os.getenv('BLOCKED_DOMAINS', ''))
        
        # Validate required settings
        self._validate_settings()
    
    def _parse_ids(self, ids_string: str) -> List[int]:
        """Parse comma-separated user IDs"""
        if not ids_string:
            return []
        
        try:
            return [int(id.strip()) for id in ids_string.split(',') if id.strip()]
        except ValueError:
            return []
    
    def _parse_list(self, list_string: str) -> List[str]:
        """Parse comma-separated string list"""
        if not list_string:
            return []
        
        return [item.strip() for item in list_string.split(',') if item.strip()]
    
    def _validate_settings(self):
        """Validate required settings"""
        if not self.TOKEN:
            raise ValueError("DISCORD_TOKEN environment variable is required")
        
        if self.ENABLE_WEB_INTERFACE and not self.web.secret_key:
            raise ValueError("WEB_SECRET_KEY is required when web interface is enabled")
    
    def is_owner(self, user_id: int) -> bool:
        """Check if user is a bot owner"""
        return user_id in self.OWNER_IDS
    
    def get_log_config(self) -> dict:
        """Get logging configuration"""
        return {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'detailed': {
                    'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
                    'datefmt': '%Y-%m-%d %H:%M:%S'
                },
                'simple': {
                    'format': '[%(levelname)s] %(name)s: %(message)s'
                }
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'level': self.LOG_LEVEL,
                    'formatter': 'simple' if self.DEBUG else 'detailed'
                },
                'file': {
                    'class': 'logging.handlers.TimedRotatingFileHandler',
                    'filename': self.LOG_FILE,
                    'when': self.LOG_ROTATION,
                    'backupCount': self.LOG_RETENTION,
                    'level': self.LOG_LEVEL,
                    'formatter': 'detailed'
                }
            },
            'root': {
                'level': self.LOG_LEVEL,
                'handlers': ['console'] + (['file'] if self.ENABLE_LOGGING else [])
            }
        }