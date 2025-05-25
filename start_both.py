#!/usr/bin/env python3
"""
مشغل البوتين معاً - Both Bots Runner
يشغل البوت الأساسي وبوت التحكم في نفس الوقت
"""

import asyncio
import subprocess
import sys
import time
import signal
import os

def signal_handler(sig, frame):
    """معالج إشارة الإيقاف"""
    print('\n🛑 تم استلام إشارة الإيقاف...')
    sys.exit(0)

async def main():
    """الدالة الرئيسية لتشغيل البوتين"""
    print("🚀 بدء تشغيل البوتين...")
    
    # تسجيل معالج الإشارات
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    userbot_process = None
    control_process = None
    
    try:
        # تشغيل البوت الأساسي في الخلفية
        print("📡 تشغيل البوت الأساسي...")
        userbot_process = subprocess.Popen([
            sys.executable, 'main.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
          universal_newlines=True, bufsize=1)
        
        # انتظار أطول للتأكد من بدء البوت الأساسي
        await asyncio.sleep(5)
        
        # تشغيل بوت التحكم مع إظهار المخرجات
        print("🎛️ تشغيل بوت التحكم...")
        control_process = subprocess.Popen([
            sys.executable, 'modern_control_bot.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
          universal_newlines=True, bufsize=1)
        
        print("✅ تم تشغيل البوتين بنجاح!")
        print("📊 البوت الأساسي: معالجة الرسائل")
        print("🎮 بوت التحكم: لوحة الإعدادات")
        print("💡 للتأكد من عمل البوتين، راقب الرسائل أدناه...")
        
        # مراقبة العمليات مع عرض المخرجات
        while True:
            # فحص حالة البوت الأساسي
            if userbot_process.poll() is not None:
                print("⚠️ البوت الأساسي توقف، إعادة تشغيل...")
                userbot_process = subprocess.Popen([
                    sys.executable, 'main.py'
                ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                  universal_newlines=True, bufsize=1)
            
            # فحص حالة بوت التحكم
            if control_process.poll() is not None:
                print("⚠️ بوت التحكم توقف، إعادة تشغيل...")
                control_process = subprocess.Popen([
                    sys.executable, 'modern_control_bot.py'
                ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                  universal_newlines=True, bufsize=1)
            
            # قراءة وعرض مخرجات البوتين
            try:
                if userbot_process.stdout and userbot_process.stdout.readable():
                    line = userbot_process.stdout.readline()
                    if line:
                        print(f"[USERBOT] {line.strip()}")
                        
                if control_process.stdout and control_process.stdout.readable():
                    line = control_process.stdout.readline()
                    if line:
                        print(f"[CONTROL] {line.strip()}")
            except:
                pass
            
            await asyncio.sleep(2)  # فحص كل ثانيتين
            
    except KeyboardInterrupt:
        print("\n🛑 إيقاف البوتين...")
        try:
            userbot_process.terminate()
            control_process.terminate()
        except:
            pass
    except Exception as e:
        print(f"❌ خطأ: {e}")

if __name__ == "__main__":
    asyncio.run(main())