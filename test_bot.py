#!/usr/bin/env python3
"""
Test Telegram Userbot - Simple test version for forwarding functionality
"""

import asyncio
import logging
import os
from telethon import TelegramClient, events
from telethon.sessions import StringSession

async def test_forwarding():
    """Test the forwarding functionality"""
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    try:
        # Get credentials
        api_id = os.getenv('TELEGRAM_API_ID')
        api_hash = os.getenv('TELEGRAM_API_HASH')
        string_session = os.getenv('TELEGRAM_STRING_SESSION')
        
        if not all([api_id, api_hash]):
            logger.error("Missing API credentials")
            return
        
        # Create client
        if string_session and len(string_session) > 10:
            client = TelegramClient(StringSession(string_session), int(api_id), api_hash)
            logger.info("Using string session")
        else:
            client = TelegramClient('test_session', int(api_id), api_hash)
            logger.info("Using file session")
        
        # Start client
        await client.start()
        
        # Get user info
        me = await client.get_me()
        logger.info(f"Logged in as: {me.first_name} (@{me.username or 'No username'})")
        
        # Test configuration
        source_chat = "@test_source"  # Replace with actual source
        target_chat = "@test_target"  # Replace with actual target
        
        logger.info(f"Ready to test forwarding from {source_chat} to {target_chat}")
        logger.info("Send a message to the source chat to test forwarding...")
        
        # Register test handler
        @client.on(events.NewMessage(chats=source_chat))
        async def test_handler(event):
            try:
                logger.info(f"Received message: {event.message.text[:50]}...")
                
                # Forward message
                await client.forward_messages(
                    entity=target_chat,
                    messages=event.message
                )
                
                logger.info("✅ Message forwarded successfully!")
                
            except Exception as e:
                logger.error(f"❌ Forward failed: {e}")
        
        logger.info("Test bot is running... Press Ctrl+C to stop")
        await client.run_until_disconnected()
        
    except Exception as e:
        logger.error(f"Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_forwarding())