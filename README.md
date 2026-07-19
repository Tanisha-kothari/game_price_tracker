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
