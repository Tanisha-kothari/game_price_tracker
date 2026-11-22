# Game Price Tracker

A fully automated, cloud-based game price tracking application. Add game store links (Steam, Epic Games, GOG) and get automatic daily price checks with email alerts — all using **free services only**.

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Streamlit     │────>│   GitHub Repo    │<────│  GitHub Actions  │
│  (Cloud UI)     │     │  (games.json,    │     │  (Daily Checker) │
│                 │     │   history.json)  │     │                  │
└─────────────────┘     └──────────────────┘     └─────────────────┘
         │                       │                        │
         │                       │                        │
         ▼                       ▼                        ▼
  User adds URL           REST API commits          Price API (Steam,
  via browser             & pushes data             Epic, GOG scrapers)
                                                         │
                                                         ▼
                                                    Email Alert
                                                 (Gmail SMTP)
```

### How it works

1. **User** opens the Streamlit app from any device (phone, desktop).
2. **User** pastes a game store URL and optionally sets a target price.
3. **Streamlit app** fetches game details via the store API, saves them to `games.json`, and commits to GitHub using the REST API.
4. **GitHub Actions** runs `checker.py` every morning on a cron schedule.
5. **Checker** reads `games.json`, queries each store's API for current prices, updates `history.json`, and commits changes.
6. **Email notification** is sent via Gmail SMTP when a price drops, rises, hits the target, or reaches a new all-time low.

## Folder Structure

```
game-price-tracker/
├── app.py                  # Streamlit UI (main web app)
├── checker.py              # Daily price checker (runs via GitHub Actions)
├── database.py             # JSON-based read/write operations
├── github_manager.py       # GitHub REST API integration (no local Git)
├── price_api.py            # Store-specific price fetchers (Steam, Epic, GOG)
├── notifier.py             # Email notification (HTML templates + Gmail SMTP)
├── utils.py                # Shared utilities (URL parsing, formatting, CSV export)
├── games.json              # Tracked games database
├── history.json            # Historical price data
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variable template
├── .streamlit/
│   └── config.toml         # Streamlit theme & server config
└── .github/workflows/
    └── daily_check.yml     # GitHub Actions workflow
```

## Prerequisites

- A **GitHub account** (free)
- A **Streamlit Community Cloud** account (free — sign in with GitHub)
- A **Gmail account** (free) with App Password enabled
- **Python 3.9+** (for local development only)

## Step-by-Step Setup

### 1. Fork or create a GitHub repository

Create a new repository named `game-price-tracker` (or any name you prefer). Push all the files from this project to that repository.

### 2. Create a GitHub Personal Access Token (classic)

1. Go to GitHub **Settings → Developer settings → Personal access tokens → Tokens (classic)**
2. Click **Generate new token (classic)**
3. Give it a name like `GAME_PRICE_TRACKER`
4. Set expiration to **No expiration** (or your preferred period)
5. Select scopes: **repo** (Full control of private repositories)
6. Click **Generate token**
7. **Copy the token immediately** — you won't see it again

### 3. Set up Gmail App Password

1. Go to your Google Account → **Security**
2. Enable **2-Step Verification** if not already enabled
3. Go to **App passwords** (search in Google Account settings)
4. Select app: **Mail**, device: **Other** (name it `Game Price Tracker`)
5. Click **Generate**
6. **Copy the 16-character password** (it looks like `abcd efgh ijkl mnop`)

### 4. Deploy to Streamlit Community Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with your GitHub account
3. Click **New app**
4. Select your `game-price-tracker` repository
5. Set branch: `main`, main file: `app.py`
6. Click **Deploy**

### 5. Configure Streamlit Secrets

1. In your Streamlit app dashboard, go to **Settings → Secrets**
2. Add the following:

```toml
GITHUB_TOKEN = "ghp_your_token_here"
REPO_OWNER = "your_github_username"
REPO_NAME = "game-price-tracker"
EMAIL_ADDRESS = "your_email@gmail.com"
EMAIL_PASSWORD = "your_16_char_app_password"
NOTIFY_TO = "your_email@gmail.com"
SEND_UNCHANGED_SUMMARY = "false"
```

3. Click **Save**. The app will automatically restart.

### 6. Configure GitHub Actions secrets

1. Go to your GitHub repository → **Settings → Secrets and variables → Actions**
2. Add the following **Repository secrets**:

| Secret | Value |
|--------|-------|
| `GITHUB_TOKEN` | Your GitHub Personal Access Token |
| `REPO_OWNER` | Your GitHub username |
| `REPO_NAME` | Your repository name |
| `EMAIL_ADDRESS` | Your Gmail address |
| `EMAIL_PASSWORD` | Your Gmail App Password |
| `NOTIFY_TO` | Email to receive alerts (same as above) |
| `SEND_UNCHANGED_SUMMARY` | `false` (set to `true` to get daily summary even when no prices change) |

### 7. Enable GitHub Actions

The workflow file is already at `.github/workflows/daily_check.yml`. It will:
- Run daily at 6:00 AM UTC
- Check all tracked game prices
- Update `history.json`
- Send email alerts if prices change
- Can also be triggered manually from the Actions tab

## Local Development

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/game-price-tracker.git
cd game-price-tracker

# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the app locally (requires environment variables set)
set GITHUB_TOKEN=ghp_your_token
set REPO_OWNER=your_username
set REPO_NAME=game-price-tracker
streamlit run app.py
```

