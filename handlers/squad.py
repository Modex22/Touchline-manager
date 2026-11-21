from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
import database as db
from engine.tactics import render_pitch_ascii
from handlers.keyboards import get_squad_actions_inline

async def show_squad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    club = db.get_club_by_manager_id(user_id)
    if not club:
        await update.effective_message.reply_text("⚠️ Create a club first with /start!")
        return

    squad = db.get_squad(club['id'])
    starters = [p for p in squad if p['is_starter']]
    bench = [p for p in squad if not p['is_starter']]

    lines = [
        f"👥 **SQUAD ROSTER: {club['name'].upper()}**",
        f"Formation: **{club['formation']}** · Starters: {len(starters)}/11 · Total: {len(squad)}/25",
        "━━━━━━━━━━━━━━━━━━━━━━━━",
        "⭐ **STARTING XI:**"
    ]

    for p in starters:
        pos = p['lineup_position'] or p['position']
        fit_emoji = "🟢" if p['fitness'] >= 85 else ("🟡" if p['fitness'] >= 70 else "🔴")
        lines.append(f"`{pos:<3}` **{p['name']}** ({p['overall_rating']} OVR) · {fit_emoji}{p['fitness']}% · €{p['value']//1_000_000}M")

    lines.append("\n🪑 **SUBSTITUTES & RESERVES:**")
    for p in bench[:10]:
        fit_emoji = "🟢" if p['fitness'] >= 85 else ("🟡" if p['fitness'] >= 70 else "🔴")
        lines.append(f"`{p['position']:<3}` {p['name']} ({p['overall_rating']} OVR) · {fit_emoji}{p['fitness']}%")

    if len(bench) > 10:
        lines.append(f"_...and {len(bench) - 10} more players in reserves._")

    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━")

    # Add quick inline buttons to inspect top players
    player_buttons = []
    top_players = sorted(squad, key=lambda x: x['overall_rating'], reverse=True)[:4]
    row = []
    for p in top_players:
        row.append(InlineKeyboardButton(f"🔍 {p['name'].split('.')[-1]} ({p['overall_rating']})", callback_data=f"view_player_{p['id']}"))
        if len(row) == 2:
            player_buttons.append(row)
            row = []
    if row:
        player_buttons.append(row)

    base_markup = get_squad_actions_inline()
    combined_keyboard = player_buttons + base_markup.inline_keyboard

    await update.effective_message.reply_text(
        "\n".join(lines),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(combined_keyboard)
    )

async def show_pitch_view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    club = db.get_club_by_manager_id(user_id)
    if not club:
        return

    squad = db.get_squad(club['id'])
    starters = [p for p in squad if p['is_starter']]
    pitch_text = render_pitch_ascii(club['formation'], starters)

    text = (
        f"📋 **STARTING LINEUP VISUALIZER**\n"
        f"Club: **{club['name']}** | Formation: **{club['formation']}**\n\n"
        f"```text\n{pitch_text}\n```\n"
        f"Tap *Auto-Pick Best XI* to optimize position placement based on player ratings."
    )

    keyboard = [
        [InlineKeyboardButton("⚡ Auto-Pick Best XI", callback_data="act_autopick")],
        [InlineKeyboardButton("🔙 Back to Squad", callback_data="nav_squad")]
    ]

    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_player_card(update: Update, context: ContextTypes.DEFAULT_TYPE, player_id: int):
    query = update.callback_query
    await query.answer()
    player = db.get_player(player_id)
    if not player:
        await query.edit_message_text("⚠️ Player not found.")
        return

    role_star = "🌟 STARTER" if player['is_starter'] else "🪑 BENCH"
    pos = player['lineup_position'] or player['position']

    card = (
        f"👤 **PLAYER PROFILE: {player['name'].upper()}**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Position: **{pos}** | Status: **{role_star}**\n"
        f"Rating: **{player['overall_rating']} OVR** | Age: {player['age']} | Nation: {player['nationality']}\n\n"
        f"📊 **DETAILED ATTRIBUTES**\n"
        f"• Pace: `{player['pace']:>2}`       • Shooting: `{player['shooting']:>2}`\n"
        f"• Passing: `{player['passing']:>2}`    • Dribbling: `{player['dribbling']:>2}`\n"
        f"• Defending: `{player['defending']:>2}`  • Physical: `{player['physical']:>2}`\n"
        f"• GK Reflexes: `{player['gk_reflexes']:>2}`\n\n"
        f"💚 Condition: {player['fitness']}% | 🔥 Morale: {player['morale']}%\n"
        f"💵 Market Value: €{player['value']:,}\n"
        f"💳 Weekly Wage: €{player['wage']:,}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━"
    )

    keyboard = [
        [InlineKeyboardButton("🏷️ List on Transfer Market", callback_data=f"market_list_prompt_{player['id']}")],
        [InlineKeyboardButton("🔙 Back to Squad", callback_data="nav_squad")]
    ]

    await query.edit_message_text(
        card,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
