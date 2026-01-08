# NutriMatch Telegram Bot

Telegram bot for nutritionists to manage their profiles, services, and view statistics.

## Features

- **Profile Management**: Create and update nutritionist profiles with FSM-based wizard
- **Services**: Add, edit, toggle, and delete consultation services
- **Schedule Management**: Create, view, and delete availability slots (PRIMARY)
- **Bookings View**: View upcoming client bookings with details
- **Calendar**: Optional Google Calendar integration (SECONDARY, non-blocking)
- **Reviews**: View client reviews with pagination
- **Statistics**: View income and consultation statistics
- **Support**: Send messages to platform support

## Availability Management

> **Important:** Manual slots are the PRIMARY method for availability management.
> Google Calendar integration is OPTIONAL and does not block any functionality.

Nutritionists can manage their availability directly in the bot:

1. **Schedule View** (`🕒 Расписание`): See all slots grouped by date
2. **Add Slot**: FSM wizard to create slots (date → time → duration → confirm)
3. **Delete Slot**: Remove free slots (booked slots cannot be deleted)
4. **View Bookings** (`📋 Мои бронирования`): See upcoming client bookings

This design ensures:
- ✅ Works without any external integrations
- ✅ Simple, intuitive UX for nutritionists
- ✅ Calendar integration can be added later without breaking existing flows

## Tech Stack

- **Python 3.11+**
- **aiogram v3** - Modern async Telegram Bot framework
- **aiohttp** - Async HTTP client for backend API
- **asyncpg** - Async PostgreSQL driver for FSM state storage

## Architecture

The bot is designed as a **fully removable module**:

- ✅ Communicates with backend ONLY via REST API
- ✅ Does NOT access database models directly (except `bot_states` table)
- ✅ Does NOT contain business logic
- ✅ Can be removed without affecting backend or client app

## Quick Start

### 1. Prerequisites

- Python 3.11+
- Running NutriMatch backend
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))

### 2. Configuration

Copy the environment template:

```bash
cp env.example .env
```

Edit `.env` with your values:

```bash
# Required
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
BOT_SERVICE_TOKEN=same_token_as_in_backend_env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/nutrimatch

# Backend
BACKEND_URL=http://localhost:5000

# Mode
TELEGRAM_MODE=polling  # or webhook for production
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Bot

**Polling mode (development):**

```bash
python bot.py
```

**Or with Docker:**

```bash
# From project root
docker compose --profile bot up
```

## Modes

### Polling Mode (Development)

Best for local development. The bot continuously polls Telegram servers for updates.

```bash
TELEGRAM_MODE=polling
```

### Webhook Mode (Production)

For production deployment. Telegram sends updates to your server.

```bash
TELEGRAM_MODE=webhook
WEBHOOK_URL=https://your-domain.com
WEBHOOK_PATH=/webhook
WEBHOOK_PORT=8443
```

**Webhook requirements:**
- HTTPS with valid SSL certificate
- Public IP/domain accessible from Telegram servers
- Port 443, 80, 88, or 8443

## BotFather Setup

1. Create bot with [@BotFather](https://t.me/BotFather):
   ```
   /newbot
   ```

2. Set bot commands:
   ```
   /setcommands
   ```
   Then send:
   ```
   start - Начать работу с ботом
   ```

3. Enable inline mode (optional):
   ```
   /setinline
   ```

4. Set up Mini App button:
   ```
   /mybots → Select bot → Bot Settings → Menu Button
   ```
   - Button text: `🍎 Открыть приложение`
   - Web App URL: Your Mini App URL

5. Configure WebApp (for inline button):
   ```
   /newapp
   ```
   Follow the prompts to create a Web App.

## Project Structure

```
apps/telegram_bot/
├── bot.py              # Main entry point
├── config.py           # Configuration management
├── api_client.py       # Backend API client
├── storage.py          # PostgreSQL FSM storage
├── states.py           # FSM state definitions
├── keyboards.py        # Inline keyboard builders
├── middleware.py       # Logging & error handling
├── handlers/
│   ├── __init__.py     # Router registration
│   ├── start.py        # /start command
│   ├── menu.py         # Menu navigation
│   ├── profile.py      # Profile FSM flow
│   ├── services.py     # Services management
│   ├── schedule.py     # Schedule & bookings management
│   ├── cabinet.py      # Cabinet (reviews, stats, etc.)
│   └── debug.py        # Debug utilities
├── requirements.txt    # Python dependencies
├── Dockerfile          # Production container
└── env.example         # Environment template
```

## Backend Integration

The bot requires these backend endpoints (under `/api/bot/`):

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/resolve-telegram-user` | GET | Get user profile and role |
| `/nutritionists/<id>/services` | GET | List services |
| `/nutritionists/<id>/services/<sid>` | PUT | Update service |
| `/nutritionists/<id>/services/<sid>` | DELETE | Delete service |
| `/nutritionists/<id>/slots` | GET | List availability slots |
| `/nutritionists/<id>/slots` | POST | Create availability slot |
| `/nutritionists/<id>/slots/<slot_id>` | DELETE | Delete availability slot |
| `/nutritionists/<id>/bookings` | GET | Get nutritionist bookings |
| `/nutritionists/<id>/calendar/status` | GET | Calendar status (optional) |
| `/nutritionists/<id>/reviews` | GET | Get reviews |
| `/nutritionists/<id>/statistics` | GET | Get statistics |
| `/support/messages` | POST | Create support ticket |

