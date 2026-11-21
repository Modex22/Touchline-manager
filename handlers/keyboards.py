from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from engine.tactics import FORMATIONS, MENTALITIES, PLAY_STYLES

def get_main_menu_keyboard():
    """Persistent bottom reply keyboard for easy navigation at all times."""
    keyboard = [
        ["🏟️ My Club", "👥 Squad", "📋 Tactics"],
        ["⚽ Matchday", "🔄 Transfers", "📊 Standings"],
        ["🏋️ Training", "💰 Finances", "🖼️ Upload Logo"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_club_actions_inline():
    keyboard = [
        [
            InlineKeyboardButton("👥 View Squad", callback_data="nav_squad"),
            InlineKeyboardButton("📋 Tactics", callback_data="nav_tactics")
        ],
        [
            InlineKeyboardButton("⚽ Play Match", callback_data="nav_matchday"),
            InlineKeyboardButton("🔄 Transfer Market", callback_data="nav_transfers")
        ],
        [
            InlineKeyboardButton("🏟️ Upgrade Stadium", callback_data="act_upgrade_stadium"),
            InlineKeyboardButton("🖼️ Change Badge", callback_data="act_prompt_logo")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_squad_actions_inline():
    keyboard = [
        [
            InlineKeyboardButton("⚡ Auto-Pick Best XI", callback_data="act_autopick"),
            InlineKeyboardButton("📋 View Lineup Pitch", callback_data="act_view_pitch")
        ],
        [
            InlineKeyboardButton("🔙 Club Overview", callback_data="nav_club")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_tactics_keyboard(current_formation: str, current_mentality: str, current_style: str):
    keyboard = []
    
    # Formations row
    form_buttons = []
    for f in FORMATIONS:
        label = f"✅ {f}" if f == current_formation else f
        form_buttons.append(InlineKeyboardButton(label, callback_data=f"set_formation_{f}"))
    keyboard.append(form_buttons[:3])
    keyboard.append(form_buttons[3:])

    # Mentality row
    ment_buttons = []
    for m in MENTALITIES:
        label = f"🎯 {m}" if m == current_mentality else m
        ment_buttons.append(InlineKeyboardButton(label, callback_data=f"set_mentality_{m}"))
    keyboard.append(ment_buttons)

    # Style row
    style_buttons = []
    for s in PLAY_STYLES:
        label = f"🔥 {s}" if s == current_style else s
        style_buttons.append(InlineKeyboardButton(label, callback_data=f"set_style_{s}"))
    keyboard.append(style_buttons[:2])
    keyboard.append(style_buttons[2:])

    keyboard.append([InlineKeyboardButton("🔙 Back to Squad", callback_data="nav_squad")])
    return InlineKeyboardMarkup(keyboard)

def get_matchday_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("🏆 Play League Match", callback_data="match_league"),
            InlineKeyboardButton("⚔️ Quick Friendly", callback_data="match_friendly")
        ],
        [
            InlineKeyboardButton("📊 View Standings", callback_data="nav_standings"),
            InlineKeyboardButton("🔙 Club Overview", callback_data="nav_club")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_training_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("🏃 Fitness Recovery", callback_data="train_Fitness"),
            InlineKeyboardButton("🎯 Finishing Drills", callback_data="train_Finishing")
        ],
        [
            InlineKeyboardButton("🛡️ Defending Drills", callback_data="train_Defending"),
            InlineKeyboardButton("👟 Passing & Vision", callback_data="train_Passing")
        ],
        [
            InlineKeyboardButton("🔙 Back", callback_data="nav_club")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)
