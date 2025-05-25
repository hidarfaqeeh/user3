#!/usr/bin/env python3
"""
Web Interface for Telegram Userbot
Simple control panel for managing bot settings
"""

import asyncio
import json
import logging
import os
import threading
from flask import Flask, render_template, request, jsonify, redirect, url_for
from utils import ConfigManager
from userbot import TelegramForwarder
import configparser

app = Flask(__name__)
bot_instance = None
bot_status = {"running": False, "authenticated": False, "message": "Bot not started"}

class BotManager:
    def __init__(self):
        self.forwarder = None
        self.loop = None
        self.thread = None
        
    def start_bot_async(self):
        """Start bot in separate thread with its own event loop"""
        def run_bot():
            try:
                self.loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self.loop)
                
                self.forwarder = TelegramForwarder()
                
                async def bot_main():
                    global bot_status
                    try:
                        await self.forwarder.start()
                        bot_status["authenticated"] = True
                        bot_status["running"] = True
                        bot_status["message"] = "Bot running successfully"
                        
                        await self.forwarder.run_until_disconnected()
                    except Exception as e:
                        bot_status["running"] = False
                        bot_status["message"] = f"Bot error: {str(e)}"
                        
                self.loop.run_until_complete(bot_main())
                
            except Exception as e:
                bot_status["running"] = False
                bot_status["message"] = f"Failed to start bot: {str(e)}"
                
        self.thread = threading.Thread(target=run_bot, daemon=True)
        self.thread.start()
        
    def stop_bot(self):
        """Stop the bot"""
        global bot_status
        if self.forwarder and self.loop:
            try:
                self.loop.call_soon_threadsafe(
                    lambda: asyncio.create_task(self.forwarder.stop())
                )
                bot_status["running"] = False
                bot_status["message"] = "Bot stopped"
            except Exception as e:
                bot_status["message"] = f"Error stopping bot: {str(e)}"

bot_manager = BotManager()

@app.route('/')
def index():
    """Main control panel page"""
    try:
        config = ConfigManager('config.ini')
        current_config = {
            'source_chat': config.get('forwarding', 'source_chat', 'Not set'),
            'target_chat': config.get('forwarding', 'target_chat', 'Not set'),
            'forward_delay': config.get('forwarding', 'forward_delay', '1'),
            'forward_media': config.get('forwarding', 'forward_media', 'true'),
            'forward_text': config.get('forwarding', 'forward_text', 'true')
        }
    except Exception as e:
        current_config = {
            'source_chat': 'Error loading config',
            'target_chat': 'Error loading config',
            'forward_delay': '1',
            'forward_media': 'true',
            'forward_text': 'true'
        }
    
    return render_template('index.html', config=current_config, status=bot_status)

@app.route('/update_config', methods=['POST'])
def update_config():
    """Update bot configuration"""
    try:
        source_chat = request.form.get('source_chat', '').strip()
        target_chat = request.form.get('target_chat', '').strip()
        forward_delay = request.form.get('forward_delay', '1')
        forward_media = request.form.get('forward_media') == 'on'
        forward_text = request.form.get('forward_text') == 'on'
        forward_stickers = request.form.get('forward_stickers') == 'on'
        forward_documents = request.form.get('forward_documents') == 'on'
        
        # Update config file
        config = configparser.ConfigParser()
        config.read('config.ini')
        
        if not config.has_section('forwarding'):
            config.add_section('forwarding')
            
        config.set('forwarding', 'source_chat', source_chat)
        config.set('forwarding', 'target_chat', target_chat)
        config.set('forwarding', 'forward_delay', str(forward_delay))
        config.set('forwarding', 'forward_media', str(forward_media).lower())
        config.set('forwarding', 'forward_text', str(forward_text).lower())
        config.set('forwarding', 'forward_stickers', str(forward_stickers).lower())
        config.set('forwarding', 'forward_documents', str(forward_documents).lower())
        config.set('forwarding', 'max_retries', '3')
        
        with open('config.ini', 'w') as configfile:
            config.write(configfile)
            
        return jsonify({"success": True, "message": "Configuration updated successfully!"})
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Error updating config: {str(e)}"})

@app.route('/start_bot', methods=['POST'])
def start_bot():
    """Start the bot"""
    try:
        global bot_status
        if bot_status["running"]:
            return jsonify({"success": False, "message": "Bot is already running"})
            
        # Check if config is properly set
        config = ConfigManager('config.ini')
        source_chat = config.get('forwarding', 'source_chat', '')
        target_chat = config.get('forwarding', 'target_chat', '')
        
        if not source_chat or not target_chat or source_chat == 'SOURCE_CHAT_ID_OR_USERNAME':
            return jsonify({"success": False, "message": "Please configure source and target chats first"})
            
        bot_status["message"] = "Starting bot..."
        bot_manager.start_bot_async()
        
        return jsonify({"success": True, "message": "Bot start initiated"})
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Error starting bot: {str(e)}"})

@app.route('/stop_bot', methods=['POST'])
def stop_bot():
    """Stop the bot"""
    try:
        bot_manager.stop_bot()
        return jsonify({"success": True, "message": "Bot stopped"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Error stopping bot: {str(e)}"})

@app.route('/status')
def get_status():
    """Get current bot status"""
    return jsonify(bot_status)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app.run(host='0.0.0.0', port=5000, debug=True)