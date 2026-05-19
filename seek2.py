import logging
import re
import unicodedata
import time
import random
import telebot
from telebot import types
import nltk
from nltk.corpus import words, wordnet
import gc
import sys
import os


NLTK_DATA = "/opt/nltk_data"

if not os.path.exists(NLTK_DATA):
    os.makedirs(NLTK_DATA, exist_ok=True)
    nltk.download("words", download_dir=NLTK_DATA)
    nltk.download("wordnet", download_dir=NLTK_DATA)

nltk.data.path.append(NLTK_DATA)

WORD_LIST = set(w.lower() for w in words.words() if len(w) == 5)

plugins = dict(root="plugins")
# ==========================================
# BOT CONFIG
# ==========================================
BOT_TOKEN = "8760502051:AAEFrIPp6pjLkg9MmhE0uHLbkr1CKx2iM0s"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# ==========================================
# LOGGING CONFIGURATION
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('wordle_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Logger Group Chat ID (Replace with your logger group chat ID)
LOGGER_GROUP_ID = -1003964165574  # Replace with your actual logger group ID

# ==========================================
# IMAGE URL
# ==========================================
IMAGE_URL = "https://res.cloudinary.com/dj0b9hcb1/image/upload/f_auto,q_auto/download_13_ka42mk"

# ==========================================
# HELPERS
# ==========================================
def normalize_word(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", text)
        if ord(c) < 128
    )

def get_start_caption(user):
    user_link = f"<a href='tg://user?id={user.id}'>{user.first_name}</a>"

    return (
        "<blockquote expandable>╭─〔 ⚡ WORDLE CORE ACTIVATED 〕─╮\n"
        f"│ 👤 {user_link}\n"
        "│ 🧠 AI MODE: ENABLED\n"
        "│ ⚔️ STATUS: UNSTOPPABLE\n"
        "╰────────────────────╯</blockquote>\n\n"

        "<blockquote>❝ Guess Less. Win More. ❞</blockquote>\n\n"

        "<blockquote expandable>╭─ SYSTEM ─\n"
        "│ 🎯 Pattern → _a__e\n"
        "│ 🧠 Hint → 'sweet fruit'\n"
        "│ 🎮 Grid → 🟥🟨🟩\n"
        "│ ⚡ Speed → Instant Solve\n"
        "╰───────────────</blockquote>\n\n"

        "<blockquote expandable>╭─ ⚡ CORE ENGINE ─\n"
        "│ 🔥 Powered By: <b>@II_DevDynasty_II</b>\n"
        "│ 🧠 Brain: Advanced NLP + WordNet\n"
        "│ ⚡ Speed: Instant Response System\n"
        "╰───────────────</blockquote>\n\n"

        "<blockquote>❝ No Luck. Only Logic ⚡ ❞</blockquote>"
    )

def get_buttons():
    markup = types.InlineKeyboardMarkup(row_width=2)

    solve = types.InlineKeyboardButton(
        "🎯 Solve Wordle",
        callback_data="solve",
        style="success"
    )

    help_btn = types.InlineKeyboardButton(
        "📖 Help",
        callback_data="help",
        style="success"
    )

    tips = types.InlineKeyboardButton(
        "⚡ Tips",
        callback_data="tips",
        style="danger"
    )

    dev = types.InlineKeyboardButton(
        "🔥 Developer",
        url="https://t.me/itachiplub02",
        style="primary"
    )

    markup.add(solve)
    markup.add(help_btn, tips)
    markup.add(dev)

    return markup

def send_logger_message(message_text):
    """Send message to logger group"""
    try:
        bot.send_message(LOGGER_GROUP_ID, message_text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Failed to send logger message: {e}")

# ==========================================
# AUTO LEAVE GROUP SYSTEM
# ==========================================
@bot.message_handler(content_types=['new_chat_members'])
def on_new_chat_member(message):
    """Auto leave groups when bot is added"""
    for new_member in message.new_chat_members:
        if new_member.id == bot.get_me().id:
            # Bot was added to a group
            try:
                leave_msg = bot.send_message(
                    message.chat.id,
                    "<blockquote>⚠️ <b>I only work in private chats!</b>\n\n"
                    "Please use me in DM. Goodbye! 👋</blockquote>",
                    parse_mode="HTML"
                )
                time.sleep(2)
                bot.leave_chat(message.chat.id)
                
                # Log the event
                logger.info(f"Bot left group: {message.chat.id} (Title: {message.chat.title})")
                send_logger_message(
                    f"<blockquote expandable>🚪 <b>Bot Left Group</b>\n"
                    f"📱 Group ID: <code>{message.chat.id}</code>\n"
                    f"📛 Group Name: {message.chat.title}\n"
                    f"👥 Members: {message.chat.get_members_count() if hasattr(message.chat, 'get_members_count') else 'Unknown'}</blockquote>"
                )
            except Exception as e:
                logger.error(f"Error leaving group: {e}")
            break

# ==========================================
# WORDLE FUNCTIONS
# ==========================================
def apply_wordle_feedback(guesses):
    candidates = set(WORD_LIST)

    for colors, word in guesses:
        word = normalize_word(word.lower())
        new_candidates = set()

        for candidate in candidates:
            ok = True

            for i, c in enumerate(word):
                color = colors[i]

                if color == "🟩":
                    if candidate[i] != c:
                        ok = False
                        break

                elif color == "🟨":
                    if c not in candidate or candidate[i] == c:
                        ok = False
                        break

                elif color == "🟥":
                    if c in candidate and any(
                        clr in ["🟩", "🟨"] and wc == c
                        for wc, clr in zip(word, colors)
                    ):
                        pass
                    elif c in candidate:
                        ok = False
                        break

            if ok:
                new_candidates.add(candidate)

        candidates = new_candidates

    return candidates

def parse_wordle_message(text):
    guesses = []

    for line in text.splitlines():
        parts = line.strip().split()

        if not parts:
            continue

        colors = [c for c in parts if c in ["🟥", "🟨", "🟩"]]

        word = parts[-1]
        word = normalize_word(word)

        if len(colors) == len(word) == 5:
            guesses.append(("".join(colors), word))

    return guesses

# ==========================================
# START COMMAND
# ==========================================
@bot.message_handler(commands=['start'])
def start(message):
    user = message.from_user
    
    # Log user start in DM
    if message.chat.type == 'private':
        logger.info(f"User started bot: {user.id} - {user.first_name}")
        send_logger_message(
            f"""
        <blockquote expandable>
       ✅ <b>New User Started Bot</b>

       👤 User: <a href='tg://user?id={user.id}'>{user.first_name}</a>
       🆔 ID: <code>{user.id}</code>
       📱 Type: <code>DM</code>
       </blockquote>
        """
        )

    # Sticker
    sticker = bot.send_sticker(
        message.chat.id,
        "CAACAgUAAxkBAAGIdhhp20c_H28MK4YTZ2fJI67ekgzaigACbiEAAko6gVe6vVkkDDjqIToE"
    )

    # Loading animation
    msg = bot.send_message(message.chat.id, "⚡ booting...")

    frames = [
        "⚡ ᴘᴏᴡᴇʀɪɴɢ sʏsᴛᴇᴍ...",
        "🧠 ʟᴏᴀᴅɪɴɢ ᴡᴏʀᴅʟᴇ ᴇɴɢɪɴᴇ...",
        "🔍 ꜱᴄᴀɴɴɪɴɢ ᴅɪᴄᴛɪᴏɴᴀʀʏ...",
        "💾 ꜱᴇᴛᴛɪɴɢ ᴀʟɢᴏʀɪᴛʜᴍ...",
        "🚀 ʀᴇᴀᴅʏ!"
    ]

    for frame in frames:
        bot.edit_message_text(
            frame,
            message.chat.id,
            msg.message_id
        )
        time.sleep(0.3)

    # Cleanup
    bot.delete_message(message.chat.id, sticker.message_id)
    bot.delete_message(message.chat.id, msg.message_id)

    # Final intro
    bot.send_photo(
        message.chat.id,
        IMAGE_URL,
        caption=get_start_caption(user),
        reply_markup=get_buttons(),
        has_spoiler=true
    )

# ==========================================
# CALLBACK BUTTONS
# ==========================================
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "help":
        bot.edit_message_caption(
            caption=(
                "📖 <b>HOW TO USE</b>\n\n"
                "🔹 Pattern: <code>_a__e</code>\n"
                "🔹 Wordle Grid:\n"
                "🟥🟨🟩 apple\n\n"
                "🔹 Hint:\n"
                "sweet fruit\n\n"
                "⚡ Bot will solve instantly!"
            ),
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton(
                    "🔙 Back",
                    callback_data="back"
                )
            )
        )
    elif call.data == "tips":
        bot.edit_message_caption(
            caption=(
                "⚡ <b>PRO TIPS</b>\n\n"
                "• Use more greens 🟩\n"
                "• Avoid repeated reds 🟥\n"
                "• Combine hints + pattern\n\n"
                "🔥 Play smarter!"
            ),
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton(
                    "🔙 Back",
                    callback_data="back"
                )
            )
        )
    elif call.data == "solve":
        bot.edit_message_caption(
            caption=(
                "🎯 <b>READY TO SOLVE?</b>\n\n"
                "Send me:\n"
                "• Pattern like <code>_a__e</code>\n"
                "• Wordle Grid with 🟥🟨🟩\n"
                "• Hint like 'sweet fruit'\n\n"
                "I'll solve it instantly!"
            ),
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton(
                    "🔙 Back",
                    callback_data="back"
                )
            )
        )
    elif call.data == "back":
        bot.edit_message_caption(
            caption=get_start_caption(call.from_user),
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=get_buttons()
        )

