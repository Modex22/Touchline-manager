from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
import database as db
from handlers.keyboards import get_main_menu_keyboard, get_club_actions_inline

# Temporary state storage for managers naming their club
PENDING_CLUB_CREATION = {}

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.register_manager(user.id, user.username or "", user.first_name or "Manager")

    club = db.get_club_by_manager_id(user.id)
    if club:
        text = (
            f"⚽ **WELCOME BACK, MANAGER {user.first_name.upper()}!**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🏟️ **Club:** {club['name']}\n"
            f"🏆 **Division:** {club['league_name']} (Tier {club['tier']})\n"
            f"💰 **Balance:** €{club['balance']:,}\n"
            f"📊 **Points:** {club['points']} pts (Played: {club['played']})\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Use the menu below or tap buttons to manage your club!"
        )
        if club['badge_file_id']:
            await update.message.reply_photo(
                photo=club['badge_file_id'],
                caption=text,
                parse_mode="Markdown",
                reply_markup=get_main_menu_keyboard()
            )
        else:
            await update.message.reply_text(
                text,
                parse_mode="Markdown",
                reply_markup=get_main_menu_keyboard()
            )
        return

    # User has no club yet: show onboarding options
    welcome_text = (
        f"👋 **WELCOME TO TOUCHLINE MANAGER!**\n\n"
        f"You are about to start your football management journey.\n"
        f"Take charge of tactics, transfers, youth development, and lead your club to glory!\n\n"
        f"How would you like to begin?"
    )

    keyboard = [
        [InlineKeyboardButton("✨ Create My Own Club", callback_data="onboard_create_custom")],
        [InlineKeyboardButton("⭐ Pick Existing Football Club", callback_data="onboard_pick_real")]
    ]
    
    webapp_url = db.os.getenv("WEBAPP_URL") if hasattr(db, 'os') else None
    
    await update.message.reply_text(
        welcome_text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_onboarding_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if data == "onboard_create_custom":
        PENDING_CLUB_CREATION[user_id] = True
        await query.edit_message_text(
            "📝 **NAME YOUR FOOTBALL CLUB**\n\n"
            "Please type and send the name for your football club (e.g. *Modex FC*, *Lagos City*, *Phoenix United*):",
            parse_mode="Markdown"
        )
    elif data == "onboard_pick_real":
        # Show real club options to choose from
        keyboard = [
            [
                InlineKeyboardButton("🔴 Arsenal FC", callback_data="pick_club_Arsenal FC"),
                InlineKeyboardButton("🔵 Man City", callback_data="pick_club_Manchester City")
            ],
            [
                InlineKeyboardButton("⚪ Real Madrid", callback_data="pick_club_Real Madrid"),
                InlineKeyboardButton("🔴 FC Barcelona", callback_data="pick_club_FC Barcelona")
            ],
            [
                InlineKeyboardButton("🔵 Chelsea FC", callback_data="pick_club_Chelsea FC"),
                InlineKeyboardButton("🔴 Liverpool FC", callback_data="pick_club_Liverpool FC")
            ],
            [
                InlineKeyboardButton("🔴 Bayern Munich", callback_data="pick_club_Bayern Munich"),
                InlineKeyboardButton("⚫ Juventus", callback_data="pick_club_Juventus")
            ],
            [InlineKeyboardButton("🔙 Back", callback_data="onboard_back")]
        ]
        await query.edit_message_text(
            "⭐ **SELECT A FOOTBALL CLUB TO MANAGE:**\n\n"
            "Choose a legendary club to take charge of:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    elif data.startswith("pick_club_"):
        club_name = data.replace("pick_club_", "")
        club_id = db.create_user_club(user_id, club_name)
        db.auto_pick_lineup(club_id)
        
        await query.edit_message_text(
            f"🎉 **APPOINTMENT CONFIRMED!**\n\n"
            f"You have been officially announced as the new manager of **{club_name}**!\n\n"
            f"Your starting squad is assembled. Use the persistent menu below to view your team, set tactics, and play your first match!",
            parse_mode="Markdown"
        )
        await context.bot.send_message(
            chat_id=user_id,
            text="⚽ Touchline Manager is ready. Select an option from the menu:",
            reply_markup=get_main_menu_keyboard()
        )
    elif data == "onboard_back":
        keyboard = [
            [InlineKeyboardButton("✨ Create My Own Club", callback_data="onboard_create_custom")],
            [InlineKeyboardButton("⭐ Pick Existing Football Club", callback_data="onboard_pick_real")]
        ]
        await query.edit_message_text(
            "👋 **WELCOME TO TOUCHLINE MANAGER!**\n\nHow would you like to begin?",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
