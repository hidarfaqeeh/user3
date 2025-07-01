#!/usr/bin/env python3
"""
Multi-Task Bridge for Telegram Bot
==================================

This module provides a bridge to load and execute multiple steering tasks
from steering_tasks.json file for the existing userbot system.

Author: Assistant
Version: 1.0
"""

import json
import os
import asyncio
import logging
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
import configparser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('multitask.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class TaskConfig:
    """Task configuration for multi-task system"""
    task_id: str
    name: str
    source_chat: str
    target_chat: str
    enabled: bool = True
    forward_delay: float = 1.0
    max_retries: int = 3
    forward_mode: str = "copy"
    forward_text: bool = True
    forward_photos: bool = True
    forward_videos: bool = True
    forward_files: bool = True
    header_enabled: bool = False
    footer_enabled: bool = False
    header_text: str = ""
    footer_text: str = ""
    blacklist_enabled: bool = False
    whitelist_enabled: bool = False
    blacklist_words: str = ""
    whitelist_words: str = ""
    clean_links: bool = False

class MultiTaskManager:
    """Manages multiple concurrent steering tasks"""
    
    def __init__(self):
        self.tasks: Dict[str, TaskConfig] = {}
        self.running_tasks: Dict[str, bool] = {}
        self.task_stats: Dict[str, Dict] = {}
        self.config = configparser.ConfigParser()
        self._load_config()
        self._load_tasks()
    
    def _load_config(self):
        """Load configuration from config.ini"""
        try:
            self.config.read('config.ini')
            logger.info("Configuration loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
    
    def _load_tasks(self):
        """Load tasks from steering_tasks.json"""
        try:
            if os.path.exists('steering_tasks.json'):
                with open('steering_tasks.json', 'r', encoding='utf-8') as f:
                    tasks_data = json.load(f)
                
                for task_data in tasks_data:
                    try:
                        task = TaskConfig(**task_data)
                        self.tasks[task.task_id] = task
                        self.running_tasks[task.task_id] = False
                        self.task_stats[task.task_id] = {
                            'messages_processed': 0,
                            'messages_forwarded': 0,
                            'messages_failed': 0,
                            'last_activity': None,
                            'status': 'ready'
                        }
                        logger.info(f"Loaded task: {task.name}")
                    except Exception as e:
                        logger.error(f"Failed to load task {task_data.get('name', 'Unknown')}: {e}")
                
                logger.info(f"Successfully loaded {len(self.tasks)} tasks")
            else:
                logger.info("No steering_tasks.json file found")
                self._create_sample_file()
        except Exception as e:
            logger.error(f"Failed to load tasks: {e}")
    
    def _create_sample_file(self):
        """Create a sample steering_tasks.json file"""
        try:
            sample_tasks = []
            
            # Check if we have config settings to create a default task
            source_chat = self.config.get('forwarding', 'source_chat', fallback='')
            target_chat = self.config.get('forwarding', 'target_chat', fallback='')
            
            if source_chat and target_chat:
                import time
                sample_task = TaskConfig(
                    task_id=f"default_task_{int(time.time())}",
                    name="المهمة الافتراضية",
                    source_chat=source_chat,
                    target_chat=target_chat,
                    enabled=True
                )
                sample_tasks.append(asdict(sample_task))
                self.tasks[sample_task.task_id] = sample_task
                self.running_tasks[sample_task.task_id] = False
            
            with open('steering_tasks.json', 'w', encoding='utf-8') as f:
                json.dump(sample_tasks, f, indent=2, ensure_ascii=False)
            
            logger.info("Created sample steering_tasks.json file")
            
        except Exception as e:
            logger.error(f"Failed to create sample file: {e}")
    
    def get_enabled_tasks(self) -> List[TaskConfig]:
        """Get list of enabled tasks"""
        return [task for task in self.tasks.values() if task.enabled]
    
    def get_task_by_id(self, task_id: str) -> Optional[TaskConfig]:
        """Get task by ID"""
        return self.tasks.get(task_id)
    
    def is_task_running(self, task_id: str) -> bool:
        """Check if task is running"""
        return self.running_tasks.get(task_id, False)
    
    def set_task_running(self, task_id: str, running: bool):
        """Set task running status"""
        self.running_tasks[task_id] = running
        if task_id in self.task_stats:
            self.task_stats[task_id]['status'] = 'running' if running else 'stopped'
    
    def update_task_stats(self, task_id: str, stat_type: str, increment: int = 1):
        """Update task statistics"""
        if task_id in self.task_stats:
            self.task_stats[task_id][stat_type] += increment
            from datetime import datetime
            self.task_stats[task_id]['last_activity'] = datetime.now().isoformat()
    
    def get_task_stats(self) -> Dict[str, Dict]:
        """Get all task statistics"""
        stats = {}
        for task_id, task in self.tasks.items():
            stats[task_id] = {
                'name': task.name,
                'source_chat': task.source_chat,
                'target_chat': task.target_chat,
                'enabled': task.enabled,
                'running': self.running_tasks.get(task_id, False),
                'stats': self.task_stats.get(task_id, {})
            }
        return stats
    
    def save_tasks(self):
        """Save tasks to file"""
        try:
            tasks_data = [asdict(task) for task in self.tasks.values()]
            with open('steering_tasks.json', 'w', encoding='utf-8') as f:
                json.dump(tasks_data, f, indent=2, ensure_ascii=False)
            logger.info("Tasks saved successfully")
        except Exception as e:
            logger.error(f"Failed to save tasks: {e}")

# Global instance
task_manager = MultiTaskManager()

def get_task_manager() -> MultiTaskManager:
    """Get the global task manager instance"""
    return task_manager

def load_tasks_for_userbot():
    """Load tasks and return configuration for userbot"""
    enabled_tasks = task_manager.get_enabled_tasks()
    
    if not enabled_tasks:
        logger.info("No enabled tasks found, using legacy configuration")
        return None
    
    # Return the first enabled task for legacy compatibility
    first_task = enabled_tasks[0]
    logger.info(f"Using task '{first_task.name}' for legacy mode")
    
    return {
        'source_chat': first_task.source_chat,
        'target_chat': first_task.target_chat,
        'forward_mode': first_task.forward_mode,
        'forward_delay': first_task.forward_delay,
        'max_retries': first_task.max_retries,
        'clean_links': first_task.clean_links,
        'header_enabled': first_task.header_enabled,
        'footer_enabled': first_task.footer_enabled,
        'header_text': first_task.header_text,
        'footer_text': first_task.footer_text
    }

def update_config_with_task(task_config: dict):
    """Update config.ini with task configuration"""
    try:
        config = configparser.ConfigParser()
        config.read('config.ini')
        
        if not config.has_section('forwarding'):
            config.add_section('forwarding')
        
        for key, value in task_config.items():
            config.set('forwarding', key, str(value))
        
        with open('config.ini', 'w') as f:
            config.write(f)
        
        logger.info("Updated config.ini with task configuration")
        
    except Exception as e:
        logger.error(f"Failed to update config: {e}")

if __name__ == "__main__":
    # Test the bridge
    logger.info("Testing Multi-Task Bridge...")
    
    manager = get_task_manager()
    enabled_tasks = manager.get_enabled_tasks()
    
    print(f"\n🎯 Multi-Task Bridge Status:")
    print(f"📊 Total tasks: {len(manager.tasks)}")
    print(f"✅ Enabled tasks: {len(enabled_tasks)}")
    
    if enabled_tasks:
        print(f"\n📋 Enabled Tasks:")
        for i, task in enumerate(enabled_tasks, 1):
            print(f"  {i}. {task.name}")
            print(f"     📥 From: {task.source_chat}")
            print(f"     📤 To: {task.target_chat}")
            print(f"     ⚙️ Mode: {task.forward_mode}")
        
        # Test legacy configuration
        legacy_config = load_tasks_for_userbot()
        if legacy_config:
            print(f"\n🔧 Legacy Configuration Applied:")
            for key, value in legacy_config.items():
                print(f"  {key}: {value}")
    else:
        print("\n⚠️ No enabled tasks found")
    
    print(f"\n✅ Multi-Task Bridge test completed")