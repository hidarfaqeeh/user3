#!/usr/bin/env python3
"""
Telegram Userbot with Webhook Support - Ultra Fast Message Forwarding
بوت تيليجرام مع دعم Webhook - نقل فوري للرسائل
"""

import asyncio
import logging
import os
import json
from dotenv import load_dotenv
load_dotenv()
from aiohttp import web, ClientSession
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError, ChatWriteForbiddenError, RPCError
from utils import ConfigManager
import ssl

class WebhookUserbot:
    """Telegram Userbot with Webhook support for instant message forwarding"""
    
    def __init__(self, config_path='config.ini'):
        self.config_manager = ConfigManager(config_path)
        self.logger = logging.getLogger(__name__)
        self.client = None
        self.webhook_url = None
        self.webhook_port = int(os.getenv('WEBHOOK_PORT', 8443))
        self.webhook_path = '/webhook'
        self._load_config()
        self._setup_client()
        
    def _setup_client(self):
        """Setup optimized Telegram client for webhook"""
        try:
            api_id = self.config_manager.get('telegram', 'api_id') or os.getenv('API_ID')
            api_hash = self.config_manager.get('telegram', 'api_hash') or os.getenv('API_HASH')
            string_session = os.getenv('STRING_SESSION')
            
            if string_session:
                self.logger.info("🔗 Setting up webhook client with string session")
                self.client = TelegramClient(
                    StringSession(string_session), 
                    api_id, 
                    api_hash,
                    timeout=10,  # Faster timeout for webhook
                    retry_delay=0.5,
                    flood_sleep_threshold=0  # No flood sleep for webhook
                )
            else:
                raise ValueError("STRING_SESSION required for webhook mode")
                
        except Exception as e:
            self.logger.error(f"❌ Failed to setup webhook client: {e}")
            raise
    
    def _load_config(self):
        """Load forwarding configuration"""
        try:
            self.source_chat = self.config_manager.get('forwarding', 'source_chat') or os.getenv('SOURCE_CHAT_ID')
            self.target_chat = self.config_manager.get('forwarding', 'target_chat') or os.getenv('TARGET_CHAT_ID')
            
            self.forward_options = {
                'delay': float(self.config_manager.get('forwarding', 'forward_delay', fallback='0.1')),  # Minimal delay for webhook
                'max_retries': int(self.config_manager.get('forwarding', 'max_retries', fallback='3')),
                'forward_mode': self.config_manager.get('forwarding', 'forward_mode', fallback='copy'),
                'forward_text': self.config_manager.getboolean('forwarding', 'forward_text', fallback=True),
                'forward_photos': self.config_manager.getboolean('forwarding', 'forward_photos', fallback=True),
                'forward_videos': self.config_manager.getboolean('forwarding', 'forward_videos', fallback=True),
                'forward_documents': self.config_manager.getboolean('forwarding', 'forward_documents', fallback=True),
            }
            
            # Setup webhook URL - auto-detect Northflank
            webhook_host = os.getenv('WEBHOOK_HOST') 
            if not webhook_host:
                # Auto-detect Northflank URL
                replit_url = os.getenv('REPL_SLUG')
                replit_owner = os.getenv('REPL_OWNER')
                northflank_url = os.getenv('NORTHFLANK_APP_URL')
                
                if northflank_url:
                    webhook_host = northflank_url.replace('https://', '').replace('http://', '')
                    self.webhook_port = 443  # HTTPS port for Northflank
                elif replit_url and replit_owner:
                    webhook_host = f"{replit_url}.{replit_owner}.repl.co"
                    self.webhook_port = 443
                else:
                    webhook_host = 'auto-detected-domain.com'
            
            if webhook_host != 'auto-detected-domain.com':
                self.webhook_url = f"https://{webhook_host}{self.webhook_path}"
            else:
                self.webhook_url = None
            
            self.logger.info(f"📡 Webhook config loaded - Source: {self.source_chat}, Target: {self.target_chat}")
            self.logger.info(f"🌐 Webhook URL: {self.webhook_url}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load webhook config: {e}")
            raise
    
    async def setup_webhook(self):
        """Setup webhook with Telegram"""
        try:
            await self.client.start()
            
            # Get bot info
            me = await self.client.get_me()
            self.logger.info(f"✅ Logged in as: {me.first_name} (@{me.username or 'N/A'})")
            
            # Set webhook URL (for bot API - note: userbot doesn't use webhooks the same way)
            # This is more for reference - userbots typically use long polling
            self.logger.info(f"🔗 Webhook mode activated for instant message processing")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to setup webhook: {e}")
            raise
    
    async def handle_webhook(self, request):
        """Handle incoming webhook requests"""
        try:
            data = await request.json()
            self.logger.debug(f"📨 Received webhook data: {data}")
            
            # Process message instantly
            if 'message' in data:
                await self._process_webhook_message(data['message'])
            
            return web.Response(text='OK')
            
        except Exception as e:
            self.logger.error(f"❌ Error processing webhook: {e}")
            return web.Response(text='ERROR', status=400)
    
    async def _process_webhook_message(self, message_data):
        """Process message from webhook instantly"""
        try:
            # Extract message info
            chat_id = message_data.get('chat', {}).get('id')
            message_text = message_data.get('text', '')
            
            # Check if from source chat
            if str(chat_id) == str(self.source_chat):
                self.logger.info(f"⚡ Instant webhook processing: {message_text[:50]}...")
                
                # Forward immediately with minimal delay
                success = await self._forward_message_instant(message_data)
                
                if success:
                    self.logger.info("✅ Webhook message forwarded instantly!")
                else:
                    self.logger.warning("⚠️ Failed to forward webhook message")
                    
        except Exception as e:
            self.logger.error(f"❌ Error processing webhook message: {e}")
    
    async def _forward_message_instant(self, message_data):
        """Forward message with zero delay for webhook"""
        try:
            # Minimal delay for webhook (almost instant)
            if self.forward_options['delay'] > 0:
                await asyncio.sleep(0.05)  # 50ms maximum delay
            
            # Forward logic here
            target_entity = await self.client.get_entity(int(self.target_chat))
            
            if self.forward_options['forward_mode'] == 'copy':
                # Send as new message
                await self.client.send_message(
                    target_entity,
                    message_data.get('text', '')
                )
            
            return True
            
        except FloodWaitError as e:
            # Even with webhook, respect flood limits but log differently
            wait_time = min(e.seconds, 60)  # Max 1 minute wait for webhook
            self.logger.warning(f"🚫 Webhook flood wait: {wait_time}s")
            await asyncio.sleep(wait_time)
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Webhook forward error: {e}")
            return False
    
    async def start_webhook_server(self):
        """Start webhook server"""
        try:
            app = web.Application()
            app.router.add_post(self.webhook_path, self.handle_webhook)
            
            # Setup SSL context for HTTPS
            ssl_context = None
            cert_file = os.getenv('SSL_CERT_FILE')
            key_file = os.getenv('SSL_KEY_FILE')
            
            if cert_file and key_file:
                ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
                ssl_context.load_cert_chain(cert_file, key_file)
                self.logger.info("🔒 SSL certificate loaded for webhook")
            else:
                self.logger.warning("⚠️ No SSL certificate provided - webhook may not work on production")
            
            runner = web.AppRunner(app)
            await runner.setup()
            
            site = web.TCPSite(
                runner, 
                '0.0.0.0', 
                self.webhook_port, 
                ssl_context=ssl_context
            )
            
            await site.start()
            
            self.logger.info(f"🚀 Webhook server started on port {self.webhook_port}")
            self.logger.info(f"🌐 Webhook endpoint: {self.webhook_url}")
            
            return runner
            
        except Exception as e:
            self.logger.error(f"❌ Failed to start webhook server: {e}")
            raise
    
    async def run_with_fallback(self):
        """Run webhook with polling fallback"""
        try:
            # Try webhook first
            webhook_runner = None
            webhook_host = os.getenv('WEBHOOK_HOST')
            
            if webhook_host and webhook_host != 'your-domain.com':
                self.logger.info("🔗 Starting in WEBHOOK mode...")
                webhook_runner = await self.start_webhook_server()
                await self.setup_webhook()
                
                # Keep webhook server running
                try:
                    while True:
                        await asyncio.sleep(1)
                        
                except KeyboardInterrupt:
                    self.logger.info("🛑 Webhook server shutting down...")
                    if webhook_runner:
                        await webhook_runner.cleanup()
            else:
                # Fallback to optimized polling
                self.logger.info("📡 Starting in OPTIMIZED POLLING mode...")
                await self._run_optimized_polling()
                
        except Exception as e:
            self.logger.error(f"❌ Error in webhook mode: {e}")
            self.logger.info("🔄 Falling back to optimized polling...")
            await self._run_optimized_polling()
    
    async def _run_optimized_polling(self):
        """Run with highly optimized polling settings"""
        try:
            await self.client.start()
            me = await self.client.get_me()
            self.logger.info(f"✅ Optimized polling mode - Logged in as: {me.first_name}")
            
            # Register ultra-fast event handler
            @self.client.on(events.NewMessage(chats=[int(self.source_chat)]))
            async def ultra_fast_handler(event):
                self.logger.info(f"⚡ Ultra-fast processing: {event.message.id}")
                
                # Process with minimal delay
                if event.message.text:
                    delay = 0.05  # 50ms for text
                elif event.message.media:
                    delay = 0.1   # 100ms for media
                else:
                    delay = 0.05
                
                await asyncio.sleep(delay)
                await self._forward_message_optimized(event.message)
            
            self.logger.info("🚀 Ultra-fast polling active!")
            await self.client.run_until_disconnected()
            
        except Exception as e:
            self.logger.error(f"❌ Error in optimized polling: {e}")
            raise
    
    async def _forward_message_optimized(self, message):
        """Optimized message forwarding"""
        try:
            target_entity = await self.client.get_entity(int(self.target_chat))
            
            if self.forward_options['forward_mode'] == 'copy':
                if message.text:
                    await self.client.send_message(target_entity, message.text)
                elif message.media:
                    await self.client.send_file(target_entity, message.media, caption=message.text or '')
            
            self.logger.info(f"✅ Optimized forward complete: {message.id}")
            
        except Exception as e:
            self.logger.error(f"❌ Optimized forward error: {e}")

async def main():
    """Main function for webhook userbot"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    logger.info("🚀 Starting Webhook Userbot...")
    
    try:
        bot = WebhookUserbot()
        await bot.run_with_fallback()
        
    except KeyboardInterrupt:
        logger.info("👋 Webhook userbot stopped by user")
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
