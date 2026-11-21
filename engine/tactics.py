FORMATION_SLOTS = {
    "4-3-3": ["GK", "LB", "CB", "CB", "RB", "CDM", "CM", "CM", "LW", "ST", "RW"],
    "4-4-2": ["GK", "LB", "CB", "CB", "RB", "LW", "CM", "CM", "RW", "ST", "ST"],
    "3-5-2": ["GK", "CB", "CB", "CB", "LB", "CDM", "CM", "CAM", "RB", "ST", "ST"],
    "4-2-3-1": ["GK", "LB", "CB", "CB", "RB", "CDM", "CDM", "CAM", "LW", "RW", "ST"],
    "5-3-2": ["GK", "LB", "CB", "CB", "CB", "RB", "CM", "CDM", "CM", "ST", "ST"]
}

FORMATIONS = list(FORMATION_SLOTS.keys())

MENTALITIES = ["Attacking", "Balanced", "Defensive"]

PLAY_STYLES = ["Possession", "High Press", "Counter-Attack", "Low Block"]

# Tactical Rock-Paper-Scissors modifiers
# style1 vs style2 -> multiplier on possession & chance creation
TACTICAL_ADVANTAGES = {
    ("High Press", "Possession"): 1.15,      # Press disrupts slow build-up
    ("Possession", "Low Block"): 1.15,       # Patient passing unpicks parked bus
    ("Low Block", "Counter-Attack"): 1.15,   # Denies space for fast breaks
    ("Counter-Attack", "High Press"): 1.20,  # Fast wingers exploit high defensive line
}

def get_tactical_modifier(style1: str, style2: str) -> float:
    if (style1, style2) in TACTICAL_ADVANTAGES:
        return TACTICAL_ADVANTAGES[(style1, style2)]
    elif (style2, style1) in TACTICAL_ADVANTAGES:
        return 1.0 / TACTICAL_ADVANTAGES[(style2, style1)]
    return 1.0

def render_pitch_ascii(formation: str, starting_players: list) -> str:
    """Renders a visual text pitch representing the starting XI."""
    by_pos = {}
    for p in starting_players:
        lineup_pos = p['lineup_position'] or p['position']
        by_pos.setdefault(lineup_pos, []).append(f"{p['name']} ({p['overall_rating']})")

    slots = FORMATION_SLOTS.get(formation, FORMATION_SLOTS["4-3-3"])
    
    lines = [
        "┌────────────────────────────────┐",
        "│           OPPONENT HALF        │",
        "│                                │"
    ]

    # Forwards
    fwds = [p for p in starting_players if (p['lineup_position'] or p['position']) in ['ST', 'LW', 'RW']]
    fwd_str = "   ".join([f"{p['name'].split('.')[-1][:7]} ({p['overall_rating']})" for p in fwds])
    lines.append(f"│  {fwd_str.center(28)}  │")
    lines.append("│                                │")

    # Midfielders
    mids = [p for p in starting_players if (p['lineup_position'] or p['position']) in ['CAM', 'CM', 'CDM']]
    mid_str = "  ".join([f"{p['name'].split('.')[-1][:7]} ({p['overall_rating']})" for p in mids])
    lines.append(f"│  {mid_str.center(28)}  │")
    lines.append("│  ──────────── O ────────────   │")

    # Defenders
    defs = [p for p in starting_players if (p['lineup_position'] or p['position']) in ['CB', 'LB', 'RB']]
    def_str = " ".join([f"{p['name'].split('.')[-1][:6]} ({p['overall_rating']})" for p in defs])
    lines.append(f"│  {def_str.center(28)}  │")
    lines.append("│                                │")

    # Goalkeeper
    gks = [p for p in starting_players if (p['lineup_position'] or p['position']) == 'GK']
    gk_str = f"🧤 {gks[0]['name']} ({gks[0]['overall_rating']})" if gks else "🧤 [No GK]"
    lines.append(f"│  {gk_str.center(28)}  │")
    lines.append("│           [ GOAL ]             │")
    lines.append("└────────────────────────────────┘")

    return "\n".join(lines)
