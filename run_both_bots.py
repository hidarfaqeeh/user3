#!/usr/bin/env python3
"""
تشغيل البوتين معاً - Simple dual bot runner
حل بسيط وموثوق لتشغيل البوت الأساسي وبوت التحكم معاً
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# إعداد التسجيل
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def run_userbot():
    """تشغيل البوت الأساسي"""
    try:
        # استيراد البوت الأساسي
        sys.path.append(str(Path(__file__).parent))
        from userbot import TelegramForwarder
        
        logger.info("🚀 بدء تشغيل البوت الأساسي...")
        
        # إنشاء وتشغيل البوت
        forwarder = TelegramForwarder()
        await forwarder.start()
        
        logger.info("✅ البوت الأساسي جاهز ويعمل!")
        
        # تشغيل البوت
        await forwarder.run_until_disconnected()
        
    except Exception as e:
        logger.error(f"❌ خطأ في البوت الأساسي: {e}")
        raise

async def run_control_bot():
    """تشغيل بوت التحكم"""
    try:
        # استيراد بوت التحكم
        from modern_control_bot import ModernControlBot
        
        logger.info("🎛️ بدء تشغيل بوت التحكم...")
        
        # إنشاء وتشغيل بوت التحكم
        control_bot = ModernControlBot()
        await control_bot.start()
        
        logger.info("✅ بوت التحكم جاهز ويعمل!")
        
        # تشغيل بوت التحكم
        await control_bot.run_until_disconnected()
        
    except Exception as e:
        logger.error(f"❌ خطأ في بوت التحكم: {e}")
        raise

async def main():
    """الدالة الرئيسية لتشغيل البوتين"""
    logger.info("🔥 تشغيل النظام المزدوج للبوتين...")
    
    try:
        # تشغيل البوتين معاً بشكل متوازي
        await asyncio.gather(
            run_userbot(),
            run_control_bot(),
            return_exceptions=True
        )
        
    except KeyboardInterrupt:
        logger.info("🛑 تم إيقاف النظام بواسطة المستخدم")
    except Exception as e:
        logger.error(f"❌ خطأ عام في النظام: {e}")
        raise

if __name__ == "__main__":
    # تشغيل النظام
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 تم إنهاء البرنامج")
    except Exception as e:
        logger.error(f"💥 فشل تشغيل النظام: {e}")
        sys.exit(1)