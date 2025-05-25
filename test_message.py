"""
Test script to send a message to the source channel for testing buttons
"""
import asyncio
import os
from telethon import TelegramClient

async def send_test_message():
    # Get credentials from environment
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    string_session = os.getenv('TELEGRAM_STRING_SESSION')
    
    # Source chat ID (from config)
    source_chat = -1002289754739
    
    # Create client
    client = TelegramClient('test_session', api_id, api_hash)
    
    try:
        # Connect using string session
        await client.start(session=string_session)
        
        # Send test message
        test_message = "🔘 اختبار الأزرار الشفافة - هذه رسالة تجريبية"
        await client.send_message(source_chat, test_message)
        
        print("✅ تم إرسال رسالة الاختبار بنجاح!")
        
    except Exception as e:
        print(f"❌ خطأ في إرسال الرسالة: {e}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(send_test_message())