For local development without GitHub, the app will show an error about missing secrets — this is expected. The `checker.py` script can be tested locally:

```bash
set GITHUB_TOKEN=ghp_your_token
set REPO_OWNER=your_username
set REPO_NAME=game-price-tracker
set EMAIL_ADDRESS=your_email@gmail.com
set EMAIL_PASSWORD=your_app_password
python checker.py
```

## Usage

### Adding a Game

1. Open your Streamlit app URL
2. Paste a game store URL (examples below)
3. Optionally enter a target price
4. Click **Add Game**

**Supported URL formats:**
- `https://store.steampowered.com/app/730/CSGO/`
- `https://store.epicgames.com/en-US/p/cyberpunk-2077`
- `https://www.gog.com/en/game/the_witcher_3_wild_hunt`

### Managing Games

Each game appears as a card with:
- **Game name** and cover image
- **Current price**, lowest recorded price, target price
- **Last checked** date
- **Delete** button — removes the game
- **Refresh** button — checks price immediately
- **Open Store** button — opens the store page

### Exporting Data

Use the **Export CSV** or **Export JSON** buttons to download your game data.

## Email Notifications

When a price changes, you receive a beautifully formatted HTML email showing:
- Game cover image and name
- Current and previous prices
- Price difference (green for drops, red for increases)
- Target price status
- All-time low indicator
- Daily summary with all changes

## Supported Stores

| Store | API Used | Notes |
|-------|----------|-------|
| Steam | Steam Storefront API | Free, no key required |
| Epic Games | Epic Content API | Free, no key required |
| GOG | GOG API | Free, no key required |

### Adding New Stores

To add a new store:

1. Create a new fetcher class in `price_api.py` that inherits from `BaseFetcher`
2. Implement `get_game_details()` and `get_current_price()`
3. Add the store domain to `STORE_DOMAINS` in `utils.py`
4. Register your fetcher in `FETCHER_MAP` in `price_api.py`

```python
class NewStoreFetcher(BaseFetcher):
    def get_game_details(self, url: str) -> GameDetails:
        # Fetch and return game details
        ...

    def get_current_price(self, url: str) -> Optional[float]:
        # Fetch and return current price
        ...

FETCHER_MAP["newstore"] = NewStoreFetcher
```

## Notification Types

- **Price decreased** — price went down
- **Price increased** — price went up
- **Target reached** — price at or below your target
- **New historical low** — cheapest price ever recorded

Configure which notifications you want by editing `notifier.py` or filtering in `checker.py`.

## Error Handling

The app handles:
- Invalid URLs with clear error messages
- Network/API failures gracefully (logs and continues)
- Duplicate games (notifies user)
- Missing secrets (shows configuration error)
- Individual game check failures (continues with remaining games)

## Automated Uptime Monitoring & Price Refresh

GameTracker strictly decouples **Uptime Monitoring** from **Price Refreshing** to prevent unneeded API hits and keep the application awake and resilient.

### 1. Health-Check Endpoint (`Part A`)
GameTracker provides a zero-overhead, unauthenticated health endpoint that avoids touching GitHub, the database, or store APIs:
- **Streamlit Web Route**: `https://<your-app>.streamlit.app/?health=1`
- **Standalone/Container Route**: `http://localhost:8080/health`

**Expected JSON Response:**
```json
{
  "status": "healthy",
  "service": "GameTracker",
  "timestamp": "2026-11-22T09:15:00.000000+00:00",
  "version": "1.0.0"
}
```

