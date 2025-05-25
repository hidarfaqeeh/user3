#!/usr/bin/env python3
"""
String Session Generator for Telegram Userbot
مولد String Session لبوت التيليجرام
"""

import os
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession

async def generate_session():
    """Generate Telegram string session"""
    
    print("🔐 مولد String Session لبوت التيليجرام")
    print("=" * 50)
    
    # Get API credentials
    api_id = input("📱 أدخل API ID: ").strip()
    api_hash = input("🔑 أدخل API Hash: ").strip()
    
    if not api_id or not api_hash:
        print("❌ يجب إدخال API ID و API Hash")
        return
    
    try:
        api_id = int(api_id)
    except ValueError:
        print("❌ API ID يجب أن يكون رقم")
        return
    
    print("\n📞 سيتم إرسال كود التحقق إلى رقم هاتفك...")
    
    # Create client
    client = TelegramClient(StringSession(), api_id, api_hash)
    
    try:
        await client.start()
        
        # Get session string
        session_string = client.session.save()
        
        print("\n✅ تم إنشاء String Session بنجاح!")
        print("=" * 50)
        print("📋 String Session الخاص بك:")
        print(f"🔐 {session_string}")
        print("=" * 50)
        print("\n📝 انسخ هذا النص وضعه في ملف .env تحت:")
        print("TELEGRAM_STRING_SESSION=your_string_session_here")
        print("\n⚠️  احتفظ بهذا النص بأمان ولا تشاركه مع أحد!")
        
        # Save to file
        with open('session_string.txt', 'w') as f:
            f.write(session_string)
        print(f"\n💾 تم حفظ String Session في ملف: session_string.txt")
        
    except Exception as e:
        print(f"❌ خطأ في إنشاء Session: {e}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(generate_session())