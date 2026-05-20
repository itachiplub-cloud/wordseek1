import logging
import re
import unicodedata
import time
import random
import telebot
from telebot import types
import json
import os
import gc
import sys

# ==========================================
# LOAD WORD DATA FROM JSON FILES
# ==========================================

def load_words_from_json(filename):
    """Load words from JSON file"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            words_list = json.load(f)
            return set(word.lower() for word in words_list)
    except FileNotFoundError:
        print(f"⚠️ Warning: {filename} not found!")
        return set()
    except json.JSONDecodeError:
        print(f"⚠️ Warning: {filename} is not valid JSON!")
        return set()

# Load word lists from JSON files
WORD_LIST_4 = load_words_from_json('all-four.json')
WORD_LIST_5 = load_words_from_json('all-five.json')
WORD_LIST_6 = load_words_from_json('all-six.json')

# Combined dictionary for quick access
WORD_DICT = {
    4: WORD_LIST_4,
    5: WORD_LIST_5,
    6: WORD_LIST_6
}

# Print loaded statistics
print(f"📊 Loaded word statistics:")
print(f"   • 4-letter words: {len(WORD_LIST_4):,}")
print(f"   • 5-letter words: {len(WORD_LIST_5):,}")
print(f"   • 6-letter words: {len(WORD_LIST_6):,}")
print(f"   • Total: {len(WORD_LIST_4) + len(WORD_LIST_5) + len(WORD_LIST_6):,} words")

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
        "│ 🎯 Pattern → _a__e (4,5,6 letters)\n"
        "│ 🧠 Hint → 'sweet fruit'\n"
        "│ 🎮 Grid → 🟥🟨🟩\n"
        "│ ⚡ Speed → Instant Solve\n"
        "╰───────────────</blockquote>\n\n"

        "<blockquote expandable>╭─ ⚡ CORE ENGINE ─\n"
        "│ 🔥 Powered By: <b>@II_DevDynasty_II</b>\n"
        "│ ⚡ Speed: Instant Response System\n"
        "│ 📏 Supports: 4, 5, 6 letter words\n"
        f"│ 📚 Word Count: {len(WORD_LIST_4) + len(WORD_LIST_5) + len(WORD_LIST_6):,}\n"
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
        style="danger"
    )

    stats = types.InlineKeyboardButton(
        "📊 Stats",
        callback_data="stats",
        style="primary"
    )

    markup.add(solve)
    markup.add(help_btn, tips)
    markup.add(dev, stats)

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
# WORDLE FUNCTIONS (Updated for multiple lengths)
# ==========================================
def apply_wordle_feedback(guesses):
    """Apply Wordle feedback for words of any length (4,5,6)"""
    if not guesses:
        return set()
    
    # Get the word length from the first guess
    word_length = len(guesses[0][1])
    
    # Get the appropriate word list
    if word_length in WORD_DICT:
        candidates = set(WORD_DICT[word_length])
    else:
        return set()

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
    """Parse Wordle grid for any word length (4,5,6)"""
    guesses = []

    for line in text.splitlines():
        parts = line.strip().split()

        if not parts:
            continue

        colors = [c for c in parts if c in ["🟥", "🟨", "🟩"]]

        word = parts[-1]
        word = normalize_word(word)

        # Support for 4, 5, and 6 letter words
        if len(colors) == len(word) and len(word) in [4, 5, 6]:
            guesses.append(("".join(colors), word))

    return guesses

def find_words_by_pattern(pattern, length):
    """Find words matching pattern for specific length"""
    if length not in WORD_DICT:
        return []
    
    pattern = pattern.replace("_", ".").replace("?", ".")
    regex = re.compile(f"^{pattern}$")
    
    return [w for w in WORD_DICT[length] if regex.match(w)]

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
        "🧠 ʟᴏᴀᴅɪɴɢ ᴊsᴏɴ ᴡᴏʀᴅ ᴅᴀᴛᴀʙᴀsᴇ...",
        "🔍 ꜱᴄᴀɴɴɪɴɢ ᴅɪᴄᴛɪᴏɴᴀʀʏ (4,5,6 letters)...",
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
        has_spoiler=True
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
                "🔹 Pattern: <code>_a__e</code> (4,5,6 letters)\n"
                "🔹 Wordle Grid:\n"
                "🟥🟨🟩 apple (5 letters)\n"
                "🟥🟨🟩🟩 game (4 letters)\n"
                "🟥🟨🟩🟨🟩🟩 rocket (6 letters)\n\n"
                "⚡ Bot will solve instantly!\n"
                "📏 Supports: 4, 5, and 6 letter words"
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
                "• Combine hints + pattern\n"
                "• Try different word lengths\n\n"
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
                "• Pattern like <code>_a__e</code> (4,5,6 letters)\n"
                "• Wordle Grid with 🟥🟨🟩\n\n"
                "I'll solve it instantly!\n"
                "📏 Works with 4, 5, and 6 letter words"
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
    elif call.data == "stats":
        total_words = len(WORD_LIST_4) + len(WORD_LIST_5) + len(WORD_LIST_6)
        bot.edit_message_caption(
            caption=(
                "📊 <b>BOT STATISTICS</b>\n"
                "━━━━━━━━━━━━━━━\n\n"
                f"📏 4-letter words: <code>{len(WORD_LIST_4):,}</code>\n"
                f"📏 5-letter words: <code>{len(WORD_LIST_5):,}</code>\n"
                f"📏 6-letter words: <code>{len(WORD_LIST_6):,}</code>\n"
                f"📚 Total words: <code>{total_words:,}</code>\n\n"
                "⚡ Status: <b>ACTIVE</b>\n"
                "🧠 Database: <b>JSON</b>\n"
                "🚀 Performance: <b>OPTIMIZED</b>"
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
# WORD FINDER (Updated for JSON database)
# ==========================================
@bot.message_handler(func=lambda m: True)
def find_word(message):
    # Only process in private chats
    if message.chat.type != 'private':
        return
    
    text = message.text.strip()

    # ======================================
    # CASE 1: WORDLE GRID (Auto-detect length)
    # ======================================
    guesses = parse_wordle_message(text)

    if guesses:
        candidates = apply_wordle_feedback(guesses)
        word_length = len(guesses[0][1]) if guesses else 0

        if candidates:
            words_list = "\n".join(
                f"• <code>{word.upper()}</code>"
                for word in sorted(list(candidates))[:20]
            )

            bot.reply_to(
                message,
                (
                    f"<b>🎯 WORDLE CANDIDATES ({word_length} letters)</b>\n"
                    "━━━━━━━━━━━━━━━\n\n"
                    f"{words_list}\n\n"
                    f"📊 Total: <code>{len(candidates)}</code> words"
                ),
                parse_mode="HTML"
            )
        else:
            bot.reply_to(
                message,
                (
                    f"<b>❌ NO POSSIBLE WORDS FOUND ({word_length} letters)</b>\n"
                    "━━━━━━━━━━━━━━━"
                ),
                parse_mode="HTML"
            )
        return
    
    # ======================================
    # CASE 2: PATTERN with length detection
    # ======================================
    if "_" in text or "?" in text:
        # Detect pattern length
        pattern_length = len(text.replace("_", "").replace("?", "").replace(" ", ""))
        
        if pattern_length in [4, 5, 6]:
            results = find_words_by_pattern(text, pattern_length)
            
            if results:
                # Show first 50 results for patterns
                display_results = results[:50]
                bot.reply_to(
                    message,
                    f"✅ <b>Possible words ({pattern_length} letters):</b>\n\n" +
                    ", ".join([f"<code>{w.upper()}</code>" for w in display_results]) +
                    (f"\n\n➕ And {len(results) - 50} more..." if len(results) > 50 else "") +
                    f"\n\n📊 Total: <code>{len(results)}</code> words",
                    parse_mode="HTML"
                )
            else:
                bot.reply_to(
                    message,
                    f"❌ No matches found for pattern: <code>{text}</code>\n"
                    f"📏 Length: {pattern_length} letters",
                    parse_mode="HTML"
                )
        else:
            bot.reply_to(
                message,
                "❌ Please use patterns for 4, 5, or 6 letter words only!\n"
                "Examples:\n"
                "<code>_a__e</code> (5 letters)\n"
                "<code>_a_e</code> (4 letters)\n"
                "<code>__o__t</code> (6 letters)",
                parse_mode="HTML"
            )
        return

# ==========================================
# MAIN
# ==========================================
def main():
    # Send alive message to logger group
    total_words = len(WORD_LIST_4) + len(WORD_LIST_5) + len(WORD_LIST_6)
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
📏 Word Lengths: <b>4, 5, 6</b>
📚 Total Words: <code>{total_words:,}</code>
🗃️ Database: <b>JSON</b>
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
    print("📏 Supporting: 4, 5, and 6 letter words")
    print(f"📚 Loaded {total_words:,} words from JSON database")
    
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