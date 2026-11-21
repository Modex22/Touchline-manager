import random

GOAL_TEMPLATES = [
    "⚽ **GOAL!** {scorer} bursts through the backline and slots it coolly into the bottom corner! Assist: {assister}.",
    "⚽ **WHAT A GOAL!** {scorer} unleashes an absolute rocket from 25 yards that rattles the crossbar and bounces in!",
    "⚽ **GOAL!** Pinpoint delivery from {assister}, and {scorer} rises highest to head it emphatically into the net!",
    "⚽ **GOAL!** A lightning-quick counterattack! {assister} threads a dream pass to {scorer}, who tucks it home with finesse!",
    "⚽ **GOAL!** Scramble inside the penalty box! The ball falls kindly to {scorer}, who pokes it past the outstretched keeper!",
    "⚽ **GOAL!** {scorer} steps up, sends the goalkeeper the wrong way, and buries the penalty with ice in their veins!"
]

SAVE_TEMPLATES = [
    "🧤 **WHAT A SAVE!** {keeper} dives full stretch to tip {shooter}'s curling effort around the post!",
    "🧤 **DENIED!** {shooter} was through on goal, but {keeper} stood tall and made a heroic point-blank block!",
    "🧤 **BIG CHANCE SAVED!** A venomous strike from {shooter}, parried away to safety by {keeper}!"
]

MISS_TEMPLATES = [
    "❌ **WOODWORK!** {shooter} strikes it with venom, but it clatters against the post! Inches away!",
    "❌ **OFF TARGET!** Great movement from {shooter}, but the final effort sails agonizingly wide of the upright."
]

CARD_TEMPLATES = [
    "🟨 **Yellow Card:** {player} mistimes a sliding challenge and enters the referee's notebook.",
    "🟨 **Yellow Card:** Tactical foul by {player} to stop a dangerous counterattack."
]

RED_CARD_TEMPLATES = [
    "🟥 **RED CARD!** A reckless lunge from {player}! The referee shows no hesitation and pulls out the straight red card! Down to 10 men!"
]

def format_goal(minute: int, team_name: str, scorer: str, assister: str = None) -> str:
    template = random.choice(GOAL_TEMPLATES)
    assister_text = assister if assister else "unassisted"
    comment = template.format(scorer=scorer, assister=assister_text)
    return f"⏱️ **{minute}'** [{team_name}] {comment}"

def format_save(minute: int, keeper_team: str, keeper: str, shooter: str) -> str:
    template = random.choice(SAVE_TEMPLATES)
    return f"⏱️ **{minute}'** [{keeper_team}] {template.format(keeper=keeper, shooter=shooter)}"

def format_miss(minute: int, team_name: str, shooter: str) -> str:
    template = random.choice(MISS_TEMPLATES)
    return f"⏱️ **{minute}'** [{team_name}] {template.format(shooter=shooter)}"

def format_card(minute: int, team_name: str, player: str, is_red: bool = False) -> str:
    if is_red:
        template = random.choice(RED_CARD_TEMPLATES)
    else:
        template = random.choice(CARD_TEMPLATES)
    return f"⏱️ **{minute}'** [{team_name}] {template.format(player=player)}"
