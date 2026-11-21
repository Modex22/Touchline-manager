import random

FIRST_NAMES = [
    "David", "Alex", "Marcus", "Lucas", "Mateo", "Liam", "Kylian", "Erling", "Bukayo",
    "Jude", "Victor", "Kevin", "Bruno", "Gabriel", "Declan", "Harry", "Martin", "Cole",
    "Rodri", "Vinicius", "Florian", "Lamine", "Rafael", "Ollie", "Julian", "Theo", "Achraf",
    "William", "Virgil", "Ruben", "Trent", "Federico", "Antoine", "Sonny", "Gavi", "Pedri",
    "Jamal", "Nico", "Khvicha", "Joshua", "Takefusa", "Tariq", "Ademola", "Samuel", "Kofi",
    "Emmanuel", "Chukwudi", "Kelechi", "Jay-Jay", "Sunday", "Taiwo", "Blessing", "Ahmed"
]

LAST_NAMES = [
    "Adeyemi", "Silva", "Johnson", "Smith", "Osimhen", "Bellingham", "Saka", "Palmer",
    "Haaland", "Foden", "Rice", "Saliba", "Van Dijk", "Dias", "Alexander", "Kane",
    "Odegaard", "Fernandes", "De Bruyne", "Rodrygo", "Camavinga", "Musiala", "Wirtz",
    "Yamal", "Leao", "Watkins", "Alvarez", "Hernandez", "Hakimi", "Valverde", "Chiesa",
    "Griezmann", "Son", "Davies", "Bastoni", "Maignan", "Alisson", "Ederson", "Raya",
    "Okafor", "Chukwueze", "Iwobi", "Lookman", "Boniface", "Ndidi", "Mendy", "Koulibaly"
]

NATIONALITIES = [
    "England", "Nigeria", "Spain", "France", "Brazil", "Germany", "Argentina", "Portugal",
    "Italy", "Netherlands", "Norway", "Belgium", "Ghana", "Senegal", "Cameroon", "Morocco",
    "Japan", "South Korea", "Croatia", "Uruguay", "Colombia", "Sweden"
]

POSITIONS = ["GK", "CB", "LB", "RB", "CDM", "CM", "CAM", "LW", "RW", "ST"]

def generate_player(position: str = None, target_rating: int = None, club_id: int = None, is_starter: int = 0, lineup_position: str = None):
    if not position:
        position = random.choice(POSITIONS)
        
    if not target_rating:
        target_rating = random.randint(68, 84)

    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    name = f"{first[0]}. {last}"
    age = random.randint(18, 33)
    nationality = random.choice(NATIONALITIES)

    # Base attributes variation around target_rating
    def stat(weight=0):
        val = target_rating + random.randint(-4, 5) + weight
        return max(35, min(99, val))

    # Position-specific stat biases
    if position == "GK":
        pace = stat(-25)
        shooting = stat(-40)
        passing = stat(-10)
        dribbling = stat(-30)
        defending = stat(-15)
        physical = stat(+2)
        gk_reflexes = stat(+5)
    elif position in ["CB", "LB", "RB"]:
        pace = stat(+2 if position != "CB" else -3)
        shooting = stat(-20)
        passing = stat(-5)
        dribbling = stat(-8)
        defending = stat(+6)
        physical = stat(+5)
        gk_reflexes = random.randint(20, 35)
    elif position in ["CDM", "CM"]:
        pace = stat(-2)
        shooting = stat(0)
        passing = stat(+6)
        dribbling = stat(+3)
        defending = stat(+4 if position == "CDM" else -2)
        physical = stat(+3)
        gk_reflexes = random.randint(20, 35)
    elif position in ["CAM", "LW", "RW"]:
        pace = stat(+6)
        shooting = stat(+3)
        passing = stat(+4)
        dribbling = stat(+7)
        defending = stat(-20)
        physical = stat(-4)
        gk_reflexes = random.randint(20, 35)
    else:  # ST
        pace = stat(+4)
        shooting = stat(+8)
        passing = stat(-4)
        dribbling = stat(+2)
        defending = stat(-25)
        physical = stat(+4)
        gk_reflexes = random.randint(20, 35)

    # Calculate overall rating
    if position == "GK":
        overall = int(gk_reflexes * 0.5 + physical * 0.25 + passing * 0.25)
    elif position in ["CB", "LB", "RB"]:
        overall = int(defending * 0.4 + physical * 0.25 + pace * 0.2 + passing * 0.15)
    elif position in ["CDM", "CM"]:
        overall = int(passing * 0.35 + defending * 0.25 + dribbling * 0.2 + physical * 0.2)
    elif position in ["CAM", "LW", "RW"]:
        overall = int(dribbling * 0.35 + pace * 0.3 + passing * 0.2 + shooting * 0.15)
    else:
        overall = int(shooting * 0.4 + pace * 0.25 + physical * 0.2 + dribbling * 0.15)

    overall = max(50, min(95, overall))

    # Valuation & wage based on overall rating and age
    age_multiplier = 1.3 if age <= 23 else (1.0 if age <= 29 else 0.7)
    base_val = int((overall ** 4.2) / 60)
    value = int(base_val * age_multiplier)
    wage = max(2500, int(value * 0.003))

    return {
        "club_id": club_id,
        "name": name,
        "age": age,
        "nationality": nationality,
        "position": position,
        "overall_rating": overall,
        "pace": pace,
        "shooting": shooting,
        "passing": passing,
        "dribbling": dribbling,
        "defending": defending,
        "physical": physical,
        "gk_reflexes": gk_reflexes,
        "fitness": 100,
        "morale": random.randint(80, 95),
        "value": value,
        "wage": wage,
        "is_starter": is_starter,
        "lineup_position": lineup_position
    }