### 2. External Uptime Monitoring (`Part B`)
- **Streamlit Community Cloud Sleep Policy**: Streamlit Community Cloud automatically puts apps into sleep/hibernation mode after prolonged inactivity (typically 7 days without browser traffic). Free-tier apps wake upon new HTTP requests, but prolonged sleep shows an idle page.
- **Hourly Ping Setup**:
  - **Option 1: Built-in GitHub Action**: Configure secret `APP_URL` in your GitHub repository secrets (e.g. `https://your-app.streamlit.app`). The included `.github/workflows/uptime_monitor.yml` runs hourly (`0 * * * *`) to ping `/?health=1`, verify HTTP 200, log response times, and publish a report to GitHub Step Summary.
  - **Option 2: External Monitor (UptimeRobot / Better Stack / Cron-Job.org)**:
    1. Create a free HTTP monitor targeting `https://<your-app>.streamlit.app/?health=1` (or `/health`).
    2. Set monitoring interval to **60 minutes** (or **15 minutes**).
    3. Assert expected status `200` and keyword `"status": "healthy"`.

### 3. Automated 6-Hour Price Refresh (`Part C`)
- **Canonical Engine**: Both manual refreshes and scheduled jobs run through the exact same engine in `checker.py` (`run_price_check()`).
- **Schedule**: Every 6 hours (`0 */6 * * *` at 00:00, 06:00, 12:00, and 18:00 UTC) via `.github/workflows/price_refresh.yml` and in-app APScheduler.
- **Concurrency Locking**: Protected by `_refresh_lock` and GitHub Actions `concurrency: group: price-refresh-job` so overlapping jobs never run simultaneously.
- **Resilience & Rate Limiting**:
  - Polite 1.0s delay between store requests to respect Steam, Epic Games, and GOG rate limits.
  - Per-game error isolation: if one store or game times out, other games continue checking normally.
  - Valid prices are **never** overwritten with `None` on failed fetches.
  - Persists `games.json`, `history.json`, and `refresh_status.json` via GitHubManager.
- **Dashboard UI Status**:
  - Displays **Last automatic refresh: [timestamp]**
  - Displays **Next scheduled refresh: [timestamp]**
  - Provides a prominent **🔄 Refresh All Prices** action button.

## Discord Bot & WhatsApp Bot Assistant

Interact with GameTracker without opening the web browser. Both bots consume the exact **same shared backend service layer (`bot_service.py`)** and access the real-time GitHub-synchronized game database.

```
                  ┌────────────────────────────────────────┐
                  │   Shared Service Layer (bot_service)    │
                  └───────────────────┬────────────────────┘
                                      │
            ┌─────────────────────────┼─────────────────────────┐
            │                         │                         │
            ▼                         ▼                         ▼
   ┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
   │  Streamlit Web  │       │   Discord Bot   │       │  WhatsApp Bot   │
   │  Lobby & UI     │       │ (Slash Commands)│       │ (Meta Cloud API)│
   └─────────────────┘       └─────────────────┘       └─────────────────┘
```

---

### 1. Discord Bot (`discord_bot.py`)

A full-featured gaming assistant bot utilizing modern Discord Slash Commands and rich embed layouts.

#### Supported Slash Commands:
- `/tracked`: Displays all tracked games on your radar with store badges and prices.
- `/game <name>`: Detailed game inspection (artwork thumbnail, current price, lowest recorded, discount %, status, last checked, and direct "Open Store" button).
- `/owned`: Displays games logged in My Library (Loot Vault) with acquisition date and price.
- `/deals`: Lists all currently discounted games sorted by highest discount percentage.
- `/search <query>`: Searches tracked collection by game title, store, or tag.
- `/refresh`: Requests an immediate price refresh (protected by operator authorization and 5-minute cooldown).
- `/help`: Displays the visual command guide.

