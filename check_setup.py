#!/usr/bin/env python3
"""
Setup Checker - فحص إعداد البوت
Verify that all required components are properly configured
"""

import os
import sys

def check_files():
    """Check if required files exist"""
    print("📁 فحص الملفات المطلوبة...")
    
    required_files = [
        'userbot.py',
        'modern_control_bot.py', 
        'utils.py',
        'config.ini'
    ]
    
    optional_files = [
        '.env',
        'generate_session.py',
        'run_bot.py'
    ]
    
    missing_required = []
    missing_optional = []
    
    for file in required_files:
        if not os.path.exists(file):
            missing_required.append(file)
        else:
            print(f"   ✅ {file}")
    
    for file in optional_files:
        if not os.path.exists(file):
            missing_optional.append(file)
        else:
            print(f"   ✅ {file}")
    
    if missing_required:
        print(f"\n❌ ملفات مطلوبة مفقودة: {', '.join(missing_required)}")
        return False
    
    if missing_optional:
        print(f"\n⚠️ ملفات اختيارية مفقودة: {', '.join(missing_optional)}")
    
    return True

def check_environment():
    """Check environment variables"""
    print("\n🔧 فحص المتغيرات البيئية...")
    
    # Load .env if available
    try:
        from dotenv import load_dotenv
        if os.path.exists('.env'):
            load_dotenv()
            print("   ✅ تم تحميل ملف .env")
        else:
            print("   ⚠️ ملف .env غير موجود")
    except ImportError:
        print("   ⚠️ python-dotenv غير مثبت")
    
    # Check required variables
    required_vars = {
        'TELEGRAM_API_ID': 'معرف API',
        'TELEGRAM_API_HASH': 'مفتاح API',
        'TELEGRAM_STRING_SESSION': 'جلسة النص',
        'TELEGRAM_BOT_TOKEN': 'رمز البوت',
        'TELEGRAM_ADMIN_USER_ID': 'معرف المدير'
    }
    
    missing_vars = []
    valid_vars = []
    
    for var, desc in required_vars.items():
        value = os.getenv(var)
        if not value or value.startswith('your_'):
            missing_vars.append((var, desc))
            print(f"   ❌ {var}: غير محدد")
        else:
            valid_vars.append((var, desc))
            # Show masked value
            if len(value) > 8:
                masked = f"{value[:4]}...{value[-4:]}"
            else:
                masked = "***"
            print(f"   ✅ {var}: {masked}")
    
    # Check optional chat IDs
    chat_vars = ['SOURCE_CHAT_ID', 'TARGET_CHAT_ID']
    for var in chat_vars:
        value = os.getenv(var)
        if value and not value.startswith('your_'):
            print(f"   ✅ {var}: {value}")
        else:
            print(f"   ⚠️ {var}: غير محدد (يمكن تعيينه لاحقاً)")
    
    if missing_vars:
        print(f"\n❌ متغيرات مطلوبة مفقودة:")
        for var, desc in missing_vars:
            print(f"   🔸 {var}: {desc}")
        return False
    
    return True

def check_dependencies():
    """Check if required Python packages are installed"""
    print("\n📦 فحص المكتبات المطلوبة...")
    
    required_packages = [
        ('telethon', 'مكتبة التيليجرام'),
        ('configparser', 'قارئ الإعدادات'),
        ('asyncio', 'العمليات اللامتزامنة')
    ]
    
    optional_packages = [
        ('dotenv', 'محمل المتغيرات البيئية'),
        ('colorlog', 'سجلات ملونة')
    ]
    
    missing_required = []
    missing_optional = []
    
    for package, desc in required_packages:
        try:
            __import__(package)
            print(f"   ✅ {package}: {desc}")
        except ImportError:
            missing_required.append((package, desc))
            print(f"   ❌ {package}: غير مثبت - {desc}")
    
    for package, desc in optional_packages:
        try:
            __import__(package)
            print(f"   ✅ {package}: {desc}")
        except ImportError:
            missing_optional.append((package, desc))
            print(f"   ⚠️ {package}: غير مثبت - {desc}")
    
    if missing_required:
        print(f"\n❌ مكتبات مطلوبة مفقودة:")
        for package, desc in missing_required:
            print(f"   pip install {package}")
        return False
    
    if missing_optional:
        print(f"\n💡 مكتبات اختيارية يُنصح بتثبيتها:")
        for package, desc in missing_optional:
            print(f"   pip install {package}")
    
    return True

def show_next_steps():
    """Show next steps based on check results"""
    print("\n" + "="*60)
    print("📋 الخطوات التالية:")
    
    if not os.path.exists('.env'):
        print("1. انسخ .env.example إلى .env:")
        print("   cp .env.example .env")
    
    print("2. املأ المتغيرات المطلوبة في ملف .env")
    
    if not os.getenv('TELEGRAM_STRING_SESSION'):
        print("3. أنشئ String Session:")
        print("   python generate_session.py")
    
    print("4. شغل البوت:")
    print("   python run_bot.py")
    
    print("\n💡 نصائح:")
    print("   • استخدم @userinfobot للحصول على معرفات القنوات")
    print("   • احصل على API من https://my.telegram.org/apps")
    print("   • أنشئ بوت تحكم من @BotFather")

def main():
    """Main function"""
    print("🔍 فحص إعداد بوت التيليجرام")
    print("="*60)
    
    # Run all checks
    files_ok = check_files()
    deps_ok = check_dependencies()
    env_ok = check_environment()
    
    print("\n" + "="*60)
    print("📊 ملخص النتائج:")
    
    if files_ok:
        print("   ✅ الملفات: جميع الملفات المطلوبة موجودة")
    else:
        print("   ❌ الملفات: ملفات مطلوبة مفقودة")
    
    if deps_ok:
        print("   ✅ المكتبات: جميع المكتبات مثبتة")
    else:
        print("   ❌ المكتبات: مكتبات مطلوبة مفقودة")
    
    if env_ok:
        print("   ✅ المتغيرات: جميع المتغيرات محددة")
    else:
        print("   ❌ المتغيرات: متغيرات مطلوبة مفقودة")
    
    # Overall status
    if files_ok and deps_ok and env_ok:
        print("\n🎉 البوت جاهز للتشغيل!")
        print("   شغل البوت: python run_bot.py")
        return True
    else:
        print("\n⚠️ يرجى إصلاح المشاكل أعلاه قبل تشغيل البوت")
        show_next_steps()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)