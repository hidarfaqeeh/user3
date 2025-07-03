#!/usr/bin/env python3
"""
Modern Telegram Control Bot - Interactive control panel for userbot
Beautiful interface with inline keyboards and interactive responses
"""

import asyncio
import configparser
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from telethon import TelegramClient, events, Button
from telethon.tl.types import User

# استيراد نظام الإحصائيات
try:
    from stats_manager import stats_manager
except ImportError:
    # إنشاء نظام إحصائيات مبسط في حالة عدم توفر المكتبة
    class SimpleStatsManager:
        def get_uptime(self):
            return "غير متاح"
        
        def get_comprehensive_stats(self):
            return {
                'messages_today': 0,
                'messages_total': 0,
                'messages_failed': 0,
                'success_rate': 100,
                'replacements_made': 0,
                'links_cleaned': 0,
                'media_forwarded': 0,
                'text_forwarded': 0,
                'uptime': "غير متاح",
                'avg_response_time': 0,
                'messages_per_minute': 0,
                'last_message': 'لا توجد',
                'cpu_usage': 0,
                'memory_usage': 0,
                'memory_available': "غير متاح",
                'recent_errors': [],
                'error_count': 0
            }
    
    stats_manager = SimpleStatsManager()

class ModernControlBot:
    """Modern interactive control bot with inline keyboards and multi-task support"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.client = None
        self.bot_token = None
        self.admin_user_id = None
        self.userbot_process = None
        self.user_states = {}  # Track user interaction states
        self.forwarder_instance = None  # Reference to TelegramForwarder instance
        self.setup_client()
        
    def setup_client(self):
        """Setup the control bot client"""
        try:
            api_id = os.getenv('TELEGRAM_API_ID')
            api_hash = os.getenv('TELEGRAM_API_HASH')
            self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
            self.admin_user_id = os.getenv('TELEGRAM_ADMIN_USER_ID','100237842')
            
            if not all([api_id, api_hash, self.bot_token]):
                raise ValueError("Missing required environment variables")
            
            self.client = TelegramClient('modern_control_bot', int(api_id), api_hash)
            
        except Exception as e:
            self.logger.error(f"Failed to setup control bot: {e}")
            raise
    
    async def start(self):
        """Start the control bot"""
        try:
            await self.client.start(bot_token=self.bot_token)
            me = await self.client.get_me()
            self.logger.info(f"Modern control bot started: @{me.username}")
            self.register_handlers()
            
        except Exception as e:
            self.logger.error(f"Failed to start control bot: {e}")
            raise
    
    def get_main_menu_keyboard(self):
        """Get main menu inline keyboard with smart status-based buttons"""
        is_running = self.userbot_process and self.userbot_process.poll() is None
        
        if is_running:
            control_buttons = [
                [Button.inline("⏹️ إيقاف البوت", b"stop_bot"),
                 Button.inline("🔄 إعادة تشغيل", b"restart_bot")]
            ]
        else:
            control_buttons = [
                [Button.inline("▶️ تشغيل البوت", b"start_bot")]
            ]
        
        return [
            [Button.inline("📊 تحديث الحالة", b"status"),
             Button.inline("⚙️ إعدادات البوت", b"settings")],
            [Button.inline("📈 لوحة الإحصائيات", b"stats_dashboard"),
             Button.inline("👀 عرض الإعدادات", b"view_settings")],
            [Button.inline("🎯 إدارة المهام المتعددة", b"multi_task_menu")],
            *control_buttons,
            [Button.inline("📋 السجلات", b"logs"),
             Button.inline("❓ مطور البوت", b"help")]
        ]
    
    def get_settings_keyboard(self):
        """Get enhanced settings menu keyboard"""
        return [
            # المجموعة الأولى: الإعدادات الأساسية
            [Button.inline("📥 المصدر", b"set_source"),
             Button.inline("📤 الهدف", b"set_target"),
             Button.inline("🔄 وضع التوجيه", b"forward_mode")],
            
            # المجموعة الثانية: فلاتر المحتوى
            [Button.inline("🎛️ فلاتر الوسائط", b"media_filters"),
             Button.inline("🧹 منظف النصوص", b"message_cleaner")],
            
            # المجموعة الثالثة: التخصيص المتقدم
            [Button.inline("🔄 الاستبدال الذكي", b"text_replacer"),
             Button.inline("🔘 الأزرار المخصصة", b"buttons_menu")],
            
            # المجموعة الرابعة: إضافات النص
            [Button.inline("📝 رأس وتذييل", b"header_footer")],
            
            # المجموعة الخامسة: نظام الفلترة
            [Button.inline("🚫 قائمة حظر", b"blacklist"),
             Button.inline("✅ قائمة سماح", b"whitelist")],
            

            
            # أزرار التنقل
            [Button.inline("🏠 القائمة الرئيسية", b"main_menu"),
             Button.inline("💾 حفظ وخروج", b"save_and_exit")]
        ]
    
    def get_advanced_settings_keyboard(self):
        """Get advanced settings keyboard"""
        return [
            [Button.inline("🎛️ فلاتر الوسائط", b"media_filters"),
             Button.inline("🔄 الاستبدال الذكي", b"text_replacer_menu")],
            [Button.inline("⚙️ إعدادات البوت", b"bot_settings"),
             Button.inline("📊 عرض السجلات", b"show_logs")],
            [Button.inline("🔄 إعادة تشغيل", b"restart_bot"),
             Button.inline("🔙 العودة", b"settings")]
        ]

    async def get_buttons_keyboard(self):
        """Get buttons management keyboard with current status"""
        config = await self.get_current_config()
        
        # Get current button settings
        buttons_enabled = config.getboolean('forwarding', 'buttons_enabled', fallback=False)
        button1_text = config.get('forwarding', 'button1_text', fallback='')
        button2_text = config.get('forwarding', 'button2_text', fallback='')
        button3_text = config.get('forwarding', 'button3_text', fallback='')
        
        status_emoji = "✅" if buttons_enabled else "❌"
        
        return [
            [Button.inline(f"🔘 الأزرار {status_emoji}", b"toggle_buttons")],
            [Button.inline(f"1️⃣ زر أول {'✏️' if button1_text else '➕'}", b"edit_button1"),
             Button.inline(f"2️⃣ زر ثاني {'✏️' if button2_text else '➕'}", b"edit_button2")],
            [Button.inline(f"3️⃣ زر ثالث {'✏️' if button3_text else '➕'}", b"edit_button3"),
             Button.inline("🗑️ مسح الكل", b"clear_all_buttons")],
            [Button.inline("👀 معاينة", b"preview_buttons"),
             Button.inline("🔙 العودة", b"main_menu")]
        ]

    async def get_media_filters_keyboard(self):
        """Get media filters keyboard with current status indicators"""
        config = await self.get_current_config()
        
        # Helper function to get status emoji
        def get_status_emoji(filter_key):
            try:
                status = config.get('forwarding', f'forward_{filter_key}', fallback='true')
                return "✅" if status.lower() == 'true' else "❌"
            except:
                return "✅"
        
        return [
            [Button.inline(f"📝 النصوص {get_status_emoji('text')}", b"filter_text"),
             Button.inline(f"📷 الصور {get_status_emoji('photos')}", b"filter_photos")],
            [Button.inline(f"🎥 الفيديوهات {get_status_emoji('videos')}", b"filter_videos"),
             Button.inline(f"🎵 الموسيقى {get_status_emoji('music')}", b"filter_music")],
            [Button.inline(f"🔊 الصوتيات {get_status_emoji('audio')}", b"filter_audio"),
             Button.inline(f"🎤 الرسائل الصوتية {get_status_emoji('voice')}", b"filter_voice")],
            [Button.inline(f"📹 رسائل الفيديو {get_status_emoji('video_messages')}", b"filter_video_messages"),
             Button.inline(f"📁 الملفات {get_status_emoji('files')}", b"filter_files")],
            [Button.inline(f"🔗 الروابط {get_status_emoji('links')}", b"filter_links"),
             Button.inline(f"🎞️ الصور المتحركة {get_status_emoji('gifs')}", b"filter_gifs")],
            [Button.inline(f"👤 جهات الاتصال {get_status_emoji('contacts')}", b"filter_contacts"),
             Button.inline(f"📍 المواقع {get_status_emoji('locations')}", b"filter_locations")],
            [Button.inline(f"📊 الاستطلاعات {get_status_emoji('polls')}", b"filter_polls"),
             Button.inline(f"😊 الملصقات {get_status_emoji('stickers')}", b"filter_stickers")],
            [Button.inline(f"🔴 الفيديوهات الدائرية {get_status_emoji('round')}", b"filter_round"),
             Button.inline(f"🎮 الألعاب {get_status_emoji('games')}", b"filter_games")],
            [Button.inline("🔙 العودة", b"advanced_settings")]
        ]
    
    def register_handlers(self):
        """Register all event handlers"""
        
        @self.client.on(events.NewMessage(pattern='/start'))
        async def start_command(event):
            if not await self.is_admin(event.sender_id):
                await event.respond("❌ غير مصرح لك باستخدام هذا البوت")
                return
            
            # Get current status to show transparent control panel
            config = await self.get_current_config()
            bot_status = "🟢 يعمل" if self.userbot_process and self.userbot_process.poll() is None else "🔴 متوقف"
            
            try:
                source_chat = config.get('forwarding', 'source_chat', fallback='غير محدد')
                target_chat = config.get('forwarding', 'target_chat', fallback='غير محدد')
            except:
                source_chat = 'غير محدد'
                target_chat = 'غير محدد'
            
            welcome_text = (
                "🚀 **لوحة التحكم الشفافة**\n\n"
                f"📊 **الحالة:** {bot_status}\n"
                f"📥 **المصدر:** `{source_chat}`\n"
                f"📤 **الهدف:** `{target_chat}`\n\n"
                "⚡ **التحكم السريع:**"
            )
            
            await event.respond(
                welcome_text,
                buttons=self.get_main_menu_keyboard()
            )
        
        @self.client.on(events.CallbackQuery)
        async def callback_handler(event):
            if not await self.is_admin(event.sender_id):
                await event.answer("❌ غير مصرح لك!", alert=True)
                return
            
            data = event.data.decode('utf-8')
            
            # Main menu callbacks
            if data == "main_menu":
                await self.show_main_menu(event)
            elif data == "settings":
                await self.show_settings_menu(event)
            elif data == "status":
                await self.show_bot_status(event)
            elif data == "start_bot":
                await self.handle_start_bot(event)
            elif data == "stop_bot":
                await self.handle_stop_bot(event)
            elif data == "restart_bot":
                await self.handle_restart_bot(event)
            elif data == "logs":
                await self.show_logs(event)
            elif data == "help":
                await self.show_help(event)
            elif data == "buttons_menu":
                await self.show_buttons_menu(event)
            elif data == "toggle_buttons":
                await self.toggle_buttons(event)
            elif data == "edit_button1":
                await self.prompt_edit_button(event, 1)
            elif data == "edit_button2":
                await self.prompt_edit_button(event, 2)
            elif data == "edit_button3":
                await self.prompt_edit_button(event, 3)
            elif data == "clear_all_buttons":
                await self.clear_all_buttons(event)
            elif data == "preview_buttons":
                await self.preview_buttons(event)
            
            # Settings callbacks
            elif data == "set_source":
                await self.prompt_source_chat(event)
            elif data == "set_target":
                await self.prompt_target_chat(event)
            elif data == "view_settings":
                await self.show_current_settings(event)
            elif data == "stats_dashboard":
                await self.show_stats_dashboard(event)
            elif data == "quick_settings":
                await self.show_quick_settings(event)
            elif data == "quick_setup":
                await self.show_quick_setup(event)
            elif data == "save_and_exit":
                await self.save_and_exit(event)


            elif data == "advanced_settings":
                await self.show_advanced_settings(event)
            elif data == "media_filters":
                await self.show_media_filters(event)
            elif data == "forward_mode":
                await self.show_forward_mode(event)
            elif data == "toggle_forward_mode":
                await self.toggle_forward_mode(event)
            elif data == "header_footer":
                await self.show_header_footer_menu(event)
            elif data == "toggle_header":
                await self.toggle_header(event)
            elif data == "toggle_footer":
                await self.toggle_footer(event)
            elif data == "edit_header":
                await self.prompt_header_edit(event)
            elif data == "edit_footer":
                await self.prompt_footer_edit(event)
            elif data == "clear_header":
                await self.clear_header(event)
            elif data == "clear_footer":
                await self.clear_footer(event)
            elif data == "blacklist":
                await self.show_blacklist_menu(event)
            elif data == "whitelist":
                await self.show_whitelist_menu(event)
            elif data == "toggle_blacklist":
                await self.toggle_blacklist(event)
            elif data == "toggle_whitelist":
                await self.toggle_whitelist(event)
            elif data == "add_blacklist":
                await self.prompt_add_blacklist(event)
            elif data == "add_whitelist":
                await self.prompt_add_whitelist(event)
            elif data == "view_blacklist":
                await self.view_blacklist(event)
            elif data == "view_whitelist":
                await self.view_whitelist(event)
            elif data == "clear_blacklist":
                await self.clear_blacklist(event)
            elif data == "clear_whitelist":
                await self.clear_whitelist(event)
            elif data == "message_cleaner":
                await self.show_message_cleaner_menu(event)
            elif data == "toggle_clean_links":
                await self.toggle_clean_links(event)
            elif data == "toggle_clean_buttons":
                await self.toggle_clean_buttons(event)
            elif data == "toggle_clean_hashtags":
                await self.toggle_clean_hashtags(event)
            elif data == "toggle_clean_formatting":
                await self.toggle_clean_formatting(event)
            elif data == "toggle_clean_empty_lines":
                await self.toggle_clean_empty_lines(event)
            elif data == "clean_lines_menu":
                await self.show_clean_lines_menu(event)
            elif data == "toggle_clean_lines_words":
                await self.toggle_clean_lines_words(event)
            elif data == "add_clean_words":
                await self.prompt_add_clean_words(event)
            elif data == "view_clean_words":
                await self.view_clean_words(event)
            elif data == "clear_clean_words":
                await self.clear_clean_words(event)
            
            # Text replacer callbacks  
            elif data == "text_replacer_menu":
                await self.show_text_replacer_menu(event)
            elif data == "toggle_replacer" or data == "toggle_text_replacer":
                await self.toggle_text_replacer(event)
            elif data == "add_replacement":
                await self.prompt_add_replacement(event)
            elif data == "view_replacements":
                await self.view_replacements(event)
            elif data == "clear_replacements":
                await self.clear_replacements(event)
            
            # Multi-task management callbacks
            elif data == "multi_task_menu":
                await self.show_multi_task_menu(event)
            elif data == "view_tasks":
                await self.view_tasks(event)
            elif data == "task_stats":
                await self.show_task_stats(event)
            elif data == "add_task":
                await self.prompt_add_task(event)
            elif data == "start_task":
                await self.prompt_start_task(event)
            elif data == "stop_task":
                await self.prompt_stop_task(event)
            elif data == "restart_task":
                await self.prompt_restart_task(event)
            elif data == "delete_task":
                await self.prompt_delete_task(event)
            elif data == "edit_task":
                await self.prompt_edit_task(event)
            elif data.startswith("confirm_delete_"):
                task_id = data.replace("confirm_delete_", "")
                await self.confirm_delete_task(event, task_id)
            elif data.startswith("start_specific_"):
                task_id = data.replace("start_specific_", "")
                await self.start_specific_task(event, task_id)
            elif data.startswith("stop_specific_"):
                task_id = data.replace("stop_specific_", "")
                await self.stop_specific_task(event, task_id)
            elif data.startswith("restart_specific_"):
                task_id = data.replace("restart_specific_", "")
                await self.restart_specific_task(event, task_id)
            elif data.startswith("edit_specific_"):
                task_id = data.replace("edit_specific_", "")
                await self.edit_specific_task(event, task_id)
            elif data.startswith("delete_confirmed_"):
                task_id = data.replace("delete_confirmed_", "")
                await self.delete_task_confirmed(event, task_id)
            
            # Task settings callbacks
            elif data.startswith("edit_forward_mode_"):
                task_id = data.replace("edit_forward_mode_", "")
                await self.edit_task_forward_mode(event, task_id)
            elif data.startswith("edit_media_filters_"):
                task_id = data.replace("edit_media_filters_", "")
                await self.edit_task_media_filters(event, task_id)
            elif data.startswith("edit_text_cleaner_"):
                task_id = data.replace("edit_text_cleaner_", "")
                await self.edit_task_text_cleaner(event, task_id)
            elif data.startswith("edit_smart_replacer_"):
                task_id = data.replace("edit_smart_replacer_", "")
                await self.edit_task_smart_replacer(event, task_id)
            elif data.startswith("edit_custom_buttons_"):
                task_id = data.replace("edit_custom_buttons_", "")
                await self.edit_task_custom_buttons(event, task_id)
            elif data.startswith("edit_header_footer_"):
                task_id = data.replace("edit_header_footer_", "")
                await self.edit_task_header_footer(event, task_id)
            elif data.startswith("edit_allow_list_"):
                task_id = data.replace("edit_allow_list_", "")
                await self.edit_task_allow_list(event, task_id)
            elif data.startswith("edit_block_list_"):
                task_id = data.replace("edit_block_list_", "")
                await self.edit_task_block_list(event, task_id)
            
            # Task specific toggle callbacks
            elif data.startswith("set_forward_mode_"):
                parts = data.replace("set_forward_mode_", "").split("_")
                task_id = "_".join(parts[:-1])
                mode = parts[-1]
                await self.set_task_forward_mode(event, task_id, mode)
            elif data.startswith("toggle_task_media_"):
                parts = data.replace("toggle_task_media_", "").split("_")
                task_id = "_".join(parts[:-1])
                media_type = parts[-1]
                await self.toggle_task_media_filter(event, task_id, media_type)
            elif data.startswith("toggle_task_clean_"):
                parts = data.replace("toggle_task_clean_", "").split("_")
                task_id = "_".join(parts[:-1])
                clean_type = parts[-1]
                await self.toggle_task_clean_option(event, task_id, clean_type)
            elif data.startswith("toggle_task_replacer_"):
                task_id = data.replace("toggle_task_replacer_", "")
                await self.toggle_task_replacer(event, task_id)
            elif data.startswith("toggle_task_buttons_"):
                task_id = data.replace("toggle_task_buttons_", "")
                await self.toggle_task_buttons(event, task_id)
            elif data.startswith("toggle_task_header_"):
                task_id = data.replace("toggle_task_header_", "")
                await self.toggle_task_header(event, task_id)
            elif data.startswith("toggle_task_footer_"):
                task_id = data.replace("toggle_task_footer_", "")
                await self.toggle_task_footer(event, task_id)
            elif data.startswith("toggle_task_whitelist_"):
                task_id = data.replace("toggle_task_whitelist_", "")
                await self.toggle_task_whitelist(event, task_id)
            elif data.startswith("toggle_task_blacklist_"):
                task_id = data.replace("toggle_task_blacklist_", "")
                await self.toggle_task_blacklist(event, task_id)
            
            # Task-specific detailed callbacks for replacements
            elif data.startswith("add_task_replacement_"):
                task_id = data.replace("add_task_replacement_", "")
                await self.prompt_add_task_replacement(event, task_id)
            elif data.startswith("view_task_replacements_"):
                task_id = data.replace("view_task_replacements_", "")
                await self.view_task_replacements(event, task_id)
            elif data.startswith("clear_task_replacements_"):
                task_id = data.replace("clear_task_replacements_", "")
                await self.clear_task_replacements(event, task_id)
            
            # Task-specific button callbacks
            elif data.startswith("edit_task_button_"):
                parts = data.replace("edit_task_button_", "").split("_")
                task_id = "_".join(parts[:-1])
                button_num = parts[-1]
                await self.prompt_edit_task_button(event, task_id, button_num)
            elif data.startswith("clear_task_buttons_"):
                task_id = data.replace("clear_task_buttons_", "")
                await self.clear_task_buttons(event, task_id)
            elif data.startswith("preview_task_buttons_"):
                task_id = data.replace("preview_task_buttons_", "")
                await self.preview_task_buttons(event, task_id)
            
            # Task-specific header/footer callbacks
            elif data.startswith("edit_task_header_text_"):
                task_id = data.replace("edit_task_header_text_", "")
                await self.prompt_edit_task_header(event, task_id)
            elif data.startswith("edit_task_footer_text_"):
                task_id = data.replace("edit_task_footer_text_", "")
                await self.prompt_edit_task_footer(event, task_id)
            elif data.startswith("clear_task_header_"):
                task_id = data.replace("clear_task_header_", "")
                await self.clear_task_header(event, task_id)
            elif data.startswith("clear_task_footer_"):
                task_id = data.replace("clear_task_footer_", "")
                await self.clear_task_footer(event, task_id)
            
            # Task-specific blacklist/whitelist callbacks
            elif data.startswith("add_task_blacklist_"):
                task_id = data.replace("add_task_blacklist_", "")
                await self.prompt_add_task_blacklist(event, task_id)
            elif data.startswith("view_task_blacklist_"):
                task_id = data.replace("view_task_blacklist_", "")
                await self.view_task_blacklist(event, task_id)
            elif data.startswith("clear_task_blacklist_"):
                task_id = data.replace("clear_task_blacklist_", "")
                await self.clear_task_blacklist(event, task_id)
            elif data.startswith("add_task_whitelist_"):
                task_id = data.replace("add_task_whitelist_", "")
                await self.prompt_add_task_whitelist(event, task_id)
            elif data.startswith("view_task_whitelist_"):
                task_id = data.replace("view_task_whitelist_", "")
                await self.view_task_whitelist(event, task_id)
            elif data.startswith("clear_task_whitelist_"):
                task_id = data.replace("clear_task_whitelist_", "")
                await self.clear_task_whitelist(event, task_id)
            
            # Task-specific clean words callbacks
            elif data.startswith("edit_task_clean_words_"):
                task_id = data.replace("edit_task_clean_words_", "")
                await self.edit_task_clean_words(event, task_id)
            
            # Task naming, source/target change callbacks
            elif data.startswith("edit_task_name_"):
                task_id = data.replace("edit_task_name_", "")
                await self.prompt_edit_task_name(event, task_id)
            elif data.startswith("edit_source_"):
                task_id = data.replace("edit_source_", "")
                await self.prompt_edit_task_source(event, task_id)
            elif data.startswith("edit_target_"):
                task_id = data.replace("edit_target_", "")
                await self.prompt_edit_task_target(event, task_id)
            elif data.startswith("edit_delay_"):
                task_id = data.replace("edit_delay_", "")
                await self.prompt_edit_task_delay(event, task_id)
            
            # New Advanced Features Callbacks
            elif data.startswith("edit_language_filter_"):
                task_id = data.replace("edit_language_filter_", "")
                await self.edit_task_language_filter(event, task_id)
            elif data.startswith("edit_link_filter_"):
                task_id = data.replace("edit_link_filter_", "")
                await self.edit_task_link_filter(event, task_id)
            elif data.startswith("edit_forwarded_filter_"):
                task_id = data.replace("edit_forwarded_filter_", "")
                await self.edit_task_forwarded_filter(event, task_id)
            elif data.startswith("edit_user_filter_"):
                task_id = data.replace("edit_user_filter_", "")
                await self.edit_task_user_filter(event, task_id)
            elif data.startswith("edit_char_limit_"):
                task_id = data.replace("edit_char_limit_", "")
                await self.edit_task_char_limit(event, task_id)
            elif data.startswith("edit_duplicate_filter_"):
                task_id = data.replace("edit_duplicate_filter_", "")
                await self.edit_task_duplicate_filter(event, task_id)
            elif data.startswith("edit_transparent_buttons_"):
                task_id = data.replace("edit_transparent_buttons_", "")
                await self.edit_task_transparent_buttons(event, task_id)
            elif data.startswith("edit_message_formatting_"):
                task_id = data.replace("edit_message_formatting_", "")
                await self.edit_task_message_formatting(event, task_id)
            elif data.startswith("edit_link_preview_"):
                task_id = data.replace("edit_link_preview_", "")
                await self.edit_task_link_preview(event, task_id)
            elif data.startswith("edit_message_delay_"):
                task_id = data.replace("edit_message_delay_", "")
                await self.edit_task_message_delay(event, task_id)
            elif data.startswith("edit_forward_delay_"):
                task_id = data.replace("edit_forward_delay_", "")
                await self.edit_task_forward_delay(event, task_id)
            elif data.startswith("edit_notification_settings_"):
                task_id = data.replace("edit_notification_settings_", "")
                await self.edit_task_notification_settings(event, task_id)
            elif data.startswith("edit_sync_settings_"):
                task_id = data.replace("edit_sync_settings_", "")
                await self.edit_task_sync_settings(event, task_id)
            elif data.startswith("edit_reply_preservation_"):
                task_id = data.replace("edit_reply_preservation_", "")
                await self.edit_task_reply_preservation(event, task_id)
            elif data.startswith("edit_pin_messages_"):
                task_id = data.replace("edit_pin_messages_", "")
                await self.edit_task_pin_messages(event, task_id)
            elif data.startswith("edit_forwarding_type_"):
                task_id = data.replace("edit_forwarding_type_", "")
                await self.edit_task_forwarding_type(event, task_id)
            
            # Toggle callbacks for new features
            elif data.startswith("toggle_language_filter_"):
                task_id = data.replace("toggle_language_filter_", "")
                await self.toggle_task_language_filter(event, task_id)
            elif data.startswith("toggle_link_filter_"):
                task_id = data.replace("toggle_link_filter_", "")
                await self.toggle_task_link_filter(event, task_id)
            elif data.startswith("toggle_forwarded_filter_"):
                task_id = data.replace("toggle_forwarded_filter_", "")
                await self.toggle_task_forwarded_filter(event, task_id)
            elif data.startswith("toggle_duplicate_filter_"):
                task_id = data.replace("toggle_duplicate_filter_", "")
                await self.toggle_task_duplicate_filter(event, task_id)
            elif data.startswith("toggle_transparent_buttons_"):
                task_id = data.replace("toggle_transparent_buttons_", "")
                await self.toggle_task_transparent_buttons(event, task_id)
            elif data.startswith("toggle_link_preview_"):
                task_id = data.replace("toggle_link_preview_", "")
                await self.toggle_task_link_preview(event, task_id)
            elif data.startswith("toggle_silent_mode_"):
                task_id = data.replace("toggle_silent_mode_", "")
                await self.toggle_task_silent_mode(event, task_id)
            elif data.startswith("toggle_pin_messages_"):
                task_id = data.replace("toggle_pin_messages_", "")
                await self.toggle_task_pin_messages(event, task_id)
            elif data.startswith("toggle_sync_delete_"):
                task_id = data.replace("toggle_sync_delete_", "")
                await self.toggle_task_sync_delete(event, task_id)
            elif data.startswith("toggle_sync_edit_"):
                task_id = data.replace("toggle_sync_edit_", "")
                await self.toggle_task_sync_edit(event, task_id)
            elif data.startswith("toggle_reply_preservation_"):
                task_id = data.replace("toggle_reply_preservation_", "")
                await self.toggle_task_reply_preservation(event, task_id)
            elif data.startswith("set_forwarding_type_"):
                parts = data.replace("set_forwarding_type_", "").split("_")
                task_id = "_".join(parts[:-1])
                forward_type = parts[-1]
                await self.set_task_forwarding_type(event, task_id, forward_type)
            elif data.startswith("set_message_format_"):
                parts = data.replace("set_message_format_", "").split("_")
                task_id = "_".join(parts[:-1])
                format_type = parts[-1]
                await self.set_task_message_format(event, task_id, format_type)
            
            # Additional filter callbacks that were missing
            elif data.startswith("toggle_task_language_filter_"):
                task_id = data.replace("toggle_task_language_filter_", "")
                await self.toggle_task_language_filter(event, task_id)
            elif data.startswith("toggle_task_link_filter_"):
                task_id = data.replace("toggle_task_link_filter_", "")
                await self.toggle_task_link_filter(event, task_id)
            elif data.startswith("toggle_task_forwarded_filter_"):
                task_id = data.replace("toggle_task_forwarded_filter_", "")
                await self.toggle_task_forwarded_filter(event, task_id)
            elif data.startswith("toggle_task_user_filter_"):
                task_id = data.replace("toggle_task_user_filter_", "")
                await self.toggle_task_user_filter(event, task_id)
            elif data.startswith("toggle_task_char_limit_"):
                task_id = data.replace("toggle_task_char_limit_", "")
                await self.toggle_task_char_limit(event, task_id)
            elif data.startswith("toggle_task_duplicate_filter_"):
                task_id = data.replace("toggle_task_duplicate_filter_", "")
                await self.toggle_task_duplicate_filter(event, task_id)
            elif data.startswith("toggle_task_transparent_buttons_"):
                task_id = data.replace("toggle_task_transparent_buttons_", "")
                await self.toggle_task_transparent_buttons(event, task_id)
            elif data.startswith("toggle_task_message_formatting_"):
                task_id = data.replace("toggle_task_message_formatting_", "")
                await self.toggle_task_message_formatting(event, task_id)
            elif data.startswith("edit_task_clean_words_"):
                task_id = data.replace("edit_task_clean_words_", "")
                await self.edit_task_clean_words(event, task_id)
            elif data.startswith("toggle_task_message_delay_"):
                task_id = data.replace("toggle_task_message_delay_", "")
                await self.toggle_task_message_delay(event, task_id)
            elif data.startswith("toggle_task_forward_delay_"):
                task_id = data.replace("toggle_task_forward_delay_", "")
                await self.toggle_task_forward_delay(event, task_id)
            elif data.startswith("set_task_delay_"):
                parts = data.replace("set_task_delay_", "").split("_")
                if len(parts) >= 2:
                    task_id = "_".join(parts[:-1])
                    delay_value = parts[-1]
                    await self.set_task_delay(event, task_id, delay_value)
            elif data.startswith("set_char_limit_"):
                parts = data.replace("set_char_limit_", "").split("_")
                if len(parts) >= 2:
                    task_id = "_".join(parts[:-1])
                    limit_type = parts[-1]
                    await self.set_task_char_limit(event, task_id, limit_type)
            
            # Advanced settings callbacks
            elif data == "set_delay":
                await self.prompt_delay_setting(event)
            elif data == "set_retries":
                await self.prompt_retries_setting(event)
            elif data.startswith("toggle_"):
                # Handle legacy toggle settings if needed
                pass
            
            # Media filter toggles
            elif data.startswith("filter_"):
                await self.toggle_media_filter(event, data.replace("filter_", ""))
            elif data.startswith("quick_toggle_"):
                await self.handle_quick_toggle(event, data.replace("quick_toggle_", ""))
        
        @self.client.on(events.NewMessage)
        async def message_handler(event):
            if not await self.is_admin(event.sender_id):
                return
            
            user_id = event.sender_id
            if user_id in self.user_states:
                state = self.user_states[user_id]
                
                if state == "waiting_source":
                    await self.process_source_input(event)
                elif state == "waiting_target":
                    await self.process_target_input(event)
                elif state == "waiting_delay":
                    await self.process_delay_input(event)
                elif state == "waiting_retries":
                    await self.process_retries_input(event)
                elif state.startswith("header_edit_"):
                    await self.process_header_input(event)
                elif state.startswith("footer_edit_"):
                    await self.process_footer_input(event)
                elif state.startswith("blacklist_add_"):
                    await self.process_blacklist_input(event)
                elif state.startswith("whitelist_add_"):
                    await self.process_whitelist_input(event)
                elif state.startswith("clean_words_add_"):
                    await self.process_clean_words_input(event)
                elif state.startswith("edit_button") and state.endswith("_text"):
                    button_num = int(state.split("button")[1].split("_")[0])
                    await self.process_button_text_input(event, button_num)
                elif state.startswith("edit_button") and state.endswith("_url"):
                    button_num = int(state.split("button")[1].split("_")[0])
                    await self.process_button_url_input(event, button_num)
                elif state == 'awaiting_replacement':
                    await self.process_replacement_input(event)
                elif state in ['waiting_task_name', 'waiting_task_source', 'waiting_task_target']:
                    await self.process_task_creation(event)
                # Task-specific input handlers
                elif state.startswith("task_replacement_"):
                    task_id = state.replace("task_replacement_", "")
                    await self.process_task_replacement_input(event, task_id)
                elif state.startswith("task_button_") and state.endswith("_text"):
                    parts = state.replace("task_button_", "").replace("_text", "").split("_")
                    task_id = "_".join(parts[:-1])
                    button_num = parts[-1]
                    await self.process_task_button_text_input(event, task_id, button_num)
                elif state.startswith("task_button_") and state.endswith("_url"):
                    parts = state.replace("task_button_", "").replace("_url", "").split("_")
                    task_id = "_".join(parts[:-1])
                    button_num = parts[-1]
                    await self.process_task_button_url_input(event, task_id, button_num)
                elif state.startswith("task_header_"):
                    task_id = state.replace("task_header_", "")
                    await self.process_task_header_input(event, task_id)
                elif state.startswith("task_footer_"):
                    task_id = state.replace("task_footer_", "")
                    await self.process_task_footer_input(event, task_id)
                elif state.startswith("task_blacklist_"):
                    task_id = state.replace("task_blacklist_", "")
                    await self.process_task_blacklist_input(event, task_id)
                elif state.startswith("task_whitelist_"):
                    task_id = state.replace("task_whitelist_", "")
                    await self.process_task_whitelist_input(event, task_id)
                elif state.startswith("task_name_"):
                    task_id = state.replace("task_name_", "")
                    await self.process_task_name_input(event, task_id)
                elif state.startswith("task_source_"):
                    task_id = state.replace("task_source_", "")
                    await self.process_task_source_input(event, task_id)
                elif state.startswith("task_target_"):
                    task_id = state.replace("task_target_", "")
                    await self.process_task_target_input(event, task_id)
                elif state.startswith("task_delay_"):
                    task_id = state.replace("task_delay_", "")
                    await self.process_task_delay_input(event, task_id)
    
    async def show_main_menu(self, event):
        """Show main menu"""
        text = (
            "🏠 **القائمة الرئيسية**\n\n"
            "🎯 **اختر الإجراء المطلوب:**"
        )
        await event.edit(text, buttons=self.get_main_menu_keyboard())
    
    async def show_settings_menu(self, event):
        """Show settings menu"""
        text = (
            "⚙️ **إعدادات البوت**\n\n"
            "🔧 **قم بتخصيص البوت حسب احتياجاتك:**"
        )
        await event.edit(text, buttons=self.get_settings_keyboard())
    
    async def show_advanced_settings(self, event):
        """Show advanced settings menu"""
        text = (
            "🔧 **الإعدادات المتقدمة**\n\n"
            "⚡ **تحكم دقيق في سلوك البوت:**"
        )
        await event.edit(text, buttons=self.get_advanced_settings_keyboard())
    
    async def show_bot_status(self, event):
        """Show current bot status with beautiful formatting"""
        try:
            # Get process status
            if self.userbot_process and self.userbot_process.poll() is None:
                status_emoji = "🟢"
                status_text = "يعمل بكفاءة"
                uptime = stats_manager.get_uptime()
            else:
                status_emoji = "🔴"
                status_text = "متوقف"
                uptime = "غير متاح"
            
            # Get comprehensive stats
            stats = stats_manager.get_comprehensive_stats()
            
            # Performance indicators
            cpu_color = "🟢" if stats['cpu_usage'] < 50 else "🟡" if stats['cpu_usage'] < 80 else "🔴"
            memory_color = "🟢" if stats['memory_usage'] < 70 else "🟡" if stats['memory_usage'] < 90 else "🔴"
            
            # Get configuration
            config = await self.get_current_config()
            source_chat = config.get('forwarding', 'source_chat', fallback='غير محدد')
            target_chat = config.get('forwarding', 'target_chat', fallback='غير محدد')
            
            status_message = (
                f"🚀 **لوحة حالة البوت المتقدمة**\n"
                f"═══════════════════════════════\n\n"
                
                f"🤖 **الحالة العامة:**\n"
                f"{status_emoji} **البوت:** {status_text}\n"
                f"⏱️ **مدة التشغيل:** {uptime}\n"
                f"📊 **معدل النجاح:** {stats['success_rate']}%\n\n"
                
                f"📈 **إحصائيات سريعة:**\n"
                f"📝 **اليوم:** {stats['messages_today']} رسالة\n"
                f"📊 **الإجمالي:** {stats['messages_total']} رسالة\n"
                f"⚡ **السرعة:** {stats['messages_per_minute']} رسالة/دقيقة\n"
                f"🕒 **آخر رسالة:** {stats['last_message']}\n\n"
                
                f"🖥️ **أداء النظام:**\n"
                f"{cpu_color} **المعالج:** {stats['cpu_usage']}%\n"
                f"{memory_color} **الذاكرة:** {stats['memory_usage']}%\n"
                f"💾 **متاح:** {stats['memory_available']}\n\n"
                
                f"📡 **القنوات المتصلة:**\n"
                f"📥 **المصدر:** `{source_chat}`\n"
                f"📤 **الهدف:** `{target_chat}`\n\n"
                
                f"🔧 **معالجة ذكية:**\n"
                f"🔄 **استبدالات:** {stats['replacements_made']}\n"
                f"🧹 **روابط محذوفة:** {stats['links_cleaned']}\n"
                f"🎬 **وسائط:** {stats['media_forwarded']} | 📝 **نصوص:** {stats['text_forwarded']}\n\n"
                
                f"⏰ **التحديث:** {datetime.now().strftime('%H:%M:%S')}"
            )
            
            # Add warning if there are recent errors
            if stats['error_count'] > 0:
                status_message += f"\n⚠️ **تحذير:** {stats['error_count']} خطأ حديث"
            
            keyboard = [
                [Button.inline("🔄 تحديث فوري", b"status"),
                 Button.inline("📈 الإحصائيات التفصيلية", b"stats_dashboard")],
                [Button.inline("🔙 القائمة الرئيسية", b"main_menu")]
            ]
            
            await event.edit(status_message, buttons=keyboard)
            
        except Exception as e:
            await event.edit(f"❌ خطأ في عرض الحالة: {e}")
            
    async def show_stats_dashboard(self, event):
        """Show comprehensive statistics dashboard"""
        try:
            stats = stats_manager.get_comprehensive_stats()
            
            # Performance grade
            overall_score = (stats['success_rate'] + (100 - stats['cpu_usage']) + (100 - stats['memory_usage'])) / 3
            if overall_score >= 90:
                grade = "🥇 ممتاز"
                grade_color = "🟢"
            elif overall_score >= 75:
                grade = "🥈 جيد جداً"
                grade_color = "🟡"
            elif overall_score >= 60:
                grade = "🥉 جيد"
                grade_color = "🟠"
            else:
                grade = "⚠️ يحتاج تحسين"
                grade_color = "🔴"
                
            dashboard_text = (
                f"📊 **لوحة الإحصائيات المتقدمة**\n"
                f"═══════════════════════════════\n\n"
                
                f"🏆 **التقييم العام:** {grade_color} {grade}\n"
                f"📈 **النقاط:** {overall_score:.1f}/100\n\n"
                
                f"📝 **إحصائيات الرسائل:**\n"
                f"🔥 **اليوم:** {stats['messages_today']} رسالة\n"
                f"📊 **الإجمالي:** {stats['messages_total']} رسالة\n"
                f"❌ **فشل:** {stats['messages_failed']} رسالة\n"
                f"✅ **معدل النجاح:** {stats['success_rate']}%\n"
                f"⚡ **السرعة الحالية:** {stats['messages_per_minute']} رسالة/دقيقة\n"
                f"⏱️ **متوسط الاستجابة:** {stats['avg_response_time']} ثانية\n\n"
                
                f"🔧 **إحصائيات المعالجة:**\n"
                f"🔄 **استبدالات ذكية:** {stats['replacements_made']}\n"
                f"🧹 **روابط محذوفة:** {stats['links_cleaned']}\n"
                f"🎬 **وسائط موجهة:** {stats['media_forwarded']}\n"
                f"📝 **نصوص موجهة:** {stats['text_forwarded']}\n\n"
                
                f"🖥️ **مراقبة النظام:**\n"
                f"⏱️ **مدة التشغيل:** {stats['uptime']}\n"
                f"🧠 **استخدام المعالج:** {stats['cpu_usage']}%\n"
                f"💾 **استخدام الذاكرة:** {stats['memory_usage']}%\n"
                f"💿 **ذاكرة متاحة:** {stats['memory_available']}\n\n"
                
                f"🔍 **الأخطاء الحديثة:**\n"
            )
            
            if stats['recent_errors']:
                for i, error in enumerate(stats['recent_errors'][-3:], 1):
                    error_time = error['time'][-8:-3]  # Extract time HH:MM
                    dashboard_text += f"  {i}. {error_time} - {error['error'][:50]}...\n"
            else:
                dashboard_text += "  ✅ لا توجد أخطاء حديثة\n"
                
            dashboard_text += (
                f"\n📱 **آخر نشاط:** {stats['last_message']}\n"
                f"🔄 **آخر تحديث:** {datetime.now().strftime('%H:%M:%S')}"
            )
            
            keyboard = [
                [Button.inline("🔄 تحديث الإحصائيات", b"stats_dashboard"),
                 Button.inline("📊 حالة سريعة", b"status")],
                [Button.inline("🔙 القائمة الرئيسية", b"main_menu")]
            ]
            
            await event.edit(dashboard_text, buttons=keyboard)
            
        except Exception as e:
            await event.edit(f"❌ خطأ في عرض لوحة الإحصائيات: {e}")
            self.logger.error(f"Error showing stats dashboard: {e}")
    
    async def show_quick_settings(self, event):
        """Show quick toggle settings for common features"""
        try:
            config = await self.get_current_config()
            
            # Get current states
            clean_links = config.getboolean('forwarding', 'clean_links', fallback=False)
            replacer_enabled = config.getboolean('text_replacer', 'replacer_enabled', fallback=False)
            header_enabled = config.getboolean('forwarding', 'header_enabled', fallback=False)
            footer_enabled = config.getboolean('forwarding', 'footer_enabled', fallback=False)
            buttons_enabled = config.getboolean('forwarding', 'buttons_enabled', fallback=False)
            
            def get_toggle_text(enabled):
                return "✅ مفعل" if enabled else "❌ معطل"
            
            text = (
                "⚡ **الإعدادات السريعة**\n"
                "┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓\n"
                "┃      🎛️ **تبديل سريع للميزات**     ┃\n"
                "┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"
                
                f"🧹 **منظف الروابط:** {get_toggle_text(clean_links)}\n"
                f"🔄 **الاستبدال الذكي:** {get_toggle_text(replacer_enabled)}\n"
                f"📝 **رأس الرسالة:** {get_toggle_text(header_enabled)}\n"
                f"📝 **تذييل الرسالة:** {get_toggle_text(footer_enabled)}\n"
                f"🔘 **الأزرار المخصصة:** {get_toggle_text(buttons_enabled)}\n\n"
                
                "💡 **اضغط على أي ميزة لتبديل حالتها فوراً**"
            )
            
            keyboard = [
                [Button.inline(f"🧹 حذف الروابط {get_toggle_text(clean_links)}", b"quick_toggle_clean_links"),
                 Button.inline(f"🔄 الاستبدال {get_toggle_text(replacer_enabled)}", b"quick_toggle_replacer")],
                [Button.inline(f"📝 الرأس {get_toggle_text(header_enabled)}", b"quick_toggle_header"),
                 Button.inline(f"📝 التذييل {get_toggle_text(footer_enabled)}", b"quick_toggle_footer")],
                [Button.inline(f"🔘 الأزرار {get_toggle_text(buttons_enabled)}", b"quick_toggle_buttons")],
                [Button.inline("🔙 القائمة الرئيسية", b"main_menu"),
                 Button.inline("⚙️ إعدادات مفصلة", b"settings")]
            ]
            
            await event.edit(text, buttons=keyboard)
            
        except Exception as e:
            await event.edit(f"❌ خطأ في عرض الإعدادات السريعة: {e}")
    
    async def show_quick_setup(self, event):
        """Show quick setup for first-time users"""
        text = (
            "🚀 **الإعداد السريع**\n"
            "┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓\n"
            "┃      👋 **مرحباً بك للمرة الأولى**   ┃\n"
            "┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"
            
            "📋 **خطوات الإعداد الأساسي:**\n\n"
            
            "1️⃣ **حدد القناة المصدر**\n"
            "   📥 القناة التي ستنسخ منها الرسائل\n\n"
            
            "2️⃣ **حدد القناة الهدف**\n"
            "   📤 القناة التي ستُرسل إليها الرسائل\n\n"
            
            "3️⃣ **اختر وضع التوجيه**\n"
            "   🔄 شفاف (بدون مصدر) أو مع المصدر\n\n"
            
            "4️⃣ **ابدأ البوت واستمتع!**\n"
            "   ▶️ تشغيل وبدء النسخ التلقائي\n\n"
            
            "💡 **ابدأ الآن بالخطوة الأولى:**"
        )
        
        keyboard = [
            [Button.inline("1️⃣ تحديد المصدر", b"set_source")],
            [Button.inline("2️⃣ تحديد الهدف", b"set_target")],
            [Button.inline("3️⃣ وضع التوجيه", b"forward_mode")],
            [Button.inline("🏠 القائمة الرئيسية", b"main_menu"),
             Button.inline("⚙️ إعدادات كاملة", b"settings")]
        ]
        
        await event.edit(text, buttons=keyboard)
    
    async def save_and_exit(self, event):
        """Save settings and return to main menu"""
        try:
            await event.answer("💾 تم حفظ جميع الإعدادات بنجاح!", alert=True)
            await self.show_main_menu(event)
        except Exception as e:
            await event.edit(f"❌ خطأ في الحفظ: {e}")
    
    async def handle_quick_toggle(self, event, toggle_type):
        """Handle quick toggle buttons"""
        try:
            config = await self.get_current_config()
            
            if toggle_type == "clean_links":
                current = config.getboolean('forwarding', 'clean_links', fallback=False)
                await self.update_config('clean_links', str(not current))
                status = "مفعل" if not current else "معطل"
                await event.answer(f"🧹 منظف الروابط أصبح {status}!", alert=False)
                
            elif toggle_type == "replacer":
                current = config.getboolean('text_replacer', 'replacer_enabled', fallback=False)
                await self.update_config_section('text_replacer', 'replacer_enabled', str(not current))
                status = "مفعل" if not current else "معطل"
                await event.answer(f"🔄 الاستبدال الذكي أصبح {status}!", alert=False)
                
            elif toggle_type == "header":
                current = config.getboolean('forwarding', 'header_enabled', fallback=False)
                await self.update_config('header_enabled', str(not current))
                status = "مفعل" if not current else "معطل"
                await event.answer(f"📝 رأس الرسالة أصبح {status}!", alert=False)
                
            elif toggle_type == "footer":
                current = config.getboolean('forwarding', 'footer_enabled', fallback=False)
                await self.update_config('footer_enabled', str(not current))
                status = "مفعل" if not current else "معطل"
                await event.answer(f"📝 تذييل الرسالة أصبح {status}!", alert=False)
                
            elif toggle_type == "buttons":
                current = config.getboolean('forwarding', 'buttons_enabled', fallback=False)
                await self.update_config('buttons_enabled', str(not current))
                status = "مفعل" if not current else "معطل"
                await event.answer(f"🔘 الأزرار المخصصة أصبحت {status}!", alert=False)
            
            # Refresh the quick settings menu
            await self.show_quick_settings(event)
            
        except Exception as e:
            await event.answer(f"❌ خطأ في التبديل: {e}", alert=True)
    
    async def update_config_section(self, section, key, value):
        """Update configuration in a specific section"""
        try:
            config = configparser.ConfigParser()
            config.read('config.ini')
            
            if not config.has_section(section):
                config.add_section(section)
            
            config.set(section, key, value)
            
            with open('config.ini', 'w') as configfile:
                config.write(configfile)
                
            self.logger.info(f"✅ تم تحديث الإعداد: {key} = {value} في قسم {section}")
            
        except Exception as e:
            self.logger.error(f"Error updating config section {section}: {e}")
            raise
    

    
    async def handle_start_bot(self, event):
        """Handle start bot action"""
        try:
            if self.userbot_process and self.userbot_process.poll() is None:
                await event.answer("ℹ️ البوت يعمل بالفعل!", alert=True)
                return
            
            # Check configuration
            config = await self.get_current_config()
            try:
                source_chat = config.get('forwarding', 'source_chat', fallback='')
                target_chat = config.get('forwarding', 'target_chat', fallback='')
                if not source_chat or not target_chat:
                    await event.answer("❌ يرجى تعيين محادثة المصدر والهدف أولاً!", alert=True)
                    return
            except:
                await event.answer("❌ خطأ في قراءة الإعدادات!", alert=True)
                return
            
            # Start userbot
            await event.answer("🚀 جاري بدء تشغيل البوت...", alert=True)
            self.userbot_process = subprocess.Popen([sys.executable, 'main.py'])
            
            success_message = (
                "✅ **تم بدء تشغيل البوت بنجاح!**\n\n"
                "🎯 **البوت الآن يراقب:**\n"
                f"📥 **المصدر:** `{source_chat}`\n"
                f"📤 **الهدف:** `{target_chat}`\n\n"
                "💡 **استخدم 'حالة البوت' لمراقبة الأداء**"
            )
            
            keyboard = [[Button.inline("📊 حالة البوت", b"status"),
                        Button.inline("🔙 القائمة الرئيسية", b"main_menu")]]
            
            await event.edit(success_message, buttons=keyboard)
            
        except Exception as e:
            await event.edit(f"❌ خطأ في تشغيل البوت: {e}")
    
    async def handle_stop_bot(self, event):
        """Handle stop bot action"""
        try:
            if not self.userbot_process or self.userbot_process.poll() is not None:
                await event.answer("ℹ️ البوت غير يعمل حالياً!", alert=True)
                return
            
            self.userbot_process.terminate()
            await event.answer("⏹️ تم إيقاف البوت بنجاح!", alert=True)
            
            stop_message = (
                "⏹️ **تم إيقاف البوت**\n\n"
                "🔴 **البوت متوقف الآن**\n"
                "💡 **يمكنك إعادة تشغيله في أي وقت**"
            )
            
            keyboard = [[Button.inline("▶️ تشغيل البوت", b"start_bot"),
                        Button.inline("🔙 القائمة الرئيسية", b"main_menu")]]
            
            await event.edit(stop_message, buttons=keyboard)
            
        except Exception as e:
            await event.edit(f"❌ خطأ في إيقاف البوت: {e}")
    
    async def handle_restart_bot(self, event):
        """Handle restart bot action"""
        try:
            await event.answer("🔄 جاري إعادة تشغيل البوت...", alert=True)
            
            # Stop current process
            if self.userbot_process and self.userbot_process.poll() is None:
                self.userbot_process.terminate()
                await asyncio.sleep(2)
            
            # Start new process
            self.userbot_process = subprocess.Popen([sys.executable, 'main.py'])
            
            restart_message = (
                "🔄 **تم إعادة تشغيل البوت بنجاح!**\n\n"
                "✨ **البوت جاهز للعمل مع آخر الإعدادات**\n"
                "💡 **تحقق من الحالة للتأكد من التشغيل**"
            )
            
            keyboard = [[Button.inline("📊 حالة البوت", b"status"),
                        Button.inline("🔙 القائمة الرئيسية", b"main_menu")]]
            
            await event.edit(restart_message, buttons=keyboard)
            
        except Exception as e:
            await event.edit(f"❌ خطأ في إعادة التشغيل: {e}")
    
    async def show_logs(self, event):
        """Show recent logs"""
        try:
            logs_text = "📋 **سجل الأحداث الأخيرة:**\n\n"
            
            if os.path.exists('userbot.log'):
                with open('userbot.log', 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    recent_logs = lines[-10:]  # Last 10 lines
                    
                for line in recent_logs:
                    logs_text += f"`{line.strip()}`\n"
            else:
                logs_text += "📝 **لا توجد سجلات متاحة حالياً**"
            
            keyboard = [[Button.inline("🔄 تحديث", b"logs"),
                        Button.inline("🔙 القائمة الرئيسية", b"main_menu")]]
            
            await event.edit(logs_text[:4000], buttons=keyboard)  # Telegram message limit
            
        except Exception as e:
            await event.edit(f"❌ خطأ في عرض السجلات: {e}")
    
    async def show_help(self, event):
        """Show help information"""
        help_text = (
    "👨‍⚕️ **نبذة عن المطور - د. حيدر**\n\n"
    "🌟 مرحباً، أنا **حيدر** - مطور هذا البوت\n\n"
    "🩺 طبيب متخصص مع شغف كبير بعالم البرمجة\n"
    "💻 أطور البوتات كهواية لخدمة المجتمع\n\n"
    "💡 **تخصصاتي في البرمجة:**\n"
    "🔹 برمجة بوتات التليجرام المتقدمة\n"
    "🔹 تطوير أنظمة تحميل الوسائط\n"
    "🔹 معالجة الفيديوهات والصوتيات\n"
    "🔹 تصميم واجهات المستخدم التفاعلية\n\n"
    "🎯 **رؤيتي:**\n"
    "الجمع بين الطب والتكنولوجيا لخدمة المجتمع\n"
    "وجعل التكنولوجيا في متناول الجميع مجاناً\n\n"
    "🚀 **أعمل على:**\n"
    "• تحسينات مستمرة للبوت\n"
    "• إضافة منصات جديدة\n"
    "• دمج التكنولوجيا مع الطب\n\n"
    "💝 أحب التواصل مع المستخدمين والمساعدة\n"
    "اضغط الزر أدناه للمحادثة المباشرة!"
)
        
        keyboard = [[Button.inline("⚙️ إعدادات البوت", b"settings"),
                    Button.inline("🔙 القائمة الرئيسية", b"main_menu")]]
        
        await event.edit(help_text, buttons=keyboard)
    
    async def prompt_source_chat(self, event):
        """Prompt for source chat input"""
        self.user_states[event.sender_id] = "waiting_source"
        
        prompt_text = (
            "📥 **تعيين محادثة المصدر**\n\n"
            "🎯 **أرسل معرف المحادثة التي تريد مراقبتها:**\n\n"
            "**أمثلة:**\n"
            "• `@my_channel` للقنوات العامة\n"
            "• `-1001234567890` للمجموعات الخاصة\n\n"
            "💡 **للحصول على المعرف:** أرسل رسالة إلى @userinfobot"
        )
        
        keyboard = [[Button.inline("❌ إلغاء", b"settings")]]
        await event.edit(prompt_text, buttons=keyboard)
    
    async def prompt_target_chat(self, event):
        """Prompt for target chat input"""
        self.user_states[event.sender_id] = "waiting_target"
        
        prompt_text = (
            "📤 **تعيين محادثة الهدف**\n\n"
            "🎯 **أرسل معرف المحادثة التي ستستقبل المنشورات:**\n\n"
            "**أمثلة:**\n"
            "• `@my_target_channel` للقنوات العامة\n"
            "• `-1001234567890` للمجموعات الخاصة\n\n"
            "⚠️ **تأكد من إضافة البوت كمشرف في المحادثة**"
        )
        
        keyboard = [[Button.inline("❌ إلغاء", b"settings")]]
        await event.edit(prompt_text, buttons=keyboard)
    
    async def process_source_input(self, event):
        """Process source chat input"""
        chat_id = event.message.text.strip()
        
        try:
            await self.update_config('source_chat', chat_id)
            del self.user_states[event.sender_id]
            
            success_text = (
                f"✅ **تم تعيين محادثة المصدر بنجاح!**\n\n"
                f"📥 **المصدر:** `{chat_id}`\n\n"
                f"💡 **الخطوة التالية:** تعيين محادثة الهدف"
            )
            
            keyboard = [[Button.inline("📤 تعيين الهدف", b"set_target"),
                        Button.inline("🔙 إعدادات", b"settings")]]
            
            await event.respond(success_text, buttons=keyboard)
            
        except Exception as e:
            await event.respond(f"❌ خطأ في حفظ الإعدادات: {e}")
    
    async def process_target_input(self, event):
        """Process target chat input"""
        chat_id = event.message.text.strip()
        
        try:
            await self.update_config('target_chat', chat_id)
            del self.user_states[event.sender_id]
            
            success_text = (
                f"✅ **تم تعيين محادثة الهدف بنجاح!**\n\n"
                f"📤 **الهدف:** `{chat_id}`\n\n"
                f"🚀 **البوت جاهز للتشغيل الآن!**"
            )
            
            keyboard = [[Button.inline("▶️ تشغيل البوت", b"start_bot"),
                        Button.inline("⚙️ إعدادات", b"settings")]]
            
            await event.respond(success_text, buttons=keyboard)
            
        except Exception as e:
            await event.respond(f"❌ خطأ في حفظ الإعدادات: {e}")
    
    async def show_current_settings(self, event):
        """Show current configuration with beautiful formatting"""
        try:
            config = await self.get_current_config()
            
            # البيانات الأساسية
            source_chat = config.get('forwarding', 'source_chat', fallback='غير محدد')
            target_chat = config.get('forwarding', 'target_chat', fallback='غير محدد')
            forward_mode = config.get('forwarding', 'forward_mode', fallback='copy')
            forward_delay = config.get('forwarding', 'forward_delay', fallback='1')
            max_retries = config.get('forwarding', 'max_retries', fallback='3')
            
            # فلاتر الوسائط
            forward_text = config.getboolean('forwarding', 'forward_text', fallback=True)
            forward_photos = config.getboolean('forwarding', 'forward_photos', fallback=True)
            forward_videos = config.getboolean('forwarding', 'forward_videos', fallback=True)
            forward_audio = config.getboolean('forwarding', 'forward_audio', fallback=True)
            forward_voice = config.getboolean('forwarding', 'forward_voice', fallback=True)
            forward_documents = config.getboolean('forwarding', 'forward_documents', fallback=True)
            forward_stickers = config.getboolean('forwarding', 'forward_stickers', fallback=True)
            forward_animations = config.getboolean('forwarding', 'forward_animations', fallback=True)
            forward_polls = config.getboolean('forwarding', 'forward_polls', fallback=True)
            
            # منظف الرسائل
            clean_links = config.getboolean('forwarding', 'clean_links', fallback=False)
            clean_hashtags = config.getboolean('forwarding', 'clean_hashtags', fallback=False)
            clean_buttons = config.getboolean('forwarding', 'clean_buttons', fallback=False)
            clean_formatting = config.getboolean('forwarding', 'clean_formatting', fallback=False)
            clean_empty_lines = config.getboolean('forwarding', 'clean_empty_lines', fallback=False)
            clean_lines_with_words = config.getboolean('forwarding', 'clean_lines_with_words', fallback=False)
            clean_words_list = config.get('forwarding', 'clean_words_list', fallback='')
            
            # الاستبدال الذكي
            replacer_enabled = config.getboolean('text_replacer', 'replacer_enabled', fallback=False)
            replacements = config.get('text_replacer', 'replacements', fallback='')
            replacement_count = len([r for r in replacements.split(',') if '->' in r]) if replacements else 0
            
            # Header & Footer
            header_enabled = config.getboolean('forwarding', 'header_enabled', fallback=False)
            footer_enabled = config.getboolean('forwarding', 'footer_enabled', fallback=False)
            header_text = config.get('forwarding', 'header_text', fallback='')
            footer_text = config.get('forwarding', 'footer_text', fallback='')
            
            # الأزرار
            buttons_enabled = config.getboolean('forwarding', 'buttons_enabled', fallback=False)
            button1_text = config.get('forwarding', 'button1_text', fallback='')
            button2_text = config.get('forwarding', 'button2_text', fallback='')
            button3_text = config.get('forwarding', 'button3_text', fallback='')
            active_buttons = sum(1 for btn in [button1_text, button2_text, button3_text] if btn.strip())
            
            # القوائم
            blacklist_enabled = config.getboolean('forwarding', 'blacklist_enabled', fallback=False)
            whitelist_enabled = config.getboolean('forwarding', 'whitelist_enabled', fallback=False)
            blacklist_words = config.get('forwarding', 'blacklist_words', fallback='')
            whitelist_words = config.get('forwarding', 'whitelist_words', fallback='')
            blacklist_count = len([w for w in blacklist_words.split(',') if w.strip()]) if blacklist_words else 0
            whitelist_count = len([w for w in whitelist_words.split(',') if w.strip()]) if whitelist_words else 0
            
            def get_status(value):
                return "✅ مفعل" if value else "❌ معطل"
            
            def get_mode_text(mode):
                return "🔄 مع المصدر" if mode == "forward" else "📋 شفاف"
            
            settings_text = (
                "📊 **ملخص شامل لإعدادات البوت**\n"
                "═══════════════════════════════\n\n"
                
                "🎯 **الإعدادات الأساسية:**\n"
                f"📥 المصدر: `{source_chat}`\n"
                f"📤 الهدف: `{target_chat}`\n"
                f"🔄 طريقة التوجيه: {get_mode_text(forward_mode)}\n"
                f"⏱️ التأخير: {forward_delay} ثانية\n"
                f"🔁 محاولات الإعادة: {max_retries}\n\n"
                
                "🎛️ **فلاتر الوسائط:**\n"
                f"📝 النصوص: {'✅' if forward_text else '❌'} | "
                f"🖼️ الصور: {'✅' if forward_photos else '❌'}\n"
                f"🎥 الفيديو: {'✅' if forward_videos else '❌'} | "
                f"🎵 الصوت: {'✅' if forward_audio else '❌'}\n"
                f"🎤 الرسائل الصوتية: {'✅' if forward_voice else '❌'} | "
                f"📁 الملفات: {'✅' if forward_documents else '❌'}\n"
                f"😊 الملصقات: {'✅' if forward_stickers else '❌'} | "
                f"🎬 المتحركة: {'✅' if forward_animations else '❌'}\n"
                f"📊 الاستطلاعات: {'✅' if forward_polls else '❌'}\n\n"
                
                "🧹 **منظف الرسائل:**\n"
                f"🔗 حذف الروابط: {get_status(clean_links)}\n"
                f"#️⃣ حذف الهاشتاجات: {get_status(clean_hashtags)}\n"
                f"🔘 حذف الأزرار: {get_status(clean_buttons)}\n"
                f"🎨 حذف التنسيق: {get_status(clean_formatting)}\n"
                f"📝 حذف الأسطر الفارغة: {get_status(clean_empty_lines)}\n"
                f"🗑️ حذف أسطر بكلمات محددة: {get_status(clean_lines_with_words)}\n"
            )
            
            if clean_lines_with_words and clean_words_list:
                words_preview = clean_words_list[:30] + "..." if len(clean_words_list) > 30 else clean_words_list
                settings_text += f"   📋 الكلمات: `{words_preview}`\n"
            
            settings_text += (
                f"\n🔄 **الاستبدال الذكي:**\n"
                f"📱 الحالة: {get_status(replacer_enabled)}\n"
            )
            
            if replacer_enabled and replacement_count > 0:
                settings_text += f"📊 عدد الاستبدالات: {replacement_count}\n"
                if replacements:
                    preview = replacements[:50] + "..." if len(replacements) > 50 else replacements
                    settings_text += f"🔍 مثال: `{preview}`\n"
            
            settings_text += (
                f"\n📝 **Header & Footer:**\n"
                f"🔝 Header: {get_status(header_enabled)}"
            )
            
            if header_enabled and header_text:
                header_preview = header_text[:20] + "..." if len(header_text) > 20 else header_text
                settings_text += f" - `{header_preview}`"
            
            settings_text += f"\n🔚 Footer: {get_status(footer_enabled)}"
            
            if footer_enabled and footer_text:
                footer_preview = footer_text[:20] + "..." if len(footer_text) > 20 else footer_text
                settings_text += f" - `{footer_preview}`"
            
            settings_text += (
                f"\n\n🔘 **الأزرار المخصصة:**\n"
                f"📱 الحالة: {get_status(buttons_enabled)}\n"
            )
            
            if buttons_enabled and active_buttons > 0:
                settings_text += f"🔢 الأزرار النشطة: {active_buttons}/3\n"
            
            settings_text += (
                f"\n🚫 **القائمة السوداء:**\n"
                f"📱 الحالة: {get_status(blacklist_enabled)}\n"
            )
            
            if blacklist_enabled and blacklist_count > 0:
                settings_text += f"📊 عدد الكلمات: {blacklist_count}\n"
            
            settings_text += (
                f"\n✅ **القائمة البيضاء:**\n"
                f"📱 الحالة: {get_status(whitelist_enabled)}\n"
            )
            
            if whitelist_enabled and whitelist_count > 0:
                settings_text += f"📊 عدد الكلمات: {whitelist_count}\n"
            
            settings_text += (
                "\n═══════════════════════════════\n"
                "💡 **ملاحظة:** يمكن تعديل جميع هذه الإعدادات\n"
                "من قائمة 'إعدادات البوت'"
            )
            
            keyboard = [
                [Button.inline("🔧 تعديل الإعدادات", b"settings")],
                [Button.inline("🔄 تحديث", b"view_settings"),
                 Button.inline("🔙 القائمة الرئيسية", b"main_menu")]
            ]
            
            await event.edit(settings_text, buttons=keyboard)
            
        except Exception as e:
            await event.edit(f"❌ خطأ في عرض الإعدادات: {e}")
            self.logger.error(f"Error showing settings: {e}")
    
    async def get_current_config(self):
        """Get current configuration with all media filters"""
        try:
            config = configparser.ConfigParser()
            config.read('config.ini')
            
            # Return the full config object for easier access
            return config
        except Exception:
            # Return empty config if file doesn't exist
            empty_config = configparser.ConfigParser()
            return empty_config
    
    async def is_admin(self, user_id):
        """Check if user is admin"""
        if self.admin_user_id:
            return str(user_id) == str(self.admin_user_id)
        return True
    
    async def show_forward_mode(self, event):
        """Show forward mode selection menu"""
        config = await self.get_current_config()
        current_mode = config.get('forwarding', 'forward_mode', fallback='forward')
        
        if current_mode == 'forward':
            mode_text = "إعادة توجيه مع إظهار المصدر"
            mode_emoji = "🔄"
            status_emoji = "✅"
        else:
            mode_text = "نسخ وإعادة إرسال بدون مصدر"
            mode_emoji = "📋"
            status_emoji = "✅"
        
        text = (
            f"{mode_emoji} **طريقة التوجيه الحالية**\n\n"
            f"{status_emoji} **الوضع النشط:** {mode_text}\n\n"
            "🔄 **إعادة توجيه مع إظهار المصدر:**\n"
            "• يظهر اسم المحادثة المصدر\n"
            "• يحتفظ بمعلومات الرسالة الأصلية\n"
            "• سريع ومباشر\n\n"
            "📋 **نسخ وإعادة إرسال:**\n"
            "• لا يظهر المصدر الأصلي\n"
            "• يبدو وكأن البوت أرسل الرسالة\n"
            "• مناسب للخصوصية\n\n"
            "💡 اضغط 'تبديل الوضع' للتغيير"
        )
        
        keyboard = [
            [Button.inline("🔄 تبديل الوضع", b"toggle_forward_mode")],
            [Button.inline("🔙 العودة للإعدادات", b"settings")]
        ]
        
        await event.edit(text, buttons=keyboard)

    async def toggle_forward_mode(self, event):
        """Toggle between forward and copy mode"""
        try:
            config = await self.get_current_config()
            current_mode = config.get('forwarding', 'forward_mode', fallback='forward')
            
            new_mode = 'copy' if current_mode == 'forward' else 'forward'
            await self.update_config('forward_mode', new_mode)
            
            if new_mode == 'forward':
                mode_text = "إعادة توجيه مع إظهار المصدر"
                mode_emoji = "🔄"
            else:
                mode_text = "نسخ وإعادة إرسال بدون مصدر"
                mode_emoji = "📋"
            
            await event.answer(f"✅ تم تحديث طريقة التوجيه إلى: {mode_text}", alert=True)
            await self.show_forward_mode(event)
            
        except Exception as e:
            await event.answer(f"❌ خطأ في تحديث طريقة التوجيه: {str(e)}", alert=True)

    async def show_header_footer_menu(self, event):
        """Show header and footer management menu"""
        config = await self.get_current_config()
        
        # Get current settings
        header_enabled = config.get('forwarding', 'header_enabled', fallback='false') == 'true'
        footer_enabled = config.get('forwarding', 'footer_enabled', fallback='false') == 'true'
        header_text = config.get('forwarding', 'header_text', fallback='').strip()
        footer_text = config.get('forwarding', 'footer_text', fallback='').strip()
        
        # Status indicators
        header_status = "✅ مفعل" if header_enabled else "❌ معطل"
        footer_status = "✅ مفعل" if footer_enabled else "❌ معطل"
        
        text = (
            "📝 **إدارة Header & Footer**\n\n"
            f"📄 **Header (رأس الرسالة):** {header_status}\n"
            f"📝 **النص:** {header_text[:30]+'...' if len(header_text) > 30 else header_text or 'غير محدد'}\n\n"
            f"📄 **Footer (تذييل الرسالة):** {footer_status}\n"
            f"📝 **النص:** {footer_text[:30]+'...' if len(footer_text) > 30 else footer_text or 'غير محدد'}\n\n"
            "💡 **يمكنك استخدام:**\n"
            "• نصوص عادية\n"
            "• رموز تعبيرية 📱\n"
            "• أسطر متعددة (Enter)\n"
            "• تنسيق Markdown\n"
        )
        
        keyboard = [
            [Button.inline(f"{'🔴' if header_enabled else '🟢'} تبديل Header", b"toggle_header"),
             Button.inline(f"{'🔴' if footer_enabled else '🟢'} تبديل Footer", b"toggle_footer")],
            [Button.inline("✏️ تعديل Header", b"edit_header"),
             Button.inline("✏️ تعديل Footer", b"edit_footer")],
            [Button.inline("🗑️ حذف Header", b"clear_header"),
             Button.inline("🗑️ حذف Footer", b"clear_footer")],
            [Button.inline("🔙 العودة للإعدادات", b"settings")]
        ]
        
        await event.edit(text, buttons=keyboard)

    async def toggle_header(self, event):
        """Toggle header on/off"""
        try:
            config = await self.get_current_config()
            current = config.get('forwarding', 'header_enabled', fallback='false') == 'true'
            new_value = 'false' if current else 'true'
            
            await self.update_config('header_enabled', new_value)
            
            status = "تم تفعيله" if new_value == 'true' else "تم تعطيله"
            await event.answer(f"✅ Header {status}", alert=True)
            await self.show_header_footer_menu(event)
            
        except Exception as e:
            await event.answer(f"❌ خطأ في تحديث Header: {str(e)}", alert=True)

    async def toggle_footer(self, event):
        """Toggle footer on/off"""
        try:
            config = await self.get_current_config()
            current = config.get('forwarding', 'footer_enabled', fallback='false') == 'true'
            new_value = 'false' if current else 'true'
            
            await self.update_config('footer_enabled', new_value)
            
            status = "تم تفعيله" if new_value == 'true' else "تم تعطيله"
            await event.answer(f"✅ Footer {status}", alert=True)
            await self.show_header_footer_menu(event)
            
        except Exception as e:
            await event.answer(f"❌ خطأ في تحديث Footer: {str(e)}", alert=True)

    async def prompt_header_edit(self, event):
        """Prompt user to edit header text"""
        config = await self.get_current_config()
        current_header = config.get('forwarding', 'header_text', fallback='')
        
        text = (
            "✏️ **تعديل Header**\n\n"
            f"📝 **النص الحالي:**\n{current_header or 'غير محدد'}\n\n"
            "💡 **إرشادات:**\n"
            "• أرسل النص الجديد للـ Header\n"
            "• يمكنك استخدام أسطر متعددة\n"
            "• يمكنك استخدام رموز تعبيرية\n"
            "• أرسل 'إلغاء' للعودة بدون تغيير\n"
        )
        
        keyboard = [[Button.inline("🔙 إلغاء", b"header_footer")]]
        await event.edit(text, buttons=keyboard)
        self.user_states[event.sender_id] = f"header_edit_{event.sender_id}"

    async def prompt_footer_edit(self, event):
        """Prompt user to edit footer text"""
        config = await self.get_current_config()
        current_footer = config.get('forwarding', 'footer_text', fallback='')
        
        text = (
            "✏️ **تعديل Footer**\n\n"
            f"📝 **النص الحالي:**\n{current_footer or 'غير محدد'}\n\n"
            "💡 **إرشادات:**\n"
            "• أرسل النص الجديد للـ Footer\n"
            "• يمكنك استخدام أسطر متعددة\n"
            "• يمكنك استخدام رموز تعبيرية\n"
            "• أرسل 'إلغاء' للعودة بدون تغيير\n"
        )
        
        keyboard = [[Button.inline("🔙 إلغاء", b"header_footer")]]
        await event.edit(text, buttons=keyboard)
        self.user_states[event.sender_id] = f"footer_edit_{event.sender_id}"

    async def clear_header(self, event):
        """Clear header text"""
        try:
            await self.update_config('header_text', '')
            await self.update_config('header_enabled', 'false')
            
            await event.answer("✅ تم حذف Header بنجاح", alert=True)
            await self.show_header_footer_menu(event)
            
        except Exception as e:
            await event.answer(f"❌ خطأ في حذف Header: {str(e)}", alert=True)

    async def clear_footer(self, event):
        """Clear footer text"""
        try:
            await self.update_config('footer_text', '')
            await self.update_config('footer_enabled', 'false')
            
            await event.answer("✅ تم حذف Footer بنجاح", alert=True)
            await self.show_header_footer_menu(event)
            
        except Exception as e:
            await event.answer(f"❌ خطأ في حذف Footer: {str(e)}", alert=True)

    async def process_header_input(self, event):
        """Process header text input"""
        try:
            text = event.text.strip()
            
            if text.lower() == 'إلغاء':
                if event.sender_id in self.user_states:
                    del self.user_states[event.sender_id]
                await self.show_header_footer_menu(event)
                return
            
            # Save header text
            await self.update_config('header_text', text)
            await self.update_config('header_enabled', 'true')
            
            # Clear user state
            if event.sender_id in self.user_states:
                del self.user_states[event.sender_id]
            
            # Show success message
            await event.respond(
                f"✅ **تم حفظ Header بنجاح!**\n\n"
                f"📝 **النص المحفوظ:**\n{text}\n\n"
                f"🔥 تم تفعيل Header تلقائياً!",
                buttons=[[Button.inline("🔙 العودة لإعدادات Header & Footer", b"header_footer")]]
            )
            
        except Exception as e:
            await event.respond(f"❌ خطأ في حفظ Header: {str(e)}")
            if event.sender_id in self.user_states:
                del self.user_states[event.sender_id]

    async def process_footer_input(self, event):
        """Process footer text input"""
        try:
            text = event.text.strip()
            
            if text.lower() == 'إلغاء':
                if event.sender_id in self.user_states:
                    del self.user_states[event.sender_id]
                await self.show_header_footer_menu(event)
                return
            
            # Save footer text
            await self.update_config('footer_text', text)
            await self.update_config('footer_enabled', 'true')
            
            # Clear user state
            if event.sender_id in self.user_states:
                del self.user_states[event.sender_id]
            
            # Show success message
            await event.respond(
                f"✅ **تم حفظ Footer بنجاح!**\n\n"
                f"📝 **النص المحفوظ:**\n{text}\n\n"
                f"🔥 تم تفعيل Footer تلقائياً!",
                buttons=[[Button.inline("🔙 العودة لإعدادات Header & Footer", b"header_footer")]]
            )
            
        except Exception as e:
            await event.respond(f"❌ خطأ في حفظ Footer: {str(e)}")
            if event.sender_id in self.user_states:
                del self.user_states[event.sender_id]

    async def show_media_filters(self, event):
        """Show media filters menu"""
        config = await self.get_current_config()
        
        text = "🎛️ **فلاتر الوسائط**\n\n"
        text += "اختر نوع الوسائط للتحكم في تحويله:\n\n"
        
        # Show current status for each filter
        filters = {
            'text': ('📝', 'النصوص'),
            'photos': ('📷', 'الصور'),
            'videos': ('🎥', 'الفيديوهات'),
            'music': ('🎵', 'الموسيقى'),
            'audio': ('🔊', 'الصوتيات'),
            'voice': ('🎤', 'الرسائل الصوتية'),
            'video_messages': ('📹', 'رسائل الفيديو'),
            'files': ('📁', 'الملفات'),
            'links': ('🔗', 'الروابط'),
            'gifs': ('🎞️', 'الصور المتحركة'),
            'contacts': ('👤', 'جهات الاتصال'),
            'locations': ('📍', 'المواقع'),
            'polls': ('📊', 'الاستطلاعات'),
            'stickers': ('😊', 'الملصقات'),
            'round': ('🔴', 'الفيديوهات الدائرية'),
            'games': ('🎮', 'الألعاب')
        }
        
        for filter_key, (emoji, name) in filters.items():
            try:
                status = config.get('forwarding', f'forward_{filter_key}', fallback='true')
                status_emoji = "✅" if status.lower() == 'true' else "❌"
                text += f"{emoji} {name}: {status_emoji}\n"
            except:
                text += f"{emoji} {name}: ✅\n"
        
        keyboard = await self.get_media_filters_keyboard()
        await event.edit(text, buttons=keyboard)

    async def toggle_media_filter(self, event, filter_type):
        """Toggle a specific media filter"""
        try:
            config = await self.get_current_config()
            current_value = config.get('forwarding', f'forward_{filter_type}', fallback='true')
            new_value = 'false' if current_value.lower() == 'true' else 'true'
            
            await self.update_config(f'forward_{filter_type}', new_value)
            
            filter_names = {
                'text': 'النصوص',
                'photos': 'الصور',
                'videos': 'الفيديوهات',
                'music': 'الموسيقى',
                'audio': 'الصوتيات',
                'voice': 'الرسائل الصوتية',
                'video_messages': 'رسائل الفيديو',
                'files': 'الملفات',
                'links': 'الروابط',
                'gifs': 'الصور المتحركة',
                'contacts': 'جهات الاتصال',
                'locations': 'المواقع',
                'polls': 'الاستطلاعات',
                'stickers': 'الملصقات',
                'round': 'الفيديوهات الدائرية',
                'games': 'الألعاب'
            }
            
            filter_name = filter_names.get(filter_type, filter_type)
            status = "تم تفعيله" if new_value == 'true' else "تم إلغاؤه"
            
            await event.answer(f"✅ فلتر {filter_name} {status}", alert=True)
            await self.show_media_filters(event)
            
        except Exception as e:
            await event.answer(f"❌ خطأ في تحديث الفلتر: {str(e)}", alert=True)

    async def update_config(self, key, value):
        """Update configuration file"""
        config = configparser.ConfigParser()
        config.read('config.ini')
        
        # Ensure both sections exist
        if not config.has_section('forwarding'):
            config.add_section('forwarding')
        if not config.has_section('text_replacer'):
            config.add_section('text_replacer')
        
        # Update in text_replacer section (primary location)
        config.set('text_replacer', key, value)
        
        # Also update in forwarding section for compatibility
        config.set('forwarding', key, value)
        
        with open('config.ini', 'w') as configfile:
            config.write(configfile)
        
        # Log the update for verification
        print(f"✅ تم تحديث الإعداد: {key} = {value}")
        
        # Verify the setting was saved in text_replacer section
        verification_config = configparser.ConfigParser()
        verification_config.read('config.ini')
        saved_value = verification_config.get('text_replacer', key, fallback='NOT_FOUND')
        print(f"🔍 التحقق من الحفظ: {key} = {saved_value}")
    
    # === القائمة السوداء والبيضاء ===
    
    async def show_blacklist_menu(self, event):
        """Show blacklist management menu"""
        config = await self.get_current_config()
        
        blacklist_enabled = config.get('forwarding', 'blacklist_enabled', fallback='false') == 'true'
        blacklist_words = config.get('forwarding', 'blacklist_words', fallback='').strip()
        words_count = len([w for w in blacklist_words.split(',') if w.strip()]) if blacklist_words else 0
        
        status = "✅ مفعلة" if blacklist_enabled else "❌ معطلة"
        
        text = (
            "🚫 **إدارة القائمة السوداء**\n\n"
            f"📊 **الحالة:** {status}\n"
            f"📝 **عدد الكلمات:** {words_count}\n\n"
            "💡 **القائمة السوداء تمنع تحويل الرسائل التي تحتوي على كلمات محددة**\n\n"
            "🔧 **الخيارات المتاحة:**"
        )
        
        toggle_text = "🔴 تعطيل" if blacklist_enabled else "🟢 تفعيل"
        
        keyboard = [
            [Button.inline(f"{toggle_text} القائمة السوداء", b"toggle_blacklist")],
            [Button.inline("➕ إضافة كلمات", b"add_blacklist"),
             Button.inline("👀 عرض القائمة", b"view_blacklist")],
            [Button.inline("🗑️ مسح القائمة", b"clear_blacklist")],
            [Button.inline("🔙 العودة للإعدادات", b"settings")]
        ]
        
        await event.edit(text, buttons=keyboard)

    async def show_whitelist_menu(self, event):
        """Show whitelist management menu"""
        config = await self.get_current_config()
        
        whitelist_enabled = config.get('forwarding', 'whitelist_enabled', fallback='false') == 'true'
        whitelist_words = config.get('forwarding', 'whitelist_words', fallback='').strip()
        words_count = len([w for w in whitelist_words.split(',') if w.strip()]) if whitelist_words else 0
        
        status = "✅ مفعلة" if whitelist_enabled else "❌ معطلة"
        
        text = (
            "✅ **إدارة القائمة البيضاء**\n\n"
            f"📊 **الحالة:** {status}\n"
            f"📝 **عدد الكلمات:** {words_count}\n\n"
            "💡 **القائمة البيضاء تسمح فقط بتحويل الرسائل التي تحتوي على كلمات محددة**\n\n"
            "🔧 **الخيارات المتاحة:**"
        )
        
        toggle_text = "🔴 تعطيل" if whitelist_enabled else "🟢 تفعيل"
        
        keyboard = [
            [Button.inline(f"{toggle_text} القائمة البيضاء", b"toggle_whitelist")],
            [Button.inline("➕ إضافة كلمات", b"add_whitelist"),
             Button.inline("👀 عرض القائمة", b"view_whitelist")],
            [Button.inline("🗑️ مسح القائمة", b"clear_whitelist")],
            [Button.inline("🔙 العودة للإعدادات", b"settings")]
        ]
        
        await event.edit(text, buttons=keyboard)

    async def toggle_blacklist(self, event):
        """Toggle blacklist on/off"""
        try:
            config = await self.get_current_config()
            current = config.get('forwarding', 'blacklist_enabled', fallback='false') == 'true'
            new_value = 'false' if current else 'true'
            
            await self.update_config('blacklist_enabled', new_value)
            
            status = "تم تفعيلها" if new_value == 'true' else "تم تعطيلها"
            await event.answer(f"✅ القائمة السوداء {status}", alert=True)
            await self.show_blacklist_menu(event)
            
        except Exception as e:
            await event.answer(f"❌ خطأ في تحديث القائمة السوداء: {str(e)}", alert=True)

    async def toggle_whitelist(self, event):
        """Toggle whitelist on/off"""
        try:
            config = await self.get_current_config()
            current = config.get('forwarding', 'whitelist_enabled', fallback='false') == 'true'
            new_value = 'false' if current else 'true'
            
            await self.update_config('whitelist_enabled', new_value)
            
            status = "تم تفعيلها" if new_value == 'true' else "تم تعطيلها"
            await event.answer(f"✅ القائمة البيضاء {status}", alert=True)
            await self.show_whitelist_menu(event)
            
        except Exception as e:
            await event.answer(f"❌ خطأ في تحديث القائمة البيضاء: {str(e)}", alert=True)

    async def prompt_add_blacklist(self, event):
        """Prompt user to add blacklist words"""
        text = (
            "🚫 **إضافة كلمات للقائمة السوداء**\n\n"
            "💡 **إرشادات:**\n"
            "• أرسل الكلمات المراد حظرها\n"
            "• فصل بين الكلمات بفاصلة (,)\n"
            "• مثال: كلمة1, كلمة2, كلمة3\n"
            "• أرسل 'إلغاء' للعودة بدون إضافة\n\n"
            "📝 **أمثلة على الاستخدام:**\n"
            "• إعلان, دعاية, ترويج\n"
            "• spam, ads, promotion"
        )
        
        keyboard = [[Button.inline("🔙 إلغاء", b"blacklist")]]
        await event.edit(text, buttons=keyboard)
        self.user_states[event.sender_id] = f"blacklist_add_{event.sender_id}"

    async def prompt_add_whitelist(self, event):
        """Prompt user to add whitelist words"""
        text = (
            "✅ **إضافة كلمات للقائمة البيضاء**\n\n"
            "💡 **إرشادات:**\n"
            "• أرسل الكلمات المسموح بها فقط\n"
            "• فصل بين الكلمات بفاصلة (,)\n"
            "• مثال: كلمة1, كلمة2, كلمة3\n"
            "• أرسل 'إلغاء' للعودة بدون إضافة\n\n"
            "📝 **أمثلة على الاستخدام:**\n"
            "• أخبار, مهم, عاجل\n"
            "• news, important, urgent"
        )
        
        keyboard = [[Button.inline("🔙 إلغاء", b"whitelist")]]
        await event.edit(text, buttons=keyboard)
        self.user_states[event.sender_id] = f"whitelist_add_{event.sender_id}"

    async def process_blacklist_input(self, event):
        """Process blacklist words input"""
        try:
            text = event.text.strip()
            
            if text.lower() == 'إلغاء':
                if event.sender_id in self.user_states:
                    del self.user_states[event.sender_id]
                await self.show_blacklist_menu(event)
                return
            
            # Get current words and add new ones
            config = await self.get_current_config()
            current_words = config.get('forwarding', 'blacklist_words', fallback='').strip()
            
            new_words = [word.strip() for word in text.split(',') if word.strip()]
            
            if current_words:
                existing_words = [word.strip() for word in current_words.split(',') if word.strip()]
                all_words = list(set(existing_words + new_words))  # Remove duplicates
            else:
                all_words = new_words
            
            final_words = ', '.join(all_words)
            
            # Save words and enable blacklist
            await self.update_config('blacklist_words', final_words)
            await self.update_config('blacklist_enabled', 'true')
            
            # Clear user state
            if event.sender_id in self.user_states:
                del self.user_states[event.sender_id]
            
            # Show success message
            await event.respond(
                f"✅ **تم إضافة الكلمات للقائمة السوداء!**\n\n"
                f"📝 **الكلمات المضافة:** {', '.join(new_words)}\n"
                f"📊 **إجمالي الكلمات:** {len(all_words)}\n\n"
                f"🔥 تم تفعيل القائمة السوداء تلقائياً!",
                buttons=[[Button.inline("🔙 العودة لإدارة القائمة السوداء", b"blacklist")]]
            )
            
        except Exception as e:
            await event.respond(f"❌ خطأ في حفظ القائمة السوداء: {str(e)}")
            if event.sender_id in self.user_states:
                del self.user_states[event.sender_id]

    async def process_whitelist_input(self, event):
        """Process whitelist words input"""
        try:
            text = event.text.strip()
            
            if text.lower() == 'إلغاء':
                if event.sender_id in self.user_states:
                    del self.user_states[event.sender_id]
                await self.show_whitelist_menu(event)
                return
            
            # Get current words and add new ones
            config = await self.get_current_config()
            current_words = config.get('forwarding', 'whitelist_words', fallback='').strip()
            
            new_words = [word.strip() for word in text.split(',') if word.strip()]
            
            if current_words:
                existing_words = [word.strip() for word in current_words.split(',') if word.strip()]
                all_words = list(set(existing_words + new_words))  # Remove duplicates
            else:
                all_words = new_words
            
            final_words = ', '.join(all_words)
            
            # Save words and enable whitelist
            await self.update_config('whitelist_words', final_words)
            await self.update_config('whitelist_enabled', 'true')
            
            # Clear user state
            if event.sender_id in self.user_states:
                del self.user_states[event.sender_id]
            
            # Show success message
            await event.respond(
                f"✅ **تم إضافة الكلمات للقائمة البيضاء!**\n\n"
                f"📝 **الكلمات المضافة:** {', '.join(new_words)}\n"
                f"📊 **إجمالي الكلمات:** {len(all_words)}\n\n"
                f"🔥 تم تفعيل القائمة البيضاء تلقائياً!",
                buttons=[[Button.inline("🔙 العودة لإدارة القائمة البيضاء", b"whitelist")]]
            )
            
        except Exception as e:
            await event.respond(f"❌ خطأ في حفظ القائمة البيضاء: {str(e)}")
            if event.sender_id in self.user_states:
                del self.user_states[event.sender_id]

    async def view_blacklist(self, event):
        """View current blacklist words"""
        config = await self.get_current_config()
        blacklist_words = config.get('forwarding', 'blacklist_words', fallback='').strip()
        
        if not blacklist_words:
            text = "🚫 **القائمة السوداء فارغة**\n\n❌ لا توجد كلمات محظورة حالياً"
        else:
            words_list = [word.strip() for word in blacklist_words.split(',') if word.strip()]
            words_display = '\n'.join([f"• {word}" for word in words_list])
            
            text = (
                f"🚫 **القائمة السوداء الحالية**\n\n"
                f"📊 **عدد الكلمات:** {len(words_list)}\n\n"
                f"📝 **الكلمات المحظورة:**\n{words_display}"
            )
        
        keyboard = [[Button.inline("🔙 العودة لإدارة القائمة السوداء", b"blacklist")]]
        await event.edit(text, buttons=keyboard)

    async def view_whitelist(self, event):
        """View current whitelist words"""
        config = await self.get_current_config()
        whitelist_words = config.get('forwarding', 'whitelist_words', fallback='').strip()
        
        if not whitelist_words:
            text = "✅ **القائمة البيضاء فارغة**\n\n❌ لا توجد كلمات مسموحة حالياً"
        else:
            words_list = [word.strip() for word in whitelist_words.split(',') if word.strip()]
            words_display = '\n'.join([f"• {word}" for word in words_list])
            
            text = (
                f"✅ **القائمة البيضاء الحالية**\n\n"
                f"📊 **عدد الكلمات:** {len(words_list)}\n\n"
                f"📝 **الكلمات المسموحة:**\n{words_display}"
            )
        
        keyboard = [[Button.inline("🔙 العودة لإدارة القائمة البيضاء", b"whitelist")]]
        await event.edit(text, buttons=keyboard)

    async def clear_blacklist(self, event):
        """Clear all blacklist words"""
        try:
            await self.update_config('blacklist_words', '')
            await self.update_config('blacklist_enabled', 'false')
            
            await event.answer("✅ تم مسح القائمة السوداء بالكامل", alert=True)
            await self.show_blacklist_menu(event)
            
        except Exception as e:
            await event.answer(f"❌ خطأ في مسح القائمة السوداء: {str(e)}", alert=True)

    async def clear_whitelist(self, event):
        """Clear all whitelist words"""
        try:
            await self.update_config('whitelist_words', '')
            await self.update_config('whitelist_enabled', 'false')
            
            await event.answer("✅ تم مسح القائمة البيضاء بالكامل", alert=True)
            await self.show_whitelist_menu(event)
            
        except Exception as e:
            await event.answer(f"❌ خطأ في مسح القائمة البيضاء: {str(e)}", alert=True)

    # === منظف الرسائل ===
    
    async def show_message_cleaner_menu(self, event):
        """Show message cleaner main menu"""
        config = await self.get_current_config()
        
        # Get current status for all cleaning options
        clean_links = config.get('forwarding', 'clean_links', fallback='false') == 'true'
        clean_buttons = config.get('forwarding', 'clean_buttons', fallback='false') == 'true'
        clean_hashtags = config.get('forwarding', 'clean_hashtags', fallback='false') == 'true'
        clean_formatting = config.get('forwarding', 'clean_formatting', fallback='false') == 'true'
        clean_empty_lines = config.get('forwarding', 'clean_empty_lines', fallback='false') == 'true'
        clean_lines_with_words = config.get('forwarding', 'clean_lines_with_words', fallback='false') == 'true'
        
        # Status indicators
        def get_status(enabled): return "✅ مفعل" if enabled else "❌ معطل"
        
        text = (
            "🧹 **منظف الرسائل**\n\n"
            "💡 **قم بتنظيف الرسائل قبل إعادة توجيهها**\n\n"
            f"🔗 **تنظيف الروابط والمعرفات:** {get_status(clean_links)}\n"
            f"🔲 **إزالة الأزرار الشفافة:** {get_status(clean_buttons)}\n" 
            f"# **إزالة الهاشتاقات:** {get_status(clean_hashtags)}\n"
            f"**B** **إزالة التنسيق:** {get_status(clean_formatting)}\n"
            f"⬜ **حذف الأسطر الفارغة:** {get_status(clean_empty_lines)}\n"
            f"🗑️ **حذف أسطر تحتوي كلمات:** {get_status(clean_lines_with_words)}\n\n"
            "🔧 **اختر الميزة المراد تعديلها:**"
        )
        
        keyboard = [
            [Button.inline("🔗 الروابط والمعرفات", b"toggle_clean_links"),
             Button.inline("🔲 الأزرار الشفافة", b"toggle_clean_buttons")],
            [Button.inline("# الهاشتاقات", b"toggle_clean_hashtags"),
             Button.inline("**B** التنسيق", b"toggle_clean_formatting")],
            [Button.inline("⬜ الأسطر الفارغة", b"toggle_clean_empty_lines")],
            [Button.inline("🗑️ أسطر تحتوي كلمات", b"clean_lines_menu")],
            [Button.inline("🔙 القائمة الرئيسية", b"main_menu")]
        ]
        
        await event.edit(text, buttons=keyboard)

    async def toggle_clean_links(self, event):
        """Toggle link cleaning on/off"""
        try:
            config = await self.get_current_config()
            current = config.get('forwarding', 'clean_links', fallback='false') == 'true'
            new_value = 'false' if current else 'true'
            
            await self.update_config('clean_links', new_value)
            
            status = "تم تفعيلها" if new_value == 'true' else "تم تعطيلها"
            await event.answer(f"✅ تنظيف الروابط والمعرفات {status}", alert=True)
            await self.show_message_cleaner_menu(event)
            
        except Exception as e:
            await event.answer(f"❌ خطأ في التحديث: {str(e)}", alert=True)

    async def toggle_clean_buttons(self, event):
        """Toggle button cleaning on/off"""
        try:
            config = await self.get_current_config()
            current = config.get('forwarding', 'clean_buttons', fallback='false') == 'true'
            new_value = 'false' if current else 'true'
            
            await self.update_config('clean_buttons', new_value)
            
            status = "تم تفعيلها" if new_value == 'true' else "تم تعطيلها"
            await event.answer(f"✅ إزالة الأزرار الشفافة {status}", alert=True)
            await self.show_message_cleaner_menu(event)
            
        except Exception as e:
            await event.answer(f"❌ خطأ في التحديث: {str(e)}", alert=True)

    async def toggle_clean_hashtags(self, event):
        """Toggle hashtag cleaning on/off"""
        try:
            config = await self.get_current_config()
            current = config.get('forwarding', 'clean_hashtags', fallback='false') == 'true'
            new_value = 'false' if current else 'true'
            
            await self.update_config('clean_hashtags', new_value)
            
            status = "تم تفعيلها" if new_value == 'true' else "تم تعطيلها"
            await event.answer(f"✅ إزالة الهاشتاقات {status}", alert=True)
            await self.show_message_cleaner_menu(event)
            
        except Exception as e:
            await event.answer(f"❌ خطأ في التحديث: {str(e)}", alert=True)

    async def toggle_clean_formatting(self, event):
        """Toggle formatting cleaning on/off"""
        try:
            config = await self.get_current_config()
            current = config.get('forwarding', 'clean_formatting', fallback='false') == 'true'
            new_value = 'false' if current else 'true'
            
            await self.update_config('clean_formatting', new_value)
            
            status = "تم تفعيلها" if new_value == 'true' else "تم تعطيلها"
            await event.answer(f"✅ إزالة التنسيق {status}", alert=True)
            await self.show_message_cleaner_menu(event)
            
        except Exception as e:
            await event.answer(f"❌ خطأ في التحديث: {str(e)}", alert=True)

    async def toggle_clean_empty_lines(self, event):
        """Toggle empty lines cleaning on/off"""
        try:
            config = await self.get_current_config()
            current = config.get('forwarding', 'clean_empty_lines', fallback='false') == 'true'
            new_value = 'false' if current else 'true'
            
            await self.update_config('clean_empty_lines', new_value)
            
            status = "تم تفعيلها" if new_value == 'true' else "تم تعطيلها"
            await event.answer(f"✅ حذف الأسطر الفارغة {status}", alert=True)
            await self.show_message_cleaner_menu(event)
            
        except Exception as e:
            await event.answer(f"❌ خطأ في التحديث: {str(e)}", alert=True)

    async def show_clean_lines_menu(self, event):
        """Show clean lines with words menu"""
        config = await self.get_current_config()
        
        clean_enabled = config.get('forwarding', 'clean_lines_with_words', fallback='false') == 'true'
        clean_words = config.get('forwarding', 'clean_words_list', fallback='').strip()
        words_count = len([w for w in clean_words.split(',') if w.strip()]) if clean_words else 0
        
        status = "✅ مفعلة" if clean_enabled else "❌ معطلة"
        
        text = (
            "🗑️ **حذف أسطر تحتوي على كلمات محددة**\n\n"
            f"📊 **الحالة:** {status}\n"
            f"📝 **عدد الكلمات:** {words_count}\n\n"
            "💡 **سيتم حذف أي سطر يحتوي على إحدى هذه الكلمات**\n\n"
            "🔧 **الخيارات المتاحة:**"
        )
        
        toggle_text = "🔴 تعطيل" if clean_enabled else "🟢 تفعيل"
        
        keyboard = [
            [Button.inline(f"{toggle_text} حذف الأسطر", b"toggle_clean_lines_words")],
            [Button.inline("➕ إضافة كلمات", b"add_clean_words"),
             Button.inline("👀 عرض الكلمات", b"view_clean_words")],
            [Button.inline("🗑️ مسح الكلمات", b"clear_clean_words")],
            [Button.inline("🔙 منظف الرسائل", b"message_cleaner")]
        ]
        
        await event.edit(text, buttons=keyboard)

    async def toggle_clean_lines_words(self, event):
        """Toggle cleaning lines with words on/off"""
        try:
            config = await self.get_current_config()
            current = config.get('forwarding', 'clean_lines_with_words', fallback='false') == 'true'
            new_value = 'false' if current else 'true'
            
            await self.update_config('clean_lines_with_words', new_value)
            
            status = "تم تفعيلها" if new_value == 'true' else "تم تعطيلها"
            await event.answer(f"✅ حذف الأسطر التي تحتوي كلمات {status}", alert=True)
            await self.show_clean_lines_menu(event)
            
        except Exception as e:
            await event.answer(f"❌ خطأ في التحديث: {str(e)}", alert=True)

    async def prompt_add_clean_words(self, event):
        """Prompt user to add clean words"""
        text = (
            "🗑️ **إضافة كلمات لحذف الأسطر**\n\n"
            "💡 **إرشادات:**\n"
            "• أرسل الكلمات المراد حذف أسطرها\n"
            "• فصل بين الكلمات بفاصلة (,)\n"
            "• مثال: إعلان, ترويج, دعاية\n"
            "• أرسل 'إلغاء' للعودة بدون إضافة\n\n"
            "📝 **مثال:**\n"
            "إذا أضفت 'إعلان' - سيحذف أي سطر يحتوي على كلمة إعلان"
        )
        
        keyboard = [[Button.inline("🔙 إلغاء", b"clean_lines_menu")]]
        await event.edit(text, buttons=keyboard)
        self.user_states[event.sender_id] = f"clean_words_add_{event.sender_id}"

    async def view_clean_words(self, event):
        """View current clean words"""
        config = await self.get_current_config()
        clean_words = config.get('forwarding', 'clean_words_list', fallback='').strip()
        
        if not clean_words:
            text = "🗑️ **قائمة كلمات حذف الأسطر فارغة**\n\n❌ لا توجد كلمات محددة حالياً"
        else:
            words_list = [word.strip() for word in clean_words.split(',') if word.strip()]
            words_display = '\n'.join([f"• {word}" for word in words_list])
            
            text = (
                f"🗑️ **كلمات حذف الأسطر الحالية**\n\n"
                f"📊 **عدد الكلمات:** {len(words_list)}\n\n"
                f"📝 **الكلمات:**\n{words_display}\n\n"
                "💡 أي سطر يحتوي على إحدى هذه الكلمات سيتم حذفه"
            )
        
        keyboard = [[Button.inline("🔙 العودة لإدارة حذف الأسطر", b"clean_lines_menu")]]
        await event.edit(text, buttons=keyboard)

    async def clear_clean_words(self, event):
        """Clear all clean words"""
        try:
            await self.update_config('clean_words_list', '')
            await self.update_config('clean_lines_with_words', 'false')
            
            await event.answer("✅ تم مسح جميع كلمات حذف الأسطر", alert=True)
            await self.show_clean_lines_menu(event)
            
        except Exception as e:
            await event.answer(f"❌ خطأ في المسح: {str(e)}", alert=True)

    async def process_clean_words_input(self, event):
        """Process clean words input"""
        try:
            text = event.text.strip()
            
            if text.lower() == 'إلغاء':
                if event.sender_id in self.user_states:
                    del self.user_states[event.sender_id]
                await self.show_clean_lines_menu(event)
                return
            
            # Get current words and add new ones
            config = await self.get_current_config()
            current_words = config.get('forwarding', 'clean_words_list', fallback='').strip()
            
            new_words = [word.strip() for word in text.split(',') if word.strip()]
            
            if current_words:
                existing_words = [word.strip() for word in current_words.split(',') if word.strip()]
                all_words = list(set(existing_words + new_words))  # Remove duplicates
            else:
                all_words = new_words
            
            final_words = ', '.join(all_words)
            
            # Save words and enable feature
            await self.update_config('clean_words_list', final_words)
            await self.update_config('clean_lines_with_words', 'true')
            
            # Clear user state
            if event.sender_id in self.user_states:
                del self.user_states[event.sender_id]
            
            # Show success message
            await event.respond(
                f"✅ **تم إضافة الكلمات لحذف الأسطر!**\n\n"
                f"📝 **الكلمات المضافة:** {', '.join(new_words)}\n"
                f"📊 **إجمالي الكلمات:** {len(all_words)}\n\n"
                f"🔥 تم تفعيل حذف الأسطر تلقائياً!",
                buttons=[[Button.inline("🔙 العودة لإدارة حذف الأسطر", b"clean_lines_menu")]]
            )
            
        except Exception as e:
            await event.respond(f"❌ خطأ في حفظ الكلمات: {str(e)}")
            if event.sender_id in self.user_states:
                del self.user_states[event.sender_id]

    async def show_buttons_menu(self, event):
        """Show buttons management menu"""
        config = await self.get_current_config()
        
        # Get current button settings
        buttons_enabled = config.getboolean('forwarding', 'buttons_enabled', fallback=False)
        button1_text = config.get('forwarding', 'button1_text', fallback='')
        button1_url = config.get('forwarding', 'button1_url', fallback='')
        button2_text = config.get('forwarding', 'button2_text', fallback='')
        button2_url = config.get('forwarding', 'button2_url', fallback='')
        button3_text = config.get('forwarding', 'button3_text', fallback='')
        button3_url = config.get('forwarding', 'button3_url', fallback='')
        
        status = "✅ مفعل" if buttons_enabled else "❌ معطل"
        
        message = f"🔘 **إدارة الأزرار الشفافة**\n\n"
        message += f"📊 **الحالة:** {status}\n\n"
        
        if buttons_enabled:
            message += "📝 **الأزرار الحالية:**\n"
            
            if button1_text and button1_url:
                message += f"1️⃣ **{button1_text}**\n   🔗 {button1_url}\n\n"
            
            if button2_text and button2_url:
                message += f"2️⃣ **{button2_text}**\n   🔗 {button2_url}\n\n"
            
            if button3_text and button3_url:
                message += f"3️⃣ **{button3_text}**\n   🔗 {button3_url}\n\n"
        else:
            message += "💡 **قم بتفعيل الأزرار وإضافة محتوى لها!**\n\n"
        
        message += "⚡ **إدارة سريعة:**"
        
        keyboard = await self.get_buttons_keyboard()
        await event.edit(message, buttons=keyboard)

    async def toggle_buttons(self, event):
        """Toggle buttons on/off"""
        config = await self.get_current_config()
        current_status = config.getboolean('forwarding', 'buttons_enabled', fallback=False)
        new_status = not current_status
        
        await self.update_config('buttons_enabled', str(new_status).lower())
        
        status_text = "تم تفعيل" if new_status else "تم إلغاء"
        await event.answer(f"✅ {status_text} الأزرار الشفافة!", alert=True)
        await self.show_buttons_menu(event)

    async def prompt_edit_button(self, event, button_num):
        """Prompt user to edit a specific button"""
        self.user_states[event.sender_id] = f'edit_button{button_num}_text'
        
        await event.edit(
            f"✏️ **تحرير الزر {button_num}**\n\n"
            f"📝 أرسل **نص الزر** الذي تريده:\n\n"
            f"💡 **أمثلة:**\n"
            f"• 📱 تابعنا على تيليجرام\n"
            f"• 🔗 الموقع الرسمي\n"
            f"• 📞 تواصل معنا\n"
            f"• ⬇️ تحميل التطبيق\n\n"
            f"🚫 **إلغاء:** /cancel",
            buttons=[[Button.inline("🚫 إلغاء", b"buttons_menu")]]
        )

    async def clear_all_buttons(self, event):
        """Clear all buttons"""
        await self.update_config('buttons_enabled', 'false')
        await self.update_config('button1_text', '')
        await self.update_config('button1_url', '')
        await self.update_config('button2_text', '')
        await self.update_config('button2_url', '')
        await self.update_config('button3_text', '')
        await self.update_config('button3_url', '')
        
        await event.answer("🗑️ تم حذف جميع الأزرار!", alert=True)
        await self.show_buttons_menu(event)

    async def preview_buttons(self, event):
        """Preview how buttons will look"""
        config = await self.get_current_config()
        
        buttons_enabled = config.getboolean('forwarding', 'buttons_enabled', fallback=False)
        
        if not buttons_enabled:
            await event.answer("❌ الأزرار غير مفعلة!", alert=True)
            return
        
        # Create preview buttons
        preview_buttons = []
        for i in range(1, 4):
            text = config.get('forwarding', f'button{i}_text', fallback='')
            url = config.get('forwarding', f'button{i}_url', fallback='')
            if text and url:
                preview_buttons.append([Button.url(text, url)])
        
        if not preview_buttons:
            await event.answer("❌ لا توجد أزرار محددة للمعاينة!", alert=True)
            return
        
        # Add back button
        preview_buttons.append([Button.inline("🔙 العودة", b"buttons_menu")])
        
        await event.edit(
            "👀 **معاينة الأزرار:**\n\n"
            "هكذا ستظهر الأزرار تحت كل رسالة مُرسلة:\n\n"
            "📝 **رسالة تجريبية**\n"
            "هذا مثال على كيفية ظهور الرسائل مع الأزرار",
            buttons=preview_buttons
        )

    async def process_button_text_input(self, event, button_num):
        """Process button text input"""
        text = event.text.strip()
        
        if text == '/cancel':
            if event.sender_id in self.user_states:
                del self.user_states[event.sender_id]
            await self.show_buttons_menu(event)
            return
        
        if len(text) > 50:
            await event.respond(
                "❌ **نص الزر طويل جداً!**\n\n"
                "📏 **الحد الأقصى:** 50 حرف\n"
                f"📊 **طول النص:** {len(text)} حرف\n\n"
                "✏️ **أرسل نص أقصر:**",
                buttons=[[Button.inline("🚫 إلغاء", b"buttons_menu")]]
            )
            return
        
        # Save text and ask for URL
        await self.update_config(f'button{button_num}_text', text)
        self.user_states[event.sender_id] = f'edit_button{button_num}_url'
        
        await event.respond(
            f"✅ **تم حفظ النص:** {text}\n\n"
            f"🔗 **الآن أرسل الرابط للزر:**\n\n"
            f"💡 **أمثلة على الروابط:**\n"
            f"• https://t.me/your_channel\n"
            f"• https://example.com\n"
            f"• https://wa.me/1234567890\n\n"
            f"🚫 **إلغاء:** /cancel",
            buttons=[[Button.inline("🚫 إلغاء", b"buttons_menu")]]
        )

    async def process_button_url_input(self, event, button_num):
        """Process button URL input"""
        url = event.text.strip()
        
        if url == '/cancel':
            if event.sender_id in self.user_states:
                del self.user_states[event.sender_id]
            await self.show_buttons_menu(event)
            return
        
        # Basic URL validation
        if not (url.startswith('http://') or url.startswith('https://') or url.startswith('t.me/')):
            await event.respond(
                "❌ **رابط غير صحيح!**\n\n"
                "📋 **الروابط المقبولة:**\n"
                "• https://example.com\n"
                "• http://example.com\n"
                "• t.me/channel_name\n\n"
                "🔗 **أرسل رابط صحيح:**",
                buttons=[[Button.inline("🚫 إلغاء", b"buttons_menu")]]
            )
            return
        
        # Fix t.me links
        if url.startswith('t.me/'):
            url = 'https://' + url
        
        # Save URL and enable buttons
        await self.update_config(f'button{button_num}_url', url)
        await self.update_config('buttons_enabled', 'true')
        
        # Clear user state
        if event.sender_id in self.user_states:
            del self.user_states[event.sender_id]
        
        config = await self.get_current_config()
        button_text = config.get('forwarding', f'button{button_num}_text', fallback='')
        
        await event.respond(
            f"🎉 **تم إنشاء الزر {button_num} بنجاح!**\n\n"
            f"📝 **النص:** {button_text}\n"
            f"🔗 **الرابط:** {url}\n\n"
            f"✅ **تم تفعيل الأزرار تلقائياً!**\n"
            f"🚀 **الزر سيظهر مع جميع الرسائل الجديدة**",
            buttons=[[Button.inline("🔙 العودة لإدارة الأزرار", b"buttons_menu")]]
        )

    async def show_text_replacer_menu(self, event):
        """Show text replacer main menu"""
        # Force reload config to get latest values
        config = await self.get_current_config()
        
        # Get current settings with fresh read
        replacer_enabled = config.getboolean('text_replacer', 'replacer_enabled', fallback=False)
        replacements = config.get('text_replacer', 'replacements', fallback='')
        
        # Count active replacements
        replacement_count = 0
        if replacements.strip():
            replacement_count = len([r for r in replacements.split(',') if '->' in r and r.split('->')[0].strip()])
        
        # Status function
        def get_status(enabled): 
            return "✅ مفعل" if enabled else "❌ معطل"
        
        # Add unique identifier to force message update
        import time
        current_time = int(time.time()) % 1000  # Last 3 digits of timestamp
        
        status_text = (
            f"🔄 **الاستبدال الذكي** `#{current_time}`\n\n"
            f"📊 **الحالة الحالية:**\n"
            f"🔄 الاستبدال: {get_status(replacer_enabled)}\n"
            f"📝 عدد الاستبدالات: {replacement_count}\n\n"
            f"💡 **الوظائف المتاحة:**\n"
            f"• تفعيل/تعطيل الاستبدال\n"
            f"• إضافة استبدالات جديدة\n"
            f"• عرض قائمة الاستبدالات\n"
            f"• حذف جميع الاستبدالات\n\n"
            f"📝 **تنسيق الاستبدال:**\n"
            f"`النص القديم->النص الجديد`\n"
            f"للحذف: `النص المراد حذفه->`"
        )
        
        keyboard = [
            [Button.inline(f"🔄 تبديل الحالة ({get_status(replacer_enabled)})", b"toggle_text_replacer")],
            [Button.inline("➕ إضافة استبدال", b"add_replacement"),
             Button.inline("👀 عرض القائمة", b"view_replacements")],
            [Button.inline("🗑️ مسح الكل", b"clear_replacements"),
             Button.inline("🔙 العودة", b"advanced_settings")]
        ]
        
        # Try edit first, if fails then send new message
        try:
            await event.edit(status_text, buttons=keyboard)
        except Exception:
            try:
                await event.respond(status_text, buttons=keyboard)
            except Exception:
                pass

    async def toggle_text_replacer(self, event):
        """Toggle text replacer on/off with complete refresh"""
        # Get current status
        config = await self.get_current_config()
        current_status = config.getboolean('text_replacer', 'replacer_enabled', fallback=False)
        new_status = not current_status
        
        # Update configuration
        await self.update_config('replacer_enabled', str(new_status).lower())
        
        # Show immediate feedback
        status_emoji = "✅" if new_status else "❌"
        await event.answer(f"🔄 تم تغيير حالة الاستبدال إلى {status_emoji}")
        
        # Wait for config to save and then refresh the entire menu
        import asyncio
        await asyncio.sleep(0.3)
        
        # Completely refresh the menu to show updated status
        await self.show_text_replacer_menu(event)

    async def prompt_add_replacement(self, event):
        """Prompt user to add a replacement"""
        self.user_states[event.sender_id] = 'awaiting_replacement'
        
        prompt_text = (
            "➕ **إضافة استبدال جديد**\n\n"
            "📝 **التنسيق المطلوب:**\n"
            "`النص القديم->النص الجديد`\n\n"
            "🔸 **أمثلة:**\n"
            "• `كلمة قديمة->كلمة جديدة`\n"
            "• `جملة كاملة->جملة محدثة`\n"
            "• `نص للحذف->` (للحذف)\n\n"
            "💡 **ملاحظات:**\n"
            "• يمكن إضافة عدة استبدالات بفاصلة\n"
            "• الاستبدال حساس للحروف الكبيرة والصغيرة\n"
            "• للحذف، اترك الجانب الأيمن فارغاً\n\n"
            "📤 **أرسل الاستبدال الآن:**"
        )
        
        keyboard = [[Button.inline("❌ إلغاء", b"text_replacer_menu")]]
        await event.edit(prompt_text, buttons=keyboard)

    async def process_replacement_input(self, event):
        """Process replacement input"""
        replacement_text = event.message.text.strip()
        
        try:
            # Get current replacements
            config = await self.get_current_config()
            current_replacements = config.get('text_replacer', 'replacements', fallback='')
            
            # Add new replacement
            if current_replacements.strip():
                new_replacements = f"{current_replacements},{replacement_text}"
            else:
                new_replacements = replacement_text
            
            await self.update_config('replacements', new_replacements)
            del self.user_states[event.sender_id]
            
            success_text = (
                f"✅ **تم إضافة الاستبدال بنجاح!**\n\n"
                f"📝 **الاستبدال المضاف:**\n`{replacement_text}`\n\n"
                f"💡 **تم حفظ الإعدادات تلقائياً**"
            )
            
            keyboard = [[Button.inline("🔙 العودة للقائمة", b"text_replacer_menu")]]
            await event.respond(success_text, buttons=keyboard)
            
        except Exception as e:
            await event.respond(f"❌ خطأ في حفظ الاستبدال: {e}")

    async def view_replacements(self, event):
        """View current replacements"""
        config = await self.get_current_config()
        replacements_str = config.get('text_replacer', 'replacements', fallback='')
        
        if not replacements_str.strip():
            replacements_text = (
                "📝 **قائمة الاستبدالات**\n\n"
                "🔍 **لا توجد استبدالات محفوظة**\n\n"
                "💡 استخدم 'إضافة استبدال' لإضافة استبدالات جديدة"
            )
        else:
            replacements_text = "📝 **قائمة الاستبدالات الحالية:**\n\n"
            
            replacements = replacements_str.split(',')
            for i, replacement in enumerate(replacements, 1):
                if '->' in replacement:
                    old_text, new_text = replacement.split('->', 1)
                    old_text = old_text.strip()
                    new_text = new_text.strip()
                    
                    if new_text:
                        replacements_text += f"{i}. `{old_text}` → `{new_text}`\n"
                    else:
                        replacements_text += f"{i}. `{old_text}` → 🗑️ **حذف**\n"
                else:
                    replacements_text += f"{i}. ⚠️ تنسيق خاطئ: `{replacement}`\n"
            
            replacements_text += "\n💡 **للتعديل:** امسح الكل وأضف مرة أخرى"
        
        keyboard = [
            [Button.inline("➕ إضافة استبدال", b"add_replacement"),
             Button.inline("🗑️ مسح الكل", b"clear_replacements")],
            [Button.inline("🔙 العودة", b"text_replacer_menu")]
        ]
        
        await event.edit(replacements_text, buttons=keyboard)

    async def clear_replacements(self, event):
        """Clear all replacements"""
        await self.update_config('replacements', '')
        
        success_text = (
            "🗑️ **تم مسح جميع الاستبدالات**\n\n"
            "✅ **تم حذف قائمة الاستبدالات بالكامل**\n\n"
            "💡 يمكنك إضافة استبدالات جديدة الآن"
        )
        
        keyboard = [
            [Button.inline("➕ إضافة استبدال", b"add_replacement")],
            [Button.inline("🔙 العودة للقائمة", b"text_replacer_menu")]
        ]
        
        await event.edit(success_text, buttons=keyboard)

    # Multi-Task Management Methods
    
    def get_multi_task_menu_keyboard(self):
        """Get multi-task management keyboard"""
        return [
            [Button.inline("📋 عرض المهام", b"view_tasks"),
             Button.inline("➕ إضافة مهمة", b"add_task")],
            [Button.inline("▶️ تشغيل مهمة", b"start_task"),
             Button.inline("⏹️ إيقاف مهمة", b"stop_task")],
            [Button.inline("🔄 إعادة تشغيل مهمة", b"restart_task"),
             Button.inline("🗑️ حذف مهمة", b"delete_task")],
            [Button.inline("📊 إحصائيات المهام", b"task_stats"),
             Button.inline("⚙️ إعدادات المهمة", b"edit_task")],
            [Button.inline("🏠 القائمة الرئيسية", b"main_menu")]
        ]
    
    async def show_multi_task_menu(self, event):
        """Show multi-task management menu"""
        try:
            # Get task statistics from userbot if available
            if self.forwarder_instance:
                task_stats = self.forwarder_instance.get_task_stats()
                total_tasks = len(task_stats)
                running_tasks = sum(1 for t in task_stats.values() if t['status'] == 'running')
                
                text = (
                    "🎯 **إدارة المهام المتعددة**\n\n"
                    f"📊 **إحصائيات سريعة:**\n"
                    f"• المهام الإجمالية: {total_tasks}\n"
                    f"• المهام النشطة: {running_tasks}\n"
                    f"• المهام المتوقفة: {total_tasks - running_tasks}\n\n"
                    "⚡ **الوظائف المتاحة:**\n"
                    "• إدارة مهام التوجيه\n"
                    "• مراقبة الأداء\n"
                    "• إعدادات فردية لكل مهمة"
                )
            else:
                text = (
                    "🎯 **إدارة المهام المتعددة**\n\n"
                    "⚠️ **البوت الأساسي غير متصل**\n\n"
                    "💡 يمكنك إعداد المهام، ولكن لن تعمل حتى يتم تشغيل البوت الأساسي"
                )
            
            await event.edit(text, buttons=self.get_multi_task_menu_keyboard())
            
        except Exception as e:
            await event.edit(f"❌ خطأ في عرض قائمة المهام: {e}")
    
    async def view_tasks(self, event):
        """View all steering tasks"""
        try:
            if not self.forwarder_instance:
                await event.edit(
                    "❌ **البوت الأساسي غير متصل**\n\n"
                    "يرجى تشغيل البوت الأساسي أولاً لعرض المهام",
                    buttons=[[Button.inline("🔙 العودة", b"multi_task_menu")]]
                )
                return
            
            task_stats = self.forwarder_instance.get_task_stats()
            
            if not task_stats:
                text = (
                    "📋 **قائمة المهام**\n\n"
                    "🔍 **لا توجد مهام محددة**\n\n"
                    "💡 استخدم 'إضافة مهمة' لإنشاء مهمة توجيه جديدة"
                )
            else:
                text = "📋 **قائمة مهام التوجيه**\n\n"
                
                for task_id, stats in task_stats.items():
                    status_emoji = "🟢" if stats['status'] == 'running' else "🔴"
                    text += f"{status_emoji} **{stats['name']}**\n"
                    text += f"   📥 من: `{stats['source_chat']}`\n"
                    text += f"   📤 إلى: `{stats['target_chat']}`\n"
                    
                    if stats['stats']:
                        task_data = stats['stats']
                        text += f"   📊 معالج: {task_data['messages_processed']}\n"
                        text += f"   ✅ موجه: {task_data['messages_forwarded']}\n"
                        text += f"   ❌ فشل: {task_data['messages_failed']}\n"
                    
                    text += "\n"
            
            keyboard = [
                [Button.inline("➕ إضافة مهمة", b"add_task"),
                 Button.inline("📊 إحصائيات تفصيلية", b"task_stats")],
                [Button.inline("🔙 العودة", b"multi_task_menu")]
            ]
            
            await event.edit(text, buttons=keyboard)
            
        except Exception as e:
            await event.edit(f"❌ خطأ في عرض المهام: {e}")
    
    async def show_task_stats(self, event):
        """Show detailed task statistics"""
        try:
            if not self.forwarder_instance:
                await event.edit(
                    "❌ **البوت الأساسي غير متصل**",
                    buttons=[[Button.inline("🔙 العودة", b"multi_task_menu")]]
                )
                return
            
            task_stats = self.forwarder_instance.get_task_stats()
            
            if not task_stats:
                text = "📊 **لا توجد مهام للإحصائيات**"
            else:
                text = "📊 **إحصائيات مفصلة للمهام**\n\n"
                
                total_processed = 0
                total_forwarded = 0
                total_failed = 0
                
                for task_id, stats in task_stats.items():
                    if stats['stats']:
                        task_data = stats['stats']
                        total_processed += task_data['messages_processed']
                        total_forwarded += task_data['messages_forwarded']
                        total_failed += task_data['messages_failed']
                
                success_rate = (total_forwarded / total_processed * 100) if total_processed > 0 else 0
                
                text += f"🎯 **الإحصائيات الإجمالية:**\n"
                text += f"📝 الرسائل المعالجة: {total_processed}\n"
                text += f"✅ الرسائل الموجهة: {total_forwarded}\n"
                text += f"❌ الرسائل الفاشلة: {total_failed}\n"
                text += f"📈 معدل النجاح: {success_rate:.1f}%\n\n"
                
                text += "📋 **تفاصيل كل مهمة:**\n\n"
                
                for task_id, stats in task_stats.items():
                    status_emoji = "🟢" if stats['status'] == 'running' else "🔴"
                    text += f"{status_emoji} **{stats['name']}**\n"
                    
                    if stats['stats']:
                        task_data = stats['stats']
                        task_success_rate = (task_data['messages_forwarded'] / task_data['messages_processed'] * 100) if task_data['messages_processed'] > 0 else 0
                        text += f"   📊 معدل النجاح: {task_success_rate:.1f}%\n"
                        text += f"   📝 معالج: {task_data['messages_processed']}\n"
                        text += f"   ✅ موجه: {task_data['messages_forwarded']}\n"
                        text += f"   ❌ فشل: {task_data['messages_failed']}\n"
                        
                        if task_data['last_activity']:
                            from datetime import datetime
                            last_activity = datetime.fromisoformat(task_data['last_activity']).strftime("%H:%M:%S")
                            text += f"   🕒 آخر نشاط: {last_activity}\n"
                    else:
                        text += "   📊 لا توجد إحصائيات (متوقف)\n"
                    
                    text += "\n"
            
            keyboard = [[Button.inline("🔄 تحديث", b"task_stats"),
                        Button.inline("🔙 العودة", b"multi_task_menu")]]
            
            await event.edit(text, buttons=keyboard)
            
        except Exception as e:
            await event.edit(f"❌ خطأ في عرض الإحصائيات: {e}")
    
    async def prompt_add_task(self, event):
        """Prompt user to add a new task"""
        self.user_states[event.sender_id] = "waiting_task_name"
        
        text = (
            "➕ **إضافة مهمة توجيه جديدة**\n\n"
            "📝 **الخطوة 1: اسم المهمة**\n\n"
            "أرسل اسماً وصفياً للمهمة الجديدة:\n\n"
            "💡 **أمثلة:**\n"
            "• توجيه الأخبار\n"
            "• نسخ المحتوى التقني\n"
            "• توجيه من قناة A إلى قناة B\n\n"
            "🚫 **إلغاء:** أرسل 'إلغاء'"
        )
        
        keyboard = [[Button.inline("❌ إلغاء", b"multi_task_menu")]]
        await event.edit(text, buttons=keyboard)
    
    async def process_task_creation(self, event):
        """Process task creation steps"""
        user_id = event.sender_id
        state = self.user_states.get(user_id, "")
        text = event.text.strip()
        
        if text.lower() == 'إلغاء':
            if user_id in self.user_states:
                del self.user_states[user_id]
            await self.show_multi_task_menu(event)
            return
        
        try:
            if state == "waiting_task_name":
                # Store task name and ask for source
                if not hasattr(self, 'temp_task_data'):
                    self.temp_task_data = {}
                
                self.temp_task_data[user_id] = {'name': text}
                self.user_states[user_id] = "waiting_task_source"
                
                await event.respond(
                    f"✅ **اسم المهمة:** {text}\n\n"
                    "📥 **الخطوة 2: القناة المصدر**\n\n"
                    "أرسل معرف أو رابط القناة المصدر:\n\n"
                    "💡 **تنسيقات مقبولة:**\n"
                    "• معرف رقمي: `-1001234567890`\n"
                    "• اسم مستخدم: `@channel_name`\n"
                    "• رابط: `https://t.me/channel_name`\n\n"
                    "🚫 **إلغاء:** أرسل 'إلغاء'"
                )
            
            elif state == "waiting_task_source":
                # Store source and ask for target
                self.temp_task_data[user_id]['source_chat'] = text
                self.user_states[user_id] = "waiting_task_target"
                
                await event.respond(
                    f"✅ **القناة المصدر:** `{text}`\n\n"
                    "📤 **الخطوة 3: القناة الهدف**\n\n"
                    "أرسل معرف أو رابط القناة الهدف:\n\n"
                    "💡 **تنسيقات مقبولة:**\n"
                    "• معرف رقمي: `-1001234567890`\n"
                    "• اسم مستخدم: `@channel_name`\n"
                    "• رابط: `https://t.me/channel_name`\n\n"
                    "🚫 **إلغاء:** أرسل 'إلغاء'"
                )
            
            elif state == "waiting_task_target":
                # Complete task creation
                self.temp_task_data[user_id]['target_chat'] = text
                await self.create_new_task(event, user_id)
            
        except Exception as e:
            await event.respond(f"❌ خطأ في إنشاء المهمة: {e}")
            if user_id in self.user_states:
                del self.user_states[user_id]
    
    async def create_new_task(self, event, user_id):
        """Create a new steering task"""
        try:
            task_data = self.temp_task_data[user_id]
            
            # Generate unique task ID
            import time
            import uuid
            task_id = f"task_{int(time.time())}_{str(uuid.uuid4())[:8]}"
            
            # Create task configuration
            from userbot import SteeringTaskConfig
            config = SteeringTaskConfig(
                task_id=task_id,
                name=task_data['name'],
                source_chat=task_data['source_chat'],
                target_chat=task_data['target_chat'],
                enabled=True
            )
            
            # Add task to forwarder if available
            if self.forwarder_instance:
                self.forwarder_instance.add_steering_task(config)
                
                # Try to start the task
                success = await self.forwarder_instance.start_steering_task(task_id)
                status_text = "✅ تم إنشاء وتشغيل المهمة" if success else "⚠️ تم إنشاء المهمة ولكن فشل في التشغيل"
            else:
                status_text = "✅ تم إنشاء المهمة (ستعمل عند تشغيل البوت الأساسي)"
            
            # Clean up
            del self.temp_task_data[user_id]
            del self.user_states[user_id]
            
            # Show success message
            text = (
                f"🎉 **{status_text}**\n\n"
                f"📝 **اسم المهمة:** {task_data['name']}\n"
                f"📥 **المصدر:** `{task_data['source_chat']}`\n"
                f"📤 **الهدف:** `{task_data['target_chat']}`\n"
                f"🆔 **معرف المهمة:** `{task_id}`\n\n"
                "🚀 **المهمة جاهزة للعمل!**"
            )
            
            keyboard = [
                [Button.inline("📋 عرض المهام", b"view_tasks")],
                [Button.inline("🔙 إدارة المهام", b"multi_task_menu")]
            ]
            
            await event.respond(text, buttons=keyboard)
            
        except Exception as e:
            await event.respond(f"❌ خطأ في إنشاء المهمة: {e}")
            if user_id in self.user_states:
                del self.user_states[user_id]
    
    async def prompt_start_task(self, event):
        """Prompt user to select a task to start"""
        try:
            if not self.forwarder_instance:
                await event.edit(
                    "❌ **البوت الأساسي غير متصل**\n\n"
                    "يرجى تشغيل البوت الأساسي أولاً",
                    buttons=[[Button.inline("🔙 العودة", b"multi_task_menu")]]
                )
                return
            
            task_stats = self.forwarder_instance.get_task_stats()
            
            if not task_stats:
                await event.edit(
                    "❌ **لا توجد مهام للتشغيل**\n\n"
                    "استخدم 'إضافة مهمة' لإنشاء مهمة جديدة",
                    buttons=[[Button.inline("🔙 العودة", b"multi_task_menu")]]
                )
                return
            
            # Show stopped tasks only
            stopped_tasks = {k: v for k, v in task_stats.items() if v['status'] != 'running'}
            
            if not stopped_tasks:
                await event.edit(
                    "✅ **جميع المهام تعمل بالفعل**\n\n"
                    "لا توجد مهام متوقفة للتشغيل",
                    buttons=[[Button.inline("🔙 العودة", b"multi_task_menu")]]
                )
                return
            
            text = "▶️ **تشغيل مهمة**\n\n🔍 **اختر مهمة للتشغيل:**\n\n"
            
            keyboard = []
            for task_id, stats in stopped_tasks.items():
                task_name = stats['name'][:20] + "..." if len(stats['name']) > 20 else stats['name']
                keyboard.append([Button.inline(f"▶️ {task_name}", f"start_specific_{task_id}".encode())])
            
            keyboard.append([Button.inline("🔙 العودة", b"multi_task_menu")])
            
            for task_id, stats in stopped_tasks.items():
                text += f"🔴 **{stats['name']}**\n"
                text += f"   📥 من: `{stats['source_chat']}`\n"
                text += f"   📤 إلى: `{stats['target_chat']}`\n\n"
            
            await event.edit(text, buttons=keyboard)
            
        except Exception as e:
            await event.edit(f"❌ خطأ في عرض المهام: {e}")

    async def prompt_stop_task(self, event):
        """Prompt user to select a task to stop"""
        try:
            if not self.forwarder_instance:
                await event.edit(
                    "❌ **البوت الأساسي غير متصل**",
                    buttons=[[Button.inline("🔙 العودة", b"multi_task_menu")]]
                )
                return
            
            task_stats = self.forwarder_instance.get_task_stats()
            
            if not task_stats:
                await event.edit(
                    "❌ **لا توجد مهام للإيقاف**",
                    buttons=[[Button.inline("🔙 العودة", b"multi_task_menu")]]
                )
                return
            
            # Show running tasks only
            running_tasks = {k: v for k, v in task_stats.items() if v['status'] == 'running'}
            
            if not running_tasks:
                await event.edit(
                    "❌ **لا توجد مهام تعمل حالياً**\n\n"
                    "جميع المهام متوقفة بالفعل",
                    buttons=[[Button.inline("🔙 العودة", b"multi_task_menu")]]
                )
                return
            
            text = "⏹️ **إيقاف مهمة**\n\n🔍 **اختر مهمة لإيقافها:**\n\n"
            
            keyboard = []
            for task_id, stats in running_tasks.items():
                task_name = stats['name'][:20] + "..." if len(stats['name']) > 20 else stats['name']
                keyboard.append([Button.inline(f"⏹️ {task_name}", f"stop_specific_{task_id}".encode())])
            
            keyboard.append([Button.inline("🔙 العودة", b"multi_task_menu")])
            
            for task_id, stats in running_tasks.items():
                text += f"🟢 **{stats['name']}**\n"
                text += f"   📥 من: `{stats['source_chat']}`\n"
                text += f"   📤 إلى: `{stats['target_chat']}`\n\n"
            
            await event.edit(text, buttons=keyboard)
            
        except Exception as e:
            await event.edit(f"❌ خطأ في عرض المهام: {e}")

    async def prompt_restart_task(self, event):
        """Prompt user to select a task to restart"""
        try:
            if not self.forwarder_instance:
                await event.edit(
                    "❌ **البوت الأساسي غير متصل**",
                    buttons=[[Button.inline("🔙 العودة", b"multi_task_menu")]]
                )
                return
            
            task_stats = self.forwarder_instance.get_task_stats()
            
            if not task_stats:
                await event.edit(
                    "❌ **لا توجد مهام لإعادة التشغيل**",
                    buttons=[[Button.inline("🔙 العودة", b"multi_task_menu")]]
                )
                return
            
            text = "🔄 **إعادة تشغيل مهمة**\n\n🔍 **اختر مهمة لإعادة تشغيلها:**\n\n"
            
            keyboard = []
            for task_id, stats in task_stats.items():
                task_name = stats['name'][:20] + "..." if len(stats['name']) > 20 else stats['name']
                status_emoji = "🟢" if stats['status'] == 'running' else "🔴"
                keyboard.append([Button.inline(f"🔄 {task_name}", f"restart_specific_{task_id}".encode())])
            
            keyboard.append([Button.inline("🔙 العودة", b"multi_task_menu")])
            
            for task_id, stats in task_stats.items():
                status_emoji = "🟢" if stats['status'] == 'running' else "🔴"
                text += f"{status_emoji} **{stats['name']}**\n"
                text += f"   📥 من: `{stats['source_chat']}`\n"
                text += f"   📤 إلى: `{stats['target_chat']}`\n\n"
            
            await event.edit(text, buttons=keyboard)
            
        except Exception as e:
            await event.edit(f"❌ خطأ في عرض المهام: {e}")

    async def prompt_delete_task(self, event):
        """Prompt user to select a task to delete"""
        try:
            if not self.forwarder_instance:
                await event.edit(
                    "❌ **البوت الأساسي غير متصل**",
                    buttons=[[Button.inline("🔙 العودة", b"multi_task_menu")]]
                )
                return
            
            task_stats = self.forwarder_instance.get_task_stats()
            
            if not task_stats:
                await event.edit(
                    "❌ **لا توجد مهام للحذف**",
                    buttons=[[Button.inline("🔙 العودة", b"multi_task_menu")]]
                )
                return
            
            text = "🗑️ **حذف مهمة**\n\n⚠️ **تحذير:** الحذف نهائي ولا يمكن التراجع\n\n🔍 **اختر مهمة للحذف:**\n\n"
            
            keyboard = []
            for task_id, stats in task_stats.items():
                task_name = stats['name'][:20] + "..." if len(stats['name']) > 20 else stats['name']
                status_emoji = "🟢" if stats['status'] == 'running' else "🔴"
                keyboard.append([Button.inline(f"🗑️ {task_name}", f"confirm_delete_{task_id}".encode())])
            
            keyboard.append([Button.inline("🔙 العودة", b"multi_task_menu")])
            
            for task_id, stats in task_stats.items():
                status_emoji = "🟢" if stats['status'] == 'running' else "🔴"
                text += f"{status_emoji} **{stats['name']}**\n"
                text += f"   📥 من: `{stats['source_chat']}`\n"
                text += f"   📤 إلى: `{stats['target_chat']}`\n\n"
            
            await event.edit(text, buttons=keyboard)
            
        except Exception as e:
            await event.edit(f"❌ خطأ في عرض المهام: {e}")

    async def prompt_edit_task(self, event):
        """Prompt user to select a task to edit settings"""
        try:
            if not self.forwarder_instance:
                await event.edit(
                    "❌ **البوت الأساسي غير متصل**",
                    buttons=[[Button.inline("🔙 العودة", b"multi_task_menu")]]
                )
                return
            
            task_stats = self.forwarder_instance.get_task_stats()
            
            if not task_stats:
                await event.edit(
                    "❌ **لا توجد مهام للتعديل**",
                    buttons=[[Button.inline("🔙 العودة", b"multi_task_menu")]]
                )
                return
            
            text = "⚙️ **إعدادات المهمة**\n\n🔍 **اختر مهمة لتعديل إعداداتها:**\n\n"
            
            keyboard = []
            for task_id, stats in task_stats.items():
                task_name = stats['name'][:20] + "..." if len(stats['name']) > 20 else stats['name']
                status_emoji = "🟢" if stats['status'] == 'running' else "🔴"
                keyboard.append([Button.inline(f"⚙️ {task_name}", f"edit_specific_{task_id}".encode())])
            
            keyboard.append([Button.inline("🔙 العودة", b"multi_task_menu")])
            
            for task_id, stats in task_stats.items():
                status_emoji = "🟢" if stats['status'] == 'running' else "🔴"
                text += f"{status_emoji} **{stats['name']}**\n"
                text += f"   📥 من: `{stats['source_chat']}`\n"
                text += f"   📤 إلى: `{stats['target_chat']}`\n\n"
            
            await event.edit(text, buttons=keyboard)
            
        except Exception as e:
            await event.edit(f"❌ خطأ في عرض المهام: {e}")

    async def start_specific_task(self, event, task_id):
        """Start a specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            success = await self.forwarder_instance.start_steering_task(task_id)
            
            if success:
                await event.answer("✅ تم تشغيل المهمة بنجاح", alert=False)
                # Refresh the view
                await self.view_tasks(event)
            else:
                await event.answer("❌ فشل في تشغيل المهمة", alert=True)
                
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    async def stop_specific_task(self, event, task_id):
        """Stop a specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            success = await self.forwarder_instance.stop_steering_task(task_id)
            
            if success:
                await event.answer("✅ تم إيقاف المهمة بنجاح", alert=False)
                # Refresh the view
                await self.view_tasks(event)
            else:
                await event.answer("❌ فشل في إيقاف المهمة", alert=True)
                
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    async def restart_specific_task(self, event, task_id):
        """Restart a specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            # First stop, then start
            await self.forwarder_instance.stop_steering_task(task_id)
            import asyncio
            await asyncio.sleep(1)  # Small delay
            success = await self.forwarder_instance.start_steering_task(task_id)
            
            if success:
                await event.answer("🔄 تم إعادة تشغيل المهمة بنجاح", alert=False)
                # Refresh the view
                await self.view_tasks(event)
            else:
                await event.answer("❌ فشل في إعادة تشغيل المهمة", alert=True)
                
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    async def confirm_delete_task(self, event, task_id):
        """Confirm task deletion"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            task_stats = self.forwarder_instance.get_task_stats()
            task_info = task_stats.get(task_id)
            
            if not task_info:
                await event.answer("❌ المهمة غير موجودة", alert=True)
                return
            
            text = (
                f"⚠️ **تأكيد حذف المهمة**\n\n"
                f"📝 **اسم المهمة:** {task_info['name']}\n"
                f"📥 **المصدر:** `{task_info['source_chat']}`\n"
                f"📤 **الهدف:** `{task_info['target_chat']}`\n\n"
                f"🚨 **تحذير:** هذا الإجراء نهائي ولا يمكن التراجع عنه!\n\n"
                f"❓ **هل أنت متأكد من حذف هذه المهمة؟**"
            )
            
            keyboard = [
                [Button.inline("🗑️ نعم، احذف المهمة", f"delete_confirmed_{task_id}".encode()),
                 Button.inline("❌ إلغاء", b"multi_task_menu")]
            ]
            
            await event.edit(text, buttons=keyboard)
            
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    async def delete_task_confirmed(self, event, task_id):
        """Execute task deletion after confirmation"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            # First stop the task if it's running
            await self.forwarder_instance.stop_steering_task(task_id)
            
            # Then delete it
            success = self.forwarder_instance.remove_steering_task(task_id)
            
            if success:
                text = (
                    "✅ **تم حذف المهمة بنجاح**\n\n"
                    "🗑️ تم حذف المهمة وجميع إعداداتها نهائياً\n\n"
                    "💡 يمكنك إنشاء مهمة جديدة في أي وقت"
                )
                
                keyboard = [
                    [Button.inline("➕ إضافة مهمة جديدة", b"add_task")],
                    [Button.inline("📋 عرض المهام", b"view_tasks"),
                     Button.inline("🔙 القائمة الرئيسية", b"multi_task_menu")]
                ]
                
                await event.edit(text, buttons=keyboard)
            else:
                await event.answer("❌ فشل في حذف المهمة", alert=True)
                await self.show_multi_task_menu(event)
                
        except Exception as e:
            await event.answer(f"❌ خطأ في حذف المهمة: {e}", alert=True)

    async def set_forwarder_instance(self, forwarder):
        """Set reference to the forwarder instance"""
        self.forwarder_instance = forwarder
        self.logger.info("Forwarder instance connected to control bot")

    async def run_until_disconnected(self):
        """Keep the bot running"""
        await self.client.run_until_disconnected()

    async def edit_specific_task(self, event, task_id):
        """Edit settings for a specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            task_stats = self.forwarder_instance.get_task_stats()
            task_info = task_stats.get(task_id)
            
            if not task_info:
                await event.answer("❌ المهمة غير موجودة", alert=True)
                return
            
            # Get task configuration if available
            task_config = self.forwarder_instance.get_task_config(task_id)
            
            status_emoji = "🟢" if task_info['status'] == 'running' else "🔴"
            
            text = (
                f"⚙️ **إعدادات المهمة**\n\n"
                f"📝 **اسم المهمة:** {task_info['name']}\n"
                f"📊 **الحالة:** {status_emoji} {task_info['status']}\n"
                f"📥 **المصدر:** `{task_info['source_chat']}`\n"
                f"📤 **الهدف:** `{task_info['target_chat']}`\n\n"
                f"🔧 **الإعدادات المتاحة:**"
            )
            
            keyboard = [
                # المجموعة الأولى: الإعدادات الأساسية
                [Button.inline("⚙️ وضع التوجيه", f"edit_forward_mode_{task_id}".encode()),
                 Button.inline("📥 تغيير المصدر", f"edit_source_{task_id}".encode())],
                [Button.inline("📤 تغيير الهدف", f"edit_target_{task_id}".encode()),
                 Button.inline("📝 تغيير الاسم", f"edit_task_name_{task_id}".encode())],
                
                # المجموعة الثانية: الفلاتر المتقدمة
                [Button.inline("🎛️ فلاتر الوسائط", f"edit_media_filters_{task_id}".encode()),
                 Button.inline("🌐 فلتر اللغة", f"edit_language_filter_{task_id}".encode())],
                [Button.inline("🔗 فلتر الروابط", f"edit_link_filter_{task_id}".encode()),
                 Button.inline("↩️ فلتر المعاد توجيهها", f"edit_forwarded_filter_{task_id}".encode())],
                [Button.inline("👥 فلتر المشرفين", f"edit_admin_filter_{task_id}".encode()),
                 Button.inline("📏 فلتر حد الأحرف", f"edit_char_limit_{task_id}".encode())],
                [Button.inline("🔄 فلتر التكرار", f"edit_duplicate_filter_{task_id}".encode()),
                 Button.inline("🔘 فلتر الأزرار الشفافة", f"edit_transparent_buttons_{task_id}".encode())],
                
                # المجموعة الثالثة: معالجة المحتوى
                [Button.inline("🧹 منظف النصوص", f"edit_text_cleaner_{task_id}".encode()),
                 Button.inline("🎨 تنسيق الرسائل", f"edit_message_formatting_{task_id}".encode())],
                [Button.inline("🔄 الاستبدال الذكي", f"edit_smart_replacer_{task_id}".encode()),
                 Button.inline("🔘 الأزرار المخصصة", f"edit_custom_buttons_{task_id}".encode())],
                [Button.inline("📝 رأس وتذييل", f"edit_header_footer_{task_id}".encode()),
                 Button.inline("🔗 معاينة الروابط", f"edit_link_preview_{task_id}".encode())],
                
                # المجموعة الرابعة: قوائم التحكم
                [Button.inline("✅ قائمة السماح", f"edit_allow_list_{task_id}".encode()),
                 Button.inline("🚫 قائمة الحظر", f"edit_block_list_{task_id}".encode())],
                
                # المجموعة الخامسة: التوقيت والتزامن
                [Button.inline("⏱️ تأخير الرسائل", f"edit_message_delay_{task_id}".encode()),
                 Button.inline("🔄 تأخير التوجيه", f"edit_forward_delay_{task_id}".encode())],
                [Button.inline("🔔 إعدادات الإشعارات", f"edit_notification_settings_{task_id}".encode()),
                 Button.inline("🔗 مزامنة التعديل/الحذف", f"edit_sync_settings_{task_id}".encode())],
                
                # المجموعة السادسة: إعدادات خاصة
                [Button.inline("💬 المحافظة على الردود", f"edit_reply_preservation_{task_id}".encode()),
                 Button.inline("📌 تثبيت الرسائل", f"edit_pin_messages_{task_id}".encode())],
                [Button.inline("🎯 نوع التوجيه", f"edit_forwarding_type_{task_id}".encode())],
                
                [Button.inline("🔙 العودة", b"multi_task_menu")]
            ]
            
            await event.edit(text, buttons=keyboard)
            
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    async def edit_task_forward_mode(self, event, task_id):
        """Edit forward mode for specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            task_config = self.forwarder_instance.get_task_config(task_id)
            if not task_config:
                await event.answer("❌ المهمة غير موجودة", alert=True)
                return
            
            current_mode = task_config.forward_mode
            
            text = (
                f"⚙️ **وضع التوجيه للمهمة**\n\n"
                f"📝 **المهمة:** {task_config.name}\n"
                f"🔧 **الوضع الحالي:** {current_mode}\n\n"
                f"💡 **اختر وضع التوجيه:**\n"
                f"📤 **Forward:** إعادة توجيه مباشر (يظهر \"Forwarded from\")\n"
                f"📝 **Copy:** نسخ المحتوى (كرسالة جديدة)\n"
            )
            
            keyboard = [
                [Button.inline("📤 Forward Mode", f"set_forward_mode_{task_id}_forward".encode()),
                 Button.inline("📝 Copy Mode", f"set_forward_mode_{task_id}_copy".encode())],
                [Button.inline("🔙 العودة لإعدادات المهمة", f"edit_specific_{task_id}".encode())]
            ]
            
            await event.edit(text, buttons=keyboard)
            
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    async def edit_task_media_filters(self, event, task_id):
        """Edit media filters for specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            task_config = self.forwarder_instance.get_task_config(task_id)
            if not task_config:
                await event.answer("❌ المهمة غير موجودة", alert=True)
                return
            
            def get_status_emoji(enabled):
                return "✅" if enabled else "❌"
            
            text = (
                f"🎛️ **فلاتر الوسائط للمهمة**\n\n"
                f"📝 **المهمة:** {task_config.name}\n\n"
                f"📱 **أنواع الوسائط:**\n"
                f"{get_status_emoji(task_config.forward_photos)} الصور\n"
                f"{get_status_emoji(task_config.forward_videos)} الفيديو\n"
                f"{get_status_emoji(task_config.forward_music)} الموسيقى\n"
                f"{get_status_emoji(task_config.forward_audio)} الصوت\n"
                f"{get_status_emoji(task_config.forward_voice)} الرسائل الصوتية\n"
                f"{get_status_emoji(task_config.forward_video_messages)} فيديو دائري\n"
                f"{get_status_emoji(task_config.forward_files)} الملفات\n"
                f"{get_status_emoji(task_config.forward_gifs)} الصور المتحركة\n"
                f"{get_status_emoji(task_config.forward_stickers)} الملصقات\n"
                f"{get_status_emoji(task_config.forward_text)} النصوص\n"
            )
            
            keyboard = [
                [Button.inline(f"📷 الصور {get_status_emoji(task_config.forward_photos)}", f"toggle_task_media_{task_id}_photos".encode()),
                 Button.inline(f"🎥 الفيديو {get_status_emoji(task_config.forward_videos)}", f"toggle_task_media_{task_id}_videos".encode())],
                [Button.inline(f"🎵 الموسيقى {get_status_emoji(task_config.forward_music)}", f"toggle_task_media_{task_id}_music".encode()),
                 Button.inline(f"🔊 الصوت {get_status_emoji(task_config.forward_audio)}", f"toggle_task_media_{task_id}_audio".encode())],
                [Button.inline(f"🎤 رسائل صوتية {get_status_emoji(task_config.forward_voice)}", f"toggle_task_media_{task_id}_voice".encode()),
                 Button.inline(f"📹 فيديو دائري {get_status_emoji(task_config.forward_video_messages)}", f"toggle_task_media_{task_id}_video_messages".encode())],
                [Button.inline(f"📁 الملفات {get_status_emoji(task_config.forward_files)}", f"toggle_task_media_{task_id}_files".encode()),
                 Button.inline(f"🎭 الملصقات {get_status_emoji(task_config.forward_stickers)}", f"toggle_task_media_{task_id}_stickers".encode())],
                [Button.inline(f"📝 النصوص {get_status_emoji(task_config.forward_text)}", f"toggle_task_media_{task_id}_text".encode()),
                 Button.inline(f"🎞️ الصور المتحركة {get_status_emoji(task_config.forward_gifs)}", f"toggle_task_media_{task_id}_gifs".encode())],
                [Button.inline("🔙 العودة لإعدادات المهمة", f"edit_specific_{task_id}".encode())]
            ]
            
            await event.edit(text, buttons=keyboard)
            
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    async def edit_task_text_cleaner(self, event, task_id):
        """Edit text cleaner settings for specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            task_config = self.forwarder_instance.get_task_config(task_id)
            if not task_config:
                await event.answer("❌ المهمة غير موجودة", alert=True)
                return
            
            def get_status_emoji(enabled):
                return "✅" if enabled else "❌"
            
            text = (
                f"🧹 **منظف النصوص للمهمة**\n\n"
                f"📝 **المهمة:** {task_config.name}\n\n"
                f"🔧 **خيارات التنظيف:**\n"
                f"{get_status_emoji(task_config.clean_links)} حذف الروابط\n"
                f"{get_status_emoji(task_config.clean_hashtags)} حذف الهاشتاغ\n"
                f"{get_status_emoji(task_config.clean_formatting)} حذف التنسيق\n"
                f"{get_status_emoji(task_config.clean_empty_lines)} حذف الأسطر الفارغة\n"
                f"{get_status_emoji(task_config.clean_lines_with_words)} حذف أسطر بكلمات محددة\n"
            )
            
            keyboard = [
                [Button.inline(f"🔗 الروابط {get_status_emoji(task_config.clean_links)}", f"toggle_task_clean_{task_id}_links".encode()),
                 Button.inline(f"# الهاشتاغ {get_status_emoji(task_config.clean_hashtags)}", f"toggle_task_clean_{task_id}_hashtags".encode())],
                [Button.inline(f"🎨 التنسيق {get_status_emoji(task_config.clean_formatting)}", f"toggle_task_clean_{task_id}_formatting".encode()),
                 Button.inline(f"📄 الأسطر الفارغة {get_status_emoji(task_config.clean_empty_lines)}", f"toggle_task_clean_{task_id}_empty_lines".encode())],
                [Button.inline(f"🚫 كلمات محددة {get_status_emoji(task_config.clean_lines_with_words)}", f"toggle_task_clean_{task_id}_words".encode())],
                [Button.inline("📝 تعديل الكلمات المحظورة", f"edit_task_clean_words_{task_id}".encode())],
                [Button.inline("🔙 العودة لإعدادات المهمة", f"edit_specific_{task_id}".encode())]
            ]
            
            await event.edit(text, buttons=keyboard)
            
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    async def edit_task_smart_replacer(self, event, task_id):
        """Edit smart text replacer for specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            task_config = self.forwarder_instance.get_task_config(task_id)
            if not task_config:
                await event.answer("❌ المهمة غير موجودة", alert=True)
                return
            
            def get_status_emoji(enabled):
                return "✅" if enabled else "❌"
            
            replacements_text = "لا توجد استبدالات"
            if task_config.replacements:
                replacements_list = [r.strip() for r in task_config.replacements.split(',') if r.strip() and '->' in r]
                if replacements_list:
                    replacements_text = "\n".join([f"• {r}" for r in replacements_list[:5]])
                    if len(replacements_list) > 5:
                        replacements_text += f"\n... و {len(replacements_list) - 5} أخرى"
            
            text = (
                f"🔄 **الاستبدال الذكي للمهمة**\n\n"
                f"📝 **المهمة:** {task_config.name}\n"
                f"🔧 **الحالة:** {get_status_emoji(task_config.replacer_enabled)}\n\n"
                f"📋 **الاستبدالات الحالية:**\n{replacements_text}\n\n"
                f"💡 **تنسيق الاستبدال:** نص قديم -> نص جديد"
            )
            
            keyboard = [
                [Button.inline(f"⚡ تفعيل/إلغاء {get_status_emoji(task_config.replacer_enabled)}", f"toggle_task_replacer_{task_id}".encode())],
                [Button.inline("➕ إضافة استبدال", f"add_task_replacement_{task_id}".encode()),
                 Button.inline("📋 عرض الاستبدالات", f"view_task_replacements_{task_id}".encode())],
                [Button.inline("🗑️ حذف جميع الاستبدالات", f"clear_task_replacements_{task_id}".encode())],
                [Button.inline("🔙 العودة لإعدادات المهمة", f"edit_specific_{task_id}".encode())]
            ]
            
            await event.edit(text, buttons=keyboard)
            
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    async def edit_task_custom_buttons(self, event, task_id):
        """Edit custom buttons for specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            task_config = self.forwarder_instance.get_task_config(task_id)
            if not task_config:
                await event.answer("❌ المهمة غير موجودة", alert=True)
                return
            
            def get_status_emoji(enabled):
                return "✅" if enabled else "❌"
            
            def get_button_status(text, url):
                if text and url:
                    return f"✅ {text[:15]}..."
                return "❌ غير مُعد"
            
            text = (
                f"🔘 **الأزرار المخصصة للمهمة**\n\n"
                f"📝 **المهمة:** {task_config.name}\n"
                f"🔧 **الحالة:** {get_status_emoji(task_config.buttons_enabled)}\n\n"
                f"🔘 **الأزرار الحالية:**\n"
                f"1️⃣ {get_button_status(task_config.button1_text, task_config.button1_url)}\n"
                f"2️⃣ {get_button_status(task_config.button2_text, task_config.button2_url)}\n"
                f"3️⃣ {get_button_status(task_config.button3_text, task_config.button3_url)}\n"
            )
            
            keyboard = [
                [Button.inline(f"⚡ تفعيل/إلغاء {get_status_emoji(task_config.buttons_enabled)}", f"toggle_task_buttons_{task_id}".encode())],
                [Button.inline("1️⃣ تعديل الزر الأول", f"edit_task_button_{task_id}_1".encode()),
                 Button.inline("2️⃣ تعديل الزر الثاني", f"edit_task_button_{task_id}_2".encode())],
                [Button.inline("3️⃣ تعديل الزر الثالث", f"edit_task_button_{task_id}_3".encode())],
                [Button.inline("🗑️ حذف جميع الأزرار", f"clear_task_buttons_{task_id}".encode())],
                [Button.inline("👀 معاينة الأزرار", f"preview_task_buttons_{task_id}".encode())],
                [Button.inline("🔙 العودة لإعدادات المهمة", f"edit_specific_{task_id}".encode())]
            ]
            
            await event.edit(text, buttons=keyboard)
            
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    async def edit_task_header_footer(self, event, task_id):
        """Edit header and footer for specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            task_config = self.forwarder_instance.get_task_config(task_id)
            if not task_config:
                await event.answer("❌ المهمة غير موجودة", alert=True)
                return
            
            def get_status_emoji(enabled):
                return "✅" if enabled else "❌"
            
            header_preview = task_config.header_text[:30] + "..." if len(task_config.header_text) > 30 else task_config.header_text
            footer_preview = task_config.footer_text[:30] + "..." if len(task_config.footer_text) > 30 else task_config.footer_text
            
            text = (
                f"📝 **رأس وتذييل للمهمة**\n\n"
                f"📝 **المهمة:** {task_config.name}\n\n"
                f"📤 **الرأس (Header):**\n"
                f"الحالة: {get_status_emoji(task_config.header_enabled)}\n"
                f"النص: {header_preview or 'غير محدد'}\n\n"
                f"📥 **التذييل (Footer):**\n"
                f"الحالة: {get_status_emoji(task_config.footer_enabled)}\n"
                f"النص: {footer_preview or 'غير محدد'}\n"
            )
            
            keyboard = [
                [Button.inline(f"📤 الرأس {get_status_emoji(task_config.header_enabled)}", f"toggle_task_header_{task_id}".encode()),
                 Button.inline(f"📥 التذييل {get_status_emoji(task_config.footer_enabled)}", f"toggle_task_footer_{task_id}".encode())],
                [Button.inline("✏️ تعديل الرأس", f"edit_task_header_text_{task_id}".encode()),
                 Button.inline("✏️ تعديل التذييل", f"edit_task_footer_text_{task_id}".encode())],
                [Button.inline("🗑️ حذف الرأس", f"clear_task_header_{task_id}".encode()),
                 Button.inline("🗑️ حذف التذييل", f"clear_task_footer_{task_id}".encode())],
                [Button.inline("🔙 العودة لإعدادات المهمة", f"edit_specific_{task_id}".encode())]
            ]
            
            await event.edit(text, buttons=keyboard)
            
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    async def edit_task_allow_list(self, event, task_id):
        """Edit allow list (whitelist) for specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            task_config = self.forwarder_instance.get_task_config(task_id)
            if not task_config:
                await event.answer("❌ المهمة غير موجودة", alert=True)
                return
            
            def get_status_emoji(enabled):
                return "✅" if enabled else "❌"
            
            whitelist_words = task_config.whitelist_words.split(',') if task_config.whitelist_words else []
            whitelist_preview = ", ".join(whitelist_words[:3])
            if len(whitelist_words) > 3:
                whitelist_preview += f" ... (+{len(whitelist_words) - 3})"
            
            text = (
                f"✅ **قائمة السماح للمهمة**\n\n"
                f"📝 **المهمة:** {task_config.name}\n"
                f"🔧 **الحالة:** {get_status_emoji(task_config.whitelist_enabled)}\n\n"
                f"📋 **الكلمات المسموحة:**\n"
                f"{whitelist_preview if whitelist_words else 'لا توجد كلمات'}\n\n"
                f"💡 **ملاحظة:** عند التفعيل، ستمرر فقط الرسائل التي تحتوي على هذه الكلمات"
            )
            
            keyboard = [
                [Button.inline(f"⚡ تفعيل/إلغاء {get_status_emoji(task_config.whitelist_enabled)}", f"toggle_task_whitelist_{task_id}".encode())],
                [Button.inline("➕ إضافة كلمات", f"add_task_whitelist_{task_id}".encode()),
                 Button.inline("📋 عرض الكلمات", f"view_task_whitelist_{task_id}".encode())],
                [Button.inline("🗑️ حذف جميع الكلمات", f"clear_task_whitelist_{task_id}".encode())],
                [Button.inline("🔙 العودة لإعدادات المهمة", f"edit_specific_{task_id}".encode())]
            ]
            
            await event.edit(text, buttons=keyboard)
            
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    async def edit_task_block_list(self, event, task_id):
        """Edit block list (blacklist) for specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            task_config = self.forwarder_instance.get_task_config(task_id)
            if not task_config:
                await event.answer("❌ المهمة غير موجودة", alert=True)
                return
            
            def get_status_emoji(enabled):
                return "✅" if enabled else "❌"
            
            blacklist_words = task_config.blacklist_words.split(',') if task_config.blacklist_words else []
            blacklist_preview = ", ".join(blacklist_words[:3])
            if len(blacklist_words) > 3:
                blacklist_preview += f" ... (+{len(blacklist_words) - 3})"
            
            text = (
                f"🚫 **قائمة الحظر للمهمة**\n\n"
                f"📝 **المهمة:** {task_config.name}\n"
                f"🔧 **الحالة:** {get_status_emoji(task_config.blacklist_enabled)}\n\n"
                f"📋 **الكلمات المحظورة:**\n"
                f"{blacklist_preview if blacklist_words else 'لا توجد كلمات'}\n\n"
                f"💡 **ملاحظة:** عند التفعيل، سيتم حظر الرسائل التي تحتوي على هذه الكلمات"
            )
            
            keyboard = [
                [Button.inline(f"⚡ تفعيل/إلغاء {get_status_emoji(task_config.blacklist_enabled)}", f"toggle_task_blacklist_{task_id}".encode())],
                [Button.inline("➕ إضافة كلمات", f"add_task_blacklist_{task_id}".encode()),
                 Button.inline("📋 عرض الكلمات", f"view_task_blacklist_{task_id}".encode())],
                [Button.inline("🗑️ حذف جميع الكلمات", f"clear_task_blacklist_{task_id}".encode())],
                [Button.inline("🔙 العودة لإعدادات المهمة", f"edit_specific_{task_id}".encode())]
            ]
            
            await event.edit(text, buttons=keyboard)
            
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    # Task-specific toggle functions
    async def set_task_forward_mode(self, event, task_id, mode):
        """Set forward mode for specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            success = self.forwarder_instance.update_task_config(task_id, forward_mode=mode)
            if success:
                mode_text = "إعادة توجيه مباشر" if mode == "forward" else "نسخ المحتوى"
                await event.answer(f"✅ تم تغيير وضع التوجيه إلى: {mode_text}", alert=False)
                await self.edit_task_forward_mode(event, task_id)
            else:
                await event.answer("❌ فشل في تحديث الإعدادات", alert=True)
                
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    async def toggle_task_media_filter(self, event, task_id, media_type):
        """Toggle media filter for specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            task_config = self.forwarder_instance.get_task_config(task_id)
            if not task_config:
                await event.answer("❌ المهمة غير موجودة", alert=True)
                return
            
            field_name = f"forward_{media_type}"
            current_value = getattr(task_config, field_name, True)
            new_value = not current_value
            
            success = self.forwarder_instance.update_task_config(task_id, **{field_name: new_value})
            if success:
                status_text = "مفعل" if new_value else "معطل"
                await event.answer(f"✅ {media_type} أصبح {status_text}", alert=False)
                await self.edit_task_media_filters(event, task_id)
            else:
                await event.answer("❌ فشل في تحديث الإعدادات", alert=True)
                
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    async def toggle_task_clean_option(self, event, task_id, clean_type):
        """Toggle text cleaning option for specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            task_config = self.forwarder_instance.get_task_config(task_id)
            if not task_config:
                await event.answer("❌ المهمة غير موجودة", alert=True)
                return
            
            field_name = f"clean_{clean_type}" if clean_type != "words" else "clean_lines_with_words"
            current_value = getattr(task_config, field_name, False)
            new_value = not current_value
            
            success = self.forwarder_instance.update_task_config(task_id, **{field_name: new_value})
            if success:
                status_text = "مفعل" if new_value else "معطل"
                clean_names = {
                    "links": "حذف الروابط",
                    "hashtags": "حذف الهاشتاغ", 
                    "formatting": "حذف التنسيق",
                    "empty_lines": "حذف الأسطر الفارغة",
                    "words": "حذف أسطر بكلمات محددة"
                }
                clean_name = clean_names.get(clean_type, clean_type)
                await event.answer(f"✅ {clean_name} أصبح {status_text}", alert=False)
                await self.edit_task_text_cleaner(event, task_id)
            else:
                await event.answer("❌ فشل في تحديث الإعدادات", alert=True)
                
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    async def toggle_task_replacer(self, event, task_id):
        """Toggle smart replacer for specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            task_config = self.forwarder_instance.get_task_config(task_id)
            if not task_config:
                await event.answer("❌ المهمة غير موجودة", alert=True)
                return
            
            new_value = not task_config.replacer_enabled
            success = self.forwarder_instance.update_task_config(task_id, replacer_enabled=new_value)
            
            if success:
                status_text = "مفعل" if new_value else "معطل"
                await event.answer(f"✅ الاستبدال الذكي أصبح {status_text}", alert=False)
                await self.edit_task_smart_replacer(event, task_id)
            else:
                await event.answer("❌ فشل في تحديث الإعدادات", alert=True)
                
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    async def toggle_task_buttons(self, event, task_id):
        """Toggle custom buttons for specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            task_config = self.forwarder_instance.get_task_config(task_id)
            if not task_config:
                await event.answer("❌ المهمة غير موجودة", alert=True)
                return
            
            new_value = not task_config.buttons_enabled
            success = self.forwarder_instance.update_task_config(task_id, buttons_enabled=new_value)
            
            if success:
                status_text = "مفعل" if new_value else "معطل"
                await event.answer(f"✅ الأزرار المخصصة أصبحت {status_text}", alert=False)
                await self.edit_task_custom_buttons(event, task_id)
            else:
                await event.answer("❌ فشل في تحديث الإعدادات", alert=True)
                
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    async def toggle_task_header(self, event, task_id):
        """Toggle header for specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            task_config = self.forwarder_instance.get_task_config(task_id)
            if not task_config:
                await event.answer("❌ المهمة غير موجودة", alert=True)
                return
            
            new_value = not task_config.header_enabled
            success = self.forwarder_instance.update_task_config(task_id, header_enabled=new_value)
            
            if success:
                status_text = "مفعل" if new_value else "معطل"
                await event.answer(f"✅ رأس الرسالة أصبح {status_text}", alert=False)
                await self.edit_task_header_footer(event, task_id)
            else:
                await event.answer("❌ فشل في تحديث الإعدادات", alert=True)
                
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    async def toggle_task_footer(self, event, task_id):
        """Toggle footer for specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            task_config = self.forwarder_instance.get_task_config(task_id)
            if not task_config:
                await event.answer("❌ المهمة غير موجودة", alert=True)
                return
            
            new_value = not task_config.footer_enabled
            success = self.forwarder_instance.update_task_config(task_id, footer_enabled=new_value)
            
            if success:
                status_text = "مفعل" if new_value else "معطل"
                await event.answer(f"✅ تذييل الرسالة أصبح {status_text}", alert=False)
                await self.edit_task_header_footer(event, task_id)
            else:
                await event.answer("❌ فشل في تحديث الإعدادات", alert=True)
                
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    async def toggle_task_whitelist(self, event, task_id):
        """Toggle whitelist for specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            task_config = self.forwarder_instance.get_task_config(task_id)
            if not task_config:
                await event.answer("❌ المهمة غير موجودة", alert=True)
                return
            
            new_value = not task_config.whitelist_enabled
            success = self.forwarder_instance.update_task_config(task_id, whitelist_enabled=new_value)
            
            if success:
                status_text = "مفعل" if new_value else "معطل"
                await event.answer(f"✅ قائمة السماح أصبحت {status_text}", alert=False)
                await self.edit_task_allow_list(event, task_id)
            else:
                await event.answer("❌ فشل في تحديث الإعدادات", alert=True)
                
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    async def toggle_task_blacklist(self, event, task_id):
        """Toggle blacklist for specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            task_config = self.forwarder_instance.get_task_config(task_id)
            if not task_config:
                await event.answer("❌ المهمة غير موجودة", alert=True)
                return
            
            new_value = not task_config.blacklist_enabled
            success = self.forwarder_instance.update_task_config(task_id, blacklist_enabled=new_value)
            
            if success:
                status_text = "مفعل" if new_value else "معطل"
                await event.answer(f"✅ قائمة الحظر أصبحت {status_text}", alert=False)
                await self.edit_task_block_list(event, task_id)
            else:
                await event.answer("❌ فشل في تحديث الإعدادات", alert=True)
                
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    # Additional task-specific functions for replacements
    async def prompt_add_task_replacement(self, event, task_id):
        """Prompt user to add replacement for specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            self.user_states[event.sender_id] = f'task_replacement_{task_id}'
            
            text = (
                f"🔄 **إضافة استبدال جديد للمهمة**\n\n"
                f"💡 **تنسيق الاستبدال:**\n"
                f"`النص القديم -> النص الجديد`\n\n"
                f"📝 **مثال:**\n"
                f"`سلام عليكم -> أهلاً وسهلاً`\n\n"
                f"✏️ **أرسل الاستبدال الآن:**"
            )
            
            keyboard = [[Button.inline("❌ إلغاء", f"edit_smart_replacer_{task_id}".encode())]]
            await event.edit(text, buttons=keyboard)
            
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    async def view_task_replacements(self, event, task_id):
        """View all replacements for specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            task_config = self.forwarder_instance.get_task_config(task_id)
            if not task_config:
                await event.answer("❌ المهمة غير موجودة", alert=True)
                return
            
            replacements_list = []
            if task_config.replacements:
                replacements_list = [r.strip() for r in task_config.replacements.split(',') if r.strip() and '->' in r]
            
            if not replacements_list:
                text = (
                    f"📋 **استبدالات المهمة**\n\n"
                    f"📝 **المهمة:** {task_config.name}\n\n"
                    f"⚠️ **لا توجد استبدالات محفوظة**\n\n"
                    f"💡 **أضف استبدالات جديدة لبدء استخدام هذه الميزة**"
                )
            else:
                text = (
                    f"📋 **استبدالات المهمة** ({len(replacements_list)})\n\n"
                    f"📝 **المهمة:** {task_config.name}\n\n"
                )
                for i, replacement in enumerate(replacements_list, 1):
                    text += f"{i}. `{replacement}`\n"
            
            keyboard = [
                [Button.inline("➕ إضافة استبدال", f"add_task_replacement_{task_id}".encode()),
                 Button.inline("🗑️ مسح الكل", f"clear_task_replacements_{task_id}".encode())],
                [Button.inline("🔙 العودة", f"edit_smart_replacer_{task_id}".encode())]
            ]
            
            await event.edit(text, buttons=keyboard)
            
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    async def clear_task_replacements(self, event, task_id):
        """Clear all replacements for specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            success = self.forwarder_instance.update_task_config(task_id, replacements="")
            if success:
                await event.answer("✅ تم حذف جميع الاستبدالات", alert=False)
                await self.edit_task_smart_replacer(event, task_id)
            else:
                await event.answer("❌ فشل في حذف الاستبدالات", alert=True)
                
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    # Task-specific button functions
    async def prompt_edit_task_button(self, event, task_id, button_num):
        """Prompt user to edit button for specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            self.user_states[event.sender_id] = f'task_button_{task_id}_{button_num}_text'
            
            text = (
                f"🔘 **تعديل الزر رقم {button_num} للمهمة**\n\n"
                f"📝 **أرسل نص الزر:**\n"
                f"💡 **مثال:** اشترك في القناة\n\n"
                f"✏️ **أرسل النص الآن:**"
            )
            
            keyboard = [[Button.inline("❌ إلغاء", f"edit_custom_buttons_{task_id}".encode())]]
            await event.edit(text, buttons=keyboard)
            
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    async def clear_task_buttons(self, event, task_id):
        """Clear all buttons for specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            success = self.forwarder_instance.update_task_config(
                task_id, 
                button1_text="", button1_url="",
                button2_text="", button2_url="",
                button3_text="", button3_url=""
            )
            
            if success:
                await event.answer("✅ تم حذف جميع الأزرار", alert=False)
                await self.edit_task_custom_buttons(event, task_id)
            else:
                await event.answer("❌ فشل في حذف الأزرار", alert=True)
                
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    async def preview_task_buttons(self, event, task_id):
        """Preview buttons for specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            task_config = self.forwarder_instance.get_task_config(task_id)
            if not task_config:
                await event.answer("❌ المهمة غير موجودة", alert=True)
                return
            
            preview_buttons = []
            if task_config.button1_text and task_config.button1_url:
                preview_buttons.append([Button.url(task_config.button1_text, task_config.button1_url)])
            if task_config.button2_text and task_config.button2_url:
                preview_buttons.append([Button.url(task_config.button2_text, task_config.button2_url)])
            if task_config.button3_text and task_config.button3_url:
                preview_buttons.append([Button.url(task_config.button3_text, task_config.button3_url)])
            
            preview_buttons.append([Button.inline("🔙 العودة", f"edit_custom_buttons_{task_id}".encode())])
            
            text = (
                f"👀 **معاينة أزرار المهمة**\n\n"
                f"📝 **المهمة:** {task_config.name}\n\n"
                f"🔘 **هذه هي الأزرار التي ستظهر مع الرسائل:**"
            )
            
            await event.edit(text, buttons=preview_buttons)
            
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    # Task-specific header/footer functions
    async def prompt_edit_task_header(self, event, task_id):
        """Prompt user to edit header for specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            self.user_states[event.sender_id] = f'task_header_{task_id}'
            
            text = (
                f"📝 **تعديل رأس المهمة**\n\n"
                f"💡 **الرأس هو نص يُضاف في بداية كل رسالة**\n\n"
                f"📝 **مثال:**\n"
                f"`📢 إعلان مهم:`\n"
                f"`🔥 عاجل:`\n\n"
                f"✏️ **أرسل نص الرأس الآن:**"
            )
            
            keyboard = [[Button.inline("❌ إلغاء", f"edit_header_footer_{task_id}".encode())]]
            await event.edit(text, buttons=keyboard)
            
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    async def prompt_edit_task_footer(self, event, task_id):
        """Prompt user to edit footer for specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            self.user_states[event.sender_id] = f'task_footer_{task_id}'
            
            text = (
                f"📝 **تعديل تذييل المهمة**\n\n"
                f"💡 **التذييل هو نص يُضاف في نهاية كل رسالة**\n\n"
                f"📝 **مثال:**\n"
                f"`📱 تابعونا على تليجرام`\n"
                f"`🔗 @YourChannel`\n\n"
                f"✏️ **أرسل نص التذييل الآن:**"
            )
            
            keyboard = [[Button.inline("❌ إلغاء", f"edit_header_footer_{task_id}".encode())]]
            await event.edit(text, buttons=keyboard)
            
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    async def clear_task_header(self, event, task_id):
        """Clear header for specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            success = self.forwarder_instance.update_task_config(task_id, header_text="", header_enabled=False)
            if success:
                await event.answer("✅ تم حذف الرأس", alert=False)
                await self.edit_task_header_footer(event, task_id)
            else:
                await event.answer("❌ فشل في حذف الرأس", alert=True)
                
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    async def clear_task_footer(self, event, task_id):
        """Clear footer for specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            success = self.forwarder_instance.update_task_config(task_id, footer_text="", footer_enabled=False)
            if success:
                await event.answer("✅ تم حذف التذييل", alert=False)
                await self.edit_task_header_footer(event, task_id)
            else:
                await event.answer("❌ فشل في حذف التذييل", alert=True)
                
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    # Task-specific blacklist/whitelist functions
    async def prompt_add_task_blacklist(self, event, task_id):
        """Prompt user to add blacklist words for specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            self.user_states[event.sender_id] = f'task_blacklist_{task_id}'
            
            text = (
                f"🚫 **إضافة كلمات للحظر**\n\n"
                f"💡 **يفصل بين الكلمات بفاصلة**\n\n"
                f"📝 **مثال:**\n"
                f"`إعلان, دعاية, سبام`\n\n"
                f"✏️ **أرسل الكلمات الآن:**"
            )
            
            keyboard = [[Button.inline("❌ إلغاء", f"edit_block_list_{task_id}".encode())]]
            await event.edit(text, buttons=keyboard)
            
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    async def view_task_blacklist(self, event, task_id):
        """View blacklist words for specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            task_config = self.forwarder_instance.get_task_config(task_id)
            if not task_config:
                await event.answer("❌ المهمة غير موجودة", alert=True)
                return
            
            blacklist_words = task_config.blacklist_words.split(',') if task_config.blacklist_words else []
            blacklist_words = [word.strip() for word in blacklist_words if word.strip()]
            
            if not blacklist_words:
                text = (
                    f"🚫 **قائمة الحظر للمهمة**\n\n"
                    f"📝 **المهمة:** {task_config.name}\n\n"
                    f"⚠️ **لا توجد كلمات محظورة**\n\n"
                    f"💡 **أضف كلمات للحظر لبدء استخدام هذه الميزة**"
                )
            else:
                text = (
                    f"🚫 **قائمة الحظر للمهمة** ({len(blacklist_words)})\n\n"
                    f"📝 **المهمة:** {task_config.name}\n\n"
                    f"📋 **الكلمات المحظورة:**\n"
                )
                for i, word in enumerate(blacklist_words, 1):
                    text += f"{i}. `{word}`\n"
            
            keyboard = [
                [Button.inline("➕ إضافة كلمات", f"add_task_blacklist_{task_id}".encode()),
                 Button.inline("🗑️ مسح الكل", f"clear_task_blacklist_{task_id}".encode())],
                [Button.inline("🔙 العودة", f"edit_block_list_{task_id}".encode())]
            ]
            
            await event.edit(text, buttons=keyboard)
            
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    async def clear_task_blacklist(self, event, task_id):
        """Clear blacklist for specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            success = self.forwarder_instance.update_task_config(task_id, blacklist_words="")
            if success:
                await event.answer("✅ تم حذف جميع الكلمات المحظورة", alert=False)
                await self.edit_task_block_list(event, task_id)
            else:
                await event.answer("❌ فشل في حذف القائمة", alert=True)
                
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    async def prompt_add_task_whitelist(self, event, task_id):
        """Prompt user to add whitelist words for specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            self.user_states[event.sender_id] = f'task_whitelist_{task_id}'
            
            text = (
                f"✅ **إضافة كلمات للسماح**\n\n"
                f"💡 **يفصل بين الكلمات بفاصلة**\n\n"
                f"📝 **مثال:**\n"
                f"`مهم, عاجل, خبر`\n\n"
                f"✏️ **أرسل الكلمات الآن:**"
            )
            
            keyboard = [[Button.inline("❌ إلغاء", f"edit_allow_list_{task_id}".encode())]]
            await event.edit(text, buttons=keyboard)
            
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    async def view_task_whitelist(self, event, task_id):
        """View whitelist words for specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            task_config = self.forwarder_instance.get_task_config(task_id)
            if not task_config:
                await event.answer("❌ المهمة غير موجودة", alert=True)
                return
            
            whitelist_words = task_config.whitelist_words.split(',') if task_config.whitelist_words else []
            whitelist_words = [word.strip() for word in whitelist_words if word.strip()]
            
            if not whitelist_words:
                text = (
                    f"✅ **قائمة السماح للمهمة**\n\n"
                    f"📝 **المهمة:** {task_config.name}\n\n"
                    f"⚠️ **لا توجد كلمات مسموحة**\n\n"
                    f"💡 **أضف كلمات للسماح لبدء استخدام هذه الميزة**"
                )
            else:
                text = (
                    f"✅ **قائمة السماح للمهمة** ({len(whitelist_words)})\n\n"
                    f"📝 **المهمة:** {task_config.name}\n\n"
                    f"📋 **الكلمات المسموحة:**\n"
                )
                for i, word in enumerate(whitelist_words, 1):
                    text += f"{i}. `{word}`\n"
            
            keyboard = [
                [Button.inline("➕ إضافة كلمات", f"add_task_whitelist_{task_id}".encode()),
                 Button.inline("🗑️ مسح الكل", f"clear_task_whitelist_{task_id}".encode())],
                [Button.inline("🔙 العودة", f"edit_allow_list_{task_id}".encode())]
            ]
            
            await event.edit(text, buttons=keyboard)
            
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    async def clear_task_whitelist(self, event, task_id):
        """Clear whitelist for specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            success = self.forwarder_instance.update_task_config(task_id, whitelist_words="")
            if success:
                await event.answer("✅ تم حذف جميع الكلمات المسموحة", alert=False)
                await self.edit_task_allow_list(event, task_id)
            else:
                await event.answer("❌ فشل في حذف القائمة", alert=True)
                
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    # Task-specific clean words function
    async def edit_task_clean_words(self, event, task_id):
        """Edit clean words for specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            task_config = self.forwarder_instance.get_task_config(task_id)
            if not task_config:
                await event.answer("❌ المهمة غير موجودة", alert=True)
                return
            
            clean_words = getattr(task_config, 'clean_words', '').split(',') if hasattr(task_config, 'clean_words') and task_config.clean_words else []
            clean_words = [word.strip() for word in clean_words if word.strip()]
            
            text = (
                f"🧹 **الكلمات المحظورة في التنظيف**\n\n"
                f"📝 **المهمة:** {task_config.name}\n\n"
                f"💡 **الأسطر التي تحتوي على هذه الكلمات سيتم حذفها**\n\n"
            )
            
            if clean_words:
                text += f"📋 **الكلمات الحالية:** ({len(clean_words)})\n"
                for i, word in enumerate(clean_words[:10], 1):
                    text += f"{i}. `{word}`\n"
                if len(clean_words) > 10:
                    text += f"... و {len(clean_words) - 10} كلمة أخرى\n"
            else:
                text += "⚠️ **لا توجد كلمات محددة**\n"
            
            keyboard = [
                [Button.inline("➕ إضافة كلمات", f"add_task_clean_words_{task_id}".encode()),
                 Button.inline("📋 عرض الكل", f"view_task_clean_words_{task_id}".encode())],
                [Button.inline("🗑️ مسح الكل", f"clear_task_clean_words_{task_id}".encode())],
                [Button.inline("🔙 العودة", f"edit_text_cleaner_{task_id}".encode())]
            ]
            
            await event.edit(text, buttons=keyboard)
            
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    # Task management functions (name, source, target, delay)
    async def prompt_edit_task_name(self, event, task_id):
        """Prompt user to edit task name"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            self.user_states[event.sender_id] = f'task_name_{task_id}'
            
            text = (
                f"📝 **تغيير اسم المهمة**\n\n"
                f"💡 **اختر اسماً وصفياً للمهمة**\n\n"
                f"📝 **مثال:**\n"
                f"`أخبار القناة الرسمية`\n"
                f"`توجيه المحتوى الترفيهي`\n\n"
                f"✏️ **أرسل الاسم الجديد:**"
            )
            
            keyboard = [[Button.inline("❌ إلغاء", f"edit_specific_{task_id}".encode())]]
            await event.edit(text, buttons=keyboard)
            
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    async def prompt_edit_task_source(self, event, task_id):
        """Prompt user to edit task source"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            self.user_states[event.sender_id] = f'task_source_{task_id}'
            
            text = (
                f"📥 **تغيير مصدر المهمة**\n\n"
                f"💡 **أرسل معرف القناة أو المجموعة المصدر**\n\n"
                f"📝 **الصيغ المقبولة:**\n"
                f"`@channel_username`\n"
                f"`-1001234567890` (معرف رقمي)\n"
                f"`https://t.me/channel_name`\n\n"
                f"✏️ **أرسل المصدر الجديد:**"
            )
            
            keyboard = [[Button.inline("❌ إلغاء", f"edit_specific_{task_id}".encode())]]
            await event.edit(text, buttons=keyboard)
            
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    async def prompt_edit_task_target(self, event, task_id):
        """Prompt user to edit task target"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            self.user_states[event.sender_id] = f'task_target_{task_id}'
            
            text = (
                f"📤 **تغيير هدف المهمة**\n\n"
                f"💡 **أرسل معرف القناة أو المجموعة الهدف**\n\n"
                f"📝 **الصيغ المقبولة:**\n"
                f"`@channel_username`\n"
                f"`-1001234567890` (معرف رقمي)\n"
                f"`https://t.me/channel_name`\n\n"
                f"✏️ **أرسل الهدف الجديد:**"
            )
            
            keyboard = [[Button.inline("❌ إلغاء", f"edit_specific_{task_id}".encode())]]
            await event.edit(text, buttons=keyboard)
            
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    async def prompt_edit_task_delay(self, event, task_id):
        """Prompt user to edit task delay"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            self.user_states[event.sender_id] = f'task_delay_{task_id}'
            
            text = (
                f"⏱️ **تأخير الإرسال للمهمة**\n\n"
                f"💡 **التأخير بين كل رسالة والتي تليها**\n\n"
                f"📝 **أرسل التأخير بالثواني:**\n"
                f"`0` - بدون تأخير\n"
                f"`5` - 5 ثوانِ\n"
                f"`30` - 30 ثانية\n"
                f"`60` - دقيقة واحدة\n\n"
                f"✏️ **أرسل التأخير الآن:**"
            )
            
            keyboard = [[Button.inline("❌ إلغاء", f"edit_specific_{task_id}".encode())]]
            await event.edit(text, buttons=keyboard)
            
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    # Input processing functions for task-specific operations
    async def process_task_replacement_input(self, event, task_id):
        """Process replacement input for specific task"""
        try:
            replacement_text = event.message.text.strip()
            
            if '->' not in replacement_text:
                await event.respond("❌ تنسيق خاطئ! استخدم: `النص القديم -> النص الجديد`")
                return
            
            if not self.forwarder_instance:
                await event.respond("❌ البوت الأساسي غير متصل")
                return
            
            task_config = self.forwarder_instance.get_task_config(task_id)
            current_replacements = task_config.replacements if task_config and task_config.replacements else ""
            
            if current_replacements:
                new_replacements = f"{current_replacements},{replacement_text}"
            else:
                new_replacements = replacement_text
            
            success = self.forwarder_instance.update_task_config(task_id, replacements=new_replacements)
            
            if success:
                await event.respond(f"✅ تم إضافة الاستبدال: `{replacement_text}`")
                del self.user_states[event.sender_id]
                await self.edit_task_smart_replacer(event, task_id)
            else:
                await event.respond("❌ فشل في إضافة الاستبدال")
                
        except Exception as e:
            await event.respond(f"❌ خطأ: {e}")

    async def process_task_button_text_input(self, event, task_id, button_num):
        """Process button text input for specific task"""
        try:
            button_text = event.message.text.strip()
            
            if len(button_text) > 50:
                await event.respond("❌ نص الزر طويل جداً! (الحد الأقصى 50 حرف)")
                return
            
            # Now ask for URL
            self.user_states[event.sender_id] = f'task_button_{task_id}_{button_num}_url'
            
            text = (
                f"🔗 **رابط الزر رقم {button_num}**\n\n"
                f"📝 **نص الزر:** {button_text}\n\n"
                f"💡 **أرسل رابط الزر:**\n"
                f"مثال: `https://t.me/yourchannel`\n\n"
                f"✏️ **أرسل الرابط الآن:**"
            )
            
            # Store button text temporarily
            if not hasattr(self, 'temp_button_data'):
                self.temp_button_data = {}
            self.temp_button_data[f'{task_id}_{button_num}'] = button_text
            
            keyboard = [[Button.inline("❌ إلغاء", f"edit_custom_buttons_{task_id}".encode())]]
            await event.respond(text, buttons=keyboard)
            
        except Exception as e:
            await event.respond(f"❌ خطأ: {e}")

    async def process_task_button_url_input(self, event, task_id, button_num):
        """Process button URL input for specific task"""
        try:
            button_url = event.message.text.strip()
            
            if not button_url.startswith(('http://', 'https://', 't.me')):
                await event.respond("❌ رابط غير صحيح! يجب أن يبدأ بـ http:// أو https:// أو t.me")
                return
            
            # Get stored button text
            if not hasattr(self, 'temp_button_data'):
                self.temp_button_data = {}
            
            button_text = self.temp_button_data.get(f'{task_id}_{button_num}', '')
            
            if not button_text:
                await event.respond("❌ خطأ في البيانات المؤقتة")
                return
            
            if not self.forwarder_instance:
                await event.respond("❌ البوت الأساسي غير متصل")
                return
            
            # Update button config
            update_data = {}
            update_data[f'button{button_num}_text'] = button_text
            update_data[f'button{button_num}_url'] = button_url
            
            success = self.forwarder_instance.update_task_config(task_id, **update_data)
            
            if success:
                await event.respond(f"✅ تم حفظ الزر رقم {button_num}")
                del self.user_states[event.sender_id]
                del self.temp_button_data[f'{task_id}_{button_num}']
                await self.edit_task_custom_buttons(event, task_id)
            else:
                await event.respond("❌ فشل في حفظ الزر")
                
        except Exception as e:
            await event.respond(f"❌ خطأ: {e}")

    async def process_task_header_input(self, event, task_id):
        """Process header input for specific task"""
        try:
            header_text = event.message.text.strip()
            
            if not self.forwarder_instance:
                await event.respond("❌ البوت الأساسي غير متصل")
                return
            
            success = self.forwarder_instance.update_task_config(
                task_id, 
                header_text=header_text, 
                header_enabled=True
            )
            
            if success:
                await event.respond(f"✅ تم حفظ الرأس: `{header_text[:50]}...`")
                del self.user_states[event.sender_id]
                await self.edit_task_header_footer(event, task_id)
            else:
                await event.respond("❌ فشل في حفظ الرأس")
                
        except Exception as e:
            await event.respond(f"❌ خطأ: {e}")

    async def process_task_footer_input(self, event, task_id):
        """Process footer input for specific task"""
        try:
            footer_text = event.message.text.strip()
            
            if not self.forwarder_instance:
                await event.respond("❌ البوت الأساسي غير متصل")
                return
            
            success = self.forwarder_instance.update_task_config(
                task_id, 
                footer_text=footer_text, 
                footer_enabled=True
            )
            
            if success:
                await event.respond(f"✅ تم حفظ التذييل: `{footer_text[:50]}...`")
                del self.user_states[event.sender_id]
                await self.edit_task_header_footer(event, task_id)
            else:
                await event.respond("❌ فشل في حفظ التذييل")
                
        except Exception as e:
            await event.respond(f"❌ خطأ: {e}")

    async def process_task_blacklist_input(self, event, task_id):
        """Process blacklist input for specific task"""
        try:
            words_text = event.message.text.strip()
            words = [word.strip() for word in words_text.split(',') if word.strip()]
            
            if not words:
                await event.respond("❌ لم يتم إدخال كلمات صحيحة")
                return
            
            if not self.forwarder_instance:
                await event.respond("❌ البوت الأساسي غير متصل")
                return
            
            task_config = self.forwarder_instance.get_task_config(task_id)
            current_words = task_config.blacklist_words if task_config and task_config.blacklist_words else ""
            
            if current_words:
                new_words = f"{current_words},{','.join(words)}"
            else:
                new_words = ','.join(words)
            
            success = self.forwarder_instance.update_task_config(task_id, blacklist_words=new_words)
            
            if success:
                await event.respond(f"✅ تم إضافة {len(words)} كلمة للحظر")
                del self.user_states[event.sender_id]
                await self.edit_task_block_list(event, task_id)
            else:
                await event.respond("❌ فشل في إضافة الكلمات")
                
        except Exception as e:
            await event.respond(f"❌ خطأ: {e}")

    async def process_task_whitelist_input(self, event, task_id):
        """Process whitelist input for specific task"""
        try:
            words_text = event.message.text.strip()
            words = [word.strip() for word in words_text.split(',') if word.strip()]
            
            if not words:
                await event.respond("❌ لم يتم إدخال كلمات صحيحة")
                return
            
            if not self.forwarder_instance:
                await event.respond("❌ البوت الأساسي غير متصل")
                return
            
            task_config = self.forwarder_instance.get_task_config(task_id)
            current_words = task_config.whitelist_words if task_config and task_config.whitelist_words else ""
            
            if current_words:
                new_words = f"{current_words},{','.join(words)}"
            else:
                new_words = ','.join(words)
            
            success = self.forwarder_instance.update_task_config(task_id, whitelist_words=new_words)
            
            if success:
                await event.respond(f"✅ تم إضافة {len(words)} كلمة للسماح")
                del self.user_states[event.sender_id]
                await self.edit_task_allow_list(event, task_id)
            else:
                await event.respond("❌ فشل في إضافة الكلمات")
                
        except Exception as e:
            await event.respond(f"❌ خطأ: {e}")

    async def process_task_name_input(self, event, task_id):
        """Process task name input"""
        try:
            new_name = event.message.text.strip()
            
            if len(new_name) < 3:
                await event.respond("❌ اسم المهمة قصير جداً! (أقل من 3 أحرف)")
                return
            
            if len(new_name) > 50:
                await event.respond("❌ اسم المهمة طويل جداً! (أكثر من 50 حرف)")
                return
            
            if not self.forwarder_instance:
                await event.respond("❌ البوت الأساسي غير متصل")
                return
            
            success = self.forwarder_instance.update_task_config(task_id, name=new_name)
            
            if success:
                await event.respond(f"✅ تم تغيير اسم المهمة إلى: `{new_name}`")
                del self.user_states[event.sender_id]
                await self.edit_specific_task(event, task_id)
            else:
                await event.respond("❌ فشل في تغيير اسم المهمة")
                
        except Exception as e:
            await event.respond(f"❌ خطأ: {e}")

    async def process_task_source_input(self, event, task_id):
        """Process task source input"""
        try:
            new_source = event.message.text.strip()
            
            if not self.forwarder_instance:
                await event.respond("❌ البوت الأساسي غير متصل")
                return
            
            success = self.forwarder_instance.update_task_config(task_id, source_chat=new_source)
            
            if success:
                await event.respond(f"✅ تم تغيير المصدر إلى: `{new_source}`")
                del self.user_states[event.sender_id]
                await self.edit_specific_task(event, task_id)
            else:
                await event.respond("❌ فشل في تغيير المصدر")
                
        except Exception as e:
            await event.respond(f"❌ خطأ: {e}")

    async def process_task_target_input(self, event, task_id):
        """Process task target input"""
        try:
            new_target = event.message.text.strip()
            
            if not self.forwarder_instance:
                await event.respond("❌ البوت الأساسي غير متصل")
                return
            
            success = self.forwarder_instance.update_task_config(task_id, target_chat=new_target)
            
            if success:
                await event.respond(f"✅ تم تغيير الهدف إلى: `{new_target}`")
                del self.user_states[event.sender_id]
                await self.edit_specific_task(event, task_id)
            else:
                await event.respond("❌ فشل في تغيير الهدف")
                
        except Exception as e:
            await event.respond(f"❌ خطأ: {e}")

    async def process_task_delay_input(self, event, task_id):
        """Process task delay input"""
        try:
            delay_text = event.message.text.strip()
            
            try:
                delay_seconds = int(delay_text)
            except ValueError:
                await event.respond("❌ يجب إدخال رقم صحيح للتأخير")
                return
            
            if delay_seconds < 0:
                await event.respond("❌ التأخير لا يمكن أن يكون سالباً")
                return
            
            if delay_seconds > 3600:  # Max 1 hour
                await event.respond("❌ التأخير كبير جداً! (الحد الأقصى 3600 ثانية)")
                return
            
            if not self.forwarder_instance:
                await event.respond("❌ البوت الأساسي غير متصل")
                return
            
            success = self.forwarder_instance.update_task_config(task_id, forward_delay=delay_seconds)
            
            if success:
                delay_text = f"{delay_seconds} ثانية" if delay_seconds > 0 else "بدون تأخير"
                await event.respond(f"✅ تم تعديل التأخير إلى: {delay_text}")
                del self.user_states[event.sender_id]
                await self.edit_specific_task(event, task_id)
            else:
                await event.respond("❌ فشل في تعديل التأخير")
                
        except Exception as e:
            await event.respond(f"❌ خطأ: {e}")

    # ===================== NEW ADVANCED FEATURES =====================
    
    # Language Filter Functions
    async def edit_task_language_filter(self, event, task_id):
        """Edit language filter for specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            task_config = self.forwarder_instance.get_task_config(task_id)
            if not task_config:
                await event.answer("❌ المهمة غير موجودة", alert=True)
                return
            
            def get_status_emoji(enabled):
                return "✅" if enabled else "❌"
            
            filter_enabled = getattr(task_config, 'language_filter_enabled', False)
            filter_type = getattr(task_config, 'language_filter_type', 'allow')  # allow or block
            allowed_languages = getattr(task_config, 'allowed_languages', '').split(',') if getattr(task_config, 'allowed_languages', '') else []
            blocked_languages = getattr(task_config, 'blocked_languages', '').split(',') if getattr(task_config, 'blocked_languages', '') else []
            
            text = (
                f"🌐 **فلتر اللغة للمهمة**\n\n"
                f"📝 **المهمة:** {task_config.name}\n"
                f"🔧 **الحالة:** {get_status_emoji(filter_enabled)}\n"
                f"📋 **نوع الفلتر:** {'السماح' if filter_type == 'allow' else 'الحظر'}\n\n"
                f"🌍 **اللغات المسموحة:** {', '.join(allowed_languages) if allowed_languages else 'لا توجد'}\n"
                f"🚫 **اللغات المحظورة:** {', '.join(blocked_languages) if blocked_languages else 'لا توجد'}\n\n"
                f"💡 **يتم تحديد اللغة تلقائياً من النص**"
            )
            
            keyboard = [
                [Button.inline(f"⚡ تفعيل/إلغاء {get_status_emoji(filter_enabled)}", f"toggle_language_filter_{task_id}".encode())],
                [Button.inline("✅ وضع السماح", f"set_language_mode_{task_id}_allow".encode()),
                 Button.inline("🚫 وضع الحظر", f"set_language_mode_{task_id}_block".encode())],
                [Button.inline("➕ إضافة لغات مسموحة", f"add_allowed_languages_{task_id}".encode()),
                 Button.inline("📋 عرض المسموحة", f"view_allowed_languages_{task_id}".encode())],
                [Button.inline("➕ إضافة لغات محظورة", f"add_blocked_languages_{task_id}".encode()),
                 Button.inline("📋 عرض المحظورة", f"view_blocked_languages_{task_id}".encode())],
                [Button.inline("🗑️ مسح كل اللغات", f"clear_all_languages_{task_id}".encode())],
                [Button.inline("🔙 العودة لإعدادات المهمة", f"edit_specific_{task_id}".encode())]
            ]
            
            await event.edit(text, buttons=keyboard)
            
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    async def toggle_task_language_filter(self, event, task_id):
        """Toggle language filter for specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            task_config = self.forwarder_instance.get_task_config(task_id)
            if not task_config:
                await event.answer("❌ المهمة غير موجودة", alert=True)
                return
            
            current_enabled = getattr(task_config, 'language_filter_enabled', False)
            new_enabled = not current_enabled
            
            success = self.forwarder_instance.update_task_config(task_id, language_filter_enabled=new_enabled)
            if success:
                status_text = "مفعل" if new_enabled else "معطل"
                await event.answer(f"✅ فلتر اللغة أصبح {status_text}", alert=False)
                await self.edit_task_language_filter(event, task_id)
            else:
                await event.answer("❌ فشل في تحديث الإعدادات", alert=True)
                
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    # Link Filter Functions
    async def edit_task_link_filter(self, event, task_id):
        """Edit link filter for specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            task_config = self.forwarder_instance.get_task_config(task_id)
            if not task_config:
                await event.answer("❌ المهمة غير موجودة", alert=True)
                return
            
            def get_status_emoji(enabled):
                return "✅" if enabled else "❌"
            
            link_filter_enabled = getattr(task_config, 'link_filter_enabled', False)
            allow_telegram_links = getattr(task_config, 'allow_telegram_links', True)
            allow_external_links = getattr(task_config, 'allow_external_links', True)
            allowed_domains = getattr(task_config, 'allowed_domains', '').split(',') if getattr(task_config, 'allowed_domains', '') else []
            blocked_domains = getattr(task_config, 'blocked_domains', '').split(',') if getattr(task_config, 'blocked_domains', '') else []
            
            text = (
                f"🔗 **فلتر الروابط للمهمة**\n\n"
                f"📝 **المهمة:** {task_config.name}\n"
                f"🔧 **الحالة:** {get_status_emoji(link_filter_enabled)}\n\n"
                f"📱 **روابط تليجرام:** {get_status_emoji(allow_telegram_links)}\n"
                f"🌐 **الروابط الخارجية:** {get_status_emoji(allow_external_links)}\n\n"
                f"✅ **المواقع المسموحة:** {', '.join(allowed_domains) if allowed_domains else 'لا توجد'}\n"
                f"🚫 **المواقع المحظورة:** {', '.join(blocked_domains) if blocked_domains else 'لا توجد'}\n"
            )
            
            keyboard = [
                [Button.inline(f"⚡ تفعيل/إلغاء {get_status_emoji(link_filter_enabled)}", f"toggle_link_filter_{task_id}".encode())],
                [Button.inline(f"📱 روابط تليجرام {get_status_emoji(allow_telegram_links)}", f"toggle_telegram_links_{task_id}".encode()),
                 Button.inline(f"🌐 روابط خارجية {get_status_emoji(allow_external_links)}", f"toggle_external_links_{task_id}".encode())],
                [Button.inline("➕ إضافة مواقع مسموحة", f"add_allowed_domains_{task_id}".encode()),
                 Button.inline("📋 عرض المسموحة", f"view_allowed_domains_{task_id}".encode())],
                [Button.inline("➕ إضافة مواقع محظورة", f"add_blocked_domains_{task_id}".encode()),
                 Button.inline("📋 عرض المحظورة", f"view_blocked_domains_{task_id}".encode())],
                [Button.inline("🗑️ مسح كل المواقع", f"clear_all_domains_{task_id}".encode())],
                [Button.inline("🔙 العودة لإعدادات المهمة", f"edit_specific_{task_id}".encode())]
            ]
            
            await event.edit(text, buttons=keyboard)
            
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    async def toggle_task_link_filter(self, event, task_id):
        """Toggle link filter for specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            task_config = self.forwarder_instance.get_task_config(task_id)
            if not task_config:
                await event.answer("❌ المهمة غير موجودة", alert=True)
                return
            
            current_enabled = getattr(task_config, 'link_filter_enabled', False)
            new_enabled = not current_enabled
            
            success = self.forwarder_instance.update_task_config(task_id, link_filter_enabled=new_enabled)
            if success:
                status_text = "مفعل" if new_enabled else "معطل"
                await event.answer(f"✅ فلتر الروابط أصبح {status_text}", alert=False)
                await self.edit_task_link_filter(event, task_id)
            else:
                await event.answer("❌ فشل في تحديث الإعدادات", alert=True)
                
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    # Forwarded Messages Filter Functions
    async def edit_task_forwarded_filter(self, event, task_id):
        """Edit forwarded messages filter for specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            task_config = self.forwarder_instance.get_task_config(task_id)
            if not task_config:
                await event.answer("❌ المهمة غير موجودة", alert=True)
                return
            
            def get_status_emoji(enabled):
                return "✅" if enabled else "❌"
            
            forwarded_filter_enabled = getattr(task_config, 'forwarded_filter_enabled', False)
            
            text = (
                f"↩️ **فلتر المعاد توجيهها للمهمة**\n\n"
                f"📝 **المهمة:** {task_config.name}\n"
                f"🔧 **الحالة:** {get_status_emoji(forwarded_filter_enabled)}\n\n"
                f"💡 **عند التفعيل، سيتم حظر الرسائل المعاد توجيهها من أي مكان آخر**\n"
                f"🔍 **هذا مفيد لضمان الحصول على محتوى أصلي فقط**\n"
                f"⚠️ **فقط الرسائل الأصلية سيتم توجيهها**"
            )
            
            keyboard = [
                [Button.inline(f"⚡ تفعيل/تعطيل الفلتر {get_status_emoji(forwarded_filter_enabled)}", f"toggle_forwarded_filter_{task_id}".encode())],
                [Button.inline("🔙 العودة لإعدادات المهمة", f"edit_specific_{task_id}".encode())]
            ]
            
            await event.edit(text, buttons=keyboard)
            
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    async def toggle_task_forwarded_filter(self, event, task_id):
        """Toggle forwarded messages filter for specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            task_config = self.forwarder_instance.get_task_config(task_id)
            if not task_config:
                await event.answer("❌ المهمة غير موجودة", alert=True)
                return
            
            current_enabled = getattr(task_config, 'forwarded_filter_enabled', False)
            new_enabled = not current_enabled
            
            success = self.forwarder_instance.update_task_config(task_id, forwarded_filter_enabled=new_enabled)
            if success:
                status_text = "مفعل" if new_enabled else "معطل"
                await event.answer(f"✅ فلتر المعاد توجيهها أصبح {status_text}", alert=False)
                await self.edit_task_forwarded_filter(event, task_id)
            else:
                await event.answer("❌ فشل في تحديث الإعدادات", alert=True)
                
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    # User Filter Functions  
    async def edit_task_user_filter(self, event, task_id):
        """Edit user filter for specific task - allow or block specific users"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            task_config = self.forwarder_instance.get_task_config(task_id)
            if not task_config:
                await event.answer("❌ المهمة غير موجودة", alert=True)
                return
            
            def get_status_emoji(enabled):
                return "✅" if enabled else "❌"
            
            user_filter_enabled = getattr(task_config, 'user_filter_enabled', False)
            filter_type = getattr(task_config, 'user_filter_type', 'allow')  # allow or block
            allowed_users = getattr(task_config, 'allowed_users', '').split(',') if getattr(task_config, 'allowed_users', '') else []
            blocked_users = getattr(task_config, 'blocked_users', '').split(',') if getattr(task_config, 'blocked_users', '') else []
            
            text = (
                f"👥 **فلتر المستخدمين للمهمة**\n\n"
                f"📝 **المهمة:** {task_config.name}\n"
                f"🔧 **الحالة:** {get_status_emoji(user_filter_enabled)}\n"
                f"📋 **نوع الفلتر:** {'السماح لمستخدمين محددين' if filter_type == 'allow' else 'حظر مستخدمين محددين'}\n\n"
                f"✅ **المستخدمون المسموحون:** {len(allowed_users)} مستخدم\n"
                f"🚫 **المستخدمون المحظورون:** {len(blocked_users)} مستخدم\n\n"
                f"💡 **يمكن إضافة المستخدمين بالمعرف أو ID أو رابط الحساب**"
            )
            
            keyboard = [
                [Button.inline(f"⚡ تفعيل/إلغاء {get_status_emoji(user_filter_enabled)}", f"toggle_user_filter_{task_id}".encode())],
                [Button.inline("✅ وضع السماح", f"set_user_filter_mode_{task_id}_allow".encode()),
                 Button.inline("🚫 وضع الحظر", f"set_user_filter_mode_{task_id}_block".encode())],
                [Button.inline("➕ إضافة مستخدمين مسموحين", f"add_allowed_users_{task_id}".encode()),
                 Button.inline("📋 عرض المسموحين", f"view_allowed_users_{task_id}".encode())],
                [Button.inline("➕ إضافة مستخدمين محظورين", f"add_blocked_users_{task_id}".encode()),
                 Button.inline("📋 عرض المحظورين", f"view_blocked_users_{task_id}".encode())],
                [Button.inline("🗑️ مسح كل المستخدمين", f"clear_all_users_{task_id}".encode())],
                [Button.inline("🔙 العودة لإعدادات المهمة", f"edit_specific_{task_id}".encode())]
            ]
            
            await event.edit(text, buttons=keyboard)
            
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    # Character Limit Filter Functions
    async def edit_task_char_limit(self, event, task_id):
        """Edit character limit filter for specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            task_config = self.forwarder_instance.get_task_config(task_id)
            if not task_config:
                await event.answer("❌ المهمة غير موجودة", alert=True)
                return
            
            def get_status_emoji(enabled):
                return "✅" if enabled else "❌"
            
            char_limit_enabled = getattr(task_config, 'char_limit_enabled', False)
            min_chars = getattr(task_config, 'min_chars', 0)
            max_chars = getattr(task_config, 'max_chars', 4096)
            
            text = (
                f"📏 **فلتر حد الأحرف للمهمة**\n\n"
                f"📝 **المهمة:** {task_config.name}\n"
                f"🔧 **الحالة:** {get_status_emoji(char_limit_enabled)}\n\n"
                f"📊 **الحد الأدنى:** {min_chars} حرف\n"
                f"📈 **الحد الأقصى:** {max_chars} حرف\n\n"
                f"💡 **سيتم حظر الرسائل التي لا تحترم هذه الحدود**"
            )
            
            keyboard = [
                [Button.inline(f"⚡ تفعيل/إلغاء {get_status_emoji(char_limit_enabled)}", f"toggle_char_limit_{task_id}".encode())],
                [Button.inline("📊 تعديل الحد الأدنى", f"set_min_chars_{task_id}".encode()),
                 Button.inline("📈 تعديل الحد الأقصى", f"set_max_chars_{task_id}".encode())],
                [Button.inline("🔄 إعادة ضبط الحدود", f"reset_char_limits_{task_id}".encode())],
                [Button.inline("🔙 العودة لإعدادات المهمة", f"edit_specific_{task_id}".encode())]
            ]
            
            await event.edit(text, buttons=keyboard)
            
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    # Duplicate Filter Functions
    async def edit_task_duplicate_filter(self, event, task_id):
        """Edit duplicate messages filter for specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            task_config = self.forwarder_instance.get_task_config(task_id)
            if not task_config:
                await event.answer("❌ المهمة غير موجودة", alert=True)
                return
            
            def get_status_emoji(enabled):
                return "✅" if enabled else "❌"
            
            duplicate_filter_enabled = getattr(task_config, 'duplicate_filter_enabled', False)
            check_period_hours = getattr(task_config, 'duplicate_check_period', 24)
            similarity_threshold = getattr(task_config, 'similarity_threshold', 90)
            
            text = (
                f"🔄 **فلتر التكرار للمهمة**\n\n"
                f"📝 **المهمة:** {task_config.name}\n"
                f"🔧 **الحالة:** {get_status_emoji(duplicate_filter_enabled)}\n\n"
                f"⏰ **فترة التحقق:** {check_period_hours} ساعة\n"
                f"📊 **حد التشابه:** {similarity_threshold}%\n\n"
                f"💡 **يمنع إرسال رسائل مشابهة أو مكررة خلال الفترة المحددة**"
            )
            
            keyboard = [
                [Button.inline(f"⚡ تفعيل/إلغاء {get_status_emoji(duplicate_filter_enabled)}", f"toggle_duplicate_filter_{task_id}".encode())],
                [Button.inline("⏰ تعديل فترة التحقق", f"set_check_period_{task_id}".encode()),
                 Button.inline("📊 تعديل حد التشابه", f"set_similarity_{task_id}".encode())],
                [Button.inline("🗑️ مسح سجل الرسائل", f"clear_message_history_{task_id}".encode())],
                [Button.inline("🔙 العودة لإعدادات المهمة", f"edit_specific_{task_id}".encode())]
            ]
            
            await event.edit(text, buttons=keyboard)
            
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    # Transparent Buttons Filter Functions
    async def edit_task_transparent_buttons(self, event, task_id):
        """Edit transparent buttons filter for specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            task_config = self.forwarder_instance.get_task_config(task_id)
            if not task_config:
                await event.answer("❌ المهمة غير موجودة", alert=True)
                return
            
            def get_status_emoji(enabled):
                return "✅" if enabled else "❌"
            
            transparent_buttons_enabled = getattr(task_config, 'transparent_buttons_enabled', False)
            remove_inline_buttons = getattr(task_config, 'remove_inline_buttons', False)
            remove_reply_buttons = getattr(task_config, 'remove_reply_buttons', False)
            
            text = (
                f"🔘 **فلتر الأزرار الشفافة للمهمة**\n\n"
                f"📝 **المهمة:** {task_config.name}\n"
                f"🔧 **الحالة:** {get_status_emoji(transparent_buttons_enabled)}\n\n"
                f"🔘 **حذف الأزرار المدمجة:** {get_status_emoji(remove_inline_buttons)}\n"
                f"⌨️ **حذف أزرار الرد:** {get_status_emoji(remove_reply_buttons)}\n\n"
                f"💡 **يزيل الأزرار الشفافة من الرسائل عند التوجيه**"
            )
            
            keyboard = [
                [Button.inline(f"⚡ تفعيل/إلغاء {get_status_emoji(transparent_buttons_enabled)}", f"toggle_transparent_buttons_{task_id}".encode())],
                [Button.inline(f"🔘 الأزرار المدمجة {get_status_emoji(remove_inline_buttons)}", f"toggle_inline_buttons_{task_id}".encode()),
                 Button.inline(f"⌨️ أزرار الرد {get_status_emoji(remove_reply_buttons)}", f"toggle_reply_buttons_{task_id}".encode())],
                [Button.inline("🔙 العودة لإعدادات المهمة", f"edit_specific_{task_id}".encode())]
            ]
            
            await event.edit(text, buttons=keyboard)
            
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    # Message Formatting Functions
    async def edit_task_message_formatting(self, event, task_id):
        """Edit message formatting for specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            task_config = self.forwarder_instance.get_task_config(task_id)
            if not task_config:
                await event.answer("❌ المهمة غير موجودة", alert=True)
                return
            
            def get_status_emoji(enabled):
                return "✅" if enabled else "❌"
            
            formatting_enabled = getattr(task_config, 'message_formatting_enabled', False)
            current_format = getattr(task_config, 'message_format', 'original')
            
            format_names = {
                'original': 'الأصلي',
                'regular': 'عادي',
                'bold': 'عريض',
                'italic': 'مائل',
                'underline': 'مسطر',
                'strike': 'مشطوب',
                'code': 'كود',
                'mono': 'أحادي المسافة',
                'quote': 'اقتباس',
                'spoiler': 'مخفي',
                'hyperlink': 'رابط'
            }
            
            text = (
                f"🎨 **تنسيق الرسائل للمهمة**\n\n"
                f"📝 **المهمة:** {task_config.name}\n"
                f"🔧 **الحالة:** {get_status_emoji(formatting_enabled)}\n"
                f"🎨 **التنسيق الحالي:** {format_names.get(current_format, current_format)}\n\n"
                f"💡 **يطبق التنسيق المحدد على النصوص قبل التوجيه**"
            )
            
            keyboard = [
                [Button.inline(f"⚡ تفعيل/إلغاء {get_status_emoji(formatting_enabled)}", f"toggle_message_formatting_{task_id}".encode())],
                [Button.inline("📝 الأصلي", f"set_message_format_{task_id}_original".encode()),
                 Button.inline("📄 عادي", f"set_message_format_{task_id}_regular".encode())],
                [Button.inline("🔲 عريض", f"set_message_format_{task_id}_bold".encode()),
                 Button.inline("🔡 مائل", f"set_message_format_{task_id}_italic".encode())],
                [Button.inline("📎 مسطر", f"set_message_format_{task_id}_underline".encode()),
                 Button.inline("🚫 مشطوب", f"set_message_format_{task_id}_strike".encode())],
                [Button.inline("💻 كود", f"set_message_format_{task_id}_code".encode()),
                 Button.inline("⌨️ أحادي", f"set_message_format_{task_id}_mono".encode())],
                [Button.inline("💬 اقتباس", f"set_message_format_{task_id}_quote".encode()),
                 Button.inline("🔒 مخفي", f"set_message_format_{task_id}_spoiler".encode())],
                [Button.inline("🔗 رابط", f"set_message_format_{task_id}_hyperlink".encode())],
                [Button.inline("🔙 العودة لإعدادات المهمة", f"edit_specific_{task_id}".encode())]
            ]
            
            await event.edit(text, buttons=keyboard)
            
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    # Enhanced Text Cleaner Functions
    async def edit_enhanced_text_cleaner(self, event, task_id):
        """Edit enhanced text cleaner for specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            task_config = self.forwarder_instance.get_task_config(task_id)
            if not task_config:
                await event.answer("❌ المهمة غير موجودة", alert=True)
                return
            
            def get_status_emoji(enabled):
                return "✅" if enabled else "❌"
            
            clean_emojis = getattr(task_config, 'clean_emojis', False)
            clean_emails = getattr(task_config, 'clean_emails', False)
            clean_usernames = getattr(task_config, 'clean_usernames', False)
            clean_phone_numbers = getattr(task_config, 'clean_phone_numbers', False)
            clean_captions = getattr(task_config, 'clean_captions', False)
            clean_punctuation = getattr(task_config, 'clean_punctuation', False)
            
            text = (
                f"🧹 **منظف النصوص المحسن للمهمة**\n\n"
                f"📝 **المهمة:** {task_config.name}\n\n"
                f"🔧 **خيارات التنظيف المتقدمة:**\n"
                f"{get_status_emoji(clean_emojis)} تنظيف الإيموجيات\n"
                f"{get_status_emoji(clean_emails)} تنظيف الإيميلات\n"
                f"{get_status_emoji(clean_usernames)} تنظيف المعرفات (@username)\n"
                f"{get_status_emoji(clean_phone_numbers)} تنظيف أرقام الهواتف\n"
                f"{get_status_emoji(clean_captions)} تنظيف الكابشن\n"
                f"{get_status_emoji(clean_punctuation)} تنظيف علامات الترقيم\n"
            )
            
            keyboard = [
                [Button.inline(f"😊 الإيموجيات {get_status_emoji(clean_emojis)}", f"toggle_clean_emojis_{task_id}".encode()),
                 Button.inline(f"📧 الإيميلات {get_status_emoji(clean_emails)}", f"toggle_clean_emails_{task_id}".encode())],
                [Button.inline(f"@ المعرفات {get_status_emoji(clean_usernames)}", f"toggle_clean_usernames_{task_id}".encode()),
                 Button.inline(f"📱 أرقام الهواتف {get_status_emoji(clean_phone_numbers)}", f"toggle_clean_phones_{task_id}".encode())],
                [Button.inline(f"📝 الكابشن {get_status_emoji(clean_captions)}", f"toggle_clean_captions_{task_id}".encode()),
                 Button.inline(f".,!? علامات الترقيم {get_status_emoji(clean_punctuation)}", f"toggle_clean_punctuation_{task_id}".encode())],
                [Button.inline("🔙 العودة لمنظف النصوص", f"edit_text_cleaner_{task_id}".encode())]
            ]
            
            await event.edit(text, buttons=keyboard)
            
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    # Link Preview Functions
    async def edit_task_link_preview(self, event, task_id):
        """Edit link preview settings for specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            task_config = self.forwarder_instance.get_task_config(task_id)
            if not task_config:
                await event.answer("❌ المهمة غير موجودة", alert=True)
                return
            
            def get_status_emoji(enabled):
                return "✅" if enabled else "❌"
            
            link_preview_enabled = getattr(task_config, 'link_preview_enabled', True)
            
            text = (
                f"🔗 **معاينة الروابط للمهمة**\n\n"
                f"📝 **المهمة:** {task_config.name}\n"
                f"🔧 **الحالة:** {get_status_emoji(link_preview_enabled)}\n\n"
                f"💡 **عند التفعيل، ستظهر معاينة الروابط مع الرسائل**\n"
                f"🚫 **عند الإلغاء، ستُرسل الروابط كنص عادي بدون معاينة**"
            )
            
            keyboard = [
                [Button.inline(f"⚡ تفعيل/إلغاء معاينة الروابط {get_status_emoji(link_preview_enabled)}", f"toggle_link_preview_{task_id}".encode())],
                [Button.inline("🔙 العودة لإعدادات المهمة", f"edit_specific_{task_id}".encode())]
            ]
            
            await event.edit(text, buttons=keyboard)
            
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    async def toggle_task_link_preview(self, event, task_id):
        """Toggle link preview for specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            task_config = self.forwarder_instance.get_task_config(task_id)
            if not task_config:
                await event.answer("❌ المهمة غير موجودة", alert=True)
                return
            
            current_enabled = getattr(task_config, 'link_preview_enabled', True)
            new_enabled = not current_enabled
            
            success = self.forwarder_instance.update_task_config(task_id, link_preview_enabled=new_enabled)
            if success:
                status_text = "مفعلة" if new_enabled else "معطلة"
                await event.answer(f"✅ معاينة الروابط أصبحت {status_text}", alert=False)
                await self.edit_task_link_preview(event, task_id)
            else:
                await event.answer("❌ فشل في تحديث الإعدادات", alert=True)
                
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    # Message Delay Functions
    async def edit_task_message_delay(self, event, task_id):
        """Edit message delay for specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            task_config = self.forwarder_instance.get_task_config(task_id)
            if not task_config:
                await event.answer("❌ المهمة غير موجودة", alert=True)
                return
            
            def get_status_emoji(enabled):
                return "✅" if enabled else "❌"
            
            message_delay_enabled = getattr(task_config, 'message_delay_enabled', False)
            message_delay_seconds = getattr(task_config, 'message_delay_seconds', 0)
            
            text = (
                f"⏱️ **تأخير الرسائل للمهمة**\n\n"
                f"📝 **المهمة:** {task_config.name}\n"
                f"🔧 **الحالة:** {get_status_emoji(message_delay_enabled)}\n"
                f"⏰ **مدة التأخير:** {message_delay_seconds} ثانية\n\n"
                f"💡 **تأخير نشر الرسالة من المصدر إلى الهدف**\n"
                f"🕒 **مفيد للتأكد من المحتوى قبل النشر**"
            )
            
            keyboard = [
                [Button.inline(f"⚡ تفعيل/إلغاء {get_status_emoji(message_delay_enabled)}", f"toggle_message_delay_{task_id}".encode())],
                [Button.inline("⏱️ تعديل مدة التأخير", f"set_message_delay_{task_id}".encode())],
                [Button.inline("🔄 إعادة ضبط", f"reset_message_delay_{task_id}".encode())],
                [Button.inline("🔙 العودة لإعدادات المهمة", f"edit_specific_{task_id}".encode())]
            ]
            
            await event.edit(text, buttons=keyboard)
            
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    # Forward Delay Functions
    async def edit_task_forward_delay(self, event, task_id):
        """Edit forward delay for specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            task_config = self.forwarder_instance.get_task_config(task_id)
            if not task_config:
                await event.answer("❌ المهمة غير موجودة", alert=True)
                return
            
            def get_status_emoji(enabled):
                return "✅" if enabled else "❌"
            
            forward_delay_enabled = getattr(task_config, 'forward_delay_enabled', False)
            forward_delay_seconds = getattr(task_config, 'forward_delay_seconds', 1)
            
            text = (
                f"🔄 **تأخير التوجيه للمهمة**\n\n"
                f"📝 **المهمة:** {task_config.name}\n"
                f"🔧 **الحالة:** {get_status_emoji(forward_delay_enabled)}\n"
                f"⏰ **الفاصل الزمني:** {forward_delay_seconds} ثانية\n\n"
                f"💡 **فاصل زمني بين كل قناة هدف عند التوجيه لعدة قنوات**\n"
                f"⚡ **يمنع التحميل الزائد على الخادم**"
            )
            
            keyboard = [
                [Button.inline(f"⚡ تفعيل/إلغاء {get_status_emoji(forward_delay_enabled)}", f"toggle_forward_delay_{task_id}".encode())],
                [Button.inline("⏱️ تعديل الفاصل الزمني", f"set_forward_delay_{task_id}".encode())],
                [Button.inline("🔄 إعادة ضبط", f"reset_forward_delay_{task_id}".encode())],
                [Button.inline("🔙 العودة لإعدادات المهمة", f"edit_specific_{task_id}".encode())]
            ]
            
            await event.edit(text, buttons=keyboard)
            
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    # Notification Settings Functions
    async def edit_task_notification_settings(self, event, task_id):
        """Edit notification settings for specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            task_config = self.forwarder_instance.get_task_config(task_id)
            if not task_config:
                await event.answer("❌ المهمة غير موجودة", alert=True)
                return
            
            def get_status_emoji(enabled):
                return "✅" if enabled else "❌"
            
            silent_mode = getattr(task_config, 'silent_mode', False)
            disable_notifications = getattr(task_config, 'disable_notifications', False)
            
            text = (
                f"🔔 **إعدادات الإشعارات للمهمة**\n\n"
                f"📝 **المهمة:** {task_config.name}\n\n"
                f"🔕 **الوضع الصامت:** {get_status_emoji(silent_mode)}\n"
                f"🔔 **تعطيل الإشعارات:** {get_status_emoji(disable_notifications)}\n\n"
                f"💡 **الوضع الصامت: لا يُظهر إشعارات للمتابعين**\n"
                f"🔕 **تعطيل الإشعارات: يمنع جميع الإشعارات**"
            )
            
            keyboard = [
                [Button.inline(f"🔕 الوضع الصامت {get_status_emoji(silent_mode)}", f"toggle_silent_mode_{task_id}".encode())],
                [Button.inline(f"🔔 تعطيل الإشعارات {get_status_emoji(disable_notifications)}", f"toggle_notifications_{task_id}".encode())],
                [Button.inline("🔙 العودة لإعدادات المهمة", f"edit_specific_{task_id}".encode())]
            ]
            
            await event.edit(text, buttons=keyboard)
            
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    async def toggle_task_silent_mode(self, event, task_id):
        """Toggle silent mode for specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            task_config = self.forwarder_instance.get_task_config(task_id)
            if not task_config:
                await event.answer("❌ المهمة غير موجودة", alert=True)
                return
            
            current_enabled = getattr(task_config, 'silent_mode', False)
            new_enabled = not current_enabled
            
            success = self.forwarder_instance.update_task_config(task_id, silent_mode=new_enabled)
            if success:
                status_text = "مفعل" if new_enabled else "معطل"
                await event.answer(f"✅ الوضع الصامت أصبح {status_text}", alert=False)
                await self.edit_task_notification_settings(event, task_id)
            else:
                await event.answer("❌ فشل في تحديث الإعدادات", alert=True)
                
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    # Sync Settings Functions
    async def edit_task_sync_settings(self, event, task_id):
        """Edit sync settings for specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            task_config = self.forwarder_instance.get_task_config(task_id)
            if not task_config:
                await event.answer("❌ المهمة غير موجودة", alert=True)
                return
            
            def get_status_emoji(enabled):
                return "✅" if enabled else "❌"
            
            sync_delete = getattr(task_config, 'sync_delete', False)
            sync_edit = getattr(task_config, 'sync_edit', False)
            
            text = (
                f"🔗 **مزامنة التعديل والحذف للمهمة**\n\n"
                f"📝 **المهمة:** {task_config.name}\n\n"
                f"🗑️ **مزامنة الحذف:** {get_status_emoji(sync_delete)}\n"
                f"✏️ **مزامنة التعديل:** {get_status_emoji(sync_edit)}\n\n"
                f"💡 **مزامنة الحذف: عند حذف رسالة في المصدر تُحذف في الهدف**\n"
                f"🔄 **مزامنة التعديل: عند تعديل رسالة في المصدر تُعدل في الهدف**"
            )
            
            keyboard = [
                [Button.inline(f"🗑️ مزامنة الحذف {get_status_emoji(sync_delete)}", f"toggle_sync_delete_{task_id}".encode())],
                [Button.inline(f"✏️ مزامنة التعديل {get_status_emoji(sync_edit)}", f"toggle_sync_edit_{task_id}".encode())],
                [Button.inline("🔙 العودة لإعدادات المهمة", f"edit_specific_{task_id}".encode())]
            ]
            
            await event.edit(text, buttons=keyboard)
            
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    async def toggle_task_sync_delete(self, event, task_id):
        """Toggle sync delete for specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            task_config = self.forwarder_instance.get_task_config(task_id)
            if not task_config:
                await event.answer("❌ المهمة غير موجودة", alert=True)
                return
            
            current_enabled = getattr(task_config, 'sync_delete', False)
            new_enabled = not current_enabled
            
            success = self.forwarder_instance.update_task_config(task_id, sync_delete=new_enabled)
            if success:
                status_text = "مفعلة" if new_enabled else "معطلة"
                await event.answer(f"✅ مزامنة الحذف أصبحت {status_text}", alert=False)
                await self.edit_task_sync_settings(event, task_id)
            else:
                await event.answer("❌ فشل في تحديث الإعدادات", alert=True)
                
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    async def toggle_task_sync_edit(self, event, task_id):
        """Toggle sync edit for specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            task_config = self.forwarder_instance.get_task_config(task_id)
            if not task_config:
                await event.answer("❌ المهمة غير موجودة", alert=True)
                return
            
            current_enabled = getattr(task_config, 'sync_edit', False)
            new_enabled = not current_enabled
            
            success = self.forwarder_instance.update_task_config(task_id, sync_edit=new_enabled)
            if success:
                status_text = "مفعلة" if new_enabled else "معطلة"
                await event.answer(f"✅ مزامنة التعديل أصبحت {status_text}", alert=False)
                await self.edit_task_sync_settings(event, task_id)
            else:
                await event.answer("❌ فشل في تحديث الإعدادات", alert=True)
                
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    # Reply Preservation Functions
    async def edit_task_reply_preservation(self, event, task_id):
        """Edit reply preservation for specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            task_config = self.forwarder_instance.get_task_config(task_id)
            if not task_config:
                await event.answer("❌ المهمة غير موجودة", alert=True)
                return
            
            def get_status_emoji(enabled):
                return "✅" if enabled else "❌"
            
            preserve_replies = getattr(task_config, 'preserve_replies', False)
            
            text = (
                f"💬 **المحافظة على الردود للمهمة**\n\n"
                f"📝 **المهمة:** {task_config.name}\n"
                f"🔧 **الحالة:** {get_status_emoji(preserve_replies)}\n\n"
                f"💡 **عند التفعيل:**\n"
                f"📩 **إذا كانت الرسالة في المصدر رد على رسالة معينة**\n"
                f"🔄 **سيتم الرد على نفس الرسالة في الهدف**\n"
                f"🔗 **يحافظ على شكل المحادثة ونظام الردود**"
            )
            
            keyboard = [
                [Button.inline(f"⚡ تفعيل/إلغاء المحافظة على الردود {get_status_emoji(preserve_replies)}", f"toggle_reply_preservation_{task_id}".encode())],
                [Button.inline("🔙 العودة لإعدادات المهمة", f"edit_specific_{task_id}".encode())]
            ]
            
            await event.edit(text, buttons=keyboard)
            
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    async def toggle_task_reply_preservation(self, event, task_id):
        """Toggle reply preservation for specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            task_config = self.forwarder_instance.get_task_config(task_id)
            if not task_config:
                await event.answer("❌ المهمة غير موجودة", alert=True)
                return
            
            current_enabled = getattr(task_config, 'preserve_replies', False)
            new_enabled = not current_enabled
            
            success = self.forwarder_instance.update_task_config(task_id, preserve_replies=new_enabled)
            if success:
                status_text = "مفعلة" if new_enabled else "معطلة"
                await event.answer(f"✅ المحافظة على الردود أصبحت {status_text}", alert=False)
                await self.edit_task_reply_preservation(event, task_id)
            else:
                await event.answer("❌ فشل في تحديث الإعدادات", alert=True)
                
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    # Pin Messages Functions
    async def edit_task_pin_messages(self, event, task_id):
        """Edit pin messages for specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            task_config = self.forwarder_instance.get_task_config(task_id)
            if not task_config:
                await event.answer("❌ المهمة غير موجودة", alert=True)
                return
            
            def get_status_emoji(enabled):
                return "✅" if enabled else "❌"
            
            pin_messages = getattr(task_config, 'pin_messages', False)
            pin_notify = getattr(task_config, 'pin_notify', True)
            
            text = (
                f"📌 **تثبيت الرسائل للمهمة**\n\n"
                f"📝 **المهمة:** {task_config.name}\n"
                f"🔧 **الحالة:** {get_status_emoji(pin_messages)}\n"
                f"🔔 **إشعار التثبيت:** {get_status_emoji(pin_notify)}\n\n"
                f"💡 **عند التفعيل:**\n"
                f"📌 **ستُثبت الرسائل المُوجهة في القناة الهدف**\n"
                f"🔔 **يمكن تفعيل/إلغاء إشعار التثبيت**"
            )
            
            keyboard = [
                [Button.inline(f"⚡ تفعيل/إلغاء التثبيت {get_status_emoji(pin_messages)}", f"toggle_pin_messages_{task_id}".encode())],
                [Button.inline(f"🔔 إشعار التثبيت {get_status_emoji(pin_notify)}", f"toggle_pin_notify_{task_id}".encode())],
                [Button.inline("🔙 العودة لإعدادات المهمة", f"edit_specific_{task_id}".encode())]
            ]
            
            await event.edit(text, buttons=keyboard)
            
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    async def toggle_task_pin_messages(self, event, task_id):
        """Toggle pin messages for specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            task_config = self.forwarder_instance.get_task_config(task_id)
            if not task_config:
                await event.answer("❌ المهمة غير موجودة", alert=True)
                return
            
            current_enabled = getattr(task_config, 'pin_messages', False)
            new_enabled = not current_enabled
            
            success = self.forwarder_instance.update_task_config(task_id, pin_messages=new_enabled)
            if success:
                status_text = "مفعل" if new_enabled else "معطل"
                await event.answer(f"✅ تثبيت الرسائل أصبح {status_text}", alert=False)
                await self.edit_task_pin_messages(event, task_id)
            else:
                await event.answer("❌ فشل في تحديث الإعدادات", alert=True)
                
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    # Forwarding Type Functions (Auto/Manual)
    async def edit_task_forwarding_type(self, event, task_id):
        """Edit forwarding type for specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            task_config = self.forwarder_instance.get_task_config(task_id)
            if not task_config:
                await event.answer("❌ المهمة غير موجودة", alert=True)
                return
            
            forwarding_type = getattr(task_config, 'forwarding_type', 'auto')  # auto or manual
            admin_chat_id = getattr(task_config, 'admin_chat_id', '')
            
            type_text = "تلقائي" if forwarding_type == 'auto' else "يدوي"
            
            text = (
                f"🎯 **نوع التوجيه للمهمة**\n\n"
                f"📝 **المهمة:** {task_config.name}\n"
                f"🔧 **النوع الحالي:** {type_text}\n\n"
                f"⚡ **تلقائي:** يُوجه الرسائل مباشرة\n"
                f"👥 **يدوي:** يرسل للمشرفين للموافقة أولاً\n"
                f"📱 **معرف المشرف:** {admin_chat_id or 'غير محدد'}\n\n"
                f"💡 **في الوضع اليدوي ستُرسل رسالة معاينة للمشرفين للموافقة أو الرفض**"
            )
            
            keyboard = [
                [Button.inline("⚡ تلقائي", f"set_forwarding_type_{task_id}_auto".encode()),
                 Button.inline("👥 يدوي", f"set_forwarding_type_{task_id}_manual".encode())],
                [Button.inline("👤 تعديل معرف المشرف", f"set_admin_chat_{task_id}".encode())],
                [Button.inline("🔙 العودة لإعدادات المهمة", f"edit_specific_{task_id}".encode())]
            ]
            
            await event.edit(text, buttons=keyboard)
            
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    async def set_task_forwarding_type(self, event, task_id, forward_type):
        """Set forwarding type for specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            success = self.forwarder_instance.update_task_config(task_id, forwarding_type=forward_type)
            if success:
                type_text = "تلقائي" if forward_type == 'auto' else "يدوي"
                await event.answer(f"✅ تم تغيير نوع التوجيه إلى: {type_text}", alert=False)
                await self.edit_task_forwarding_type(event, task_id)
            else:
                await event.answer("❌ فشل في تحديث الإعدادات", alert=True)
                
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    async def set_task_message_format(self, event, task_id, format_type):
        """Set message format for specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            success = self.forwarder_instance.update_task_config(task_id, message_format=format_type)
            if success:
                format_names = {
                    'original': 'الأصلي',
                    'regular': 'عادي',
                    'bold': 'عريض',
                    'italic': 'مائل',
                    'underline': 'مسطر',
                    'strike': 'مشطوب',
                    'code': 'كود',
                    'mono': 'أحادي المسافة',
                    'quote': 'اقتباس',
                    'spoiler': 'مخفي',
                    'hyperlink': 'رابط'
                }
                format_name = format_names.get(format_type, format_type)
                await event.answer(f"✅ تم تغيير التنسيق إلى: {format_name}", alert=False)
                await self.edit_task_message_formatting(event, task_id)
            else:
                await event.answer("❌ فشل في تحديث الإعدادات", alert=True)
                
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    # Add missing toggle functions that we need
    async def toggle_task_user_filter(self, event, task_id):
        """Toggle user filter for specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            task_config = self.forwarder_instance.get_task_config(task_id)
            if not task_config:
                await event.answer("❌ المهمة غير موجودة", alert=True)
                return
            
            current_value = getattr(task_config, 'user_filter_enabled', False)
            new_value = not current_value
            
            success = self.forwarder_instance.update_task_config(task_id, user_filter_enabled=new_value)
            if success:
                status_text = "مفعل" if new_value else "معطل"
                await event.answer(f"✅ فلتر المستخدمين أصبح {status_text}", alert=False)
                await self.edit_task_user_filter(event, task_id)
            else:
                await event.answer("❌ فشل في تحديث الإعدادات", alert=True)
                
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    async def toggle_task_char_limit(self, event, task_id):
        """Toggle char limit filter for specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            task_config = self.forwarder_instance.get_task_config(task_id)
            if not task_config:
                await event.answer("❌ المهمة غير موجودة", alert=True)
                return
            
            current_value = getattr(task_config, 'char_limit_enabled', False)
            new_value = not current_value
            
            success = self.forwarder_instance.update_task_config(task_id, char_limit_enabled=new_value)
            if success:
                status_text = "مفعل" if new_value else "معطل"
                await event.answer(f"✅ فلتر حد الأحرف أصبح {status_text}", alert=False)
                await self.edit_task_char_limit(event, task_id)
            else:
                await event.answer("❌ فشل في تحديث الإعدادات", alert=True)
                
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    async def toggle_task_duplicate_filter(self, event, task_id):
        """Toggle duplicate filter for specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            task_config = self.forwarder_instance.get_task_config(task_id)
            if not task_config:
                await event.answer("❌ المهمة غير موجودة", alert=True)
                return
            
            current_value = getattr(task_config, 'duplicate_filter_enabled', False)
            new_value = not current_value
            
            success = self.forwarder_instance.update_task_config(task_id, duplicate_filter_enabled=new_value)
            if success:
                status_text = "مفعل" if new_value else "معطل"
                await event.answer(f"✅ فلتر التكرار أصبح {status_text}", alert=False)
                await self.edit_task_duplicate_filter(event, task_id)
            else:
                await event.answer("❌ فشل في تحديث الإعدادات", alert=True)
                
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    async def toggle_task_transparent_buttons(self, event, task_id):
        """Toggle transparent buttons filter for specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            task_config = self.forwarder_instance.get_task_config(task_id)
            if not task_config:
                await event.answer("❌ المهمة غير موجودة", alert=True)
                return
            
            current_value = getattr(task_config, 'transparent_buttons_enabled', False)
            new_value = not current_value
            
            success = self.forwarder_instance.update_task_config(task_id, transparent_buttons_enabled=new_value)
            if success:
                status_text = "مفعل" if new_value else "معطل"
                await event.answer(f"✅ فلتر الأزرار الشفافة أصبح {status_text}", alert=False)
                await self.edit_task_transparent_buttons(event, task_id)
            else:
                await event.answer("❌ فشل في تحديث الإعدادات", alert=True)
                
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    async def toggle_task_message_formatting(self, event, task_id):
        """Toggle message formatting for specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            task_config = self.forwarder_instance.get_task_config(task_id)
            if not task_config:
                await event.answer("❌ المهمة غير موجودة", alert=True)
                return
            
            current_value = getattr(task_config, 'message_formatting_enabled', False)
            new_value = not current_value
            
            success = self.forwarder_instance.update_task_config(task_id, message_formatting_enabled=new_value)
            if success:
                status_text = "مفعل" if new_value else "معطل"
                await event.answer(f"✅ تنسيق الرسائل أصبح {status_text}", alert=False)
                await self.edit_task_message_formatting(event, task_id)
            else:
                await event.answer("❌ فشل في تحديث الإعدادات", alert=True)
                
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    async def toggle_task_message_delay(self, event, task_id):
        """Toggle message delay for specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            task_config = self.forwarder_instance.get_task_config(task_id)
            if not task_config:
                await event.answer("❌ المهمة غير موجودة", alert=True)
                return
            
            current_value = getattr(task_config, 'message_delay_enabled', False)
            new_value = not current_value
            
            success = self.forwarder_instance.update_task_config(task_id, message_delay_enabled=new_value)
            if success:
                status_text = "مفعل" if new_value else "معطل"
                await event.answer(f"✅ تأخير الرسائل أصبح {status_text}", alert=False)
                await self.edit_task_message_delay(event, task_id)
            else:
                await event.answer("❌ فشل في تحديث الإعدادات", alert=True)
                
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

    async def toggle_task_forward_delay(self, event, task_id):
        """Toggle forward delay for specific task"""
        try:
            if not self.forwarder_instance:
                await event.answer("❌ البوت الأساسي غير متصل", alert=True)
                return
            
            task_config = self.forwarder_instance.get_task_config(task_id)
            if not task_config:
                await event.answer("❌ المهمة غير موجودة", alert=True)
                return
            
            current_value = getattr(task_config, 'forward_delay_enabled', False)
            new_value = not current_value
            
            success = self.forwarder_instance.update_task_config(task_id, forward_delay_enabled=new_value)
            if success:
                status_text = "مفعل" if new_value else "معطل"
                await event.answer(f"✅ تأخير التوجيه أصبح {status_text}", alert=False)
                await self.edit_task_forward_delay(event, task_id)
            else:
                await event.answer("❌ فشل في تحديث الإعدادات", alert=True)
                
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)
                return
            
            format_names = {
                'original': 'الأصلي',
                'regular': 'عادي',
                'bold': 'عريض',
                'italic': 'مائل',
                'underline': 'مسطر',
                'strike': 'مشطوب',
                'code': 'كود',
                'mono': 'أحادي المسافة',
                'quote': 'اقتباس',
                'spoiler': 'مخفي',
                'hyperlink': 'رابط'
            }
            
            success = self.forwarder_instance.update_task_config(task_id, message_format=format_type)
            if success:
                format_text = format_names.get(format_type, format_type)
                await event.answer(f"✅ تم تغيير تنسيق الرسالة إلى: {format_text}", alert=False)
                await self.edit_task_message_formatting(event, task_id)
            else:
                await event.answer("❌ فشل في تحديث الإعدادات", alert=True)
                
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)

async def main():
    """Main function"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        control_bot = ModernControlBot()
        await control_bot.start()
        print("🚀 Modern control bot is running...")
        await control_bot.run_until_disconnected()
    except KeyboardInterrupt:
        print("⏹️ Modern control bot stopped")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
