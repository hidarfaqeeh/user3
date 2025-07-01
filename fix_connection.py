#!/usr/bin/env python3
"""
أداة تشخيص وإصلاح مشاكل اتصال البوت
Connection Diagnostic and Fix Tool
"""

import os
import configparser
import json
from pathlib import Path

def check_environment_variables():
    """Check if required environment variables are set"""
    print("🔍 فحص متغيرات البيئة...")
    
    required_vars = {
        'TELEGRAM_API_ID': 'معرف API من my.telegram.org',
        'TELEGRAM_API_HASH': 'مفتاح API من my.telegram.org', 
        'TELEGRAM_STRING_SESSION': 'جلسة النص من generate_session.py',
        'TELEGRAM_BOT_TOKEN': 'رمز البوت من @BotFather',
        'TELEGRAM_ADMIN_USER_ID': 'معرف المستخدم المدير'
    }
    
    missing_vars = []
    found_vars = []
    
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value and len(value.strip()) > 5:  # Basic validation
            found_vars.append(var)
            if var == 'TELEGRAM_API_ID':
                print(f"   ✅ {var}: {value}")
            elif var == 'TELEGRAM_ADMIN_USER_ID':
                print(f"   ✅ {var}: {value}")
            else:
                print(f"   ✅ {var}: {'*' * 8}...{value[-4:]}")
        else:
            missing_vars.append((var, description))
            print(f"   ❌ {var}: غير موجود أو فارغ")
    
    return len(missing_vars) == 0, missing_vars, found_vars

def check_config_file():
    """Check config.ini file"""
    print("\n📄 فحص ملف config.ini...")
    
    config_path = "config.ini"
    if not os.path.exists(config_path):
        print("   ❌ ملف config.ini غير موجود")
        return False
    
    config = configparser.ConfigParser()
    config.read(config_path, encoding='utf-8')
    
    # Check telegram section
    if 'telegram' not in config:
        print("   ❌ قسم [telegram] غير موجود")
        return False
    
    api_id = config.get('telegram', 'api_id', fallback='').strip()
    api_hash = config.get('telegram', 'api_hash', fallback='').strip()
    
    if not api_id or not api_hash:
        print("   ⚠️ api_id أو api_hash فارغ في config.ini")
        return False
    
    print("   ✅ ملف config.ini موجود ويحتوي على إعدادات أساسية")
    return True

def check_session_files():
    """Check for session files"""
    print("\n🔐 فحص ملفات الجلسة...")
    
    session_files = [
        'userbot_session.session',
        'modern_control_bot.session', 
        'userbot.session'
    ]
    
    found_sessions = []
    for session_file in session_files:
        if os.path.exists(session_file):
            size = os.path.getsize(session_file)
            if size > 100:  # Valid session file should be larger than 100 bytes
                found_sessions.append(session_file)
                print(f"   ✅ {session_file} ({size:,} bytes)")
            else:
                print(f"   ⚠️ {session_file} (صغير جداً: {size} bytes)")
        else:
            print(f"   ❌ {session_file} غير موجود")
    
    return len(found_sessions) > 0, found_sessions

def check_dependencies():
    """Check if required dependencies are installed"""
    print("\n📦 فحص المكتبات المطلوبة...")
    
    required_packages = ['telethon', 'asyncio', 'configparser']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"   ✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"   ❌ {package}")
    
    return len(missing_packages) == 0, missing_packages

