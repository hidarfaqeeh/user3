#!/usr/bin/env python3
"""
Unified Bot Runner - تشغيل البوت مع دعم المتغيرات البيئية
Run both userbot and control bot with environment variables support
"""

import os
import sys
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ تم تحميل المتغيرات من ملف .env")
except ImportError:
    print("⚠️ python-dotenv غير مثبت، سيتم استخدام متغيرات النظام")

def check_environment():
    """Check if all required environment variables are set"""
    required_vars = {
        'TELEGRAM_API_ID': 'معرف API من my.telegram.org',
        'TELEGRAM_API_HASH': 'مفتاح API من my.telegram.org',
        'TELEGRAM_STRING_SESSION': 'جلسة النص من generate_session.py',
        'TELEGRAM_BOT_TOKEN': 'رمز البوت من @BotFather',
        'TELEGRAM_ADMIN_USER_ID': 'معرف المستخدم المدير'
    }
    
    missing_vars = []
    for var, description in required_vars.items():
        if not os.getenv(var):
            missing_vars.append((var, description))
    
    if missing_vars:
        print("❌ المتغيرات التالية مطلوبة ولكنها غير موجودة:")
        for var, desc in missing_vars:
            print(f"   🔸 {var}: {desc}")
        print("\n📝 أضف هذه المتغيرات إلى ملف .env أو إلى متغيرات النظام")
        return False
    
    # Optional variables with defaults
    optional_vars = {
        'SOURCE_CHAT_ID': os.getenv('SOURCE_CHAT_ID', 'سيتم تعيينه من لوحة التحكم'),
        'TARGET_CHAT_ID': os.getenv('TARGET_CHAT_ID', 'سيتم تعيينه من لوحة التحكم'),
        'FORWARD_MODE': os.getenv('FORWARD_MODE', 'copy'),
        'MESSAGE_DELAY': os.getenv('MESSAGE_DELAY', '1'),
        'LOG_LEVEL': os.getenv('LOG_LEVEL', 'INFO')
    }
    
    print("✅ جميع المتغيرات المطلوبة متوفرة")
    print("\n📊 الإعدادات الحالية:")
    print("=" * 50)
    
    # Show API info (masked)
    api_id = os.getenv('TELEGRAM_API_ID')
    print(f"API ID      : {api_id}")
    print(f"API Hash    : {'*' * 8}...{os.getenv('TELEGRAM_API_HASH', '')[-4:]}")
    print(f"Bot Token   : {'*' * 8}...{os.getenv('TELEGRAM_BOT_TOKEN', '')[-4:]}")
    print(f"String Sess : {'*' * 8}...{os.getenv('TELEGRAM_STRING_SESSION', '')[-8:]}")
    print(f"Admin ID    : {os.getenv('TELEGRAM_ADMIN_USER_ID')}")
    
    print("\n📋 إعدادات اختيارية:")
    for var, value in optional_vars.items():
        print(f"{var:15}: {value}")
    
    print("=" * 50)
    return True

async def run_userbot():
    """Run the main userbot"""
    try:
        from userbot import TelegramForwarder
        
        forwarder = TelegramForwarder()
        await forwarder.start()
        await forwarder.run_until_disconnected()
    except Exception as e:
        logging.error(f"خطأ في البوت الأساسي: {e}")
        raise

async def run_control_bot():
    """Run the control bot"""
    try:
        from modern_control_bot import ModernControlBot
        
        control_bot = ModernControlBot()
        await control_bot.start()
        await control_bot.run_until_disconnected()
    except Exception as e:
        logging.error(f"خطأ في بوت التحكم: {e}")
        raise

async def run_both_bots():
    """Run both bots concurrently"""
    print("🚀 بدء تشغيل البوتات...")
    
    # Setup logging
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Run both bots concurrently
        await asyncio.gather(
            run_userbot(),
            run_control_bot(),
            return_exceptions=True
        )
    except KeyboardInterrupt:
        print("\n⏹️ إيقاف البوتات...")
    except Exception as e:
        print(f"❌ خطأ في تشغيل البوتات: {e}")
        raise

def main():
    """Main function"""
    print("🤖 مشغل البوت الموحد - Telegram Userbot Runner")
    print("=" * 60)
    
    # Check environment
    if not check_environment():
        print("\n❌ يرجى إصلاح المتغيرات المفقودة قبل المتابعة")
        print("\n💡 نصائح:")
        print("   1. انسخ ملف .env.example إلى .env")
        print("   2. املأ جميع المتغيرات المطلوبة")
        print("   3. استخدم generate_session.py لإنشاء String Session")
        print("   4. شغل البوت مرة أخرى")
        sys.exit(1)
    
    print("\n🎯 اختر وضع التشغيل:")
    print("1. تشغيل البوت الأساسي فقط")
    print("2. تشغيل بوت التحكم فقط") 
    print("3. تشغيل البوتين معاً (مستحسن)")
    print("4. فحص الإعدادات فقط")
    
    try:
        choice = input("\nاختر رقم (1-4) أو اضغط Enter للخيار 3: ").strip()
        
        if choice == "1":
            print("🚀 تشغيل البوت الأساسي...")
            asyncio.run(run_userbot())
        elif choice == "2":
            print("🚀 تشغيل بوت التحكم...")
            asyncio.run(run_control_bot())
        elif choice == "4":
            print("✅ فحص الإعدادات مكتمل")
            return
        else:  # Default: run both
            print("🚀 تشغيل البوتين معاً...")
            asyncio.run(run_both_bots())
            
    except KeyboardInterrupt:
        print("\n⏹️ تم إيقاف البرنامج بواسطة المستخدم")
    except Exception as e:
        print(f"\n❌ خطأ في التشغيل: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()