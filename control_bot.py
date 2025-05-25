#!/usr/bin/env python3
"""
Telegram Control Bot - Remote control for the userbot
Allows managing the userbot through Telegram commands
"""

import asyncio
import configparser
import logging
import os
import signal
import subprocess
import sys
from telethon import TelegramClient, events, Button
from telethon.tl.types import User

class TelegramControlBot:
    """Control bot for managing the userbot remotely"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.client = None
        self.bot_token = None
        self.admin_user_id = None
        self.userbot_process = None
        self.setup_client()
        
    def setup_client(self):
        """Setup the control bot client"""
        try:
            # Get credentials
            api_id = os.getenv('TELEGRAM_API_ID')
            api_hash = os.getenv('TELEGRAM_API_HASH')
            self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
            self.admin_user_id = os.getenv('TELEGRAM_ADMIN_USER_ID')
            
            if not all([api_id, api_hash, self.bot_token]):
                raise ValueError("Please set TELEGRAM_API_ID, TELEGRAM_API_HASH, and TELEGRAM_BOT_TOKEN")
            
            # Create bot client
            self.client = TelegramClient('control_bot_session', int(api_id), api_hash)
            
        except Exception as e:
            self.logger.error(f"Failed to setup control bot: {e}")
            raise
    
    async def start(self):
        """Start the control bot"""
        try:
            await self.client.start(bot_token=self.bot_token)
            me = await self.client.get_me()
            self.logger.info(f"Control bot started: @{me.username}")
            
            # Register command handlers
            self.register_handlers()
            
        except Exception as e:
            self.logger.error(f"Failed to start control bot: {e}")
            raise
    
    def register_handlers(self):
        """Register command handlers"""
        
        @self.client.on(events.NewMessage(pattern='/start'))
        async def start_command(event):
            if not await self.is_admin(event.sender_id):
                await event.respond("❌ غير مصرح لك باستخدام هذا البوت")
                return
                
            await event.respond(
                "🤖 **بوت التحكم في Userbot**\n\n"
                "**الأوامر المتاحة:**\n"
                "📝 `/config` - عرض الإعدادات الحالية\n"
                "⚙️ `/set_source <chat_id>` - تعيين محادثة المصدر\n"
                "🎯 `/set_target <chat_id>` - تعيين محادثة الهدف\n"
                "▶️ `/start_bot` - تشغيل البوت\n"
                "⏹️ `/stop_bot` - إيقاف البوت\n"
                "📊 `/status` - حالة البوت\n"
                "🔄 `/restart` - إعادة تشغيل البوت\n"
                "ℹ️ `/help` - عرض المساعدة"
            )
        
        @self.client.on(events.NewMessage(pattern='/config'))
        async def config_command(event):
            if not await self.is_admin(event.sender_id):
                return
                
            try:
                config = configparser.ConfigParser()
                config.read('config.ini')
                
                source_chat = config.get('forwarding', 'source_chat', fallback='غير محدد')
                target_chat = config.get('forwarding', 'target_chat', fallback='غير محدد')
                forward_delay = config.get('forwarding', 'forward_delay', fallback='1')
                forward_media = config.get('forwarding', 'forward_media', fallback='true')
                forward_text = config.get('forwarding', 'forward_text', fallback='true')
                
                await event.respond(
                    f"⚙️ **الإعدادات الحالية:**\n\n"
                    f"📥 **محادثة المصدر:** `{source_chat}`\n"
                    f"📤 **محادثة الهدف:** `{target_chat}`\n"
                    f"⏱️ **تأخير التحويل:** `{forward_delay}` ثانية\n"
                    f"🖼️ **تحويل الوسائط:** `{forward_media}`\n"
                    f"📝 **تحويل النص:** `{forward_text}`"
                )
                
            except Exception as e:
                await event.respond(f"❌ خطأ في قراءة الإعدادات: {e}")
        
        @self.client.on(events.NewMessage(pattern=r'/set_source (.+)'))
        async def set_source_command(event):
            if not await self.is_admin(event.sender_id):
                return
                
            try:
                chat_id = event.pattern_match.group(1).strip()
                await self.update_config('source_chat', chat_id)
                await event.respond(f"✅ تم تعيين محادثة المصدر: `{chat_id}`")
            except Exception as e:
                await event.respond(f"❌ خطأ في تعيين محادثة المصدر: {e}")
        
        @self.client.on(events.NewMessage(pattern=r'/set_target (.+)'))
        async def set_target_command(event):
            if not await self.is_admin(event.sender_id):
                return
                
            try:
                chat_id = event.pattern_match.group(1).strip()
                await self.update_config('target_chat', chat_id)
                await event.respond(f"✅ تم تعيين محادثة الهدف: `{chat_id}`")
            except Exception as e:
                await event.respond(f"❌ خطأ في تعيين محادثة الهدف: {e}")
        
        @self.client.on(events.NewMessage(pattern='/start_bot'))
        async def start_bot_command(event):
            if not await self.is_admin(event.sender_id):
                return
                
            try:
                if self.userbot_process and self.userbot_process.poll() is None:
                    await event.respond("ℹ️ البوت يعمل بالفعل")
                    return
                
                # Check configuration
                config = configparser.ConfigParser()
                config.read('config.ini')
                source_chat = config.get('forwarding', 'source_chat', fallback='')
                target_chat = config.get('forwarding', 'target_chat', fallback='')
                
                if not source_chat or not target_chat or 'SOURCE_CHAT' in source_chat:
                    await event.respond("❌ يرجى تعيين محادثة المصدر والهدف أولاً")
                    return
                
                # Start userbot
                self.userbot_process = subprocess.Popen([sys.executable, 'main.py'])
                await event.respond("▶️ تم بدء تشغيل البوت")
                
            except Exception as e:
                await event.respond(f"❌ خطأ في تشغيل البوت: {e}")
        
        @self.client.on(events.NewMessage(pattern='/stop_bot'))
        async def stop_bot_command(event):
            if not await self.is_admin(event.sender_id):
                return
                
            try:
                if self.userbot_process and self.userbot_process.poll() is None:
                    self.userbot_process.terminate()
                    await event.respond("⏹️ تم إيقاف البوت")
                else:
                    await event.respond("ℹ️ البوت غير يعمل")
            except Exception as e:
                await event.respond(f"❌ خطأ في إيقاف البوت: {e}")
        
        @self.client.on(events.NewMessage(pattern='/status'))
        async def status_command(event):
            if not await self.is_admin(event.sender_id):
                return
                
            try:
                if self.userbot_process and self.userbot_process.poll() is None:
                    status = "🟢 يعمل"
                else:
                    status = "🔴 متوقف"
                
                await event.respond(f"📊 **حالة البوت:** {status}")
            except Exception as e:
                await event.respond(f"❌ خطأ في التحقق من الحالة: {e}")
        
        @self.client.on(events.NewMessage(pattern='/restart'))
        async def restart_command(event):
            if not await self.is_admin(event.sender_id):
                return
                
            try:
                # Stop current process
                if self.userbot_process and self.userbot_process.poll() is None:
                    self.userbot_process.terminate()
                    await asyncio.sleep(2)
                
                # Start new process
                self.userbot_process = subprocess.Popen([sys.executable, 'main.py'])
                await event.respond("🔄 تم إعادة تشغيل البوت")
                
            except Exception as e:
                await event.respond(f"❌ خطأ في إعادة التشغيل: {e}")
        
        @self.client.on(events.NewMessage(pattern='/help'))
        async def help_command(event):
            if not await self.is_admin(event.sender_id):
                return
                
            await event.respond(
                "🆘 **المساعدة:**\n\n"
                "**لتعيين محادثة المصدر:**\n"
                "`/set_source @channel_name` للقنوات العامة\n"
                "`/set_source -1001234567890` للمجموعات الخاصة\n\n"
                "**لتعيين محادثة الهدف:**\n"
                "`/set_target @channel_name` للقنوات العامة\n"
                "`/set_target -1001234567890` للمجموعات الخاصة\n\n"
                "**للحصول على معرف المحادثة:**\n"
                "1. أرسل رسالة في المحادثة\n"
                "2. أرسلها إلى @userinfobot\n"
                "3. سيعطيك معرف المحادثة"
            )
    
    async def is_admin(self, user_id):
        """Check if user is admin"""
        if self.admin_user_id:
            return str(user_id) == str(self.admin_user_id)
        return True  # If no admin set, allow all users
    
    async def update_config(self, key, value):
        """Update configuration file"""
        config = configparser.ConfigParser()
        config.read('config.ini')
        
        if not config.has_section('forwarding'):
            config.add_section('forwarding')
        
        config.set('forwarding', key, value)
        
        with open('config.ini', 'w') as configfile:
            config.write(configfile)
    
    async def run_until_disconnected(self):
        """Keep the bot running"""
        await self.client.run_until_disconnected()

async def main():
    """Main function"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        control_bot = TelegramControlBot()
        await control_bot.start()
        print("Control bot is running...")
        await control_bot.run_until_disconnected()
    except KeyboardInterrupt:
        print("Control bot stopped")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())