All endpoints require `X-Service-Token` header.

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | ✅ | - | Bot token from BotFather |
| `BOT_SERVICE_TOKEN` | ✅ | - | Service token for backend auth |
| `DATABASE_URL` | ✅ | - | PostgreSQL connection string |
| `BACKEND_URL` | ✅ | `http://localhost:5000` | Backend API URL |
| `TELEGRAM_MODE` | ❌ | `polling` | `polling` or `webhook` |
| `WEBHOOK_URL` | ❌* | - | *Required if webhook mode |
| `WEBHOOK_PATH` | ❌ | `/webhook` | Webhook endpoint path |
| `WEBHOOK_PORT` | ❌ | `8443` | Webhook server port |
| `WEBAPP_URL` | ❌ | - | Mini App URL for WebApp button |
| `LOG_LEVEL` | ❌ | `INFO` | Logging level |

## Docker Commands

```bash
# Start bot with all services
docker compose --profile bot up

# Start bot only (backend already running)
docker compose --profile bot up telegram-bot

# View logs
docker compose logs -f telegram-bot

# Rebuild after changes
docker compose --profile bot up --build telegram-bot
```

## Development Tips

1. **Hot Reload**: In polling mode, just restart the script
2. **Debug Logging**: Set `LOG_LEVEL=DEBUG`
3. **Test API**: Use `curl` to test backend endpoints directly
4. **FSM State**: States are persisted in `bot_states` table

## Troubleshooting

### Bot doesn't start

- Check `TELEGRAM_BOT_TOKEN` is correct
- Verify backend is running and accessible
- Check `BOT_SERVICE_TOKEN` matches backend config

### Commands not responding

- Check bot is running (no errors in logs)
- Verify no other instance is running (polling conflict)
- Check FSM storage connection

### Webhook not working

- Verify SSL certificate is valid
- Check WEBHOOK_URL is publicly accessible
- Ensure port is in allowed list (443, 80, 88, 8443)

## Removing the Bot

To completely remove the bot module:

1. Stop the bot container:
   ```bash
   docker compose --profile bot down telegram-bot
   ```

2. Remove the directory:
   ```bash
   rm -rf apps/telegram_bot
   ```

3. Optionally remove from docker-compose.yml:
   - Remove the `telegram-bot` service block

4. Optionally clean up database:
   ```sql
   DROP TABLE IF EXISTS bot_states;
   ```

The backend and client app will continue to work normally.

