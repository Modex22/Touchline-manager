# ⚽ Touchline Manager — Telegram Football Game

**Touchline Manager** is a full-featured, multiplayer-ready football management game designed exclusively for Telegram. Manage your club, upload custom club badges, build tactical formations, develop footballers, buy/sell on the transfer market, and compete in a dynamic 4-tier league pyramid.

---

## 🌟 Key Features

1. **Telegram-Native UX**
   - **Persistent Bottom Keyboard Menu** for one-tap navigation at all times (`🏟️ My Club`, `👥 Squad`, `📋 Tactics`, `⚽ Matchday`, etc.).
   - Interactive **Inline Keyboards** for deep tactical changes, player cards, and transfer bids.

2. **Custom Club Badge Upload**
   - Send any photo directly to the bot.
   - Automatically resized and optimized into a crisp 512×512 badge, displayed on club dashboards and match previews.

3. **90-Minute Event-Driven Match Engine**
   - Tactical Rock-Paper-Scissors: *High Press* disrupts *Possession*, *Counter-Attack* beats *High Press*, *Low Block* stops *Counter-Attack*, and *Possession* unlocks *Low Block*.
   - Realistic chance creation, Expected Goals ($xG$), and goalkeeper reflex saves.
   - Live text commentary for goals, screamers, assists, yellow/red cards, and saves.
   - Full post-match report with official statistics, Man of the Match, and ticket gate receipts credited to your balance.

4. **Squad & Transfer Market**
   - Detailed attributes: Pace, Shooting, Passing, Dribbling, Defending, Physical, GK Reflexes, Fitness, and Morale.
   - Visual ASCII pitch visualizer for starting formations (4-3-3, 4-4-2, 3-5-2, 4-2-3-1, 5-3-2).
   - Instant "⚡ Auto-Pick Best XI".
   - Dynamic transfer market with free agents and player bidding.

5. **League Pyramid & Finances**
   - 4 Divisions: **Premier Division**, **Championship**, **National League**, and **Development League**.
   - Promotion and relegation based on league standings.
   - Stadium expansion to boost matchday ticket revenue.

---

## 🚀 How to Deploy on Render

### Step 1: Create Your Bot on Telegram
1. Open Telegram and search for [@BotFather](https://t.me/BotFather).
2. Send `/newbot`, name your bot (e.g., `Touchline Manager`), and choose a username ending in `bot` (e.g., `touchline_manager_bot`).
3. Copy the **HTTP API Token** provided by BotFather.

---

### Step 2: Push to GitHub
Initialize git and push this project to your GitHub repository:
```bash
git init
git add .
git commit -m "Initial commit of Touchline Manager"
git branch -M main
git remote add origin https://github.com/<your-username>/touchline-manager.git
git push -u origin main
```

---

### Step 3: Deploy on Render
1. Go to [Render Dashboard](https://dashboard.render.com/) and click **New +** -> **Web Service**.
2. Connect your GitHub repository.
3. Configure settings:
   - **Name**: `touchline-manager`
   - **Region**: Closest to you (e.g., Frankfurt or Oregon)
   - **Environment**: `Python`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python bot.py`
4. Under **Environment Variables**, add:
   - `BOT_TOKEN`: Paste your token from @BotFather.
   - `PORT`: `10000` (Render sets this by default)
5. Click **Deploy Web Service**!

> **Note on Render Web Service:** Touchline Manager includes a built-in lightweight health check server on `/health`. Render will verify the health port, display **Live / Healthy**, and keep your Telegram bot active!

---

## 💻 Local Testing

1. Create a `.env` file from `.env.example`:
   ```bash
   cp .env.example .env
   ```
2. Paste your `BOT_TOKEN` in `.env`.
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the bot:
   ```bash
   python bot.py
   ```
5. Open your bot on Telegram and type `/start`!

---

## 📁 Project Architecture

```text
touchline_manager/
│
├── bot.py                   # Telegram bot entry point & Render health server
├── config.py                # Environment configs, game constants, file paths
├── database.py              # SQLite schema, queries, seeded AI clubs & squads
│
├── handlers/                # Telegram UI & command controllers
│   ├── start.py             # /start registration & onboarding wizard
│   ├── club.py              # Club dashboard, logo photo upload & finances
│   ├── squad.py             # Squad list, visual pitch & player detail card
│   ├── tactics.py           # Formations, mentalities & playing styles
│   ├── matchday.py          # Match simulation & post-match report
│   ├── market.py            # Transfer market & player bidding
│   ├── training.py          # Squad drills (Fitness, Shooting, Defending, Passing)
│   ├── standings.py         # Multi-tier league tables
│   └── keyboards.py         # Persistent menu & inline action keyboards
│
├── engine/                  # Core Football Simulation Engine
│   ├── match_engine.py      # 90-minute tick simulation, xG, stats & MOTM
│   ├── player_generator.py  # Realistic player generator & starter squads
│   ├── tactics.py           # Formations, synergy matrix & ASCII pitch
│   └── commentary.py        # Dynamic match commentary strings
│
├── render.yaml              # Render Blueprint deployment config
├── Procfile                 # Process file for Render / Railway
└── requirements.txt         # Dependencies (python-telegram-bot, pillow, aiohttp)
```
