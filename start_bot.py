#!/usr/bin/env python3
"""
سكريبت تشغيل محسن للبوت مع فحص المتطلبات
Enhanced Bot Startup Script with Requirements Check
"""

import os
import sys
import asyncio

def check_requirements():
    """Check all requirements before starting"""
    print("🔍 فحص المتطلبات...")
    
    # Check environment variables
    required_vars = [
        'TELEGRAM_API_ID', 'TELEGRAM_API_HASH', 
        'TELEGRAM_STRING_SESSION', 'TELEGRAM_BOT_TOKEN'
    ]
    
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        print(f"❌ متغيرات مفقودة: {', '.join(missing)}")
        print("💡 تحقق من ملف .env أو متغيرات النظام")
        return False
    
    print("✅ جميع المتغيرات موجودة")
    return True

async def start_integrated_bot():
    """Start both bots with proper integration"""
    if not check_requirements():
        return
    
    try:
        # Load environment variables
        try:
            from dotenv import load_dotenv
            load_dotenv()
            print("✅ تم تحميل متغيرات .env")
        except ImportError:
            print("⚠️ python-dotenv غير مثبت، استخدام متغيرات النظام")
        
        # Import and start bots
        from userbot import TelegramForwarder
        from modern_control_bot import ModernControlBot
        
        print("🔧 إنشاء البوتات...")
        forwarder = TelegramForwarder()
        control_bot = ModernControlBot()
        
        print("🔗 ربط البوتات...")
        await control_bot.set_forwarder_instance(forwarder)
        
        print("🚀 بدء تشغيل بوت التحكم...")
        await control_bot.start()
        
        print("🚀 بدء تشغيل البوت الأساسي...")
        await forwarder.start()
        
        print("✅ تم تشغيل البوتين بنجاح مع دعم المهام المتعددة!")
        
        # Run both bots
        await asyncio.gather(
            forwarder.run_until_disconnected(),
            control_bot.run_until_disconnected(),
            return_exceptions=True
        )
        
    except Exception as e:
        print(f"❌ خطأ في التشغيل: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        asyncio.run(start_integrated_bot())
    except KeyboardInterrupt:
        print("\n⏹️ تم إيقاف البوت بواسطة المستخدم")
    except Exception as e:
        print(f"\n❌ خطأ عام: {e}")
