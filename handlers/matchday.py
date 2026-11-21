import random
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
import database as db
from engine.match_engine import MatchEngine
from handlers.keyboards import get_matchday_keyboard

async def show_matchday(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    club = db.get_club_by_manager_id(user_id)
    if not club:
        await update.effective_message.reply_text("⚠️ Create a club first with /start!")
        return

    text = (
        f"⚽ **TOUCHLINE MATCHDAY CENTRE**\n"
        f"Club: **{club['name']}** | {club['league_name']}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🏟️ **Stadium:** {club['stadium_name']}\n"
        f"👥 **Squad Condition:** Ready for action\n\n"
        f"Select match type:\n"
        f"• **🏆 League Match:** Official league fixture with points on the line.\n"
        f"• **⚔️ Quick Friendly:** Test tactical setups without risk to league standing."
    )

    await update.effective_message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_matchday_keyboard()
    )

async def run_match_simulation(update: Update, context: ContextTypes.DEFAULT_TYPE, is_league: bool = True):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    home_club = db.get_club_by_manager_id(user_id)
    if not home_club:
        return

    # Find opponent in same league
    with db.get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clubs WHERE id != ? AND division_id = ? ORDER BY RANDOM() LIMIT 1", 
                       (home_club['id'], home_club['division_id']))
        away_club = cursor.fetchone()

    if not away_club:
        # Fallback to any club
        with db.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM clubs WHERE id != ? ORDER BY RANDOM() LIMIT 1", (home_club['id'],))
            away_club = cursor.fetchone()

    home_squad = db.get_squad(home_club['id'])
    away_squad = db.get_squad(away_club['id'])

    # Inform manager kick-off has begun
    await query.edit_message_text(
        f"📢 **KICK-OFF AT {home_club['stadium_name'].upper()}!**\n\n"
        f"**{home_club['name']}** 🆚 **{away_club['name']}**\n\n"
        f"⏱️ _The referee blows the whistle! The simulation is running..._",
        parse_mode="Markdown"
    )

    # Simulate match
    engine = MatchEngine(dict(home_club), dict(away_club), [dict(p) for p in home_squad], [dict(p) for p in away_squad])
    result = engine.simulate()

    # Save to database and credit ticket revenue
    match_type = 'league' if is_league else 'friendly'
    revenue, attendance = db.apply_match_result(
        home_club['id'], 
        away_club['id'], 
        result['home_score'], 
        result['away_score'], 
        match_type, 
        result['events'], 
        result['stats']
    )

    # Format goals list
    h_scorers_str = ", ".join(result['home_scorers']) if result['home_scorers'] else "None"
    a_scorers_str = ", ".join(result['away_scorers']) if result['away_scorers'] else "None"

    # Select up to 4 key events for commentary recap
    key_events = result['events']
    if len(key_events) > 5:
        key_events = key_events[:2] + key_events[-3:]
    events_str = "\n".join(key_events) if key_events else "A hard-fought midfield battle with few clear chances."

    stats = result['stats']
    report = (
        f"🏁 **FULL TIME REPORT**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"**{home_club['name']}  {result['home_score']} — {result['away_score']}  {away_club['name']}**\n"
        f"⚽ {home_club['name']}: {h_scorers_str}\n"
        f"⚽ {away_club['name']}: {a_scorers_str}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎙️ **MATCHDAY HIGHLIGHTS:**\n"
        f"{events_str}\n\n"
        f"📊 **OFFICIAL MATCH STATISTICS:**\n"
        f"• Possession: `{stats['possession']['home']}%` — `{stats['possession']['away']}%`\n"
        f"• Expected Goals (xG): `{stats['home']['xg']}` — `{stats['away']['xg']}`\n"
        f"• Total Shots: `{stats['home']['shots']}` — `{stats['away']['shots']}`\n"
        f"• Shots on Target: `{stats['home']['on_target']}` — `{stats['away']['on_target']}`\n"
        f"• Corners: `{stats['home']['corners']}` — `{stats['away']['corners']}`\n"
        f"• Fouls: `{stats['home']['fouls']}` (🟨{stats['home']['yellows']}) — `{stats['away']['fouls']}` (🟨{stats['away']['yellows']})\n\n"
        f"⭐ **Player of the Match:** {result['motm']}\n"
        f"🎟️ **Gate Receipts:** €{revenue:,} added to club treasury ({attendance:,} attendance)!\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━"
    )

    keyboard = [
        [InlineKeyboardButton("⚽ Play Another Match", callback_data="nav_matchday")],
        [InlineKeyboardButton("📊 View Standings", callback_data="nav_standings")],
        [InlineKeyboardButton("🔙 Club Overview", callback_data="nav_club")]
    ]

    await context.bot.send_message(
        chat_id=user_id,
        text=report,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
