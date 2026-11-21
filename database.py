import sqlite3
import json
import os
import random
from config import DATABASE_PATH, STARTING_BUDGET, DEFAULT_STADIUM_CAPACITY

def get_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Leagues
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS leagues (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            tier INTEGER NOT NULL
        )
        """)

        # Managers (Telegram users)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS managers (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Clubs
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS clubs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            manager_id INTEGER UNIQUE,
            name TEXT NOT NULL,
            badge_file_id TEXT,
            badge_path TEXT,
            division_id INTEGER NOT NULL DEFAULT 4,
            balance INTEGER NOT NULL DEFAULT 25000000,
            stadium_name TEXT NOT NULL DEFAULT 'Touchline Arena',
            stadium_capacity INTEGER NOT NULL DEFAULT 25000,
            formation TEXT NOT NULL DEFAULT '4-3-3',
            mentality TEXT NOT NULL DEFAULT 'Balanced',
            play_style TEXT NOT NULL DEFAULT 'Possession',
            reputation INTEGER NOT NULL DEFAULT 3,
            points INTEGER NOT NULL DEFAULT 0,
            played INTEGER NOT NULL DEFAULT 0,
            won INTEGER NOT NULL DEFAULT 0,
            drawn INTEGER NOT NULL DEFAULT 0,
            lost INTEGER NOT NULL DEFAULT 0,
            goals_for INTEGER NOT NULL DEFAULT 0,
            goals_against INTEGER NOT NULL DEFAULT 0,
            is_ai INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (manager_id) REFERENCES managers(user_id),
            FOREIGN KEY (division_id) REFERENCES leagues(id)
        )
        """)

        # Players
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            club_id INTEGER,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            nationality TEXT NOT NULL,
            position TEXT NOT NULL,
            overall_rating INTEGER NOT NULL,
            pace INTEGER NOT NULL,
            shooting INTEGER NOT NULL,
            passing INTEGER NOT NULL,
            dribbling INTEGER NOT NULL,
            defending INTEGER NOT NULL,
            physical INTEGER NOT NULL,
            gk_reflexes INTEGER NOT NULL DEFAULT 50,
            fitness INTEGER NOT NULL DEFAULT 100,
            morale INTEGER NOT NULL DEFAULT 85,
            value INTEGER NOT NULL DEFAULT 1000000,
            wage INTEGER NOT NULL DEFAULT 15000,
            is_starter INTEGER NOT NULL DEFAULT 0,
            lineup_position TEXT,
            FOREIGN KEY (club_id) REFERENCES clubs(id)
        )
        """)

        # Transfer Market Listings
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS transfers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER NOT NULL UNIQUE,
            seller_club_id INTEGER,
            asking_price INTEGER NOT NULL,
            listed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (player_id) REFERENCES players(id),
            FOREIGN KEY (seller_club_id) REFERENCES clubs(id)
        )
        """)

        # Matches history
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            home_club_id INTEGER NOT NULL,
            away_club_id INTEGER NOT NULL,
            home_score INTEGER NOT NULL,
            away_score INTEGER NOT NULL,
            match_type TEXT NOT NULL,
            events_json TEXT,
            stats_json TEXT,
            played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (home_club_id) REFERENCES clubs(id),
            FOREIGN KEY (away_club_id) REFERENCES clubs(id)
        )
        """)

        conn.commit()

    seed_default_data()

def seed_default_data():
    from engine.player_generator import generate_squad_for_club

    with get_db() as conn:
        cursor = conn.cursor()
        
        # Check if leagues exist
        cursor.execute("SELECT COUNT(*) FROM leagues")
        if cursor.fetchone()[0] == 0:
            leagues = [
                (1, "Premier Division", 1),
                (2, "Championship", 2),
                (3, "National League", 3),
                (4, "Development League", 4),
            ]
            cursor.executemany("INSERT INTO leagues (id, name, tier) VALUES (?, ?, ?)", leagues)

        # Check if AI clubs exist
        cursor.execute("SELECT COUNT(*) FROM clubs WHERE is_ai = 1")
        if cursor.fetchone()[0] == 0:
            default_clubs = [
                # Premier Division
                ("Arsenal FC", 1, 85, 60000, 4),
                ("Manchester City", 1, 87, 55000, 5),
                ("Liverpool FC", 1, 86, 54000, 5),
                ("Real Madrid", 1, 88, 81000, 5),
                ("FC Barcelona", 1, 86, 85000, 5),
                ("Bayern Munich", 1, 87, 75000, 5),
                ("Paris SG", 1, 85, 48000, 4),
                ("Inter Milan", 1, 84, 75000, 4),
                
                # Championship
                ("Chelsea FC", 2, 82, 40000, 4),
                ("Manchester United", 2, 82, 74000, 4),
                ("Juventus", 2, 81, 41000, 4),
                ("Atletico Madrid", 2, 83, 68000, 4),
                ("Borussia Dortmund", 2, 82, 81000, 4),
                ("AC Milan", 2, 81, 75000, 4),
                ("Tottenham Hotspur", 2, 81, 62000, 4),
                ("Newcastle United", 2, 80, 52000, 3),

                # National League
                ("Aston Villa", 3, 79, 42000, 3),
                ("Napoli", 3, 80, 54000, 3),
                ("AS Roma", 3, 78, 70000, 3),
                ("Sporting CP", 3, 78, 50000, 3),
                ("SL Benfica", 3, 78, 64000, 3),
                ("AFC Ajax", 3, 77, 55000, 3),

                # Development League (Starter league for new managers + rival AI clubs)
                ("Phoenix Athletic", 4, 73, 20000, 2),
                ("Royal SC", 4, 74, 22000, 2),
                ("Blackstar FC", 4, 72, 18000, 2),
                ("Lagos City FC", 4, 73, 21000, 2),
                ("Apex Wanderers", 4, 71, 15000, 2),
                ("Red Star United", 4, 72, 19000, 2)
            ]

            for name, div_id, target_ovr, capacity, rep in default_clubs:
                cursor.execute("""
                INSERT INTO clubs (name, division_id, stadium_name, stadium_capacity, reputation, is_ai, balance)
                VALUES (?, ?, ?, ?, ?, 1, 35000000)
                """, (name, div_id, f"{name} Stadium", capacity, rep))
                club_id = cursor.lastrowid
                
                # Generate AI squad
                squad = generate_squad_for_club(club_id, base_rating=target_ovr)
                for p in squad:
                    cursor.execute("""
                    INSERT INTO players (
                        club_id, name, age, nationality, position, overall_rating,
                        pace, shooting, passing, dribbling, defending, physical, gk_reflexes,
                        fitness, morale, value, wage, is_starter, lineup_position
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        club_id, p['name'], p['age'], p['nationality'], p['position'], p['overall_rating'],
                        p['pace'], p['shooting'], p['passing'], p['dribbling'], p['defending'], p['physical'], p['gk_reflexes'],
                        p['fitness'], p['morale'], p['value'], p['wage'], p['is_starter'], p['lineup_position']
                    ))

        conn.commit()