def create_sample_env_file():
    """Create a sample .env file"""
    print("\n📝 إنشاء ملف .env نموذجي...")
    
    env_content = """# Telegram API Credentials
# احصل عليها من https://my.telegram.org
TELEGRAM_API_ID=your_api_id_here
TELEGRAM_API_HASH=your_api_hash_here

# String Session
# احصل عليها من تشغيل generate_session.py
TELEGRAM_STRING_SESSION=your_string_session_here

# Bot Token
# احصل عليها من @BotFather
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Admin User ID
# معرف المستخدم المدير (يمكن الحصول عليه من @userinfobot)
TELEGRAM_ADMIN_USER_ID=your_user_id_here

# Optional Settings
SOURCE_CHAT_ID=
TARGET_CHAT_ID=
FORWARD_MODE=copy
MESSAGE_DELAY=1
LOG_LEVEL=INFO
"""
    
    with open('.env.example', 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print("   ✅ تم إنشاء ملف .env.example")
    print("   💡 انسخه إلى .env وأدخل بياناتك الحقيقية")

def create_startup_script():
    """Create an improved startup script"""
    print("\n🚀 إنشاء سكريبت تشغيل محسن...")
    
    startup_script = """#!/usr/bin/env python3
\"\"\"
سكريبت تشغيل محسن للبوت مع فحص المتطلبات
Enhanced Bot Startup Script with Requirements Check
\"\"\"

import os
import sys
import asyncio

def check_requirements():
    \"\"\"Check all requirements before starting\"\"\"
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
    \"\"\"Start both bots with proper integration\"\"\"
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
        print("\\n⏹️ تم إيقاف البوت بواسطة المستخدم")
    except Exception as e:
        print(f"\\n❌ خطأ عام: {e}")
"""
    
    with open('start_bot.py', 'w', encoding='utf-8') as f:
        f.write(startup_script)
    
    print("   ✅ تم إنشاء start_bot.py")

def fix_config_file():
    """Fix config.ini with environment variables"""
    print("\n🔧 إصلاح ملف config.ini...")
    
    config = configparser.ConfigParser()
    
    # Load existing config if exists
    if os.path.exists('config.ini'):
        config.read('config.ini', encoding='utf-8')
    
    # Ensure sections exist
    if 'telegram' not in config:
        config.add_section('telegram')
    if 'forwarding' not in config:
        config.add_section('forwarding')
    if 'logging' not in config:
        config.add_section('logging')
    
    # Fill with environment variables if available
    api_id = os.getenv('TELEGRAM_API_ID', '')
    api_hash = os.getenv('TELEGRAM_API_HASH', '')
    
    if api_id:
        config.set('telegram', 'api_id', api_id)
    if api_hash:
        config.set('telegram', 'api_hash', api_hash)
    
    # Set some reasonable defaults
    config.set('forwarding', 'forward_delay', '1.0')
    config.set('forwarding', 'max_retries', '3')
    config.set('forwarding', 'forward_mode', 'copy')
    config.set('forwarding', 'multi_mode_enabled', 'true')
    config.set('logging', 'log_level', 'INFO')
    config.set('logging', 'log_file', 'userbot.log')
    
    # Save config
    with open('config.ini', 'w', encoding='utf-8') as f:
        config.write(f)
    
    print("   ✅ تم إصلاح ملف config.ini")

def create_initial_tasks():
    """Create initial steering tasks if none exist"""
    print("\n📋 إنشاء مهام أولية...")
    
    tasks_file = 'steering_tasks.json'
    
    if os.path.exists(tasks_file):
        print("   ✅ ملف المهام موجود بالفعل")
        return
    
    # Create a sample task
    sample_tasks = [
        {
            "task_id": "default_task_001",
            "name": "مهمة تجريبية - احذفها بعد الإعداد",
            "source_chat": "@sample_source",
            "target_chat": "@sample_target", 
            "enabled": False,
            "forward_delay": 1.0,
            "max_retries": 3,
            "forward_mode": "copy",
            "forward_text": True,
            "forward_photos": True,
            "forward_videos": True,
            "forward_music": True,
            "forward_audio": True,
            "forward_voice": True,
            "forward_video_messages": True,
            "forward_files": True,
            "forward_links": True,
            "forward_gifs": True,
            "forward_contacts": True,
            "forward_locations": True,
            "forward_polls": True,
            "forward_stickers": True,
            "forward_round": True,
            "forward_games": True,
            "header_enabled": False,
            "footer_enabled": False,
            "header_text": "",
            "footer_text": "",
            "blacklist_enabled": False,
            "whitelist_enabled": False,
            "blacklist_words": "",
            "whitelist_words": "",
            "clean_links": False,
            "clean_buttons": False,
            "clean_hashtags": False,
            "clean_formatting": False,
            "clean_empty_lines": False,
            "clean_lines_with_words": False,
            "clean_words_list": "",
            "buttons_enabled": False,
            "button1_text": "",
            "button1_url": "",
            "button2_text": "",
            "button2_url": "",
            "button3_text": "",
            "button3_url": "",
            "replacer_enabled": False,
            "replacements": ""
        }
    ]
    
    with open(tasks_file, 'w', encoding='utf-8') as f:
        json.dump(sample_tasks, f, indent=2, ensure_ascii=False)
    
    print("   ✅ تم إنشاء ملف المهام الأولي")

def main():
    """Main diagnostic function"""
    print("🔧 أداة تشخيص وإصلاح مشاكل البوت")
    print("=" * 50)
    
    # Step 1: Check environment variables
    env_ok, missing_vars, found_vars = check_environment_variables()
    
    # Step 2: Check config file
    config_ok = check_config_file()
    
    # Step 3: Check session files
    session_ok, session_files = check_session_files()
    
    # Step 4: Check dependencies
    deps_ok, missing_deps = check_dependencies()
    
    print("\n" + "=" * 50)
    print("📊 ملخص التشخيص:")
    
    if env_ok:
        print("   ✅ متغيرات البيئة: مكتملة")
    else:
        print(f"   ❌ متغيرات البيئة: {len(missing_vars)} مفقودة")
    
    if config_ok:
        print("   ✅ ملف الإعدادات: صحيح")
    else:
        print("   ❌ ملف الإعدادات: يحتاج إصلاح")
    
    if session_ok:
        print("   ✅ ملفات الجلسة: موجودة")
    else:
        print("   ❌ ملفات الجلسة: مفقودة")
    
    if deps_ok:
        print("   ✅ المكتبات المطلوبة: مثبتة")
    else:
        print(f"   ❌ المكتبات المطلوبة: {len(missing_deps)} مفقودة")
    
    # Provide fixes
    print("\n🔧 الإصلاحات المقترحة:")
    
    if not env_ok:
        print("\n1. إعداد متغيرات البيئة:")
        create_sample_env_file()
        for var, desc in missing_vars:
            print(f"   • {var}: {desc}")
    
    if not config_ok:
        print("\n2. إصلاح ملف الإعدادات:")
        fix_config_file()
    
    if not session_ok:
        print("\n3. إنشاء جلسة تيليجرام:")
        print("   💡 قم بتشغيل: python generate_session.py")
        print("   💡 أو استخدم TELEGRAM_STRING_SESSION في متغيرات البيئة")
    
    if not deps_ok:
        print("\n4. تثبيت المكتبات المفقودة:")
        for package in missing_deps:
            print(f"   💡 pip install {package}")
    
    # Create helpful files
    create_startup_script()
    create_initial_tasks()
    
    print("\n" + "=" * 50)
    
    if all([env_ok, config_ok, session_ok, deps_ok]):
        print("🎉 جميع المتطلبات مكتملة! البوت جاهز للتشغيل")
        print("🚀 قم بتشغيل: python start_bot.py")
    else:
        print("⚠️ يرجى إصلاح المشاكل المذكورة أعلاه قبل تشغيل البوت")
        print("💡 بعد الإصلاح، قم بتشغيل: python start_bot.py")

if __name__ == "__main__":
    main()