"""
Utility classes and functions for the Telegram userbot
"""

import asyncio
import configparser
import logging
import time
from typing import Any, Optional

class ConfigManager:
    """Configuration manager for handling config.ini files"""
    
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = configparser.ConfigParser()
        self.logger = logging.getLogger(__name__)
        self._load_config()
    
    def _load_config(self):
        """Load configuration from file"""
        try:
            self.config.read(self.config_path)
            self.logger.info(f"Configuration loaded from {self.config_path}")
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            raise
    
    def get(self, section: str, key: str, fallback: Any = None) -> str:
        """Get configuration value"""
        try:
            return self.config.get(section, key, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError):
            if fallback is not None:
                return fallback
            raise
    
    def getint(self, section: str, key: str, fallback: Any = None) -> int:
        """Get integer configuration value"""
        try:
            return self.config.getint(section, key, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError):
            if fallback is not None:
                return fallback
            raise
    
    def getfloat(self, section: str, key: str, fallback: Any = None) -> float:
        """Get float configuration value"""
        try:
            return self.config.getfloat(section, key, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError):
            if fallback is not None:
                return fallback
            raise
    
    def getboolean(self, section: str, key: str, fallback: Any = None) -> bool:
        """Get boolean configuration value"""
        try:
            return self.config.getboolean(section, key, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError):
            if fallback is not None:
                return fallback
            raise

class RateLimiter:
    """Rate limiter to prevent hitting Telegram API limits"""
    
    def __init__(self, min_interval: float = 1.0, burst_limit: int = 20):
        self.min_interval = min_interval
        self.burst_limit = burst_limit
        self.last_request_time = 0
        self.request_count = 0
        self.window_start = time.time()
        self.logger = logging.getLogger(__name__)
    
    async def wait(self):
        """Wait if necessary to respect rate limits"""
        current_time = time.time()
        
        # Reset window if needed (1 minute window)
        if current_time - self.window_start >= 60:
            self.request_count = 0
            self.window_start = current_time
        
        # Check burst limit
        if self.request_count >= self.burst_limit:
            wait_time = 60 - (current_time - self.window_start)
            if wait_time > 0:
                self.logger.info(f"Rate limit reached, waiting {wait_time:.1f} seconds...")
                await asyncio.sleep(wait_time)
                self.request_count = 0
                self.window_start = time.time()
        
        # Check minimum interval
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_interval:
            wait_time = self.min_interval - time_since_last
            await asyncio.sleep(wait_time)
        
        self.last_request_time = time.time()
        self.request_count += 1

class MessageStats:
    """Simple statistics tracker for forwarded messages"""
    
    def __init__(self):
        self.total_processed = 0
        self.total_forwarded = 0
        self.total_failed = 0
        self.start_time = time.time()
        self.logger = logging.getLogger(__name__)
    
    def message_processed(self, forwarded: bool):
        """Record a processed message"""
        self.total_processed += 1
        if forwarded:
            self.total_forwarded += 1
        else:
            self.total_failed += 1
    
    def get_stats(self) -> dict:
        """Get current statistics"""
        runtime = time.time() - self.start_time
        return {
            'total_processed': self.total_processed,
            'total_forwarded': self.total_forwarded,
            'total_failed': self.total_failed,
            'success_rate': (self.total_forwarded / max(self.total_processed, 1)) * 100,
            'runtime_seconds': runtime,
            'messages_per_minute': (self.total_processed / max(runtime / 60, 1))
        }
    
    def log_stats(self):
        """Log current statistics"""
        stats = self.get_stats()
        self.logger.info(
            f"Stats: {stats['total_processed']} processed, "
            f"{stats['total_forwarded']} forwarded, "
            f"{stats['total_failed']} failed "
            f"({stats['success_rate']:.1f}% success rate)"
        )

def format_chat_id(chat_id: str) -> str:
    """Format chat ID for display"""
    if chat_id.startswith('@'):
        return chat_id
    elif chat_id.lstrip('-').isdigit():
        return f"ID: {chat_id}"
    else:
        return chat_id

def validate_chat_identifier(chat_id: str) -> bool:
    """Validate if chat identifier is properly formatted"""
    if not chat_id:
        return False
    
    # Username format (@username)
    if chat_id.startswith('@'):
        return len(chat_id) > 1 and chat_id[1:].replace('_', '').isalnum()
    
    # Numeric ID (can be negative for groups/channels)
    if chat_id.lstrip('-').isdigit():
        return True
    
    return False
