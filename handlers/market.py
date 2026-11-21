from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
import database as db
from engine.player_generator import generate_player
import random

def ensure_market_listings():
    """Ensure there are always interesting prospects on the transfer market."""
    with db.get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM transfers")
        count = cursor.fetchone()[0]
        
        if count < 6:
            # Generate 4-6 free agents / scouted prospects
            for _ in range(6 - count):
                p = generate_player(target_rating=random.randint(71, 84))
                cursor.execute("""
                INSERT INTO players (
                    club_id, name, age, nationality, position, overall_rating,
                    pace, shooting, passing, dribbling, defending, physical, gk_reflexes,
                    fitness, morale, value, wage, is_starter
                ) VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                """, (
                    p['name'], p['age'], p['nationality'], p['position'], p['overall_rating'],
                    p['pace'], p['shooting'], p['passing'], p['dribbling'], p['defending'], p['physical'], p['gk_reflexes'],
                    p['fitness'], p['morale'], p['value'], p['wage']
                ))
                p_id = cursor.lastrowid
                asking = int(p['value'] * random.uniform(0.9, 1.25))
                cursor.execute("INSERT INTO transfers (player_id, seller_club_id, asking_price) VALUES (?, NULL, ?)", (p_id, asking))
            conn.commit()

async def show_market(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    club = db.get_club_by_manager_id(user_id)
    if not club:
        await update.effective_message.reply_text("⚠️ Create a club first with /start!")
        return

    ensure_market_listings()
    listings = db.get_market_players(limit=8)

    lines = [
        "🔄 **GLOBAL TRANSFER MARKET**",
        f"Your Transfer Budget: **€{club['balance']:,}**",
        "━━━━━━━━━━━━━━━━━━━━━━━━",
        "Available footballers for signing:"
    ]

    buttons = []
    for t in listings:
        seller = t['club_name'] or "Free Agent"
        lines.append(
            f"• `{t['position']:<3}` **{t['name']}** ({t['overall_rating']} OVR, {t['age']}y) "
            f"— Fee: **€{t['asking_price']:,}** [{seller}]"
        )
        buttons.append([
            InlineKeyboardButton(
                f"✍️ Sign {t['name'].split('.')[-1]} (€{t['asking_price']//1_000_000}M)", 
                callback_data=f"buy_transfer_{t['transfer_id']}"
            )
        ])

    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("💡 To sell your own players: go to **👥 Squad**, tap a player, and select *List on Transfer Market*.")

    buttons.append([InlineKeyboardButton("🔙 Club Overview", callback_data="nav_club")])

    await update.effective_message.reply_text(
        "\n".join(lines),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def handle_buy_player(update: Update, context: ContextTypes.DEFAULT_TYPE, transfer_id: int):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    club = db.get_club_by_manager_id(user_id)
    if not club:
        return

    # Check squad size
    squad = db.get_squad(club['id'])
    if len(squad) >= 25:
        await query.edit_message_text(
            "⚠️ **Squad is Full!** Maximum squad capacity is 25 players. Sell a player before buying new ones.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Market", callback_data="nav_transfers")]])
        )
        return

    success, msg = db.buy_player(club['id'], transfer_id)
    keyboard = [
        [InlineKeyboardButton("🔄 Transfer Market", callback_data="nav_transfers")],
        [InlineKeyboardButton("👥 View Squad", callback_data="nav_squad")]
    ]
    
    prefix = "🎉" if success else "❌"
    await query.edit_message_text(
        f"{prefix} **TRANSFER REPORT**\n\n{msg}",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
