#!/usr/bin/env python3
"""
Statistics Manager - إدارة إحصائيات البوت
Real-time bot statistics and performance monitoring
"""

import time
import json
import os
from datetime import datetime, timedelta
from collections import defaultdict, deque
import psutil
import asyncio

class StatsManager:
    """Manager for bot statistics and performance monitoring"""
    
    def __init__(self):
        self.stats_file = 'bot_stats.json'
        self.start_time = time.time()
        
        # إحصائيات الرسائل
        self.messages_today = 0
        self.messages_total = 0
        self.messages_failed = 0
        self.messages_per_hour = defaultdict(int)
        
        # إحصائيات الأداء
        self.response_times = deque(maxlen=100)
        self.last_message_time = None
        self.error_log = deque(maxlen=50)
        
        # إحصائيات المعالجة
        self.replacements_made = 0
        self.links_cleaned = 0
        self.media_forwarded = 0
        self.text_forwarded = 0
        
        # تحميل الإحصائيات المحفوظة
        self._load_stats()
        
    def _load_stats(self):
        """Load saved statistics"""
        try:
            if os.path.exists(self.stats_file):
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.messages_total = data.get('messages_total', 0)
                    self.replacements_made = data.get('replacements_made', 0)
                    self.links_cleaned = data.get('links_cleaned', 0)
                    self.media_forwarded = data.get('media_forwarded', 0)
                    self.text_forwarded = data.get('text_forwarded', 0)
                    
                    # تحقق من التاريخ لإعادة تعيين الإحصائيات اليومية
                    last_date = data.get('last_date', '')
                    today = datetime.now().strftime('%Y-%m-%d')
                    if last_date == today:
                        self.messages_today = data.get('messages_today', 0)
        except Exception as e:
            print(f"Error loading stats: {e}")
    
    def _save_stats(self):
        """Save current statistics"""
        try:
            data = {
                'messages_total': self.messages_total,
                'messages_today': self.messages_today,
                'replacements_made': self.replacements_made,
                'links_cleaned': self.links_cleaned,
                'media_forwarded': self.media_forwarded,
                'text_forwarded': self.text_forwarded,
                'last_date': datetime.now().strftime('%Y-%m-%d'),
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving stats: {e}")
    
    def record_message_processed(self, success=True, message_type='text', has_media=False):
        """Record a processed message"""
        if success:
            self.messages_total += 1
            self.messages_today += 1
            self.last_message_time = datetime.now()
            
            # تسجيل النوع
            if has_media:
                self.media_forwarded += 1
            else:
                self.text_forwarded += 1
                
            # تسجيل الساعة
            hour = datetime.now().hour
            self.messages_per_hour[hour] += 1
        else:
            self.messages_failed += 1
            
        self._save_stats()
    
    def record_replacement_made(self):
        """Record a text replacement"""
        self.replacements_made += 1
        self._save_stats()
    
    def record_link_cleaned(self):
        """Record a link cleaned"""
        self.links_cleaned += 1
        self._save_stats()
    
    def record_response_time(self, response_time):
        """Record response time"""
        self.response_times.append(response_time)
    
    def record_error(self, error_msg):
        """Record an error"""
        error_entry = {
            'time': datetime.now().isoformat(),
            'error': str(error_msg)
        }
        self.error_log.append(error_entry)
    
    def get_uptime(self):
        """Get bot uptime"""
        uptime_seconds = time.time() - self.start_time
        hours, remainder = divmod(uptime_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
    
    def get_system_stats(self):
        """Get system performance stats"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            return {
                'cpu_usage': cpu_percent,
                'memory_usage': memory.percent,
                'memory_available': f"{memory.available / (1024**3):.1f} GB"
            }
        except Exception:
            return {
                'cpu_usage': 0,
                'memory_usage': 0,
                'memory_available': "غير متاح"
            }
    
    def get_average_response_time(self):
        """Get average response time"""
        if not self.response_times:
            return 0
        return sum(self.response_times) / len(self.response_times)
    
    def get_messages_per_minute(self):
        """Calculate messages per minute"""
        if not self.last_message_time:
            return 0
            
        # حساب الرسائل في آخر 10 دقائق
        now = datetime.now()
        ten_minutes_ago = now - timedelta(minutes=10)
        
        current_hour = now.hour
        messages_this_hour = self.messages_per_hour.get(current_hour, 0)
        
        # تقدير تقريبي
        return round(messages_this_hour / 60, 2) if messages_this_hour > 0 else 0
    
    def get_today_hourly_stats(self):
        """Get today's hourly message distribution"""
        current_hour = datetime.now().hour
        stats = []
        
        for hour in range(24):
            count = self.messages_per_hour.get(hour, 0)
            status = "🔴" if hour == current_hour else "⚫"
            stats.append(f"{status} {hour:02d}:00 - {count} رسائل")
        
        return stats
    
    def get_comprehensive_stats(self):
        """Get comprehensive statistics"""
        system_stats = self.get_system_stats()
        
        return {
            # إحصائيات الرسائل
            'messages_today': self.messages_today,
            'messages_total': self.messages_total,
            'messages_failed': self.messages_failed,
            'success_rate': round((self.messages_total / (self.messages_total + self.messages_failed)) * 100, 1) if (self.messages_total + self.messages_failed) > 0 else 100,
            
            # إحصائيات المعالجة
            'replacements_made': self.replacements_made,
            'links_cleaned': self.links_cleaned,
            'media_forwarded': self.media_forwarded,
            'text_forwarded': self.text_forwarded,
            
            # إحصائيات الأداء
            'uptime': self.get_uptime(),
            'avg_response_time': round(self.get_average_response_time(), 2),
            'messages_per_minute': self.get_messages_per_minute(),
            'last_message': self.last_message_time.strftime('%H:%M:%S') if self.last_message_time else 'لا توجد',
            
            # إحصائيات النظام
            'cpu_usage': system_stats['cpu_usage'],
            'memory_usage': system_stats['memory_usage'],
            'memory_available': system_stats['memory_available'],
            
            # آخر الأخطاء
            'recent_errors': list(self.error_log)[-5:] if self.error_log else [],
            'error_count': len(self.error_log)
        }
    
    def reset_daily_stats(self):
        """Reset daily statistics"""
        self.messages_today = 0
        self.messages_per_hour.clear()
        self._save_stats()

# إنشاء مثيل عام للإحصائيات
stats_manager = StatsManager()