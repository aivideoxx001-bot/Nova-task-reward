()
import os
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = os.environ["BOT_TOKEN"]
ADMIN_ID = int(os.environ["ADMIN_ID"])
WEBHOOK_SECRET = os.environ["WEBHOOK_SECRET"]

DB = "nova.db"


def database():
    conn = sqlite3.connect(DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance REAL DEFAULT 0,
            referrals INTEGER DEFAULT 0
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            proof TEXT,
            status TEXT DEFAULT 'Pending'
        )
    """)
    conn.commit()
    conn.close()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    conn = sqlite3.connect(DB)
    conn.execute(
        "INSERT OR IGNORE INTO users (user_id) VALUES (?)",
        (user.id,)
    )
    conn.commit()
    conn.close()

    keyboard = [
        [InlineKeyboardButton("📋 Available Tasks", callback_data="tasks")],
        [InlineKeyboardButton("📤 Submit Task", callback_data="submit")],
        [InlineKeyboardButton("💰 My Balance", callback_data="balance")],
        [InlineKeyboardButton("👥 Refer Friends", callback_data="refer")],
        [InlineKeyboardButton("⚙️ Admin Panel", callback_data="admin")],
    ]

    await update.message.reply_text(
        f"🎉 Welcome to Nova Task Reward, {user.first_name}!\n\n"
        "Complete tasks and submit your proof.\n"
        "This is currently a demo reward bot.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "tasks":
        await query.message.reply_text(
            "📋 AVAILABLE TASKS\n\n"
            "1. Follow a social media page\n"
            "2. Visit a website\n"
            "3. Complete a survey\n\n"
            "Use Submit Task to send your proof."
        )

    elif query.data == "submit":
        context.user_data["waiting_proof"] = True
        await query.message.reply_text(
            "📤 Send your task proof as a text message."
        )

    elif query.data == "balance":
        conn = sqlite3.connect(DB)
        row = conn.execute(
            "SELECT balance
