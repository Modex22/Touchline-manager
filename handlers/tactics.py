from telegram import Update
from telegram.ext import ContextTypes
import database as db
from handlers.keyboards import get_tactics_keyboard

async def show_tactics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    club = db.get_club_by_manager_id(user_id)
    if not club:
        await update.effective_message.reply_text("⚠️ Create a club first with /start!")
        return

    text = (
        f"📋 **TACTICS & FORMATION BOARD**\n"
        f"Club: **{club['name']}**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚽ **Active Formation:** `{club['formation']}`\n"
        f"🧠 **Mentality:** `{club['mentality']}`\n"
        f"⚔️ **Play Style:** `{club['play_style']}`\n\n"
        f"💡 **TACTICAL SYNERGY GUIDE:**\n"
        f"• **High Press** disrupts *Possession* teams.\n"
        f"• **Counter-Attack** punishes *High Press*.\n"
        f"• **Low Block** suffocates *Counter-Attack*.\n"
        f"• **Possession** unlocks and breaks down *Low Block*.\n\n"
        f"Select your tactical options below:"
    )

    markup = get_tactics_keyboard(club['formation'], club['mentality'], club['play_style'])
    await update.effective_message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=markup
    )

async def handle_tactics_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    club = db.get_club_by_manager_id(user_id)
    if not club:
        return

    if data.startswith("set_formation_"):
        new_form = data.replace("set_formation_", "")
        db.update_club_tactics(club['id'], formation=new_form)
        db.auto_pick_lineup(club['id'], formation=new_form)
    elif data.startswith("set_mentality_"):
        new_ment = data.replace("set_mentality_", "")
        db.update_club_tactics(club['id'], mentality=new_ment)
    elif data.startswith("set_style_"):
        new_style = data.replace("set_style_", "")
        db.update_club_tactics(club['id'], play_style=new_style)

    # Refresh view
    updated_club = db.get_club_by_id(club['id'])
    text = (
        f"📋 **TACTICS & FORMATION BOARD**\n"
        f"Club: **{updated_club['name']}**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚽ **Active Formation:** `{updated_club['formation']}`\n"
        f"🧠 **Mentality:** `{updated_club['mentality']}`\n"
        f"⚔️ **Play Style:** `{updated_club['play_style']}`\n\n"
        f"💡 **TACTICAL SYNERGY GUIDE:**\n"
        f"• **High Press** disrupts *Possession* teams.\n"
        f"• **Counter-Attack** punishes *High Press*.\n"
        f"• **Low Block** suffocates *Counter-Attack*.\n"
        f"• **Possession** unlocks and breaks down *Low Block*.\n\n"
        f"Select your tactical options below:"
    )
    markup = get_tactics_keyboard(updated_club['formation'], updated_club['mentality'], updated_club['play_style'])
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=markup)
