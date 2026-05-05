import logging
import asyncio
import secrets
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters, ConversationHandler
import requests
import json
import os
import sys
from threading import Thread
from flask import Flask, jsonify

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Flask app for keep-alive
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return jsonify({
        "status": "running",
        "bot": BOT_DISPLAY_NAME,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

@flask_app.route('/health')
def health():
    return jsonify({"status": "healthy"})

def run_flask():
    flask_app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)), debug=False, use_reloader=False)

# Bot Configuration
BOT_TOKEN = "8656072423:AAF8EV7ijvVk5hVB5Ae40PiEeMywO-8Zzds"
ADMIN_ID = 8379062893
BOT_USERNAME = "EXUFILEBOT"

BOT_DISPLAY_NAME = "𝐋𝐎𝐍𝐆 𝐁𝐈𝐎 𝐁𝐎𝐓〆𝐄𝐗𝐔"

# Conversation states
METHOD_SELECTION, WAITING_UID, WAITING_PASSWORD, WAITING_ACCESS_TOKEN, WAITING_JWT, WAITING_BIO, WAITING_REGION = range(7)
BAN_USER_STATE = 10
UNBAN_USER_STATE = 11
BROADCAST_STATE = 12

# ============================================
# CHANNELS AND GROUPS FOR SUBSCRIPTION
# ============================================
SUBSCRIPTION_ENTITIES = [
    {
        "id": -1003564583501,
        "name": "𝐕𝐀𝐍𝐙𝐎〆𝐂𝐈𝐙𝐘",
        "type": "channel",
        "link": "https://t.me/+Kp4wwNKJKp42MmQ1"
    },
    {
        "id": -1003360548513,
        "name": "𝐄𝐗𝐔 𝐂𝐎𝐃𝐄𝐑 ⚡",
        "type": "channel",
        "link": "https://t.me/exucoder1"
    },
    {
        "id": -1003645019104,
        "name": "ᴡᴇʙꜱɪᴛᴇ〆ꜰɪʟᴇ",
        "type": "channel",
        "link": "https://t.me/+hsxmKaYRjRA2Mzk9"
    },
    {
        "id": -1003669933791,
        "name": "𝐄𝐗𝐔〆𝐏𝐑𝐈𝐌𝐄",
        "type": "channel",
        "link": "https://t.me/exucodex"
    }
]

TOTAL_SUBSCRIPTIONS = len(SUBSCRIPTION_ENTITIES)

# API Configuration
API_URL = "https://loing-io.vercel.app/bio_upload"

# Data files
USERS_DATA_FILE = "users_data.json"
BANNED_USERS_FILE = "banned_users.json"
BROADCAST_HISTORY_FILE = "broadcast_history.json"
USER_SUBSCRIPTION_STATUS = {}

# Region mapping
REGIONS = {
    "🇮🇳 𝐈𝐍𝐃": "IND",
    "🇦🇪 𝐌𝐄": "ME",
    "🇻🇳 𝐕𝐍": "VN",
    "🇧🇩 𝐁𝐃": "BD",
    "🇵🇰 𝐏𝐊": "PK",
    "🇸🇬 𝐒𝐆": "SG",
    "🇧🇷 𝐁𝐑": "BR",
    "🇺🇸 𝐍𝐀": "NA",
    "🇮🇩 𝐈𝐃": "ID",
    "🇷🇺 𝐑𝐔": "RU",
    "🇹🇭 𝐓𝐇": "TH"
}

def load_json_file(filename, default_data):
    try:
        if os.path.exists(filename) and os.path.getsize(filename) > 0:
            with open(filename, 'r') as f:
                return json.load(f)
        return default_data
    except:
        return default_data

def save_json_file(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f)

def load_users_data():
    return load_json_file(USERS_DATA_FILE, {})

def save_users_data(data):
    save_json_file(USERS_DATA_FILE, data)

def load_banned_users():
    return load_json_file(BANNED_USERS_FILE, [])

def save_banned_users(data):
    save_json_file(BANNED_USERS_FILE, data)

def load_broadcast_history():
    return load_json_file(BROADCAST_HISTORY_FILE, [])

def save_broadcast_history(data):
    save_json_file(BROADCAST_HISTORY_FILE, data)

users_data = load_users_data()
banned_users = load_banned_users()
broadcast_history = load_broadcast_history()

