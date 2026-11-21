import asyncio
import logging
import sys
import os
from aiohttp import web
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

from config import BOT_TOKEN, PORT, HOST
import database as db

# Import Handlers
from handlers.start import start_command, handle_onboarding_callbacks, PENDING_CLUB_CREATION
from handlers.club import (
    show_club_dashboard, 
    handle_logo_upload, 
    show_finances,
    PENDING_LOGO_UPLOAD
)
from handlers.squad import show_squad, show_pitch_view, show_player_card
from handlers.tactics import show_tactics, handle_tactics_callbacks
from handlers.matchday import show_matchday, run_match_simulation
from handlers.market import show_market, handle_buy_player
from handlers.training import show_training, handle_training_drill
from handlers.standings import show_standings
from handlers.keyboards import get_main_menu_keyboard

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("TouchlineBot")

# --- Persistent Menu Text Router ---
async def handle_menu_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id

    # Check if user was in middle of naming their custom club
    if user_id in PENDING_CLUB_CREATION:
        club_name = text.strip()
        if len(club_name) < 3 or len(club_name) > 30:
            await update.message.reply_text("⚠️ Club name must be between 3 and 30 characters. Please try again:")
            return
        
        club_id = db.create_user_club(user_id, club_name)
        db.auto_pick_lineup(club_id)
        del PENDING_CLUB_CREATION[user_id]

        await update.message.reply_text(
            f"🎉 **CONGRATULATIONS, BOSS!**\n\n"
            f"**{club_name}** has been successfully founded!\n"
            f"Your starting squad is assembled in the **Development League**.\n"
            f"You can now set your tactics, train your squad, and prepare for matchday!",
            parse_mode="Markdown",
            reply_markup=get_main_menu_keyboard()
        )
        await show_club_dashboard(update, context)
        return

    # Check menu options
    if text == "🏟️ My Club":
        await show_club_dashboard(update, context)
    elif text == "👥 Squad":
        await show_squad(update, context)
    elif text == "📋 Tactics":
        await show_tactics(update, context)
    elif text == "⚽ Matchday":
        await show_matchday(update, context)
    elif text == "🔄 Transfers":
        await show_market(update, context)
    elif text == "📊 Standings":
        await show_standings(update, context)
    elif text == "🏋️ Training":
        await show_training(update, context)
    elif text == "💰 Finances":
        await show_finances(update, context)
    elif text == "🖼️ Upload Logo":
        PENDING_LOGO_UPLOAD.add(user_id)
        await update.message.reply_text(
            "🖼️ **UPLOAD CLUB BADGE**\n\n"
            "Please send a photo or image file to set as your official club badge!\n"
            "(A square PNG or JPG works best)",
            parse_mode="Markdown"
        )
    else:
        # Generic message: show menu
        await update.message.reply_text(
            "⚽ Use the menu below to navigate Touchline Manager:",
            reply_markup=get_main_menu_keyboard()
        )

