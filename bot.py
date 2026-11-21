import asyncio
import logging
import sys
import os
from aiohttp import web
from telegram import Update, MenuButtonWebApp, MenuButtonCommands, WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
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

# Handlers
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

# Helper to resolve WebApp URL
def get_webapp_url():
    url = os.getenv("WEBAPP_URL") or os.getenv("RENDER_EXTERNAL_URL") or os.getenv("RENDER_EXTERNAL_HOSTNAME")
    if url:
        if not url.startswith("http://") and not url.startswith("https://"):
            url = f"https://{url}"
        return url
    return None

# --- Persistent Menu Text Router ---
async def handle_menu_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id

    # Handle club naming
    if user_id in PENDING_CLUB_CREATION:
        club_name = text.strip()
        if len(club_name) < 3 or len(club_name) > 30:
            await update.message.reply_text("⚠️ Club name must be between 3 and 30 characters. Please try again:")
            return
        
        club_id = db.create_user_club(user_id, club_name)
        db.auto_pick_lineup(club_id)
        del PENDING_CLUB_CREATION[user_id]

        webapp_url = get_webapp_url()
        buttons = []
        if webapp_url:
            buttons.append([InlineKeyboardButton("🎮 Open Touchline Play Screen", web_app=WebAppInfo(url=webapp_url))])

        await update.message.reply_text(
            f"🎉 **CONGRATULATIONS, BOSS!**\n\n"
            f"**{club_name}** has been successfully founded!\n"
            f"Your starting squad is assembled in the **Development League**.\n"
            f"You can now set your tactics, train your squad, and prepare for matchday!",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(buttons) if buttons else get_main_menu_keyboard()
        )
        await show_club_dashboard(update, context)
        return

    # Check text menu buttons
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
        webapp_url = get_webapp_url()
        keyboard = []
        if webapp_url:
            keyboard.append([InlineKeyboardButton("🎮 Play Screen (Full App)", web_app=WebAppInfo(url=webapp_url))])
        
        await update.message.reply_text(
            "⚽ Use the menu below or tap Play Screen to manage your club:",
            reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else get_main_menu_keyboard()
        )

# --- Universal Callback Query Router with Safe Error Handling ---
async def callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    # Always acknowledge the query immediately so the button stops loading
    try:
        await query.answer()
    except Exception as e:
        logger.warning(f"Failed to answer callback query: {e}")

    data = query.data
    user_id = query.from_user.id

    try:
        # Onboarding
        if data.startswith("onboard_") or data.startswith("pick_club_"):
            await handle_onboarding_callbacks(update, context)
            return

        # Navigation
        if data == "nav_club":
            await show_club_dashboard(update, context)
        elif data == "nav_squad":
            await show_squad(update, context)
        elif data == "nav_tactics":
            await show_tactics(update, context)
        elif data == "nav_matchday":
            await show_matchday(update, context)
        elif data == "nav_transfers":
            await show_market(update, context)
        elif data == "nav_standings":
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

        # Tactics
        elif data.startswith("set_"):
            await handle_tactics_callbacks(update, context)

        # Matchday
        elif data == "match_league":
            await run_match_simulation(update, context, is_league=True)
        elif data == "match_friendly":
            await run_match_simulation(update, context, is_league=False)

        # Transfers
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

        # Training
        elif data.startswith("train_"):
            focus = data.replace("train_", "")
            await handle_training_drill(update, context, focus)

        # Stadium Upgrades
        elif data == "act_upgrade_stadium":
            club = db.get_club_by_manager_id(user_id)
            if club:
                success, msg = db.upgrade_stadium(club['id'])
                await query.answer(msg, show_alert=True)
                await show_club_dashboard(update, context)
        elif data == "act_prompt_logo":
            PENDING_LOGO_UPLOAD.add(user_id)
            await context.bot.send_message(
                chat_id=user_id,
                text="🖼️ Send a photo now to set it as your club badge!"
            )

        # Division switcher
        elif data.startswith("view_div_"):
            div_id = int(data.replace("view_div_", ""))
            await show_standings(update, context, division_id=div_id)

    except Exception as e:
        logger.error(f"Error handling callback {data}: {e}", exc_info=True)
        await context.bot.send_message(
            chat_id=user_id,
            text="⚠️ An update occurred. Please use the menu below to continue:",
            reply_markup=get_main_menu_keyboard()
        )

# --- Render Health Check & WebApp Server ---
async def start_web_server():
    """Serves the Telegram Web App and health checks."""
    app = web.Application()
    
    template_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")

    async def serve_webapp(request):
        if os.path.exists(template_path):
            with open(template_path, "r", encoding="utf-8") as f:
                content = f.read()
            return web.Response(text=content, content_type="text/html")
        return web.Response(text="Touchline Manager WebApp is building...", status=200)

    async def health_check(request):
        return web.Response(text="Touchline Manager is online and running! ⚽", status=200)

    # API endpoints for live webapp integration
    async def api_club_data(request):
        # Default preview data or lookup by query param
        return web.json_response({
            "name": "MODEX FC",
            "country": "Spain",
            "tier": 2,
            "division": "Championship",
            "balance": 15000000,
            "stars": 100,
            "rating": 54.20
        })

    app.router.add_get("/", serve_webapp)
    app.router.add_get("/webapp", serve_webapp)
    app.router.add_get("/health", health_check)
    app.router.add_get("/api/club", api_club_data)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, HOST, PORT)
    await site.start()
    logger.info(f"Web server & WebApp listening on http://{HOST}:{PORT}")

async def setup_menu_button(bot):
    """Configures the native Telegram Menu button next to chat input."""
    webapp_url = get_webapp_url()
    try:
        if webapp_url:
            await bot.set_chat_menu_button(
                menu_button=MenuButtonWebApp(
                    text="Play",
                    web_app=WebAppInfo(url=webapp_url)
                )
            )
            logger.info(f"Set native Telegram Menu Button to WebApp: {webapp_url}")
        else:
            await bot.set_chat_menu_button(menu_button=MenuButtonCommands())
            logger.info("Set native Telegram Menu Button to standard Commands")
    except Exception as e:
        logger.warning(f"Could not set chat menu button: {e}")

async def main():
    # Initialize database
    logger.info("Initializing Touchline Manager Database...")
    db.init_db()
    logger.info("Database ready!")

    # Start health & webapp server
    await start_web_server()

    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN is not set in environment or .env file!")
        logger.info("Health server is running so Render remains healthy. Please set BOT_TOKEN.")
        while True:
            await asyncio.sleep(3600)

    # Build Telegram Bot application
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Configure native Telegram menu button
    await setup_menu_button(app.bot)

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

    # Photo handler
    app.add_handler(MessageHandler(filters.PHOTO, handle_logo_upload))

    # Text message handler
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