# ============= KEYBOARDS =============
def get_admin_panel():
    keyboard = [
        [KeyboardButton("📊 𝐒𝐭𝐚𝐭𝐬"), KeyboardButton("👥 𝐔𝐬𝐞𝐫𝐬")],
        [KeyboardButton("📢 𝐁𝐫𝐨𝐚𝐝𝐜𝐚𝐬𝐭"), KeyboardButton("🔄 𝐅𝐨𝐫𝐰𝐚𝐫𝐝")],
        [KeyboardButton("🚫 𝐁𝐚𝐧 𝐔𝐬𝐞𝐫"), KeyboardButton("✅ 𝐔𝐧𝐛𝐚𝐧 𝐔𝐬𝐞𝐫")],
        [KeyboardButton("📜 𝐁𝐚𝐧𝐧𝐞𝐝 𝐋𝐢𝐬𝐭"), KeyboardButton("📋 𝐁𝐫𝐨𝐚𝐝𝐜𝐚𝐬𝐭 𝐋𝐨𝐠")],
        [KeyboardButton("🗑️ 𝐂𝐥𝐞𝐚𝐫 𝐃𝐚𝐭𝐚"), KeyboardButton("⚙️ 𝐂𝐡𝐞𝐜𝐤 𝐀𝐏𝐈")],
        [KeyboardButton("❓ 𝐇𝐞𝐥𝐩")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_user_keyboard():
    keyboard = [
        [KeyboardButton("🔐 𝐔𝐈𝐃 + 𝐏𝐀𝐒𝐒𝐖𝐎𝐑𝐃")],
        [KeyboardButton("🎫 𝐀𝐂𝐂𝐄𝐒𝐒 𝐓𝐎𝐊𝐄𝐍")],
        [KeyboardButton("🔑 𝐉𝐖𝐓 𝐓𝐎𝐊𝐄𝐍")],
        [KeyboardButton("❓ 𝐇𝐞𝐥𝐩")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_cancel_keyboard():
    return ReplyKeyboardMarkup([[KeyboardButton("❌ 𝐂𝐚𝐧𝐜𝐞𝐥")]], resize_keyboard=True)

def get_region_keyboard():
    keyboard = []
    row = []
    for i, (flag, code) in enumerate(REGIONS.items()):
        row.append(KeyboardButton(flag))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([KeyboardButton("🌍 𝐀𝐔𝐓𝐎-𝐃𝐄𝐓𝐄𝐂𝐓")])
    keyboard.append([KeyboardButton("❌ 𝐂𝐚𝐧𝐜𝐞𝐥")])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ============= SUBSCRIPTION CHECK =============
async def check_subscription_change(user_id: int, username: str, first_name: str, context: ContextTypes.DEFAULT_TYPE):
    global USER_SUBSCRIPTION_STATUS
    
    current_status = []
    unjoined = []
    
    for entity in SUBSCRIPTION_ENTITIES:
        try:
            chat_member = await context.bot.get_chat_member(chat_id=entity["id"], user_id=user_id)
            if chat_member.status in ['left', 'kicked']:
                current_status.append(f"❌ {entity['name']}")
                unjoined.append(entity)
            else:
                current_status.append(f"✅ {entity['name']}")
        except Exception as e:
            logger.error(f"Error checking {entity['name']}: {e}")
            current_status.append(f"❌ {entity['name']} (Error)")
            unjoined.append(entity)
    
    if str(user_id) in USER_SUBSCRIPTION_STATUS:
        old_status = USER_SUBSCRIPTION_STATUS[str(user_id)]
        if old_status != current_status:
            notification = f"🔔 𝐒𝐮𝐛𝐬𝐜𝐫𝐢𝐩𝐭𝐢𝐨𝐧 𝐂𝐡𝐚𝐧𝐠𝐞 𝐃𝐞𝐭𝐞𝐜𝐭𝐞𝐝!\n\n"
            notification += f"👤 𝐔𝐬𝐞𝐫: {first_name}\n"
            notification += f"🆔 𝐔𝐬𝐞𝐫 𝐈𝐃: {user_id}\n"
            notification += f"📛 𝐔𝐬𝐞𝐫𝐧𝐚𝐦𝐞: @{username if username else '𝐍𝐨𝐭 𝐬𝐞𝐭'}\n\n"
            notification += f"📋 𝐂𝐮𝐫𝐫𝐞𝐧𝐭 𝐒𝐭𝐚𝐭𝐮𝐬:\n"
            for status in current_status:
                notification += f"{status}\n"
            if unjoined:
                notification += f"\n⚠️ 𝐌𝐢𝐬𝐬𝐢𝐧𝐠: {len(unjoined)}/{TOTAL_SUBSCRIPTIONS}"
            else:
                notification += f"\n✅ 𝐀𝐥𝐥 {TOTAL_SUBSCRIPTIONS} 𝐣𝐨𝐢𝐧𝐞𝐝!"
            try:
                await context.bot.send_message(chat_id=ADMIN_ID, text=notification)
            except Exception as e:
                logger.error(f"Error notifying admin: {e}")
    
    USER_SUBSCRIPTION_STATUS[str(user_id)] = current_status
    return unjoined

async def force_subscription_check(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user_id = update.effective_user.id
    
    if user_id == ADMIN_ID:
        return True
    
    if user_id in banned_users:
        await update.message.reply_text(
            "🚫 𝐘𝐨𝐮 𝐚𝐫𝐞 𝐛𝐚𝐧𝐧𝐞𝐝 𝐟𝐫𝐨𝐦 𝐮𝐬𝐢𝐧𝐠 𝐭𝐡𝐢𝐬 𝐛𝐨𝐭!\n\n"
            "𝐂𝐨𝐧𝐭𝐚𝐜𝐭 𝐚𝐝𝐦𝐢𝐧 𝐟𝐨𝐫 𝐢𝐧𝐪𝐮𝐢𝐫𝐢𝐞𝐬."
        )
        return False
    
    user = update.effective_user
    unjoined_entities = await check_subscription_change(user_id, user.username, user.first_name, context)
    
    if unjoined_entities:
        keyboard = []
        for entity in unjoined_entities:
            if entity["link"]:
                keyboard.append([InlineKeyboardButton(f"📢 𝐉𝐨𝐢𝐧 {entity['name']}", url=entity["link"])])
        keyboard.append([InlineKeyboardButton("✅ 𝐕𝐞𝐫𝐢𝐟𝐲 𝐒𝐮𝐛𝐬𝐜𝐫𝐢𝐩𝐭𝐢𝐨𝐧", callback_data="verify_subscription")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        joined_count = TOTAL_SUBSCRIPTIONS - len(unjoined_entities)
        
        await update.message.reply_text(
            f"🚫 𝐀𝐜𝐜𝐞𝐬𝐬 𝐃𝐞𝐧𝐢𝐞𝐝!\n\n"
            f"📊 𝐏𝐫𝐨𝐠𝐫𝐞𝐬𝐬: {joined_count}/{TOTAL_SUBSCRIPTIONS} 𝐣𝐨𝐢𝐧𝐞𝐝\n\n"
            f"⚠️ 𝐓𝐨 𝐮𝐬𝐞 𝐭𝐡𝐢𝐬 𝐛𝐨𝐭, 𝐲𝐨𝐮 𝐦𝐮𝐬𝐭 𝐣𝐨𝐢𝐧 𝐚𝐥𝐥 𝐜𝐡𝐚𝐧𝐧𝐞𝐥𝐬 𝐟𝐢𝐫𝐬𝐭!\n\n"
            f"👇 𝐂𝐥𝐢𝐜𝐤 𝐭𝐡𝐞 𝐛𝐮𝐭𝐭𝐨𝐧𝐬 𝐛𝐞𝐥𝐨𝐰 𝐭𝐨 𝐣𝐨𝐢𝐧: 👇",
            reply_markup=reply_markup
        )
        return False
    
    return True

# ============= START COMMAND =============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = update.effective_user
    
    if user_id in banned_users:
        await update.message.reply_text("🚫 𝐘𝐨𝐮 𝐚𝐫𝐞 𝐛𝐚𝐧𝐧𝐞𝐝!")
        return
    
    if str(user_id) not in users_data and user_id != ADMIN_ID:
        users_data[str(user_id)] = {
            "first_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "total_bio_changes": 0
        }
        save_users_data(users_data)
    
    if not await force_subscription_check(update, context):
        return
    
    current_hour = datetime.now().hour
    if current_hour < 12:
        greeting = "𝐆𝐨𝐨𝐝 𝐌𝐨𝐫𝐧𝐢𝐧𝐠"
    elif current_hour < 17:
        greeting = "𝐆𝐨𝐨𝐝 𝐀𝐟𝐭𝐞𝐫𝐧𝐨𝐨𝐧"
    else:
        greeting = "𝐆𝐨𝐨𝐝 𝐄𝐯𝐞𝐧𝐢𝐧𝐠"
    
    welcome_text = (
        f"╔═══《 🎉 {greeting}! 》═══╗\n\n"
        f"👤 𝐔𝐬𝐞𝐫: {user.first_name}\n"
        f"🆔 𝐔𝐬𝐞𝐫 𝐈𝐃: {user_id}\n"
        f"🌟 𝐒𝐭𝐚𝐭𝐮𝐬: {'𝐀𝐝𝐦𝐢𝐧𝐢𝐬𝐭𝐫𝐚𝐭𝐨𝐫' if user_id == ADMIN_ID else '𝐕𝐚𝐥𝐮𝐞𝐝 𝐔𝐬𝐞𝐫'}\n\n"
        f"╰═══════《 🤖 》═══════╝\n\n"
        f"𝐖𝐞𝐥𝐜𝐨𝐦𝐞 𝐭𝐨 𝐋𝐎𝐍𝐆 𝐁𝐈𝐎 𝐁𝐎𝐓〆𝐄𝐗𝐔\n\n"
        f"📌 𝐀𝐛𝐨𝐮𝐭 𝐓𝐡𝐢𝐬 𝐁𝐨𝐭:\n"
        f"• 🔐 𝐒𝐞𝐜𝐮𝐫𝐞 𝐁𝐢𝐨 𝐔𝐩𝐝𝐚𝐭𝐞𝐫\n"
        f"• 📤 𝐄𝐚𝐬𝐲 𝐅𝐫𝐞𝐞 𝐅𝐢𝐫𝐞 𝐁𝐢𝐨 𝐂𝐡𝐚𝐧𝐠𝐞\n"
        f"• 🔗 𝐌𝐮𝐥𝐭𝐢𝐩𝐥𝐞 𝐋𝐨𝐠𝐢𝐧 𝐌𝐞𝐭𝐡𝐨𝐝𝐬\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"✅ 𝐀𝐜𝐜𝐞𝐬𝐬 𝐆𝐫𝐚𝐧𝐭𝐞𝐝!\n"
        f"𝐘𝐨𝐮 𝐡𝐚𝐯𝐞 𝐬𝐮𝐜𝐜𝐞𝐬𝐬𝐟𝐮𝐥𝐥𝐲 𝐣𝐨𝐢𝐧𝐞𝐝 𝐚𝐥𝐥 {TOTAL_SUBSCRIPTIONS} 𝐜𝐡𝐚𝐧𝐧𝐞𝐥𝐬.\n\n"
        f"📌 𝐐𝐮𝐢𝐜𝐤 𝐆𝐮𝐢𝐝𝐞:\n"
        f"• 𝐔𝐬𝐞 𝐭𝐡𝐞 𝐛𝐮𝐭𝐭𝐨𝐧𝐬 𝐛𝐞𝐥𝐨𝐰 𝐭𝐨 𝐜𝐡𝐨𝐨𝐬𝐞 𝐥𝐨𝐠𝐢𝐧 𝐦𝐞𝐭𝐡𝐨𝐝\n"
        f"• 𝐄𝐧𝐭𝐞𝐫 𝐲𝐨𝐮𝐫 𝐜𝐫𝐞𝐝𝐞𝐧𝐭𝐢𝐚𝐥𝐬\n"
        f"• 𝐄𝐧𝐭𝐞𝐫 𝐲𝐨𝐮𝐫 𝐛𝐢𝐨 𝐭𝐞𝐱𝐭\n\n"
        f"⚠️ 𝐍𝐨𝐭𝐞: 𝐈𝐟 𝐲𝐨𝐮 𝐥𝐞𝐚𝐯𝐞 𝐚𝐧𝐲 𝐜𝐡𝐚𝐧𝐧𝐞𝐥, 𝐲𝐨𝐮 𝐰𝐢𝐥𝐥 𝐥𝐨𝐬𝐞 𝐚𝐜𝐜𝐞𝐬𝐬!"
    )
    
    if user_id == ADMIN_ID:
        reply_markup = get_admin_panel()
    else:
        reply_markup = get_user_keyboard()
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

# ============= VERIFY CALLBACK =============
async def verify_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user = query.from_user
    
    if query.data == "verify_subscription":
        unjoined_entities = await check_subscription_change(user_id, user.username, user.first_name, context)
        
        if not unjoined_entities:
            await query.edit_message_text(
                f"✅ 𝐒𝐮𝐛𝐬𝐜𝐫𝐢𝐩𝐭𝐢𝐨𝐧 𝐕𝐞𝐫𝐢𝐟𝐢𝐞𝐝!\n\n"
                f"𝐍𝐨𝐰 𝐲𝐨𝐮 𝐜𝐚𝐧 𝐮𝐬𝐞 𝐭𝐡𝐞 𝐛𝐨𝐭.\n"
                f"𝐔𝐬𝐞 /𝐬𝐭𝐚𝐫𝐭 𝐭𝐨 𝐜𝐨𝐧𝐭𝐢𝐧𝐮𝐞."
            )
        else:
            entity_list = ""
            for i, entity in enumerate(unjoined_entities, 1):
                entity_list += f"{i}. {entity['name']}\n"
            
            await query.edit_message_text(
                f"❌ 𝐕𝐞𝐫𝐢𝐟𝐢𝐜𝐚𝐭𝐢𝐨𝐧 𝐅𝐚𝐢𝐥𝐞𝐝!\n\n"
                f"𝐘𝐨𝐮 𝐡𝐚𝐯𝐞𝐧'𝐭 𝐣𝐨𝐢𝐧𝐞𝐝 𝐚𝐥𝐥 𝐜𝐡𝐚𝐧𝐧𝐞𝐥𝐬 𝐲𝐞𝐭.\n\n"
                f"𝐏𝐥𝐞𝐚𝐬𝐞 𝐣𝐨𝐢𝐧 𝐭𝐡𝐞𝐬𝐞:\n\n"
                f"{entity_list}\n"
                f"𝐀𝐟𝐭𝐞𝐫 𝐣𝐨𝐢𝐧𝐢𝐧𝐠, 𝐜𝐥𝐢𝐜𝐤 /𝐬𝐭𝐚𝐫𝐭"
            )

# ============= BIO UPLOAD CONVERSATION HANDLERS =============
async def bio_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    
    if user_id in banned_users:
        await update.message.reply_text("🚫 𝐘𝐨𝐮 𝐚𝐫𝐞 𝐛𝐚𝐧𝐧𝐞𝐝!")
        return ConversationHandler.END
    
    if text == "🔐 𝐔𝐈𝐃 + 𝐏𝐀𝐒𝐒𝐖𝐎𝐑𝐃":
        context.user_data['method'] = 'uid'
        await update.message.reply_text("𝐒𝐞𝐧𝐝 𝐲𝐨𝐮𝐫 𝐔𝐈𝐃:", reply_markup=get_cancel_keyboard())
        return WAITING_UID
    
    elif text == "🎫 𝐀𝐂𝐂𝐄𝐒𝐒 𝐓𝐎𝐊𝐄𝐍":
        context.user_data['method'] = 'access'
        await update.message.reply_text("𝐒𝐞𝐧𝐝 𝐲𝐨𝐮𝐫 𝐀𝐜𝐜𝐞𝐬𝐬 𝐓𝐨𝐤𝐞𝐧:", reply_markup=get_cancel_keyboard())
        return WAITING_ACCESS_TOKEN
    
    elif text == "🔑 𝐉𝐖𝐓 𝐓𝐎𝐊𝐄𝐍":
        context.user_data['method'] = 'jwt'
        await update.message.reply_text("𝐒𝐞𝐧𝐝 𝐲𝐨𝐮𝐫 𝐉𝐖𝐓 𝐓𝐨𝐤𝐞𝐧:", reply_markup=get_cancel_keyboard())
        return WAITING_JWT
    
    return ConversationHandler.END

async def get_uid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ 𝐂𝐚𝐧𝐜𝐞𝐥":
        await update.message.reply_text("❌ 𝐂𝐚𝐧𝐜𝐞𝐥𝐥𝐞𝐝.", reply_markup=get_user_keyboard())
        return ConversationHandler.END
    
    context.user_data['uid'] = update.message.text.strip()
    await update.message.reply_text("𝐒𝐞𝐧𝐝 𝐲𝐨𝐮𝐫 𝐏𝐚𝐬𝐬𝐰𝐨𝐫𝐝:", reply_markup=get_cancel_keyboard())
    return WAITING_PASSWORD

async def get_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ 𝐂𝐚𝐧𝐜𝐞𝐥":
        await update.message.reply_text("❌ 𝐂𝐚𝐧𝐜𝐞𝐥𝐥𝐞𝐝.", reply_markup=get_user_keyboard())
        return ConversationHandler.END
    
    context.user_data['password'] = update.message.text.strip()
    await update.message.reply_text("𝐒𝐞𝐧𝐝 𝐲𝐨𝐮𝐫 𝐁𝐈𝐎 𝐭𝐞𝐱𝐭:", reply_markup=get_cancel_keyboard())
    return WAITING_BIO

async def get_access_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ 𝐂𝐚𝐧𝐜𝐞𝐥":
        await update.message.reply_text("❌ 𝐂𝐚𝐧𝐜𝐞𝐥𝐥𝐞𝐝.", reply_markup=get_user_keyboard())
        return ConversationHandler.END
    
    context.user_data['access_token'] = update.message.text.strip()
    await update.message.reply_text("𝐒𝐞𝐧𝐝 𝐲𝐨𝐮𝐫 𝐁𝐈𝐎 𝐭𝐞𝐱𝐭:", reply_markup=get_cancel_keyboard())
    return WAITING_BIO

async def get_jwt_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ 𝐂𝐚𝐧𝐜𝐞𝐥":
        await update.message.reply_text("❌ 𝐂𝐚𝐧𝐜𝐞𝐥𝐥𝐞𝐝.", reply_markup=get_user_keyboard())
        return ConversationHandler.END
    
    context.user_data['jwt_token'] = update.message.text.strip()
    await update.message.reply_text("𝐒𝐞𝐧𝐝 𝐲𝐨𝐮𝐫 𝐁𝐈𝐎 𝐭𝐞𝐱𝐭:", reply_markup=get_cancel_keyboard())
    return WAITING_BIO

async def get_bio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ 𝐂𝐚𝐧𝐜𝐞𝐥":
        await update.message.reply_text("❌ 𝐂𝐚𝐧𝐜𝐞𝐥𝐥𝐞𝐝.", reply_markup=get_user_keyboard())
        return ConversationHandler.END
    
    context.user_data['bio'] = update.message.text.strip()
    
    if context.user_data.get('method') == 'uid':
        await update.message.reply_text("𝐂𝐡𝐨𝐨𝐬𝐞 𝐫𝐞𝐠𝐢𝐨𝐧:", reply_markup=get_region_keyboard())
        return WAITING_REGION
    else:
        await process_bio_upload(update, context, region=None)
        return ConversationHandler.END

async def get_region(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ 𝐂𝐚𝐧𝐜𝐞𝐥":
        await update.message.reply_text("❌ 𝐂𝐚𝐧𝐜𝐞𝐥𝐥𝐞𝐝.", reply_markup=get_user_keyboard())
        return ConversationHandler.END
    
    region = None if update.message.text == "🌍 𝐀𝐔𝐓𝐎-𝐃𝐄𝐓𝐄𝐂𝐓" else REGIONS.get(update.message.text)
    await process_bio_upload(update, context, region)
    return ConversationHandler.END

async def process_bio_upload(update: Update, context: ContextTypes.DEFAULT_TYPE, region=None):
    method = context.user_data.get('method')
    bio = context.user_data.get('bio')
    
    params = {"bio": bio}
    
    if method == 'uid':
        params["uid"] = context.user_data.get('uid')
        params["pass"] = context.user_data.get('password')
    elif method == 'access':
        params["access"] = context.user_data.get('access_token')
    elif method == 'jwt':
        params["jwt"] = context.user_data.get('jwt_token')
    
    if region:
        params["region"] = region
    
    await update.message.reply_text("⏳ 𝐏𝐥𝐞𝐚𝐬𝐞 𝐰𝐚𝐢𝐭, 𝐩𝐫𝐨𝐜𝐞𝐬𝐬𝐢𝐧𝐠 𝐲𝐨𝐮𝐫 𝐫𝐞𝐪𝐮𝐞𝐬𝐭...")
    
    try:
        response = requests.get(API_URL, params=params, timeout=30)
        result = response.json()
        
        user_id = str(update.effective_user.id)
        if user_id in users_data:
            users_data[user_id]['total_bio_changes'] = users_data[user_id].get('total_bio_changes', 0) + 1
            save_users_data(users_data)
        
        if result.get("code") == 200:
            # POLITE BOLD STYLE SUCCESS MESSAGE
            method_display = {
                'uid': '🔐 UID + Password',
                'access': '🎫 Access Token',
                'jwt': '🔑 JWT Token'
            }.get(method, 'Unknown')
            
            region_display = {
                'IND': '🇮🇳 India',
                'ME': '🇦🇪 Middle East',
                'VN': '🇻🇳 Vietnam',
                'BD': '🇧🇩 Bangladesh',
                'PK': '🇵🇰 Pakistan',
                'SG': '🇸🇬 Singapore',
                'BR': '🇧🇷 Brazil',
                'NA': '🇺🇸 North America',
                'ID': '🇮🇩 Indonesia',
                'RU': '🇷🇺 Russia',
                'TH': '🇹🇭 Thailand'
            }.get(result.get('selected_region'), result.get('selected_region', 'Auto'))
            
            reply = f"""
╔══════════════════════════════════════╗
║          ✅ 𝐒𝐔𝐂𝐂𝐄𝐒𝐒! ✅            ║
╚══════════════════════════════════════╝

𝐃𝐞𝐚𝐫 𝐔𝐬𝐞𝐫, 𝐲𝐨𝐮𝐫 𝐅𝐫𝐞𝐞 𝐅𝐢𝐫𝐞 𝐛𝐢𝐨 𝐡𝐚𝐬 𝐛𝐞𝐞𝐧 
𝐬𝐮𝐜𝐜𝐞𝐬𝐬𝐟𝐮𝐥𝐥𝐲 𝐮𝐩𝐝𝐚𝐭𝐞𝐝!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 𝐍𝐞𝐰 𝐁𝐢𝐨:      {result['bio']} 🔥
🔑 𝐋𝐨𝐠𝐢𝐧 𝐌𝐞𝐭𝐡𝐨𝐝:  {method_display}
👤 𝐘𝐨𝐮𝐫 𝐔𝐈𝐃:       {result['uid']}
🌍 𝐒𝐞𝐥𝐞𝐜𝐭𝐞𝐝 𝐑𝐞𝐠𝐢𝐨𝐧:  {region_display}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💫 𝐘𝐨𝐮𝐫 𝐛𝐢𝐨 𝐢𝐬 𝐧𝐨𝐰 𝐥𝐢𝐯𝐞 𝐨𝐧 𝐲𝐨𝐮𝐫 𝐩𝐫𝐨𝐟𝐢𝐥𝐞!

𝐓𝐡𝐚𝐧𝐤 𝐲𝐨𝐮 𝐟𝐨𝐫 𝐮𝐬𝐢𝐧𝐠 𝐨𝐮𝐫 𝐬𝐞𝐫𝐯𝐢𝐜𝐞. 💐

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 𝐁𝐨𝐭 𝐛𝐲: {BOT_DISPLAY_NAME}
"""
        else:
            reply = f"""
╔══════════════════════════════════════╗
║          ❌ 𝐅𝐀𝐈𝐋𝐄𝐃! ❌            ║
╚══════════════════════════════════════╝

𝐃𝐞𝐚𝐫 𝐔𝐬𝐞𝐫, 𝐰𝐞 𝐚𝐫𝐞 𝐮𝐧𝐚𝐛𝐥𝐞 𝐭𝐨 𝐮𝐩𝐝𝐚𝐭𝐞 
𝐲𝐨𝐮𝐫 𝐅𝐫𝐞𝐞 𝐅𝐢𝐫𝐞 𝐛𝐢𝐨 𝐚𝐭 𝐭𝐡𝐢𝐬 𝐦𝐨𝐦𝐞𝐧𝐭.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 𝐒𝐭𝐚𝐭𝐮𝐬: {result.get('status')}
🔢 𝐂𝐨𝐝𝐞: {result.get('code')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 𝐓𝐢𝐩: 𝐏𝐥𝐞𝐚𝐬𝐞 𝐭𝐫𝐲 𝐮𝐬𝐢𝐧𝐠 𝐭𝐡𝐞 
🔐 𝐔𝐈𝐃 + 𝐏𝐀𝐒𝐒𝐖𝐎𝐑𝐃 𝐦𝐞𝐭𝐡𝐨𝐝

𝐈𝐟 𝐭𝐡𝐞 𝐩𝐫𝐨𝐛𝐥𝐞𝐦 𝐩𝐞𝐫𝐬𝐢𝐬𝐭𝐬, 𝐩𝐥𝐞𝐚𝐬𝐞 
𝐜𝐨𝐧𝐭𝐚𝐜𝐭 𝐬𝐮𝐩𝐩𝐨𝐫𝐭. 🙏

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 𝐁𝐨𝐭 𝐛𝐲: {BOT_DISPLAY_NAME}
"""
        
        user_id = update.effective_user.id
        if user_id == ADMIN_ID:
            await update.message.reply_text(reply, parse_mode='Markdown', reply_markup=get_admin_panel())
        else:
            await update.message.reply_text(reply, parse_mode='Markdown', reply_markup=get_user_keyboard())
        
    except Exception as e:
        error_reply = f"""
╔══════════════════════════════════════╗
║          ❌ 𝐄𝐑𝐑𝐎𝐑! ❌             ║
╚══════════════════════════════════════╝

𝐃𝐞𝐚𝐫 𝐔𝐬𝐞𝐫, 𝐚𝐧 𝐞𝐫𝐫𝐨𝐫 𝐨𝐜𝐜𝐮𝐫𝐫𝐞𝐝 𝐰𝐡𝐢𝐥𝐞 
𝐩𝐫𝐨𝐜𝐞𝐬𝐬𝐢𝐧𝐠 𝐲𝐨𝐮𝐫 𝐫𝐞𝐪𝐮𝐞𝐬𝐭.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 𝐄𝐫𝐫𝐨𝐫: {str(e)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

𝐏𝐥𝐞𝐚𝐬𝐞 𝐭𝐫𝐲 𝐚𝐠𝐚𝐢𝐧 𝐥𝐚𝐭𝐞𝐫 𝐨𝐫 𝐜𝐨𝐧𝐭𝐚𝐜𝐭 
𝐬𝐮𝐩𝐩𝐨𝐫𝐭 𝐢𝐟 𝐭𝐡𝐞 𝐢𝐬𝐬𝐮𝐞 𝐩𝐞𝐫𝐬𝐢𝐬𝐭𝐬. 🙏

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 𝐁𝐨𝐭 𝐛𝐲: {BOT_DISPLAY_NAME}
"""
        if user_id == ADMIN_ID:
            await update.message.reply_text(error_reply, parse_mode='Markdown', reply_markup=get_admin_panel())
        else:
            await update.message.reply_text(error_reply, parse_mode='Markdown', reply_markup=get_user_keyboard())
    
    context.user_data.clear()

# ============= ADMIN FEATURES =============
async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ 𝐘𝐨𝐮 𝐚𝐫𝐞 𝐧𝐨𝐭 𝐚𝐮𝐭𝐡𝐨𝐫𝐢𝐳𝐞𝐝!")
        return
    
    total_bio_changes = sum(user.get('total_bio_changes', 0) for user in users_data.values())
    
    stats_text = (
        f"📈 *𝐁𝐨𝐭 𝐒𝐭𝐚𝐭𝐢𝐬𝐭𝐢𝐜𝐬*\n\n"
        f"👥 𝐓𝐨𝐭𝐚𝐥 𝐔𝐬𝐞𝐫𝐬: `{len(users_data)}`\n"
        f"🚫 𝐁𝐚𝐧𝐧𝐞𝐝 𝐔𝐬𝐞𝐫𝐬: `{len(banned_users)}`\n"
        f"📢 𝐂𝐡𝐚𝐧𝐧𝐞𝐥𝐬: `{TOTAL_SUBSCRIPTIONS}`\n"
        f"📝 𝐓𝐨𝐭𝐚𝐥 𝐁𝐢𝐨 𝐂𝐡𝐚𝐧𝐠𝐞𝐬: `{total_bio_changes}`\n"
        f"📋 𝐁𝐫𝐨𝐚𝐝𝐜𝐚𝐬𝐭 𝐇𝐢𝐬𝐭𝐨𝐫𝐲: `{len(broadcast_history)}`\n\n"
        f"🤖 𝐁𝐨𝐭 𝐛𝐲: {BOT_DISPLAY_NAME}"
    )
    await update.message.reply_text(stats_text, parse_mode='Markdown', reply_markup=get_admin_panel())

async def admin_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ 𝐘𝐨𝐮 𝐚𝐫𝐞 𝐧𝐨𝐭 𝐚𝐮𝐭𝐡𝐨𝐫𝐢𝐳𝐞𝐝!")
        return
    
    if not users_data:
        await update.message.reply_text("📭 𝐍𝐨 𝐮𝐬𝐞𝐫𝐬 𝐟𝐨𝐮𝐧𝐝.", reply_markup=get_admin_panel())
        return
    
    users_list = "👥 *𝐔𝐬𝐞𝐫𝐬 𝐋𝐢𝐬𝐭:*\n\n"
    for i, (uid, data) in enumerate(list(users_data.items())[:20], 1):
        users_list += f"{i}. {data.get('first_name', 'Unknown')}\n"
        users_list += f"   🆔 `{uid}`\n"
        users_list += f"   📅 {data.get('first_seen', 'Unknown')}\n"
        users_list += f"   📝 Bio changes: {data.get('total_bio_changes', 0)}\n\n"
    
    if len(users_data) > 20:
        users_list += f"\n📊 *Total users: {len(users_data)}* (showing first 20)"
    
    await update.message.reply_text(users_list, parse_mode='Markdown', reply_markup=get_admin_panel())

async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ 𝐘𝐨𝐮 𝐚𝐫𝐞 𝐧𝐨𝐭 𝐚𝐮𝐭𝐡𝐨𝐫𝐢𝐳𝐞𝐝!")
        return
    
    await update.message.reply_text(
        "📢 *𝐁𝐫𝐨𝐚𝐝𝐜𝐚𝐬𝐭 𝐌𝐨𝐝𝐞*\n\n"
        f"👥 𝐓𝐨𝐭𝐚𝐥 𝐔𝐬𝐞𝐫𝐬: `{len(users_data)}`\n\n"
        "𝐒𝐞𝐧𝐝 𝐦𝐞 𝐭𝐡𝐞 𝐦𝐞𝐬𝐬𝐚𝐠𝐞 𝐲𝐨𝐮 𝐰𝐚𝐧𝐭 𝐭𝐨 𝐛𝐫𝐨𝐚𝐝𝐜𝐚𝐬𝐭.\n"
        "𝐒𝐮𝐩𝐩𝐨𝐫𝐭𝐞𝐝: 𝐓𝐞𝐱𝐭, 𝐏𝐡𝐨𝐭𝐨, 𝐕𝐢𝐝𝐞𝐨, 𝐃𝐨𝐜𝐮𝐦𝐞𝐧𝐭\n\n"
        "𝐓𝐲𝐩𝐞 /𝐜𝐚𝐧𝐜𝐞𝐥 𝐭𝐨 𝐚𝐛𝐨𝐫𝐭.",
        parse_mode='Markdown',
        reply_markup=get_cancel_keyboard()
    )
    context.user_data['broadcast_mode'] = True

async def admin_forward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ 𝐘𝐨𝐮 𝐚𝐫𝐞 𝐧𝐨𝐭 𝐚𝐮𝐭𝐡𝐨𝐫𝐢𝐳𝐞𝐝!")
        return
    
    await update.message.reply_text(
        "🔄 *𝐅𝐨𝐫𝐰𝐚𝐫𝐝 𝐌𝐨𝐝𝐞*\n\n"
        f"👥 𝐓𝐨𝐭𝐚𝐥 𝐔𝐬𝐞𝐫𝐬: `{len(users_data)}`\n\n"
        "𝐅𝐨𝐫𝐰𝐚𝐫𝐝 𝐚𝐧𝐲 𝐦𝐞𝐬𝐬𝐚𝐠𝐞 𝐭𝐨 𝐛𝐫𝐨𝐚𝐝𝐜𝐚𝐬𝐭.\n\n"
        "𝐓𝐲𝐩𝐞 /𝐜𝐚𝐧𝐜𝐞𝐥 𝐭𝐨 𝐚𝐛𝐨𝐫𝐭.",
        parse_mode='Markdown',
        reply_markup=get_cancel_keyboard()
    )
    context.user_data['forward_mode'] = True

async def process_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    
    message = update.message
    
    if message.text and message.text == "/cancel":
        context.user_data.pop('broadcast_mode', None)
        context.user_data.pop('forward_mode', None)
        await update.message.reply_text("❌ 𝐁𝐫𝐨𝐚𝐝𝐜𝐚𝐬𝐭 𝐜𝐚𝐧𝐜𝐞𝐥𝐥𝐞𝐝.", reply_markup=get_admin_panel())
        return
    
    await update.message.reply_text(f"📢 𝐁𝐫𝐨𝐚𝐝𝐜𝐚𝐬𝐭𝐢𝐧𝐠...\n\n𝐒𝐞𝐧𝐝𝐢𝐧𝐠 𝐭𝐨 {len(users_data)} 𝐮𝐬𝐞𝐫𝐬.")
    
    success_count = 0
    fail_count = 0
    is_forward = context.user_data.get('forward_mode', False)
    
    for user_id_str in users_data.keys():
        try:
            user_id_int = int(user_id_str)
            if user_id_int == ADMIN_ID:
                continue
                
            if is_forward:
                await message.forward(chat_id=user_id_int)
            else:
                if message.text:
                    await context.bot.send_message(
                        chat_id=user_id_int,
                        text=f"{message.text}\n\n━━━━━━━━━━━━━━━━━━━━━━\n📢 𝐁𝐫𝐨𝐚𝐝𝐜𝐚𝐬𝐭\n🤖 {BOT_DISPLAY_NAME}"
                    )
                elif message.photo:
                    caption = message.caption or ""
                    caption += f"\n\n━━━━━━━━━━━━━━━━━━━━━━\n📢 𝐁𝐫𝐨𝐚𝐝𝐜𝐚𝐬𝐭\n🤖 {BOT_DISPLAY_NAME}"
                    await context.bot.send_photo(
                        chat_id=user_id_int,
                        photo=message.photo[-1].file_id,
                        caption=caption
                    )
                elif message.video:
                    caption = message.caption or ""
                    caption += f"\n\n━━━━━━━━━━━━━━━━━━━━━━\n📢 𝐁𝐫𝐨𝐚𝐝𝐜𝐚𝐬𝐭\n🤖 {BOT_DISPLAY_NAME}"
                    await context.bot.send_video(
                        chat_id=user_id_int,
                        video=message.video.file_id,
                        caption=caption
                    )
                elif message.document:
                    caption = message.caption or ""
                    caption += f"\n\n━━━━━━━━━━━━━━━━━━━━━━\n📢 𝐁𝐫𝐨𝐚𝐝𝐜𝐚𝐬𝐭\n🤖 {BOT_DISPLAY_NAME}"
                    await context.bot.send_document(
                        chat_id=user_id_int,
                        document=message.document.file_id,
                        caption=caption
                    )
            success_count += 1
            await asyncio.sleep(0.05)
        except Exception as e:
            fail_count += 1
    
    broadcast_history.append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type": "forward" if is_forward else "broadcast",
        "success": success_count,
        "fail": fail_count,
        "total": len(users_data)
    })
    save_broadcast_history(broadcast_history)
    
    await update.message.reply_text(
        f"📢 *𝐁𝐫𝐨𝐚𝐝𝐜𝐚𝐬𝐭 𝐂𝐨𝐦𝐩𝐥𝐞𝐭𝐞𝐝!*\n\n"
        f"✅ 𝐒𝐮𝐜𝐜𝐞𝐬𝐬: `{success_count}`\n"
        f"❌ 𝐅𝐚𝐢𝐥𝐞𝐝: `{fail_count}`\n"
        f"👥 𝐓𝐨𝐭𝐚𝐥: `{len(users_data)}`",
        parse_mode='Markdown',
        reply_markup=get_admin_panel()
    )
    
    context.user_data.pop('broadcast_mode', None)
    context.user_data.pop('forward_mode', None)

async def admin_ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ 𝐘𝐨𝐮 𝐚𝐫𝐞 𝐧𝐨𝐭 𝐚𝐮𝐭𝐡𝐨𝐫𝐢𝐳𝐞𝐝!")
        return ConversationHandler.END
    
    await update.message.reply_text(
        "🚫 *𝐁𝐚𝐧 𝐔𝐬𝐞𝐫*\n\n"
        "𝐒𝐞𝐧𝐝 𝐭𝐡𝐞 𝐔𝐬𝐞𝐫 𝐈𝐃 𝐭𝐨 𝐛𝐚𝐧.\n"
        "𝐄𝐱𝐚𝐦𝐩𝐥𝐞: `8379062893`\n\n"
        "𝐓𝐲𝐩𝐞 /𝐜𝐚𝐧𝐜𝐞𝐥 𝐭𝐨 𝐚𝐛𝐨𝐫𝐭.",
        parse_mode='Markdown',
        reply_markup=get_cancel_keyboard()
    )
    return BAN_USER_STATE

async def process_ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return ConversationHandler.END
    
    if update.message.text == "❌ 𝐂𝐚𝐧𝐜𝐞𝐥":
        await update.message.reply_text("❌ 𝐂𝐚𝐧𝐜𝐞𝐥𝐥𝐞𝐝.", reply_markup=get_admin_panel())
        return ConversationHandler.END
    
    try:
        user_id = int(update.message.text.strip())
        if user_id == ADMIN_ID:
            await update.message.reply_text("❌ 𝐂𝐚𝐧𝐧𝐨𝐭 𝐛𝐚𝐧 𝐚𝐝𝐦𝐢𝐧!", reply_markup=get_admin_panel())
            return ConversationHandler.END
        
        if user_id not in banned_users:
            banned_users.append(user_id)
            save_banned_users(banned_users)
            await update.message.reply_text(f"✅ 𝐔𝐬𝐞𝐫 `{user_id}` 𝐛𝐚𝐧𝐧𝐞𝐝!", parse_mode='Markdown', reply_markup=get_admin_panel())
        else:
            await update.message.reply_text(f"⚠️ 𝐔𝐬𝐞𝐫 `{user_id}` 𝐚𝐥𝐫𝐞𝐚𝐝𝐲 𝐛𝐚𝐧𝐧𝐞𝐝!", parse_mode='Markdown', reply_markup=get_admin_panel())
    except:
        await update.message.reply_text("❌ 𝐈𝐧𝐯𝐚𝐥𝐢𝐝 𝐔𝐬𝐞𝐫 𝐈𝐃!", reply_markup=get_admin_panel())
    
    return ConversationHandler.END

async def admin_unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ 𝐘𝐨𝐮 𝐚𝐫𝐞 𝐧𝐨𝐭 𝐚𝐮𝐭𝐡𝐨𝐫𝐢𝐳𝐞𝐝!")
        return ConversationHandler.END
    
    await update.message.reply_text(
        "✅ *𝐔𝐧𝐛𝐚𝐧 𝐔𝐬𝐞𝐫*\n\n"
        "𝐒𝐞𝐧𝐝 𝐭𝐡𝐞 𝐔𝐬𝐞𝐫 𝐈𝐃 𝐭𝐨 𝐮𝐧𝐛𝐚𝐧.\n"
        "𝐄𝐱𝐚𝐦𝐩𝐥𝐞: `8379062893`\n\n"
        "𝐓𝐲𝐩𝐞 /𝐜𝐚𝐧𝐜𝐞𝐥 𝐭𝐨 𝐚𝐛𝐨𝐫𝐭.",
        parse_mode='Markdown',
        reply_markup=get_cancel_keyboard()
    )
    return UNBAN_USER_STATE

async def process_unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return ConversationHandler.END
    
    if update.message.text == "❌ 𝐂𝐚𝐧𝐜𝐞𝐥":
        await update.message.reply_text("❌ 𝐂𝐚𝐧𝐜𝐞𝐥𝐥𝐞𝐝.", reply_markup=get_admin_panel())
        return ConversationHandler.END
    
    try:
        user_id = int(update.message.text.strip())
        if user_id in banned_users:
            banned_users.remove(user_id)
            save_banned_users(banned_users)
            await update.message.reply_text(f"✅ 𝐔𝐬𝐞𝐫 `{user_id}` 𝐮𝐧𝐛𝐚𝐧𝐧𝐞𝐝!", parse_mode='Markdown', reply_markup=get_admin_panel())
        else:
            await update.message.reply_text(f"⚠️ 𝐔𝐬𝐞𝐫 `{user_id}` 𝐧𝐨𝐭 𝐛𝐚𝐧𝐧𝐞𝐝!", parse_mode='Markdown', reply_markup=get_admin_panel())
    except:
        await update.message.reply_text("❌ 𝐈𝐧𝐯𝐚𝐥𝐢𝐝 𝐔𝐬𝐞𝐫 𝐈𝐃!", reply_markup=get_admin_panel())
    
    return ConversationHandler.END

async def admin_banned_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ 𝐘𝐨𝐮 𝐚𝐫𝐞 𝐧𝐨𝐭 𝐚𝐮𝐭𝐡𝐨𝐫𝐢𝐳𝐞𝐝!")
        return
    
    if not banned_users:
        await update.message.reply_text("📭 𝐍𝐨 𝐛𝐚𝐧𝐧𝐞𝐝 𝐮𝐬𝐞𝐫𝐬.", reply_markup=get_admin_panel())
        return
    
    banned_list = "🚫 *𝐁𝐚𝐧𝐧𝐞𝐝 𝐔𝐬𝐞𝐫𝐬:*\n\n"
    for i, uid in enumerate(banned_users, 1):
        banned_list += f"{i}. `{uid}`\n"
    
    await update.message.reply_text(banned_list, parse_mode='Markdown', reply_markup=get_admin_panel())

async def admin_broadcast_log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ 𝐘𝐨𝐮 𝐚𝐫𝐞 𝐧𝐨𝐭 𝐚𝐮𝐭𝐡𝐨𝐫𝐢𝐳𝐞𝐝!")
        return
    
    if not broadcast_history:
        await update.message.reply_text("📭 𝐍𝐨 𝐛𝐫𝐨𝐚𝐝𝐜𝐚𝐬𝐭 𝐡𝐢𝐬𝐭𝐨𝐫𝐲.", reply_markup=get_admin_panel())
        return
    
    log_text = "📋 *𝐁𝐫𝐨𝐚𝐝𝐜𝐚𝐬𝐭 𝐇𝐢𝐬𝐭𝐨𝐫𝐲:*\n\n"
    for i, record in enumerate(broadcast_history[-10:], 1):
        log_text += f"{i}. 📅 {record['timestamp']}\n"
        log_text += f"   📋 Type: {record['type'].upper()}\n"
        log_text += f"   ✅ {record['success']} | ❌ {record['fail']}\n\n"
    
    await update.message.reply_text(log_text, parse_mode='Markdown', reply_markup=get_admin_panel())

async def admin_clear_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ 𝐘𝐨𝐮 𝐚𝐫𝐞 𝐧𝐨𝐭 𝐚𝐮𝐭𝐡𝐨𝐫𝐢𝐳𝐞𝐝!")
        return
    
    keyboard = [
        [InlineKeyboardButton("🗑️ 𝐂𝐥𝐞𝐚𝐫 𝐔𝐬𝐞𝐫𝐬", callback_data="clear_users")],
        [InlineKeyboardButton("🗑️ 𝐂𝐥𝐞𝐚𝐫 𝐁𝐚𝐧𝐧𝐞𝐝", callback_data="clear_banned")],
        [InlineKeyboardButton("🗑️ 𝐂𝐥𝐞𝐚𝐫 𝐀𝐥𝐥", callback_data="clear_all")],
        [InlineKeyboardButton("❌ 𝐂𝐚𝐧𝐜𝐞𝐥", callback_data="clear_cancel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "⚠️ *𝐂𝐥𝐞𝐚𝐫 𝐃𝐚𝐭𝐚 - 𝐖𝐀𝐑𝐍𝐈𝐍𝐆!*\n\n"
        "𝐓𝐡𝐢𝐬 𝐚𝐜𝐭𝐢𝐨𝐧 𝐜𝐚𝐧𝐧𝐨𝐭 𝐛𝐞 𝐮𝐧𝐝𝐨𝐧𝐞!\n\n"
        "𝐒𝐞𝐥𝐞𝐜𝐭 𝐰𝐡𝐚𝐭 𝐭𝐨 𝐜𝐥𝐞𝐚𝐫:",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def clear_data_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "clear_users":
        users_data.clear()
        save_users_data(users_data)
        await query.edit_message_text("✅ 𝐔𝐬𝐞𝐫 𝐝𝐚𝐭𝐚 𝐜𝐥𝐞𝐚𝐫𝐞𝐝!", reply_markup=get_admin_panel())
    elif query.data == "clear_banned":
        banned_users.clear()
        save_banned_users(banned_users)
        await query.edit_message_text("✅ 𝐁𝐚𝐧𝐧𝐞𝐝 𝐥𝐢𝐬𝐭 𝐜𝐥𝐞𝐚𝐫𝐞𝐝!", reply_markup=get_admin_panel())
    elif query.data == "clear_all":
        users_data.clear()
        banned_users.clear()
        broadcast_history.clear()
        save_users_data(users_data)
        save_banned_users(banned_users)
        save_broadcast_history(broadcast_history)
        await query.edit_message_text("✅ 𝐀𝐥𝐥 𝐝𝐚𝐭𝐚 𝐜𝐥𝐞𝐚𝐫𝐞𝐝!", reply_markup=get_admin_panel())
    elif query.data == "clear_cancel":
        await query.edit_message_text("❌ 𝐂𝐥𝐞𝐚𝐫 𝐜𝐚𝐧𝐜𝐞𝐥𝐥𝐞𝐝.", reply_markup=get_admin_panel())

async def admin_check_api(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ 𝐘𝐨𝐮 𝐚𝐫𝐞 𝐧𝐨𝐭 𝐚𝐮𝐭𝐡𝐨𝐫𝐢𝐳𝐞𝐝!")
        return
    
    await update.message.reply_text("⏳ 𝐂𝐡𝐞𝐜𝐤𝐢𝐧𝐠 𝐀𝐏𝐈...")
    
    try:
        response = requests.get("https://loing-io.vercel.app/", timeout=10)
        api_status = "✅ 𝐎𝐧𝐥𝐢𝐧𝐞" if response.status_code == 200 else f"⚠️ Status: {response.status_code}"
    except:
        api_status = "❌ 𝐎𝐟𝐟𝐥𝐢𝐧𝐞"
    
    await update.message.reply_text(
        f"⚙️ *𝐀𝐏𝐈 𝐂𝐨𝐧𝐟𝐢𝐠*\n\n"
        f"🔗 𝐔𝐑𝐋: `{API_URL}`\n"
        f"📡 𝐒𝐭𝐚𝐭𝐮𝐬: {api_status}",
        parse_mode='Markdown',
        reply_markup=get_admin_panel()
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not await force_subscription_check(update, context):
        return
    
    if user_id == ADMIN_ID:
        help_text = (
            "🤖 *𝐀𝐝𝐦𝐢𝐧 𝐇𝐞𝐥𝐩*\n\n"
            "📊 𝐒𝐭𝐚𝐭𝐬 - Bot statistics\n"
            "👥 𝐔𝐬𝐞𝐫𝐬 - User list\n"
            "📢 𝐁𝐫𝐨𝐚𝐝𝐜𝐚𝐬𝐭 - Send message\n"
            "🔄 𝐅𝐨𝐫𝐰𝐚𝐫𝐝 - Forward message\n"
            "🚫 𝐁𝐚𝐧 - Ban user\n"
            "✅ 𝐔𝐧𝐛𝐚𝐧 - Unban user\n"
            "📜 𝐁𝐚𝐧𝐧𝐞𝐝 - Banned list\n"
            "📋 𝐋𝐨𝐠 - Broadcast history\n"
            "🗑️ 𝐂𝐥𝐞𝐚𝐫 - Clear data\n"
            "⚙️ 𝐀𝐏𝐈 - Check API\n\n"
            f"📢 {TOTAL_SUBSCRIPTIONS} channels"
        )
        reply_markup = get_admin_panel()
    else:
        help_text = (
            "🤖 *𝐔𝐬𝐞𝐫 𝐇𝐞𝐥𝐩*\n\n"
            "*𝐇𝐨𝐰 𝐭𝐨 𝐮𝐬𝐞:*\n\n"
            "1️⃣ Click 🔐 𝐔𝐈𝐃 + 𝐏𝐀𝐒𝐒𝐖𝐎𝐑𝐃\n"
            "2️⃣ Enter UID\n"
            "3️⃣ Enter password\n"
            "4️⃣ Enter bio\n"
            "5️⃣ Select region\n\n"
            f"⚠️ Must join {TOTAL_SUBSCRIPTIONS} channels"
        )
        reply_markup = get_user_keyboard()
    
    await update.message.reply_text(help_text, parse_mode='Markdown', reply_markup=reply_markup)

# ============= MAIN =============
def main():
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Bio upload conversation
    bio_conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^🔐 𝐔𝐈𝐃 + 𝐏𝐀𝐒𝐒𝐖𝐎𝐑𝐃$"), bio_menu_handler),
            MessageHandler(filters.Regex("^🎫 𝐀𝐂𝐂𝐄𝐒𝐒 𝐓𝐎𝐊𝐄𝐍$"), bio_menu_handler),
            MessageHandler(filters.Regex("^🔑 𝐉𝐖𝐓 𝐓𝐎𝐊𝐄𝐍$"), bio_menu_handler),
        ],
        states={
            WAITING_UID: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_uid)],
            WAITING_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_password)],
            WAITING_ACCESS_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_access_token)],
            WAITING_JWT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_jwt_token)],
            WAITING_BIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_bio)],
            WAITING_REGION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_region)],
        },
        fallbacks=[CommandHandler("cancel", start)],
    )
    
    # Ban conversation
    ban_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🚫 𝐁𝐚𝐧 𝐔𝐬𝐞𝐫$"), admin_ban_user)],
        states={BAN_USER_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_ban_user)]},
        fallbacks=[CommandHandler("cancel", start)],
    )
    
    # Unban conversation
    unban_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^✅ 𝐔𝐧𝐛𝐚𝐧 𝐔𝐬𝐞𝐫$"), admin_unban_user)],
        states={UNBAN_USER_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_unban_user)]},
        fallbacks=[CommandHandler("cancel", start)],
    )
    
    application.add_handler(bio_conv_handler)
    application.add_handler(ban_handler)
    application.add_handler(unban_handler)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(verify_callback, pattern="verify_subscription"))
    application.add_handler(CallbackQueryHandler(clear_data_callback, pattern="clear_"))
    application.add_handler(MessageHandler(filters.Regex("^📊 𝐒𝐭𝐚𝐭𝐬$"), admin_stats))
    application.add_handler(MessageHandler(filters.Regex("^👥 𝐔𝐬𝐞𝐫𝐬$"), admin_users))
    application.add_handler(MessageHandler(filters.Regex("^📢 𝐁𝐫𝐨𝐚𝐝𝐜𝐚𝐬𝐭$"), admin_broadcast))
    application.add_handler(MessageHandler(filters.Regex("^🔄 𝐅𝐨𝐫𝐰𝐚𝐫𝐝$"), admin_forward))
    application.add_handler(MessageHandler(filters.Regex("^📜 𝐁𝐚𝐧𝐧𝐞𝐝 𝐋𝐢𝐬𝐭$"), admin_banned_list))
    application.add_handler(MessageHandler(filters.Regex("^📋 𝐁𝐫𝐨𝐚𝐝𝐜𝐚𝐬𝐭 𝐋𝐨𝐠$"), admin_broadcast_log))
    application.add_handler(MessageHandler(filters.Regex("^🗑️ 𝐂𝐥𝐞𝐚𝐫 𝐃𝐚𝐭𝐚$"), admin_clear_data))
    application.add_handler(MessageHandler(filters.Regex("^⚙️ 𝐂𝐡𝐞𝐜𝐤 𝐀𝐏𝐈$"), admin_check_api))
    application.add_handler(MessageHandler(filters.Regex("^❓ 𝐇𝐞𝐥𝐩$"), help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_broadcast))
    
    print(f"🤖 {BOT_DISPLAY_NAME} is running...")
    print(f"👑 Admin ID: {ADMIN_ID}")
    print(f"📢 Channels: {TOTAL_SUBSCRIPTIONS}")
    print(f"👥 Users: {len(users_data)}")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