# ==========================================
# GET FILE ID
# ==========================================
@bot.message_handler(commands=['getfileid'])
def get_file_id(message):
    if message.reply_to_message and message.reply_to_message.sticker:
        bot.reply_to(
            message,
            message.reply_to_message.sticker.file_id
        )
    else:
        bot.reply_to(
            message,
            "Reply to sticker with /getfileid"
        )

# ==========================================
# WORD FINDER
# ==========================================
@bot.message_handler(func=lambda m: True)
def find_word(message):
    # Only process in private chats
    if message.chat.type != 'private':
        return
    
    text = message.text.strip()

    # ======================================
    # CASE 1: WORDLE GRID
    # ======================================
    guesses = parse_wordle_message(text)

    if guesses:
        candidates = apply_wordle_feedback(guesses)

        if candidates:
            words_list = "\n".join(
                f"• <code>{word.upper()}</code>"
                for word in sorted(list(candidates))[:20]
            )

            bot.reply_to(
                message,
                (
                    "<b>🎯 WORDLE CANDIDATES</b>\n"
                    "━━━━━━━━━━━━━━━\n\n"
                    f"{words_list}"
                ),
                parse_mode="HTML"
            )
        else:
            bot.reply_to(
                message,
                (
                    "<b>❌ NO POSSIBLE WORDS FOUND</b>\n"
                    "━━━━━━━━━━━━━━━"
                ),
                parse_mode="HTML"
            )
        return
    
    # ======================================
    # CASE 2: PATTERN
    # ======================================
    if "_" in text or "?" in text:
        pattern = text.replace("_", ".").replace("?", ".")
        regex = re.compile(f"^{pattern}$")
        
        results = [
            w for w in WORD_LIST
            if regex.match(w)
        ]
        
        if results:
            bot.reply_to(
                message,
                "✅ Possible words:\n\n" +
                ", ".join(results[:20])
            )
        else:
            bot.reply_to(
                message,
                "❌ No matches found!"
            )
        return

    # ======================================
    # CASE 3: HINT SEARCH
    # ======================================
    results = []
    for w in WORD_LIST:
        for s in wordnet.synsets(w):
            if text.lower() in s.definition().lower():
                results.append(w)
                break
    
    if results:
        bot.reply_to(
            message,
            "💡 Hint matches:\n\n" +
            ", ".join(results[:20])
        )
    else:
        bot.reply_to(
            message,
            "❌ No word found for that hint."
        )

# ==========================================
# MAIN
# ==========================================
def main():
    # Send alive message to logger group
    alive_message = (
         f"""
    <blockquote expandable>
    🤖 <b>WORDLE BOT IS ALIVE!</b>
    ━━━━━━━━━━━━━━━
   ⏰ Time: <code>{time.strftime('%Y-%m-%d %H:%M:%S')}</code>
   ⚡ Status: <b>RUNNING</b>
   🎯 Mode: <code>ACTIVE</code>
   💾 Memory: <b>ACTIVE</b>
   🔄 Auto-GC: <b>ENABLED</b>
   </blockquote>
   """
    )
    
    logger.info("Bot started successfully!")
    send_logger_message(alive_message)
    
    # Enable auto garbage collection
    gc.enable()
    gc.set_threshold(700, 10, 5)
    
    print("🤖 WORDLE TELEBOT RUNNING...")
    print("⚡ Auto GC Enabled")
    print("📋 Logger Active")
    print("🚪 Auto Leave Groups: ACTIVE")
    
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        send_logger_message("🛑 <b>Bot Stopped!</b>")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
        send_logger_message(f"❌ <b>Bot Crashed!</b>\nError: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
