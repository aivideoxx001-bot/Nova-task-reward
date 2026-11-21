 import os
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

db = sqlite3.connect("nova.db", check_same_thread=False)
db.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    balance REAL DEFAULT 0,
    referrals INTEGER DEFAULT 0
)
""")
db.commit()

def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Available Tasks", callback_data="tasks")],
        [InlineKeyboardButton("💰 My Balance", callback_data="balance")],
        [InlineKeyboardButton("📤 Submit Task", callback_data="submit")],
        [InlineKeyboardButton("👥 Refer Friends", callback_data="refer")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.execute("INSERT OR IGNORE INTO users(id) VALUES(?)", (user.id,))
    db.commit()

    if context.args:
        try:
            ref = int(context.args[0])
            if ref != user.id:
                cursor = db.execute(
                    "UPDATE users SET referrals=referrals+1 WHERE id=?",
                    (ref,)
                )
                db.commit()
        except ValueError:
            pass

    await update.message.reply_text(
        f"Welcome to Nova Task Reward Bot, {user.first_name}!\n\n"
        "Complete demo tasks and earn virtual rewards.",
        reply_markup=menu()
    )

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "tasks":
        await query.message.reply_text(
            "📋 AVAILABLE DEMO TASKS\n\n"
            "1. Visit a website - ₦100\n"
            "2. Follow a social page - ₦150\n"
            "3. Watch a video - ₦200\n\n"
            "These are simulated tasks for testing."
        )

    elif query.data == "balance":
        row = db.execute(
            "SELECT balance, referrals FROM users WHERE id=?",
            (user_id,)
        ).fetchone()
        await query.message.reply_text(
            f"💰 Your Demo Balance: ₦{row[0]:.2f}\n"
            f"👥 Referrals: {row[1]}"
        )

    elif query.data == "submit":
        context.user_data["waiting"] = True
        await query.message.reply_text(
            "📤 Send your demo task submission here."
        )

    elif query.data == "refer":
        me = await context.bot.get_me()
        link = f"https://t.me/{me.username}?start={user_id}"
        await query.message.reply_text(
            f"👥 Invite friends using your link:\n\n{link}"
        )

async def submission(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("waiting"):
        return

    context.user_data["waiting"] = False
    user = update.effective_user

    await update.message.reply_text(
        "✅ Your demo submission has been received!\n"
        "It is waiting for admin review."
    )

    if ADMIN_ID:
        await context.bot.send_message(
            ADMIN_ID,
            f"📩 NEW DEMO SUBMISSION\n"
            f"User: {user.first_name}\n"
            f"ID: {user.id}\n\n"
            f"Submission: {update.message.text}"
        )

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID or ADMIN_ID == 0:
        return

    count = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    await update.message.reply_text(
        f"⚙️ NOVA ADMIN PANEL\n\nTotal users: {count}"
    )

def main():
    if not TOKEN:
        raise ValueError("BOT_TOKEN is missing!")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, submission))

    print("Nova Task Reward Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
