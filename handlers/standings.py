from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
import database as db

async def show_standings(update: Update, context: ContextTypes.DEFAULT_TYPE, division_id: int = None):
    user_id = update.effective_user.id
    club = db.get_club_by_manager_id(user_id)
    
    if division_id is None:
        division_id = club['division_id'] if club else 4

    standings = db.get_league_standings(division_id)
    
    with db.get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name, tier FROM leagues WHERE id = ?", (division_id,))
        league = cursor.fetchone()
        league_name = league['name'] if league else "League"

    lines = [
        f"📊 **OFFICIAL STANDINGS: {league_name.upper()}**",
        "```text",
        f"{'#':<3}{'Club':<16}{'P':<3}{'W':<3}{'D':<3}{'L':<3}{'GD':<4}{'Pts'}"
    ]

    for rank, c in enumerate(standings, start=1):
        is_user = (club and c['id'] == club['id'])
        c_name = (c['name'][:14] + "..") if len(c['name']) > 15 else c['name']
        marker = "⭐" if is_user else f"{rank}."
        gd = c['goal_diff']
        gd_str = f"+{gd}" if gd > 0 else str(gd)
        lines.append(f"{rank:<3}{c_name:<16}{c['played']:<3}{c['won']:<3}{c['drawn']:<3}{c['lost']:<3}{gd_str:<4}{c['points']}")

    lines.append("```")
    lines.append("🏆 *Top 2 promoted* | 🔻 *Bottom 2 relegated*")

    # League tier navigation buttons
    nav_buttons = [
        [
            InlineKeyboardButton("Tier 1: Premier", callback_data="view_div_1"),
            InlineKeyboardButton("Tier 2: Champ", callback_data="view_div_2")
        ],
        [
            InlineKeyboardButton("Tier 3: National", callback_data="view_div_3"),
            InlineKeyboardButton("Tier 4: Dev", callback_data="view_div_4")
        ],
        [InlineKeyboardButton("🔙 Club Overview", callback_data="nav_club")]
    ]

    markup = InlineKeyboardMarkup(nav_buttons)

    if update.callback_query:
        await update.callback_query.edit_message_text(
            "\n".join(lines),
            parse_mode="Markdown",
            reply_markup=markup
        )
    else:
        await update.effective_message.reply_text(
            "\n".join(lines),
            parse_mode="Markdown",
            reply_markup=markup
        )