def generate_squad_for_club(club_id: int, base_rating: int = 78):
    """Generates a complete 20-player squad for an AI club."""
    squad = []
    # 2 GKs
    squad.append(generate_player("GK", base_rating, club_id, is_starter=1, lineup_position="GK"))
    squad.append(generate_player("GK", base_rating - 4, club_id, is_starter=0))
    
    # 6 Defenders
    squad.append(generate_player("CB", base_rating, club_id, is_starter=1, lineup_position="CB"))
    squad.append(generate_player("CB", base_rating - 1, club_id, is_starter=1, lineup_position="CB"))
    squad.append(generate_player("LB", base_rating - 1, club_id, is_starter=1, lineup_position="LB"))
    squad.append(generate_player("RB", base_rating, club_id, is_starter=1, lineup_position="RB"))
    squad.append(generate_player("CB", base_rating - 3, club_id, is_starter=0))
    squad.append(generate_player("RB", base_rating - 4, club_id, is_starter=0))

    # 6 Midfielders
    squad.append(generate_player("CDM", base_rating, club_id, is_starter=1, lineup_position="CDM"))
    squad.append(generate_player("CM", base_rating + 1, club_id, is_starter=1, lineup_position="CM"))
    squad.append(generate_player("CM", base_rating - 1, club_id, is_starter=1, lineup_position="CM"))
    squad.append(generate_player("CAM", base_rating, club_id, is_starter=0))
    squad.append(generate_player("CM", base_rating - 3, club_id, is_starter=0))
    squad.append(generate_player("CDM", base_rating - 4, club_id, is_starter=0))

    # 6 Forwards
    squad.append(generate_player("LW", base_rating, club_id, is_starter=1, lineup_position="LW"))
    squad.append(generate_player("RW", base_rating + 1, club_id, is_starter=1, lineup_position="RW"))
    squad.append(generate_player("ST", base_rating + 2, club_id, is_starter=1, lineup_position="ST"))
    squad.append(generate_player("ST", base_rating - 2, club_id, is_starter=0))
    squad.append(generate_player("LW", base_rating - 3, club_id, is_starter=0))
    squad.append(generate_player("RW", base_rating - 4, club_id, is_starter=0))

    return squad

def generate_starter_squad(club_id: int):
    """Generates a balanced starter squad (~73 OVR) for a newly registered manager."""
    return generate_squad_for_club(club_id, base_rating=73)