# --- Helper functions for Application ---

def get_club_by_manager_id(user_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT c.*, l.name as league_name, l.tier
        FROM clubs c
        JOIN leagues l ON c.division_id = l.id
        WHERE c.manager_id = ?
        """, (user_id,))
        return cursor.fetchone()

def get_club_by_id(club_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT c.*, l.name as league_name, l.tier
        FROM clubs c
        JOIN leagues l ON c.division_id = l.id
        WHERE c.id = ?
        """, (club_id,))
        return cursor.fetchone()

def register_manager(user_id: int, username: str, first_name: str):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT OR IGNORE INTO managers (user_id, username, first_name)
        VALUES (?, ?, ?)
        """, (user_id, username, first_name))
        conn.commit()

def create_user_club(user_id: int, club_name: str, template_club_id: int = None):
    from engine.player_generator import generate_starter_squad
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # If user picked a real club template, copy attributes or place in respective division
        div_id = 4  # Default starts in Development League
        stadium_cap = DEFAULT_STADIUM_CAPACITY
        
        cursor.execute("""
        INSERT INTO clubs (manager_id, name, division_id, balance, stadium_name, stadium_capacity, is_ai)
        VALUES (?, ?, ?, ?, ?, ?, 0)
        """, (user_id, club_name, div_id, STARTING_BUDGET, f"{club_name} Ground", stadium_cap))
        club_id = cursor.lastrowid

        # Generate custom starter squad (rating ~72-76)
        squad = generate_starter_squad(club_id)
        for p in squad:
            cursor.execute("""
            INSERT INTO players (
                club_id, name, age, nationality, position, overall_rating,
                pace, shooting, passing, dribbling, defending, physical, gk_reflexes,
                fitness, morale, value, wage, is_starter, lineup_position
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                club_id, p['name'], p['age'], p['nationality'], p['position'], p['overall_rating'],
                p['pace'], p['shooting'], p['passing'], p['dribbling'], p['defending'], p['physical'], p['gk_reflexes'],
                p['fitness'], p['morale'], p['value'], p['wage'], p['is_starter'], p['lineup_position']
            ))
        
        conn.commit()
        return club_id

