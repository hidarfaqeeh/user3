#!/usr/bin/env python3
"""
Ultra Fast Bot Runner - اختيار بين Webhook والـ Polling المحسن
يختار تلقائياً أفضل وضع حسب الإعدادات المتاحة
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# إعداد التسجيل
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def run_webhook_mode():
    """تشغيل وضع Webhook السريع"""
    try:
        from webhook_userbot import WebhookUserbot
        
        logger.info("🚀 بدء تشغيل وضع Webhook (السريع جداً)")
        
        bot = WebhookUserbot()
        await bot.run_with_fallback()
        
    except Exception as e:
        logger.error(f"❌ خطأ في وضع Webhook: {e}")
        raise

async def run_optimized_polling():
    """تشغيل وضع Polling المحسن"""
    try:
        from userbot import TelegramForwarder
        
        logger.info("⚡ بدء تشغيل وضع Polling المحسن")
        
        forwarder = TelegramForwarder()
        await forwarder.start()
        await forwarder.run_until_disconnected()
        
    except Exception as e:
        logger.error(f"❌ خطأ في وضع Polling: {e}")
        raise

async def run_control_bot():
    """تشغيل بوت التحكم"""
    try:
        from modern_control_bot import ModernControlBot
        
        logger.info("🎛️ بدء تشغيل بوت التحكم")
        
        control_bot = ModernControlBot()
        await control_bot.start()
        await control_bot.run_until_disconnected()
        
    except Exception as e:
        logger.error(f"❌ خطأ في بوت التحكم: {e}")
        raise

def check_webhook_requirements():
    """فحص متطلبات Webhook مع دعم التعرف التلقائي على Northflank"""
    # فحص إعدادات Webhook اليدوية
    webhook_host = os.getenv('WEBHOOK_HOST')
    
    # التعرف التلقائي على منصات النشر
    northflank_url = os.getenv('NORTHFLANK_APP_URL') or os.getenv('NF_DOMAIN')
    replit_url = os.getenv('REPL_SLUG')
    replit_owner = os.getenv('REPL_OWNER')
    railway_url = os.getenv('RAILWAY_STATIC_URL')
    render_url = os.getenv('RENDER_EXTERNAL_URL')
    
    # أولوية للإعدادات اليدوية
    if webhook_host and webhook_host != 'your-domain.com':
        logger.info(f"✅ Webhook host (يدوي): {webhook_host}")
        return True
    
    # التعرف على Northflank
    if northflank_url:
        logger.info(f"🔥 تم اكتشاف Northflank تلقائياً: {northflank_url}")
        logger.info("⚡ سيتم تفعيل Webhook للحصول على أقصى سرعة!")
        return True
    
    # التعرف على Replit
    if replit_url and replit_owner:
        logger.info(f"🔧 تم اكتشاف Replit: {replit_url}.{replit_owner}.repl.co")
        logger.info("⚡ سيتم تفعيل Webhook تلقائياً!")
        return True
    
    # التعرف على Railway
    if railway_url:
        logger.info(f"🚂 تم اكتشاف Railway: {railway_url}")
        return True
    
    # التعرف على Render
    if render_url:
        logger.info(f"🎨 تم اكتشاف Render: {render_url}")
        return True
    
    logger.info("📡 لم يتم اكتشاف منصة نشر - استخدام Polling المحسن")
    return False

async def main():
    """الدالة الرئيسية لتشغيل النظام الأمثل"""
    logger.info("🎯 Ultra Fast Bot System - نظام البوت السريع")
    
    # فحص وضع التشغيل
    force_polling = os.getenv('FORCE_POLLING', '').lower() == 'true'
    webhook_ready = check_webhook_requirements()
    
    try:
        if webhook_ready and not force_polling:
            # وضع Webhook (الأسرع)
            logger.info("🔗 تم اختيار وضع Webhook التلقائي")
            logger.info("⚡ السرعة المتوقعة: 0.1-0.3 ثانية")
            
            await asyncio.gather(
                run_webhook_mode(),
                run_control_bot(),
                return_exceptions=True
            )
            
        else:
            # وضع Polling المحسن
            if force_polling:
                logger.info("📡 تم فرض وضع Polling")
            else:
                logger.info("📡 وضع Webhook غير متاح، استخدام Polling المحسن")
            
            logger.info("⚡ السرعة المتوقعة: 0.3-0.8 ثانية")
            
            await asyncio.gather(
                run_optimized_polling(),
                run_control_bot(),
                return_exceptions=True
            )
            
    except KeyboardInterrupt:
        logger.info("🛑 تم إيقاف النظام بواسطة المستخدم")
    except Exception as e:
        logger.error(f"💥 خطأ عام في النظام: {e}")
        
        # محاولة التشغيل بوضع آمن
        logger.info("🔄 محاولة التشغيل بالوضع الآمن...")
        try:
            await run_optimized_polling()
        except Exception as fallback_error:
            logger.error(f"💥 فشل الوضع الآمن: {fallback_error}")
            sys.exit(1)

if __name__ == "__main__":
    print("🚀 Ultra Fast Telegram Bot")
    print("=" * 50)
    print("⚡ يختار تلقائياً أسرع وضع متاح:")
    print("🔗 Webhook (0.1-0.3 ثانية) إذا توفرت المتطلبات")
    print("📡 Polling محسن (0.3-0.8 ثانية) كبديل")
    print("=" * 50)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 تم إنهاء البرنامج")
    except Exception as e:
        print(f"💥 خطأ فادح: {e}")
        sys.exit(1)