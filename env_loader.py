#!/usr/bin/env python3
"""
Environment Variables Loader for Telegram Userbot
محمل المتغيرات البيئية لبوت التيليجرام
"""

import os
from dotenv import load_dotenv

def load_environment():
    """Load environment variables from .env file"""
    
    # Load .env file if it exists
    env_file = '.env'
    if os.path.exists(env_file):
        load_dotenv(env_file)
        print(f"✅ تم تحميل المتغيرات من {env_file}")
    else:
        print("⚠️ ملف .env غير موجود، سيتم استخدام متغيرات النظام")
    
    # Check required variables
    required_vars = [
        'TELEGRAM_API_ID',
        'TELEGRAM_API_HASH',
        'TELEGRAM_STRING_SESSION',
        'TELEGRAM_BOT_TOKEN',
        'TELEGRAM_ADMIN_USER_ID'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ المتغيرات التالية مطلوبة ولكنها غير موجودة:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n📝 يرجى إضافة هذه المتغيرات إلى ملف .env أو متغيرات النظام")
        return False
    
    print("✅ جميع المتغيرات المطلوبة متوفرة")
    return True

def get_config_summary():
    """Get a summary of current configuration"""
    
    config = {
        'API ID': os.getenv('TELEGRAM_API_ID', 'غير محدد'),
        'API Hash': '***' if os.getenv('TELEGRAM_API_HASH') else 'غير محدد',
        'Bot Token': '***' if os.getenv('TELEGRAM_BOT_TOKEN') else 'غير محدد',
        'String Session': '***' if os.getenv('TELEGRAM_STRING_SESSION') else 'غير محدد',
        'Admin User ID': os.getenv('TELEGRAM_ADMIN_USER_ID', 'غير محدد'),
        'Source Chat': os.getenv('SOURCE_CHAT_ID', 'غير محدد'),
        'Target Chat': os.getenv('TARGET_CHAT_ID', 'غير محدد'),
        'Forward Mode': os.getenv('FORWARD_MODE', 'copy'),
        'Environment': os.getenv('ENVIRONMENT', 'development'),
    }
    
    print("\n📊 ملخص الإعدادات الحالية:")
    print("=" * 40)
    for key, value in config.items():
        print(f"{key:15}: {value}")
    print("=" * 40)
    
    return config

if __name__ == "__main__":
    print("🔧 فحص المتغيرات البيئية...")
    
    if load_environment():
        get_config_summary()
        print("\n🚀 النظام جاهز للتشغيل!")
    else:
        print("\n❌ يرجى إصلاح المتغيرات المفقودة قبل التشغيل")