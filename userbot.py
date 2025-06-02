"""
Telegram Userbot - Core forwarding functionality
"""

import asyncio
import configparser
import logging
import os
from telethon import TelegramClient, events
from telethon.errors import (
    FloodWaitError, 
    ChatWriteForbiddenError, 
    MessageNotModifiedError,
    RPCError
)
from telethon.tl.types import (
    MessageMediaPhoto, 
    MessageMediaDocument
)
from utils import ConfigManager, RateLimiter
from stats_manager import StatsManager

# Initialize global stats manager
stats_manager = StatsManager()

class TelegramForwarder:
    """Main class for Telegram message forwarding"""
    
    def __init__(self, config_path='config.ini'):
        self.logger = logging.getLogger(__name__)
        self.config_manager = ConfigManager(config_path)
        self.rate_limiter = RateLimiter()
        
        # Initialize Telegram client
        self.client = None
        self.source_chat = None
        self.target_chat = None
        self.forward_options = {}
        
        self._setup_client()
        self._load_config()
    
    def _setup_client(self):
        """Setup Telegram client with credentials"""
        try:
            # Get API credentials from environment or config
            api_id = os.getenv('TELEGRAM_API_ID') or self.config_manager.get('telegram', 'api_id')
            api_hash = os.getenv('TELEGRAM_API_HASH') or self.config_manager.get('telegram', 'api_hash')
            
            if not api_id or not api_hash or api_id == 'YOUR_API_ID':
                raise ValueError("Please set TELEGRAM_API_ID and TELEGRAM_API_HASH environment variables or update config.ini")
            
            # Check for string session first
            string_session = os.getenv('TELEGRAM_STRING_SESSION')
            
            if string_session and len(string_session) > 10:
                try:
                    # Use string session
                    from telethon.sessions import StringSession
                    self.client = TelegramClient(StringSession(string_session), int(api_id), api_hash)
                    self.logger.info("Using string session for authentication")
                except Exception as e:
                    self.logger.warning(f"Failed to use string session: {e}, falling back to file session")
                    self.client = TelegramClient('userbot_session', int(api_id), api_hash)
                    self.logger.info("Using session file for authentication")
            else:
                # Create client with session file
                self.client = TelegramClient('userbot_session', int(api_id), api_hash)
                self.logger.info("Using session file for authentication")
            
        except Exception as e:
            self.logger.error(f"Failed to setup Telegram client: {e}")
            raise
    
    def _load_config(self):
        """Load configuration settings"""
        try:
            # Load chat configurations - support multiple sources and targets
            source_chat_raw = self.config_manager.get('forwarding', 'source_chat')
            target_chat_raw = self.config_manager.get('forwarding', 'target_chat')

            # Parse multiple sources 
            if ',' in source_chat_raw:
                self.source_chats = [chat.strip() for chat in source_chat_raw.split(',') if chat.strip()]
            else:
                self.source_chats = [source_chat_raw.strip()]
            
            # Parse multiple targets (comma-separated)
            if ',' in target_chat_raw:
                self.target_chats = [chat.strip() for chat in target_chat_raw.split(',') if chat.strip()]
            else:
                self.target_chats = [target_chat_raw.strip()]
            
            # Keep backward compatibility
            self.source_chat = self.source_chats[0]
            self.target_chat = self.target_chats[0]
            
            # Load forwarding options including all media filters
            self.forward_options = {
                'delay': self.config_manager.getfloat('forwarding', 'forward_delay', fallback=1.0),
                'max_retries': self.config_manager.getint('forwarding', 'max_retries', fallback=3),
                'forward_text': self.config_manager.getboolean('forwarding', 'forward_text', fallback=True),
                'forward_photos': self.config_manager.getboolean('forwarding', 'forward_photos', fallback=True),
                'forward_videos': self.config_manager.getboolean('forwarding', 'forward_videos', fallback=True),
                'forward_music': self.config_manager.getboolean('forwarding', 'forward_music', fallback=True),
                'forward_audio': self.config_manager.getboolean('forwarding', 'forward_audio', fallback=True),
                'forward_voice': self.config_manager.getboolean('forwarding', 'forward_voice', fallback=True),
                'forward_video_messages': self.config_manager.getboolean('forwarding', 'forward_video_messages', fallback=True),
                'forward_files': self.config_manager.getboolean('forwarding', 'forward_files', fallback=True),
                'forward_links': self.config_manager.getboolean('forwarding', 'forward_links', fallback=True),
                'forward_gif': self.config_manager.getboolean('forwarding', 'forward_gif', fallback=True),
                'forward_gifs': self.config_manager.getboolean('forwarding', 'forward_gifs', fallback=True),
                'forward_contacts': self.config_manager.getboolean('forwarding', 'forward_contacts', fallback=True),
                'forward_locations': self.config_manager.getboolean('forwarding', 'forward_locations', fallback=True),
                'forward_polls': self.config_manager.getboolean('forwarding', 'forward_polls', fallback=True),
                'forward_stickers': self.config_manager.getboolean('forwarding', 'forward_stickers', fallback=True),
                'forward_round': self.config_manager.getboolean('forwarding', 'forward_round', fallback=True),
                'forward_games': self.config_manager.getboolean('forwarding', 'forward_games', fallback=True),
                'forward_mode': self.config_manager.get('forwarding', 'forward_mode', fallback='forward'),
                'header_enabled': self.config_manager.getboolean('forwarding', 'header_enabled', fallback=False),
                'footer_enabled': self.config_manager.getboolean('forwarding', 'footer_enabled', fallback=False),
                'header_text': self.config_manager.get('forwarding', 'header_text', fallback=''),
                'footer_text': self.config_manager.get('forwarding', 'footer_text', fallback=''),
                'blacklist_enabled': self.config_manager.getboolean('forwarding', 'blacklist_enabled', fallback=False),
                'whitelist_enabled': self.config_manager.getboolean('forwarding', 'whitelist_enabled', fallback=False),
                'blacklist_words': self.config_manager.get('forwarding', 'blacklist_words', fallback=''),
                'whitelist_words': self.config_manager.get('forwarding', 'whitelist_words', fallback=''),
                'clean_links': self.config_manager.getboolean('forwarding', 'clean_links', fallback=False),
                'clean_buttons': self.config_manager.getboolean('forwarding', 'clean_buttons', fallback=False),
                'clean_hashtags': self.config_manager.getboolean('forwarding', 'clean_hashtags', fallback=False),
                'clean_formatting': self.config_manager.getboolean('forwarding', 'clean_formatting', fallback=False),
                'clean_empty_lines': self.config_manager.getboolean('forwarding', 'clean_empty_lines', fallback=False),
                'clean_lines_with_words': self.config_manager.getboolean('forwarding', 'clean_lines_with_words', fallback=False),
                'clean_words_list': self.config_manager.get('forwarding', 'clean_words_list', fallback=''),
                'buttons_enabled': self.config_manager.getboolean('forwarding', 'buttons_enabled', fallback=False),
                'button1_text': self.config_manager.get('forwarding', 'button1_text', fallback=''),
                'button1_url': self.config_manager.get('forwarding', 'button1_url', fallback=''),
                'button2_text': self.config_manager.get('forwarding', 'button2_text', fallback=''),
                'button2_url': self.config_manager.get('forwarding', 'button2_url', fallback=''),
                'button3_text': self.config_manager.get('forwarding', 'button3_text', fallback=''),
                'button3_url': self.config_manager.get('forwarding', 'button3_url', fallback=''),
                # Text replacer settings
                'replacer_enabled': self.config_manager.getboolean('text_replacer', 'replacer_enabled', fallback=False),
                'replacements': self.config_manager.get('text_replacer', 'replacements', fallback=''),
                # Multi-mode settings
                'multi_mode_enabled': self.config_manager.getboolean('forwarding', 'multi_mode_enabled', fallback=False)
            }
            
            if not self.source_chat or not self.target_chat:
                raise ValueError("Please configure source_chat and target_chat in config.ini")
                
            self.logger.info(f"Configuration loaded - Source: {self.source_chat}, Target: {self.target_chat}")
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            raise
    
    async def start(self):
        """Start the userbot and authenticate"""
        try:
            await self.client.start()
            
            # Get user info
            me = await self.client.get_me()
            self.logger.info(f"Logged in as: {me.first_name} {me.last_name or ''} (@{me.username or 'N/A'})")
            
            # Validate chat access
            await self._validate_chats()
            
            # Register event handlers
            self._register_handlers()
            
            self.logger.info("Userbot started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start userbot: {e}")
            raise
    
    async def _validate_chats(self):
        """Validate access to source and target chats"""
        try:
            # Validate all source chats
            for i, source_chat in enumerate(self.source_chats):
                try:
                    try:
                        source_entity = await self.client.get_entity(int(source_chat))
                        self.logger.info(f"Source chat {i+1} validated: {getattr(source_entity, 'title', 'Private Chat')} ({source_chat})")
                    except ValueError:
                        # Try as username if not numeric
                        source_entity = await self.client.get_entity(source_chat)
                        self.logger.info(f"Source chat {i+1} validated: {getattr(source_entity, 'title', 'Private Chat')} ({source_chat})")
                except Exception as e:
                    self.logger.warning(f"Source chat {i+1} ({source_chat}) validation failed, but continuing: {e}")
            
            # Validate all target chats
            for i, target_chat in enumerate(self.target_chats):
                try:
                    try:
                        target_entity = await self.client.get_entity(int(target_chat))
                        self.logger.info(f"Target chat {i+1} validated: {getattr(target_entity, 'title', 'Private Chat')} ({target_chat})")
                    except ValueError:
                        # Try as username if not numeric
                        target_entity = await self.client.get_entity(target_chat)
                        self.logger.info(f"Target chat {i+1} validated: {getattr(target_entity, 'title', 'Private Chat')} ({target_chat})")
                except Exception as e:
                    self.logger.warning(f"Target chat {i+1} ({target_chat}) validation failed, but continuing: {e}")
            
        except Exception as e:
            self.logger.warning(f"Chat validation had issues, but starting anyway: {e}")
            # Don't raise - let the bot try to work and show specific errors when forwarding
    
    def _register_handlers(self):
        """Register event handlers for message monitoring"""
        
        # Ping command handler - responds to /ping from admin
        @self.client.on(events.NewMessage(pattern='/ping', from_users='me'))
        async def ping_handler(event):
            try:
                import time
                start_time = time.time()
                
                # Send ping response
                sources_list = "\n".join([f"  • `{chat}`" for chat in self.source_chats])
                targets_list = "\n".join([f"  • `{chat}`" for chat in self.target_chats])
                
                response = await event.respond(
                    "🤖 **Userbot Status**\n\n"
                    f"✅ **Online and Working**\n"
                    f"📥 **Monitoring ({len(self.source_chats)} sources):**\n{sources_list}\n"
                    f"📤 **Forwarding to ({len(self.target_chats)} targets):**\n{targets_list}\n"
                    f"⚡ **Response time:** {round((time.time() - start_time) * 1000)}ms\n"
                    f"🔄 **Forward delay:** {self.forward_options['delay']}s"
                )
                
                self.logger.info(f"Ping command received and responded")
                
            except Exception as e:
                self.logger.error(f"Error in ping handler: {e}")
        
        # Initialize processed messages tracker
        self.processed_messages = set()
        
        # Message forwarding handler - multiple sources support
        source_chat_ids = []
        for chat in self.source_chats:
            try:
                source_chat_ids.append(int(chat))
            except ValueError:
                # For username-based chats, we'll handle them in the event handler
                source_chat_ids.append(chat)
        
        @self.client.on(events.NewMessage(chats=source_chat_ids))
        async def handle_new_message(event):
            
            message_key = f"{event.chat_id}_{event.message.id}"
            
            if message_key in self.processed_messages:
                self.logger.info(f"🚫 Skipping duplicate: {message_key}")
                return
            
            self.processed_messages.add(message_key)
            self.logger.info(f"🔄 Processing: {message_key}")
            
            await self._process_message(event)
    
    async def _process_message(self, event):
        """Process and forward a new message"""
        try:
            message = event.message
            
            # Skip if message is from self
            if message.sender_id == (await self.client.get_me()).id:
                return
            
            # Reload configuration to get latest filter settings including Header/Footer
            # Force reload from file to get latest changes
            self.config_manager = ConfigManager('config.ini')
            self._load_config()

            # Log current filter settings for verification  
            text_enabled = self.forward_options.get('forward_text', True)
            photos_enabled = self.forward_options.get('forward_photos', True)
            forward_mode = self.forward_options.get('forward_mode', 'forward')
            header_enabled = self.forward_options.get('header_enabled', False)
            footer_enabled = self.forward_options.get('footer_enabled', False)
            header_text = self.forward_options.get('header_text', '')
            footer_text = self.forward_options.get('footer_text', '')
            source_chat_id = str(message.chat_id)
            self.logger.info(f"📋 معالجة رسالة من {source_chat_id} - النصوص: {text_enabled}, الصور: {photos_enabled}, الوضع: {forward_mode}, أهداف: {len(self.target_chats)}")
            
            # Apply rate limiting
            await self.rate_limiter.wait()
            
            # Check message type and forwarding options
            if not self._should_forward_message(message):
                self.logger.debug(f"Skipping message due to filter settings")
                return
            
            # Forward the message to all target chats
            successful_forwards = 0
            failed_forwards = 0
            
            for target_chat in self.target_chats:
                success = await self._forward_message_to_target(message, target_chat)
                if success:
                    successful_forwards += 1
                else:
                    failed_forwards += 1
            
            self.logger.info(f"Message (ID: {message.id}) - Success: {successful_forwards}/{len(self.target_chats)} targets")
            if failed_forwards > 0:
                self.logger.warning(f"Failed forwards: {failed_forwards}/{len(self.target_chats)} targets")
                
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
    
    def _should_forward_message(self, message):
        """Check if message should be forwarded based on configuration"""
        
        # First check blacklist and whitelist filters
        message_text = message.text or getattr(message, 'caption', '') or ""
        if message_text:
            try:
                # Reload config to get latest settings
                self._load_config()
                
                # Check blacklist (if enabled)
                blacklist_enabled = self.forward_options.get('blacklist_enabled', False)
                self.logger.info(f"🔍 Blacklist check: enabled={blacklist_enabled}")
                
                if blacklist_enabled:
                    blacklist_words = self.forward_options.get('blacklist_words', '').strip()
                    self.logger.info(f"🔍 Blacklist words: '{blacklist_words}'")
                    
                    if blacklist_words:
                        blacklist_list = [word.strip().lower() for word in blacklist_words.split(',') if word.strip()]
                        message_lower = message_text.lower()
                        self.logger.info(f"🔍 Checking message: '{message_text[:50]}...' against blacklist")
                        
                        for word in blacklist_list:
                            if word in message_lower:
                                self.logger.info(f"🚫 Message BLOCKED by blacklist: contains '{word}'")
                                return False
                        
                        self.logger.info(f"✅ Message passed blacklist check")
                
                # Check whitelist (if enabled)
                whitelist_enabled = self.forward_options.get('whitelist_enabled', False)
                self.logger.info(f"🔍 Whitelist check: enabled={whitelist_enabled}")
                
                if whitelist_enabled:
                    whitelist_words = self.forward_options.get('whitelist_words', '').strip()
                    self.logger.info(f"🔍 Whitelist words: '{whitelist_words}'")
                    
                    if whitelist_words:
                        whitelist_list = [word.strip().lower() for word in whitelist_words.split(',') if word.strip()]
                        message_lower = message_text.lower()
                        found_allowed_word = False
                        
                        for word in whitelist_list:
                            if word in message_lower:
                                found_allowed_word = True
                                self.logger.info(f"✅ Message ALLOWED by whitelist: contains '{word}'")
                                break
                        
                        if not found_allowed_word:
                            self.logger.info(f"⚪ Message BLOCKED by whitelist: no allowed words found")
                            return False
                        
            except Exception as e:
                self.logger.error(f"Error checking blacklist/whitelist: {str(e)}")
        
        # Check text messages
        if message.text and not message.media:
            return self.forward_options.get('forward_text', True)
        
        # Check media types
        if message.media:
            # Photos
            if message.photo:
                return self.forward_options.get('forward_photos', True)
            
            # Videos (including GIFs)
            if message.video:
                if message.gif:
                    return self.forward_options.get('forward_gif', True) or \
                           self.forward_options.get('forward_gifs', True)
                return self.forward_options.get('forward_videos', True)
            
            # Document-based media
            if message.document:
                # Stickers
                if message.sticker:
                    return self.forward_options.get('forward_stickers', True)
                
                # Voice messages
                if message.voice:
                    return self.forward_options.get('forward_voice', True)
                
                # Video messages (round videos)
                if message.video_note:
                    return self.forward_options.get('forward_round', True)
                
                # Audio files
                if message.audio:
                    # Check if it's music or regular audio
                    if hasattr(message.audio, 'title') and message.audio.title:
                        return self.forward_options.get('forward_music', True)
                    return self.forward_options.get('forward_audio', True)
                
                # Video messages (not round)
                if hasattr(message.document, 'mime_type') and message.document.mime_type:
                    if message.document.mime_type.startswith('video/'):
                        return self.forward_options.get('forward_video_messages', True)
                
                # Regular files/documents
                return self.forward_options.get('forward_files', True)
            
            # Contact
            if message.contact:
                return self.forward_options.get('forward_contacts', True)
            
            # Location/Venue
            if message.geo or message.venue:
                return self.forward_options.get('forward_locations', True)
            
            # Polls
            if message.poll:
                return self.forward_options.get('forward_polls', True)
            
            # Games
            if message.game:
                return self.forward_options.get('forward_games', True)
        
        # Check for web links in text
        if message.text and any(url in message.text.lower() for url in ['http://', 'https://', 'www.', 't.me/']):
            return self.forward_options.get('forward_links', True)
        
        return True
    
    async def _forward_message_to_target(self, message, target_chat):
        """Forward a message to a specific target with retry logic"""
        max_retries = self.forward_options['max_retries']
        
        for attempt in range(max_retries):
            try:
                # Try different formats for target chat
                target_entities_to_try = [
                    target_chat,
                    int(target_chat),
                    int(target_chat.replace('-100', '')) if str(target_chat).startswith('-100') else target_chat
                ]
                
                forwarded = False
                forward_mode = self.forward_options.get('forward_mode', 'forward')
                self.logger.info(f"🚀 Forward mode: {forward_mode}")
                
                for target_entity in target_entities_to_try:
                    try:
                        if forward_mode == 'copy':
                            # Copy mode: Send message as new without showing source
                            self.logger.info(f"📋 Using copy mode to {target_chat}")
                            await self._copy_message(message, target_entity)
                        else:
                            # Forward mode: Traditional forward with source info
                            self.logger.info(f"➡️ Using forward mode to {target_chat}")
                            await self.client.forward_messages(
                                entity=target_entity,
                                messages=message
                            )
                        
                        forwarded = True
                        break
                    except ValueError as ve:
                        self.logger.debug(f"Failed with entity {target_entity}: {ve}")
                        continue
                
                if not forwarded:
                    raise ValueError(f"Could not forward to any target entity format")
                
                # Smart delay: reduce delay for text, keep for media
                delay = self.forward_options['delay']
                if message.text and not message.media:
                    # Text messages can be faster
                    delay = max(0.1, delay * 0.3)
                elif message.media:
                    # Media needs more careful handling
                    delay = delay * 1.5
                
                if delay > 0:
                    await asyncio.sleep(delay)
                
                return True
                
            except FloodWaitError as e:
                # Smart flood wait handling
                if e.seconds <= 10:
                    # Short waits: wait the full time
                    wait_time = e.seconds
                elif e.seconds <= 60:
                    # Medium waits: wait 80% of the time
                    wait_time = int(e.seconds * 0.8)
                else:
                    # Long waits: cap at 5 minutes and retry more frequently
                    wait_time = min(300, int(e.seconds * 0.5))
                
                self.logger.warning(f"🛑 Rate limited by Telegram, waiting {wait_time} seconds (original: {e.seconds})")
                await asyncio.sleep(wait_time)
                
                # Add progressive delay reduction after flood wait
                if hasattr(self, '_consecutive_floods'):
                    self._consecutive_floods += 1
                else:
                    self._consecutive_floods = 1
                    
                if self._consecutive_floods > 3:
                    # Temporarily increase delay to avoid repeated floods
                    self.forward_options['delay'] = min(5, self.forward_options['delay'] * 1.5)
                    self.logger.info(f"⚡ Temporarily increased delay to {self.forward_options['delay']} seconds")
                
            except ChatWriteForbiddenError:
                self.logger.error("Cannot write to target chat - check permissions")
                return False
                
            except RPCError as e:
                self.logger.error(f"Telegram API error: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    continue
                return False
                
            except Exception as e:
                self.logger.error(f"Unexpected error forwarding message: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                return False

    async def _forward_message(self, message):
        """Forward a message to all targets - backward compatibility method"""
        successful_forwards = 0
        
        for target_chat in self.target_chats:
            success = await self._forward_message_to_target(message, target_chat)
            if success:
                successful_forwards += 1
        
        return successful_forwards > 0

    async def _copy_message(self, message, target_entity):
        """Copy message content without showing source"""
        # Initialize variables
        final_text = ""
        target_chat = None
        
        try:
            # Get original text (from text or caption), clean it, then add header and footer
            original_text = message.text or getattr(message, 'caption', '') or ""
            self.logger.info(f"🔧 Before cleaning: '{original_text[:50]}...' (length: {len(original_text)})")
            cleaned_text = self._clean_message_text(original_text)
            self.logger.info(f"🔧 After cleaning: '{cleaned_text[:50]}...' (length: {len(cleaned_text)})")
            final_text = self._add_header_footer(cleaned_text)
            
            # Try multiple ways to get the target entity
            target_formats = [
                target_entity,
                int(target_entity),
                int(str(target_entity).replace('-100', '')) if str(target_entity).startswith('-100') else target_entity
            ]
            
            for target_format in target_formats:
                try:
                    target_chat = await self.client.get_entity(target_format)
                    self.logger.info(f"✅ Found target entity: {target_format}")
                    break
                except Exception as e:
                    self.logger.debug(f"Failed with format {target_format}: {e}")
                    continue
            
            if not target_chat:
                raise ValueError(f"Could not find target entity with any format")
            
            # Log message type for debugging
            media_type = "None"
            if message.media:
                if hasattr(message.media, '__class__'):
                    media_type = message.media.__class__.__name__
            self.logger.info(f"🔍 Copy mode - Message type: text={bool(message.text)}, media={bool(message.media)} ({media_type}), web_preview={bool(getattr(message, 'web_preview', None))}")
            
            # Handle different message types for copy mode
            # Check if it's actual media (not just web preview)
            has_actual_media = message.media and not (hasattr(message.media, '__class__') and 'WebPage' in str(message.media.__class__))
            
            # Get inline buttons
            buttons = self._create_inline_buttons()
            self.logger.info(f"🔍 Buttons status: {buttons}")
            
            if has_actual_media:
                # Media message - send with caption if available
                self.logger.info("📎 Sending as media message (copy mode)")
                # Send media with caption and buttons
                await self.client.send_file(
                    target_chat, 
                    message.media, 
                    caption=final_text if final_text.strip() else None,
                    buttons=buttons
                )
            elif message.text or getattr(message, 'caption', ''):
                # Text message (including messages with links and link previews)
                self.logger.info("📝 Sending as text message (copy mode)")
                await self.client.send_message(
                    target_chat, 
                    final_text, 
                    link_preview=False,
                    buttons=buttons
                )
            else:
                # Empty message - skip
                self.logger.info("⚠️ Empty message, skipping")
                return
                
        except Exception as e:
            # If copy fails completely, raise error to trigger fallback
            self.logger.error(f"Copy failed: {e}")
            raise e

    def _add_header_footer(self, original_text):
        """Add header and footer to message text"""
        try:
            # Get current configuration using the existing loaded config
            header_enabled = self.forward_options.get('header_enabled', False)
            footer_enabled = self.forward_options.get('footer_enabled', False)
            header_text = self.forward_options.get('header_text', '').strip()
            footer_text = self.forward_options.get('footer_text', '').strip()
            
            # Build final message
            parts = []
            
            # Add header if enabled and text exists
            if header_enabled and header_text:
                parts.append(header_text)
            
            # Add original message
            if original_text:
                parts.append(original_text)
            
            # Add footer if enabled and text exists
            if footer_enabled and footer_text:
                parts.append(footer_text)
            
            # Join with double newlines for clear separation
            return '\n\n'.join(parts) if parts else original_text
            
        except Exception as e:
            self.logger.error(f"Error adding header/footer: {e}")
            return original_text

    def _create_inline_buttons(self):
        """Create inline keyboard buttons based on configuration"""
        try:
            # Get button settings from current config
            buttons_enabled = self.forward_options.get('buttons_enabled', False)
            
            if not buttons_enabled:
                return None
            
            # Import Button for inline keyboards
            from telethon import Button
            
            # Create simple button list for Telethon
            buttons = []
            
            # Check for up to 3 buttons
            for i in range(1, 4):
                button_text = self.forward_options.get(f'button{i}_text', '').strip()
                button_url = self.forward_options.get(f'button{i}_url', '').strip()
                
                if button_text and button_url:
                    # Create button for each row
                    buttons.append(Button.url(button_text, button_url))
            
            if buttons:
                self.logger.info(f"🔘 Created {len(buttons)} inline buttons")
                for i, button in enumerate(buttons):
                    self.logger.info(f"🔘 Button [{i}]: {button.text} -> {button.url}")
                
                return buttons
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error creating inline buttons: {e}")
            return None

    def _replace_text_content(self, text):
        """Replace text content based on configuration"""
        if not text:
            return text
            
        try:
            # Check if text replacer is enabled
            replacer_enabled = self.forward_options.get('replacer_enabled', False)
            if not replacer_enabled:
                return text
                
            original_text = text
            replacements_str = self.forward_options.get('replacements', '')
            
            if not replacements_str.strip():
                return text
                
            # Parse replacements (format: old1->new1,old2->new2,old3->)
            replacements = []
            for replacement in replacements_str.split(','):
                if '->' in replacement:
                    old_text, new_text = replacement.split('->', 1)
                    old_text = old_text.strip()
                    new_text = new_text.strip()
                    if old_text:  # Only add if old_text is not empty
                        replacements.append((old_text, new_text))
            
            if not replacements:
                return text
                
            # Apply replacements
            replacements_made = []
            for old_text, new_text in replacements:
                if old_text in text:
                    text = text.replace(old_text, new_text)
                    replacements_made.append(f"'{old_text}' -> '{new_text}'")
                    stats_manager.record_replacement_made()
            
            if replacements_made:
                self.logger.info(f"🔄 Text replacements made: {', '.join(replacements_made)}")
                self.logger.info(f"📝 Text length: {len(original_text)} -> {len(text)} chars")
            
            return text
            
        except Exception as e:
            self.logger.error(f"Error replacing text: {e}")
            return text

    def _clean_message_text(self, text):
        """Clean message text based on configuration settings"""
        if not text:
            return text
        
        try:
            # Apply text replacements first
            text = self._replace_text_content(text)
            
            # Get cleaning settings from current config
            clean_links = self.forward_options.get('clean_links', False)
            clean_hashtags = self.forward_options.get('clean_hashtags', False)
            clean_formatting = self.forward_options.get('clean_formatting', False)
            clean_empty_lines = self.forward_options.get('clean_empty_lines', False)
            clean_lines_with_words = self.forward_options.get('clean_lines_with_words', False)
            clean_words_list = self.forward_options.get('clean_words_list', '').strip()
            
            # Log cleaning settings for debugging
            self.logger.info(f"🧹 Cleaning settings: links={clean_links}, hashtags={clean_hashtags}, formatting={clean_formatting}")
            self.logger.info(f"📝 Original text: '{text[:100]}...' (length: {len(text)})")
            
            cleaned_text = text
            
            # Clean links and usernames
            if clean_links:
                import re
                # Remove HTTP(S) links
                cleaned_text = re.sub(r'https?://[^\s]+', '', cleaned_text)
                # Remove telegram links (all forms, case insensitive)
                cleaned_text = re.sub(r'[Tt]\.me/[\w\d_]+', '', cleaned_text)
                # Remove www links
                cleaned_text = re.sub(r'www\.[^\s]+', '', cleaned_text)
                # Remove domain links with simple and compound extensions (like .com.ye, .co.uk)
                cleaned_text = re.sub(r'[\w\d-]+\.(com|org|net|info|co|io|me|ly|tv|fm|cc|tk|ml|ga|cf|ye|sa|ae|eg|jo|iq|sy|lb|ma|dz|tn|ly|sd|kw|qa|bh|om|ps)\.[a-z]{2,3}[^\s]*', '', cleaned_text)
                # Remove domain links with single extensions
                cleaned_text = re.sub(r'[\w\d-]+\.(com|org|net|info|co|io|me|ly|tv|fm|cc|tk|ml|ga|cf|ye|sa|ae|eg|jo|iq|sy|lb|ma|dz|tn|ly|sd|kw|qa|bh|om|ps)[^\s]*', '', cleaned_text)
                # Remove @usernames
                cleaned_text = re.sub(r'@[\w\d_]+', '', cleaned_text)
                self.logger.info(f"🧽 Links cleaned from text")
            
            # Clean hashtags
            if clean_hashtags:
                import re
                cleaned_text = re.sub(r'#[\w\d_\u0600-\u06FF]+', '', cleaned_text)
            
            # Clean formatting (remove markdown/HTML)
            if clean_formatting:
                import re
                # Remove markdown formatting
                cleaned_text = re.sub(r'[*_`]', '', cleaned_text)
                # Remove HTML tags
                cleaned_text = re.sub(r'<[^>]+>', '', cleaned_text)
            
            # Clean lines with specific words
            if clean_lines_with_words and clean_words_list:
                clean_words = [word.strip().lower() for word in clean_words_list.split(',') if word.strip()]
                if clean_words:
                    lines = cleaned_text.split('\n')
                    filtered_lines = []
                    for line in lines:
                        line_lower = line.lower()
                        should_remove = any(word in line_lower for word in clean_words)
                        if not should_remove:
                            filtered_lines.append(line)
                    cleaned_text = '\n'.join(filtered_lines)
            
            # Clean empty lines
            if clean_empty_lines:
                lines = cleaned_text.split('\n')
                # Remove empty lines and lines with only whitespace
                non_empty_lines = [line for line in lines if line.strip()]
                cleaned_text = '\n'.join(non_empty_lines)
            
            # Clean up extra spaces and newlines
            import re
            cleaned_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned_text)  # Remove excessive newlines
            cleaned_text = re.sub(r' +', ' ', cleaned_text)  # Remove excessive spaces
            cleaned_text = cleaned_text.strip()
            
            return cleaned_text
            
        except Exception as e:
            self.logger.error(f"Error cleaning message text: {e}")
            return text
    
    async def run_until_disconnected(self):
        """Keep the client running until disconnected with optimized settings"""
        # Optimize client for faster message processing
        if hasattr(self.client, '_flood_sleep_threshold'):
            self.client._flood_sleep_threshold = 0  # Disable built-in flood sleep
        
        await self.client.run_until_disconnected()
    
    async def stop(self):
        """Stop the userbot gracefully"""
        if self.client and self.client.is_connected():
            await self.client.disconnect()
            self.logger.info("Userbot disconnected")
