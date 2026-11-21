import random
from engine.tactics import get_tactical_modifier
from engine.commentary import format_goal, format_save, format_miss, format_card

class MatchEngine:
    def __init__(self, home_club: dict, away_club: dict, home_squad: list, away_squad: list):
        self.home_club = home_club
        self.away_club = away_club
        
        # Filter starting XI (fallback to top 11 if starters not set)
        self.home_xi = [p for p in home_squad if p['is_starter']] or home_squad[:11]
        self.away_xi = [p for p in away_squad if p['is_starter']] or away_squad[:11]
        
        self.events = []
        self.home_goals = 0
        self.away_goals = 0
        self.home_scorers = []
        self.away_scorers = []

        # Ratings tracker {player_id: rating}
        self.ratings = {}
        for p in self.home_xi + self.away_xi:
            self.ratings[p['id']] = 6.0

        # Stats tracker
        self.stats = {
            "home": {"shots": 0, "on_target": 0, "xg": 0.0, "corners": 0, "fouls": 0, "yellows": 0, "reds": 0},
            "away": {"shots": 0, "on_target": 0, "xg": 0.0, "corners": 0, "fouls": 0, "yellows": 0, "reds": 0},
            "possession": {"home": 50, "away": 50}
        }

    def _calc_sector_ratings(self, xi: list):
        gk = [p for p in xi if (p.get('lineup_position') or p['position']) == 'GK']
        defs = [p for p in xi if (p.get('lineup_position') or p['position']) in ['CB', 'LB', 'RB']]
        mids = [p for p in xi if (p.get('lineup_position') or p['position']) in ['CM', 'CDM', 'CAM']]
        fwds = [p for p in xi if (p.get('lineup_position') or p['position']) in ['ST', 'LW', 'RW']]

        gk_obj = gk[0] if gk else xi[0]
        gk_stat = gk_obj['gk_reflexes']

        def_stat = sum(p['defending'] + p['physical'] for p in defs) / (len(defs) * 2) if defs else 65
        mid_stat = sum(p['passing'] + p['dribbling'] for p in mids) / (len(mids) * 2) if mids else 65
        att_stat = sum(p['shooting'] + p['pace'] for p in fwds) / (len(fwds) * 2) if fwds else 65

        return gk_obj, gk_stat, def_stat, mid_stat, att_stat, defs, mids, fwds

    def simulate(self):
        # Calculate sector strengths
        h_gk, h_gk_stat, h_def, h_mid, h_att, h_defs, h_mids, h_fwds = self._calc_sector_ratings(self.home_xi)
        a_gk, a_gk_stat, a_def, a_mid, a_att, a_defs, a_mids, a_fwds = self._calc_sector_ratings(self.away_xi)

        # Home ground advantage: +4%
        h_mid *= 1.04
        h_att *= 1.04

        # Tactical matchup
        tactical_mod = get_tactical_modifier(
            self.home_club.get('play_style', 'Possession'), 
            self.away_club.get('play_style', 'Possession')
        )
        h_mid *= tactical_mod

        # Mentality modifiers
        if self.home_club.get('mentality') == 'Attacking':
            h_att *= 1.10
            h_def *= 0.92
        elif self.home_club.get('mentality') == 'Defensive':
            h_att *= 0.90
            h_def *= 1.12

        if self.away_club.get('mentality') == 'Attacking':
            a_att *= 1.10
            a_def *= 0.92
        elif self.away_club.get('mentality') == 'Defensive':
            a_att *= 0.90
            a_def *= 1.12

        # Final possession split
        total_mid = h_mid + a_mid
        home_poss = int(round((h_mid / total_mid) * 100))
        home_poss = max(30, min(70, home_poss))
        away_poss = 100 - home_poss
        self.stats["possession"]["home"] = home_poss
        self.stats["possession"]["away"] = away_poss

        # Simulation loop over 90 minutes (sampled at chance generation intervals)
        for minute in range(1, 91):
            # Base probability of an attack happening in any given minute (~18% chance)
            if random.random() < 0.18:
                # Decide which team attacks based on possession
                is_home_attack = random.random() < (home_poss / 100.0)
                
                attacking_club = self.home_club if is_home_attack else self.away_club
                defending_club = self.away_club if is_home_attack else self.home_club
                
                att_side = "home" if is_home_attack else "away"
                def_side = "away" if is_home_attack else "home"

                att_pool = h_fwds + h_mids if is_home_attack else a_fwds + a_mids
                def_pool = a_defs + a_mids if is_home_attack else h_defs + h_mids
                keeper = a_gk if is_home_attack else h_gk
                keeper_stat = a_gk_stat if is_home_attack else h_gk_stat

                shooter = random.choice(att_pool) if att_pool else (self.home_xi[0] if is_home_attack else self.away_xi[0])
                assister = random.choice([p for p in att_pool if p['id'] != shooter['id']]) if len(att_pool) > 1 else None

                self.stats[att_side]["shots"] += 1
                
                # Shot accuracy chance
                shot_accuracy = (shooter['shooting'] * 0.6 + shooter['dribbling'] * 0.4)
                on_target_prob = max(0.25, min(0.75, shot_accuracy / 110.0))

                if random.random() < on_target_prob:
                    self.stats[att_side]["on_target"] += 1
                    
                    # Calculate Expected Goal value (xG)
                    shot_quality = (shooter['shooting'] * 0.7 + shooter['pace'] * 0.3)
                    defense_res = (a_def if is_home_attack else h_def)
                    xg = round(max(0.06, min(0.72, (shot_quality - defense_res * 0.5) / 100.0)), 2)
                    self.stats[att_side]["xg"] += xg

                    # Goal probability vs goalkeeper reflexes
                    goal_prob = xg * (1.1 - (keeper_stat / 200.0))
                    
                    if random.random() < goal_prob:
                        # GOAL!
                        if is_home_attack:
                            self.home_goals += 1
                            self.home_scorers.append(f"{shooter['name']} {minute}'")
                        else:
                            self.away_goals += 1
                            self.away_scorers.append(f"{shooter['name']} {minute}'")
                        
                        self.events.append(format_goal(
                            minute, 
                            attacking_club['name'], 
                            shooter['name'], 
                            assister['name'] if assister else None
                        ))
                        self.ratings[shooter['id']] += 1.2
                        if assister:
                            self.ratings[assister['id']] += 0.8
                    else:
                        # Saved by keeper
                        if random.random() < 0.65:
                            self.events.append(format_save(
                                minute, 
                                defending_club['name'], 
                                keeper['name'], 
                                shooter['name']
                            ))
                            self.ratings[keeper['id']] += 0.4
                        self.stats[att_side]["corners"] += 1
                else:
                    # Off-target / Woodwork
                    if random.random() < 0.20:
                        self.events.append(format_miss(minute, attacking_club['name'], shooter['name']))

            # Foul / Card chance (~5% per minute)
            if random.random() < 0.05:
                is_home_foul = random.random() < 0.50
                side = "home" if is_home_foul else "away"
                self.stats[side]["fouls"] += 1
                
                foul_club = self.home_club if is_home_foul else self.away_club
                foul_squad = self.home_xi if is_home_foul else self.away_xi
                offender = random.choice(foul_squad)

                if random.random() < 0.22:
                    is_red = random.random() < 0.04
                    if is_red:
                        self.stats[side]["reds"] += 1
                        self.ratings[offender['id']] -= 1.5
                    else:
                        self.stats[side]["yellows"] += 1
                        self.ratings[offender['id']] -= 0.3
                    
                    self.events.append(format_card(minute, foul_club['name'], offender['name'], is_red=is_red))

        # Round xG
        self.stats["home"]["xg"] = round(self.stats["home"]["xg"], 2)
        self.stats["away"]["xg"] = round(self.stats["away"]["xg"], 2)

        # Man of the Match
        all_xi = self.home_xi + self.away_xi
        motm = max(all_xi, key=lambda p: self.ratings[p['id']])
        motm_rating = round(min(10.0, max(6.0, self.ratings[motm['id']] + random.uniform(0.2, 0.7))), 1)

        return {
            "home_score": self.home_goals,
            "away_score": self.away_goals,
            "events": self.events,
            "stats": self.stats,
            "home_scorers": self.home_scorers,
            "away_scorers": self.away_scorers,
            "motm": f"{motm['name']} ({motm_rating})"
        }
