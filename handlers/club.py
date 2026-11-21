import os
from telegram import Update
from telegram.ext import ContextTypes
from PIL import Image
import database as db
from config import LOGOS_DIR
from handlers.keyboards import get_club_actions_inline, get_main_menu_keyboard

# State to track managers who tapped "Upload Logo"
PENDING_LOGO_UPLOAD = set()

async def show_club_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    club = db.get_club_by_manager_id(user_id)

    if not club:
        await update.effective_message.reply_text(
            "⚠️ You don't have a club yet! Type /start to create or pick your team.",
            reply_markup=get_main_menu_keyboard()
        )
        return

    squad = db.get_squad(club['id'])
    starters = [p for p in squad if p['is_starter']]
    avg_ovr = int(sum(p['overall_rating'] for p in starters) / len(starters)) if starters else 70
    wage_bill = sum(p['wage'] for p in squad)

    caption = (
        f"🏟️ **CLUB DASHBOARD: {club['name'].upper()}**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🏆 **Division:** {club['league_name']} (Tier {club['tier']})\n"
        f"⭐ **Club Reputation:** {'★' * club['reputation']}{'☆' * (5 - club['reputation'])}\n"
        f"📊 **League Points:** {club['points']} pts (P: {club['played']} | W: {club['won']} | D: {club['drawn']} | L: {club['lost']})\n\n"
        f"💰 **FINANCIAL OVERVIEW**\n"
        f"• Balance: €{club['balance']:,}\n"
        f"• Weekly Wage Bill: €{wage_bill:,}\n"
        f"• Stadium: {club['stadium_name']} ({club['stadium_capacity']:,} seats)\n\n"
        f"👥 **SQUAD STATUS**\n"
        f"• Squad Size: {len(squad)}/25 players\n"
        f"• First XI Rating: **{avg_ovr} OVR**\n"
        f"• Formation: {club['formation']} | Style: {club['play_style']}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━"
    )

    if club['badge_file_id']:
        await context.bot.send_photo(
            chat_id=user_id,
            photo=club['badge_file_id'],
            caption=caption,
            parse_mode="Markdown",
            reply_markup=get_club_actions_inline()
        )
    else:
        await context.bot.send_message(
            chat_id=user_id,
            text=f"🛡️ **[ NO BADGE UPLOADED ]**\n\n{caption}",
            parse_mode="Markdown",
            reply_markup=get_club_actions_inline()
        )

async def handle_logo_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    club = db.get_club_by_manager_id(user_id)

    if not club:
        await update.message.reply_text("⚠️ You must create a club first with /start!")
        return

    photos = update.message.photo
    if not photos:
        await update.message.reply_text("⚠️ Please send an image photo for your club badge.")
        return

    # Get highest resolution photo
    highest_res_photo = photos[-1]
    file_id = highest_res_photo.file_id

    # Download and process locally to standard square badge
    badge_local_path = None
    try:
        tg_file = await context.bot.get_file(file_id)
        raw_path = os.path.join(LOGOS_DIR, f"temp_{club['id']}.jpg")
        await tg_file.download_to_drive(custom_path=raw_path)

        # Process with Pillow: resize and crop to 512x512
        with Image.open(raw_path) as img:
            img = img.convert("RGBA")
            # Make square thumbnail
            img.thumbnail((512, 512), Image.Resampling.LANCZOS)
            badge_filename = f"badge_club_{club['id']}.png"
            badge_local_path = os.path.join(LOGOS_DIR, badge_filename)
            img.save(badge_local_path, "PNG")

        if os.path.exists(raw_path):
            os.remove(raw_path)
    except Exception as e:
        # Fallback to pure file_id if image library has issue
        badge_local_path = None

    # Update database
    db.update_club_badge(club['id'], file_id, badge_local_path)
    if user_id in PENDING_LOGO_UPLOAD:
        PENDING_LOGO_UPLOAD.remove(user_id)

    await update.message.reply_photo(
        photo=file_id,
        caption=(
            f"✅ **NEW CLUB BADGE CONFIRMED!**\n\n"
            f"Your official club logo for **{club['name']}** has been updated.\n"
            f"It will now be displayed on matchdays, standings, and your club profile!"
        ),
        parse_mode="Markdown",
        reply_markup=get_main_menu_keyboard()
    )

async def show_finances(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    club = db.get_club_by_manager_id(user_id)
    if not club:
        return

    squad = db.get_squad(club['id'])
    total_wages = sum(p['wage'] for p in squad)
    squad_value = sum(p['value'] for p in squad)
    ticket_revenue_per_match = int(club['stadium_capacity'] * 0.85 * 35)

    text = (
        f"💰 **FINANCIAL BALANCE SHEET: {club['name'].upper()}**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💵 **Current Treasury:** €{club['balance']:,}\n"
        f"💎 **Total Squad Valuation:** €{squad_value:,}\n\n"
        f"📉 **Weekly Expenses:**\n"
        f"• Player Wages: -€{total_wages:,} / week\n"
        f"• Staff & Maintenance: -€25,000 / week\n\n"
        f"📈 **Matchday Revenue:**\n"
        f"• Est. Gate Receipts: +€{ticket_revenue_per_match:,} / home match\n"
        f"• Stadium Capacity: {club['stadium_capacity']:,} seats\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Stadium expansion adds +5,000 seats (€5,000,000 cost) to boost match income."
    )
    
    from telegram import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = [
        [InlineKeyboardButton("🏟️ Expand Stadium (+5,000 seats)", callback_data="act_upgrade_stadium")],
        [InlineKeyboardButton("🔙 Club Overview", callback_data="nav_club")]
    ]
    
    await update.effective_message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
