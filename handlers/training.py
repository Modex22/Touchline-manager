from telegram import Update
from telegram.ext import ContextTypes
import database as db
from handlers.keyboards import get_training_keyboard

async def show_training(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    club = db.get_club_by_manager_id(user_id)
    if not club:
        await update.effective_message.reply_text("⚠️ Create a club first with /start!")
        return

    text = (
        f"🏋️ **TRAINING COMPLEX: {club['name'].upper()}**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Keep your players in peak physical and tactical condition.\n\n"
        f"Select a training focus for the squad:\n"
        f"• **🏃 Fitness Recovery:** Restores +10% fitness to all squad members.\n"
        f"• **🎯 Finishing Drills:** Enhances shooting and composure in front of goal.\n"
        f"• **🛡️ Defending Drills:** Improves tackling, marking, and aerial physical duels.\n"
        f"• **👟 Passing & Vision:** Boosts distribution and playmaking.\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━"
    )

    await update.effective_message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_training_keyboard()
    )

async def handle_training_drill(update: Update, context: ContextTypes.DEFAULT_TYPE, focus: str):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    club = db.get_club_by_manager_id(user_id)
    if not club:
        return

    db.train_squad(club['id'], focus)
    
    from telegram import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = [
        [InlineKeyboardButton("👥 Check Squad", callback_data="nav_squad")],
        [InlineKeyboardButton("🔙 Club Overview", callback_data="nav_club")]
    ]

    await query.edit_message_text(
        f"✅ **TRAINING SESSION COMPLETE!**\n\n"
        f"Your squad completed intensive **{focus}** drills.\n"
        f"Squad morale has increased, and player attributes have responded positively!",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