def update_club_badge(club_id: int, badge_file_id: str, badge_path: str = None):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE clubs SET badge_file_id = ?, badge_path = ? WHERE id = ?
        """, (badge_file_id, badge_path, club_id))
        conn.commit()

def get_squad(club_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT * FROM players 
        WHERE club_id = ?
        ORDER BY is_starter DESC, 
            CASE position 
                WHEN 'GK' THEN 1
                WHEN 'CB' THEN 2
                WHEN 'LB' THEN 3
                WHEN 'RB' THEN 4
                WHEN 'CDM' THEN 5
                WHEN 'CM' THEN 6
                WHEN 'CAM' THEN 7
                WHEN 'LW' THEN 8
                WHEN 'RW' THEN 9
                WHEN 'ST' THEN 10
                ELSE 11
            END,
            overall_rating DESC
        """, (club_id,))
        return cursor.fetchall()

def get_player(player_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM players WHERE id = ?", (player_id,))
        return cursor.fetchone()

def update_club_tactics(club_id: int, formation: str = None, mentality: str = None, play_style: str = None):
    with get_db() as conn:
        cursor = conn.cursor()
        updates = []
        params = []
        if formation:
            updates.append("formation = ?")
            params.append(formation)
        if mentality:
            updates.append("mentality = ?")
            params.append(mentality)
        if play_style:
            updates.append("play_style = ?")
            params.append(play_style)
        
        if updates:
            params.append(club_id)
            query = f"UPDATE clubs SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            conn.commit()

def auto_pick_lineup(club_id: int, formation: str = '4-3-3'):
    from engine.tactics import FORMATION_SLOTS
    slots = FORMATION_SLOTS.get(formation, FORMATION_SLOTS['4-3-3'])

    with get_db() as conn:
        cursor = conn.cursor()
        # Reset all players to bench first
        cursor.execute("UPDATE players SET is_starter = 0, lineup_position = NULL WHERE club_id = ?", (club_id,))
        
        # Get all squad players
        cursor.execute("SELECT id, position, overall_rating FROM players WHERE club_id = ?", (club_id,))
        players = cursor.fetchall()
        
        assigned_player_ids = set()
        
        # Fill slots with exact position matches first, then best rating
        for slot in slots:
            candidates = [p for p in players if p['id'] not in assigned_player_ids and p['position'] == slot]
            if not candidates:
                # Fallback to general category (D, M, F)
                if slot in ['CB', 'LB', 'RB']:
                    candidates = [p for p in players if p['id'] not in assigned_player_ids and p['position'] in ['CB', 'LB', 'RB']]
                elif slot in ['CM', 'CDM', 'CAM']:
                    candidates = [p for p in players if p['id'] not in assigned_player_ids and p['position'] in ['CM', 'CDM', 'CAM', 'LW', 'RW']]
                elif slot in ['ST', 'LW', 'RW']:
                    candidates = [p for p in players if p['id'] not in assigned_player_ids and p['position'] in ['ST', 'LW', 'RW', 'CAM']]
            
            if not candidates:
                # Any player remaining
                candidates = [p for p in players if p['id'] not in assigned_player_ids]

            if candidates:
                best = max(candidates, key=lambda x: x['overall_rating'])
                assigned_player_ids.add(best['id'])
                cursor.execute("""
                UPDATE players SET is_starter = 1, lineup_position = ? WHERE id = ?
                """, (slot, best['id']))

        conn.commit()

def get_league_standings(division_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT *, (goals_for - goals_against) as goal_diff
        FROM clubs
        WHERE division_id = ?
        ORDER BY points DESC, goal_diff DESC, goals_for DESC
        """, (division_id,))
        return cursor.fetchall()

def get_market_players(limit: int = 15):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT t.id as transfer_id, t.asking_price, p.*, c.name as club_name
        FROM transfers t
        JOIN players p ON t.player_id = p.id
        LEFT JOIN clubs c ON t.seller_club_id = c.id
        ORDER BY p.overall_rating DESC
        LIMIT ?
        """, (limit,))
        return cursor.fetchall()

def list_player_for_sale(player_id: int, club_id: int, asking_price: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT OR REPLACE INTO transfers (player_id, seller_club_id, asking_price)
        VALUES (?, ?, ?)
        """, (player_id, club_id, asking_price))
        # Bench player if listed
        cursor.execute("UPDATE players SET is_starter = 0 WHERE id = ?", (player_id,))
        conn.commit()

def buy_player(buyer_club_id: int, transfer_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT t.*, p.name as player_name, p.value
        FROM transfers t
        JOIN players p ON t.player_id = p.id
        WHERE t.id = ?
        """, (transfer_id,))
        transfer = cursor.fetchone()
        
        if not transfer:
            return False, "Player is no longer on the transfer market."
            
        cursor.execute("SELECT balance FROM clubs WHERE id = ?", (buyer_club_id,))
        buyer = cursor.fetchone()
        
        if buyer['balance'] < transfer['asking_price']:
            return False, f"Insufficient funds! You need €{transfer['asking_price']:,}."
            
        # Deduct from buyer
        cursor.execute("UPDATE clubs SET balance = balance - ? WHERE id = ?", (transfer['asking_price'], buyer_club_id))
        
        # Credit seller if user or existing club
        if transfer['seller_club_id']:
            cursor.execute("UPDATE clubs SET balance = balance + ? WHERE id = ?", (transfer['asking_price'], transfer['seller_club_id']))
            
        # Transfer player ownership
        cursor.execute("UPDATE players SET club_id = ?, is_starter = 0, lineup_position = NULL WHERE id = ?", 
                       (buyer_club_id, transfer['player_id']))
        
        # Remove listing
        cursor.execute("DELETE FROM transfers WHERE id = ?", (transfer_id,))
        conn.commit()
        return True, f"Successfully signed {transfer['player_name']} for €{transfer['asking_price']:,}!"

def apply_match_result(home_id: int, away_id: int, home_score: int, away_score: int, match_type: str, events: list, stats: dict):
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Save match
        cursor.execute("""
        INSERT INTO matches (home_club_id, away_club_id, home_score, away_score, match_type, events_json, stats_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (home_id, away_id, home_score, away_score, match_type, json.dumps(events), json.dumps(stats)))
        
        # If league match, update standings
        if match_type == 'league':
            # Home update
            h_won = 1 if home_score > away_score else 0
            h_drawn = 1 if home_score == away_score else 0
            h_lost = 1 if home_score < away_score else 0
            h_pts = 3 if h_won else (1 if h_drawn else 0)

            cursor.execute("""
            UPDATE clubs SET 
                played = played + 1,
                won = won + ?,
                drawn = drawn + ?,
                lost = lost + ?,
                goals_for = goals_for + ?,
                goals_against = goals_against + ?,
                points = points + ?
            WHERE id = ?
            """, (h_won, h_drawn, h_lost, home_score, away_score, h_pts, home_id))

            # Away update
            a_won = 1 if away_score > home_score else 0
            a_drawn = 1 if home_score == away_score else 0
            a_lost = 1 if away_score < home_score else 0
            a_pts = 3 if a_won else (1 if a_drawn else 0)

            cursor.execute("""
            UPDATE clubs SET 
                played = played + 1,
                won = won + ?,
                drawn = drawn + ?,
                lost = lost + ?,
                goals_for = goals_for + ?,
                goals_against = goals_against + ?,
                points = points + ?
            WHERE id = ?
            """, (a_won, a_drawn, a_lost, away_score, home_score, a_pts, away_id))

        # Credit gate receipts to home club
        cursor.execute("SELECT stadium_capacity FROM clubs WHERE id = ?", (home_id,))
        stadium = cursor.fetchone()
        capacity = stadium['stadium_capacity'] if stadium else DEFAULT_STADIUM_CAPACITY
        attendance = int(capacity * random.uniform(0.75, 0.98))
        revenue = attendance * 35  # €35 average ticket price
        cursor.execute("UPDATE clubs SET balance = balance + ? WHERE id = ?", (revenue, home_id))

        conn.commit()
        return revenue, attendance

def train_squad(club_id: int, focus: str):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, overall_rating, pace, shooting, passing, dribbling, defending, physical, fitness, morale FROM players WHERE club_id = ?", (club_id,))
        players = cursor.fetchall()
        
        for p in players:
            new_fitness = min(100, p['fitness'] + 10) if focus == 'Fitness' else max(50, p['fitness'] - 3)
            new_morale = min(100, p['morale'] + random.randint(2, 5))
            
            p_upgrades = {}
            if focus == 'Finishing':
                p_upgrades['shooting'] = min(99, p['shooting'] + (1 if random.random() < 0.35 else 0))
            elif focus == 'Defending':
                p_upgrades['defending'] = min(99, p['defending'] + (1 if random.random() < 0.35 else 0))
            elif focus == 'Passing':
                p_upgrades['passing'] = min(99, p['passing'] + (1 if random.random() < 0.35 else 0))
            elif focus == 'Fitness':
                p_upgrades['physical'] = min(99, p['physical'] + (1 if random.random() < 0.25 else 0))

            set_clauses = ["fitness = ?", "morale = ?"]
            params = [new_fitness, new_morale]
            for stat, val in p_upgrades.items():
                set_clauses.append(f"{stat} = ?")
                params.append(val)
            
            params.append(p['id'])
            cursor.execute(f"UPDATE players SET {', '.join(set_clauses)} WHERE id = ?", params)

        conn.commit()

def upgrade_stadium(club_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT balance, stadium_capacity FROM clubs WHERE id = ?", (club_id,))
        club = cursor.fetchone()
        
        cost = 5_000_000
        capacity_boost = 5_000
        
        if club['balance'] < cost:
            return False, f"Stadium upgrade costs €{cost:,}. Your balance is €{club['balance']:,}."
            
        new_capacity = club['stadium_capacity'] + capacity_boost
        cursor.execute("""
        UPDATE clubs 
        SET balance = balance - ?, stadium_capacity = ?
        WHERE id = ?
        """, (cost, new_capacity, club_id))
        conn.commit()
        return True, f"Stadium upgraded to {new_capacity:,} seats! (Cost: €{cost:,})"
