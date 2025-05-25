# Telegram Userbot - Message Forwarder

A Python Telegram userbot using Telethon that monitors a source chat and automatically forwards messages to a target chat.

## Features

- Monitor any Telegram chat/channel for new messages
- Automatically forward messages to target chat/channel
- Support for all message types (text, media, files, stickers)
- Rate limiting to avoid Telegram restrictions
- Configurable forwarding options
- Error handling and retry logic
- Detailed logging and monitoring
- Session management

## Prerequisites

1. **Telegram API Credentials**
   - Go to [https://my.telegram.org/apps](https://my.telegram.org/apps)
   - Create a new application to get `api_id` and `api_hash`

2. **Python Libraries**
   - The following libraries will be installed automatically:
     - telethon
     - asyncio (built-in)
     - configparser (built-in)
     - logging (built-in)

## Setup

1. **Configure the bot**
   - Edit `config.ini` with your credentials and chat information
   - Or set environment variables:
     ```bash
     export TELEGRAM_API_ID="your_api_id"
     export TELEGRAM_API_HASH="your_api_hash"
     ```

2. **Update config.ini**
   ```ini
   [telegram]
   api_id = YOUR_API_ID
   api_hash = YOUR_API_HASH
   phone_number = YOUR_PHONE_NUMBER

   [forwarding]
   source_chat = SOURCE_CHAT_ID_OR_USERNAME
   target_chat = TARGET_CHAT_ID_OR_USERNAME
   ```

## Usage

1. **Run the bot**
   ```bash
   python main.py
   ```

2. **First time setup**
   - The bot will ask for your phone number and verification code
   - This creates a session file for future use

3. **Chat identifiers**
   - Public channels/groups: Use `@username`
   - Private chats: Use numeric chat ID
   - To get chat ID, forward a message to @userinfobot

## Configuration Options

### Forwarding Settings
- `forward_delay`: Delay between forwards (seconds)
- `max_retries`: Maximum retry attempts for failed forwards
- `forward_media`: Forward photos and videos
- `forward_text`: Forward text messages
- `forward_stickers`: Forward stickers
- `forward_documents`: Forward files and documents

### Example Configuration
```ini
[forwarding]
source_chat = @source_channel
target_chat = @target_channel
forward_delay = 1
max_retries = 3
forward_media = true
forward_text = true
forward_stickers = true
forward_documents = true
