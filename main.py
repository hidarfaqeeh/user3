#!/usr/bin/env python3
"""
Telegram Userbot - Message Forwarder
Main entry point for the Telegram userbot application
"""

import asyncio
import logging
import os
import sys
from userbot import TelegramForwarder

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('userbot.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

async def main():
    """Main function to run the userbot"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize the forwarder
        forwarder = TelegramForwarder()
        
        # Start the userbot
        logger.info("Starting Telegram Userbot...")
        await forwarder.start()
        
        # Keep the bot running
        logger.info("Bot is running. Press Ctrl+C to stop.")
        await forwarder.run_until_disconnected()
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        logger.info("Bot shutdown complete")

if __name__ == "__main__":
    asyncio.run(main())