#### Discord Bot Setup:
1. Go to the [Discord Developer Portal](https://discord.com/developers/applications) and create a **New Application**.
2. Navigate to **Bot** → click **Reset Token** to copy your bot token.
3. In **OAuth2 → URL Generator**, select scopes: `bot`, `applications.commands`, and permissions: `Send Messages`, `Embed Links`, `Read Message History`.
4. Invite the bot to your Discord server using the generated URL.
5. Set environment variables / Streamlit secrets:
   ```env
   DISCORD_BOT_TOKEN="your_bot_token_here"
   DISCORD_AUTHORIZED_USERS="123456789012345678,987654321098765432" # Comma-separated Discord User IDs
   ```
6. Run the bot:
   ```bash
   python discord_bot.py
   ```
   *(Can be run locally, on a VPS, or as a background worker on platforms like Render or Railway).*

---

### 2. WhatsApp Bot (`whatsapp_bot.py`)

An official integration using the **Meta WhatsApp Cloud API (Graph API)**. No unofficial web-scraping or browser automation required.

#### Supported Commands (Case-insensitive):
- `TRACKED`: Returns all tracked games and prices.
- `GAME <title>`: Returns details and store link for a specific game (e.g. `GAME Skyrim`).
- `DEALS`: Shows currently discounted games sorted by discount.
- `OWNED`: Shows purchased games from My Library (restricted to authorized phone numbers).
- `SEARCH <query>`: Searches tracked games collection (e.g. `SEARCH Witcher`).
- `REFRESH`: Triggers an application-wide price check (authorized operators only, 5-minute cooldown).
- `HELP`: Displays command menu and interactive reply buttons.

#### Meta WhatsApp Cloud API Setup:
1. Register on the [Meta for Developers Portal](https://developers.facebook.com/) and create a Business App with the **WhatsApp** product.
2. In the WhatsApp dashboard, obtain:
   - **Phone Number ID**: `WHATSAPP_PHONE_NUMBER_ID`
   - **System User Permanent Access Token**: `WHATSAPP_ACCESS_TOKEN`
   - **App Secret** (from App Settings → Basic): `WHATSAPP_APP_SECRET`
3. Configure your Webhook in Meta App Dashboard:
   - **Callback URL**: `https://<your-app-domain>/whatsapp/webhook`
   - **Verify Token**: Choose a secret string (e.g. `my_gametracker_verify_token`) and set as `WHATSAPP_VERIFY_TOKEN`.
   - Subscribe to the `messages` webhook field.
4. Set environment variables / Streamlit secrets:
   ```env
   WHATSAPP_ACCESS_TOKEN="EAA..."
   WHATSAPP_PHONE_NUMBER_ID="1006..."
   WHATSAPP_VERIFY_TOKEN="my_gametracker_verify_token"
   WHATSAPP_APP_SECRET="c2d4..."
   WHATSAPP_AUTHORIZED_NUMBERS="+1234567890,+919876543210" # Numbers authorized for library and refresh
   ```
5. Test the bot by sending `DEALS` or `HELP` to your registered WhatsApp business phone number!

---

### 3. Bot Security & Protection Against Abuse
- **Shared Service Layer**: Both bots invoke [bot_service.py](file:///c:/Users/tanisha/Downloads/price-tracker/bot_service.py), guaranteeing unified logic, currency handling, and zero database desynchronization.
- **Refresh Abuse Protection**: Both `/refresh` and `REFRESH` require operator authorization and enforce an in-memory 5-minute (300-second) cooldown to prevent store API flooding.
- **Webhook Cryptographic Integrity**: WhatsApp webhooks verify Meta's `X-Hub-Signature-256` header via HMAC SHA-256 using `WHATSAPP_APP_SECRET`.
- **Private Data Protection**: Access to `OWNED` (My Library) on WhatsApp is restricted to numbers listed in `WHATSAPP_AUTHORIZED_NUMBERS`.
- **Zero Exposed Secrets**: All tokens, keys, and authorization headers are read from environment variables or Streamlit secrets and masked in logs.

## Logging

All operations are logged:
- `INFO` — Price checks, GitHub commits, email sent
- `WARNING` — Failed price fetches, duplicate games
- `ERROR` — API failures, GitHub errors, email failures

## Future Improvements

The architecture is designed to easily support:

- **Notifications**: Telegram, Discord, WhatsApp, Slack
- **Storage**: SQLite, PostgreSQL, MongoDB (swap `database.py`)
- **Charts**: Price history graphs in Streamlit
- **Multi-user**: OAuth login, per-user wishlists
- **AI features**: Sale predictions, purchase recommendations
- **Mobile app**: Companion app using the same API

## Troubleshooting

### "GitHub secrets not configured"
Add secrets in Streamlit Cloud dashboard → Settings → Secrets.

### "Cannot connect to GitHub"
- Verify your token has `repo` scope
- Check repository name and owner are correct
- Ensure the repository exists

### Emails not sending
- Verify App Password (not your regular Gmail password)
- Ensure 2-Step Verification is enabled on your Google account
- Check spam folder

### Price check fails for a game
- Some stores block automated requests — the app logs these errors
- Try the "Refresh" button on the game card
- Verify the URL is correct

### GitHub Actions failing
- Go to your repo → Actions tab → click failed workflow → check logs
- Verify all secrets are set in Repository Settings → Secrets
- Ensure `GITHUB_TOKEN` in Actions secrets has `repo` scope

### "Could not identify the game from the URL"
Make sure you're using a supported URL format. Game pages work best (not search or storefront pages).

## License

MIT