# --- Universal Callback Query Router ---
async def callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id

    # Onboarding callbacks
    if data.startswith("onboard_") or data.startswith("pick_club_"):
        await handle_onboarding_callbacks(update, context)
        return

    # Navigation callbacks
    if data == "nav_club":
        await query.answer()
        await show_club_dashboard(update, context)
    elif data == "nav_squad":
        await query.answer()
        await show_squad(update, context)
    elif data == "nav_tactics":
        await query.answer()
        await show_tactics(update, context)
    elif data == "nav_matchday":
        await query.answer()
        await show_matchday(update, context)
    elif data == "nav_transfers":
        await query.answer()
        await show_market(update, context)
    elif data == "nav_standings":
        await query.answer()
        await show_standings(update, context)

    # Squad actions
    elif data == "act_autopick":
        club = db.get_club_by_manager_id(user_id)
        if club:
            db.auto_pick_lineup(club['id'], club['formation'])
            await query.answer("⚡ Starting XI auto-picked!", show_alert=True)
            await show_squad(update, context)
    elif data == "act_view_pitch":
        await show_pitch_view(update, context)
    elif data.startswith("view_player_"):
        player_id = int(data.replace("view_player_", ""))
        await show_player_card(update, context, player_id)

    # Tactics actions
    elif data.startswith("set_"):
        await handle_tactics_callbacks(update, context)

    # Matchday actions
    elif data == "match_league":
        await run_match_simulation(update, context, is_league=True)
    elif data == "match_friendly":
        await run_match_simulation(update, context, is_league=False)

    # Transfer actions
    elif data.startswith("buy_transfer_"):
        transfer_id = int(data.replace("buy_transfer_", ""))
        await handle_buy_player(update, context, transfer_id)
    elif data.startswith("market_list_prompt_"):
        player_id = int(data.replace("market_list_prompt_", ""))
        club = db.get_club_by_manager_id(user_id)
        player = db.get_player(player_id)
        if club and player:
            asking_price = int(player['value'] * 1.1)
            db.list_player_for_sale(player_id, club['id'], asking_price)
            await query.answer(f"✅ {player['name']} listed for €{asking_price:,}!", show_alert=True)
            await show_market(update, context)

    # Training actions
    elif data.startswith("train_"):
        focus = data.replace("train_", "")
        await handle_training_drill(update, context, focus)

    # Club upgrades
    elif data == "act_upgrade_stadium":
        club = db.get_club_by_manager_id(user_id)
        if club:
            success, msg = db.upgrade_stadium(club['id'])
            await query.answer(msg, show_alert=True)
            await show_club_dashboard(update, context)
    elif data == "act_prompt_logo":
        PENDING_LOGO_UPLOAD.add(user_id)
        await query.answer()
        await context.bot.send_message(
            chat_id=user_id,
            text="🖼️ Send a photo now to set it as your club badge!"
        )

    # Division standings switch
    elif data.startswith("view_div_"):
        div_id = int(data.replace("view_div_", ""))
        await show_standings(update, context, division_id=div_id)

# --- Render Health Check HTTP Server ---
async def start_health_server():
    """Lightweight web server so Render Web Service health checks succeed."""
    app = web.Application()
    
    async def health_check(request):
        return web.Response(text="Touchline Manager is online and running! ⚽", status=200)

    app.router.add_get("/", health_check)
    app.router.add_get("/health", health_check)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, HOST, PORT)
    await site.start()
    logger.info(f"Health server listening on http://{HOST}:{PORT}")

async def main():
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN is not set in environment or .env file!")
        logger.info("Please get a bot token from @BotFather and set BOT_TOKEN in .env")
        # Keep web server alive so Render doesn't crash on initial deployment before token is added
        await start_health_server()
        while True:
            await asyncio.sleep(3600)

    # Initialize database tables and seed AI teams
    logger.info("Initializing Touchline Manager Database...")
    db.init_db()
    logger.info("Database ready!")

    # Start health server for Render
    await start_health_server()

    # Build Telegram Bot application
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Register handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("club", show_club_dashboard))
    app.add_handler(CommandHandler("squad", show_squad))
    app.add_handler(CommandHandler("tactics", show_tactics))
    app.add_handler(CommandHandler("match", show_matchday))
    app.add_handler(CommandHandler("market", show_market))
    app.add_handler(CommandHandler("standings", show_standings))
    app.add_handler(CommandHandler("training", show_training))
    app.add_handler(CommandHandler("finances", show_finances))

    # Photo handler for club badge uploads
    app.add_handler(MessageHandler(filters.PHOTO, handle_logo_upload))

    # Text message handler for persistent keyboard menu
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu_text))

    # Inline buttons callback handler
    app.add_handler(CallbackQueryHandler(callback_router))

    logger.info("Touchline Manager Bot started polling...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling(allowed_updates=Update.ALL_TYPES)

    # Keep running
    try:
        while True:
            await asyncio.sleep(3600)
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Touchline Manager stopped.")
