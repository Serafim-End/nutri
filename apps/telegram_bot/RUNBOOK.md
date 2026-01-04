# NutriMatch Telegram Bot — Operations Runbook

## Overview

This runbook provides operational guidance for running, debugging, and troubleshooting the NutriMatch Telegram bot for nutritionists.

---

## Quick Start

### Running Locally (Polling Mode)

1. **Ensure dependencies are installed:**
   ```bash
   cd apps/telegram_bot
   pip install -r requirements.txt
   ```

2. **Set environment variables:**
   ```bash
   export TELEGRAM_BOT_TOKEN="your_bot_token"
   export BACKEND_URL="http://localhost:5000"
   export BOT_SERVICE_TOKEN="your_service_token"
   export DATABASE_URL="postgresql://user:pass@localhost:5432/nutri"
   export WEBAPP_URL="https://t.me/your_bot/app"
   export TELEGRAM_MODE="polling"
   export BOT_DEBUG="true"  # Enable debug commands
   export LOG_LEVEL="DEBUG"
   ```

3. **Run smoke tests first:**
   ```bash
   python scripts/smoke.py
   ```

4. **Start the bot:**
   ```bash
   python bot.py
   ```

### Running with Docker

```bash
docker-compose up telegram_bot
```

---

## Environment Variables

### Required

| Variable | Description | Example |
|----------|-------------|---------|
| `TELEGRAM_BOT_TOKEN` | Bot token from @BotFather | `123456:ABC-DEF...` |
| `BACKEND_URL` | Backend API base URL | `http://localhost:5000` |
| `BOT_SERVICE_TOKEN` | Service token for API auth | `secret-token-123` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://...` |

### Optional

| Variable | Description | Default |
|----------|-------------|---------|
| `WEBAPP_URL` | Telegram Mini App URL | `https://t.me/your_bot/app` |
| `TELEGRAM_MODE` | `polling` or `webhook` | `polling` |
| `BOT_DEBUG` | Enable debug commands | `false` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `WEBHOOK_URL` | Public webhook URL | None |
| `WEBHOOK_PATH` | Webhook endpoint path | `/webhook` |
| `WEBHOOK_HOST` | Host to bind | `0.0.0.0` |
| `WEBHOOK_PORT` | Port to bind | `8443` |

---

## Viewing Logs

### Log Format

```
[TYPE] corr_id=XXXXXXXX user_id=NNNNNNNN type=message|callback action=... fsm_state=...
```

### Log Types

| Prefix | Meaning |
|--------|---------|
| `[REQ]` | Incoming request from Telegram |
| `[OK]` | Request completed successfully |
| `[ERR]` | Error during handler execution |
| `[API]` | Backend API call |
| `[THROTTLE]` | Rate limit triggered |
| `[FATAL]` | Unhandled exception |

### Filtering Logs

```bash
# View all requests from specific user
grep "user_id=123456789" logs/bot.log

# View all API calls
grep "\[API\]" logs/bot.log

# View all errors
grep "\[ERR\]\|\[FATAL\]" logs/bot.log

# Follow correlation ID through request
grep "corr_id=abc12345" logs/bot.log
```

### Log Levels

Set `LOG_LEVEL` environment variable:

- `DEBUG` — Verbose, includes API responses
- `INFO` — Standard operations (default)
- `WARNING` — Warnings and errors only
- `ERROR` — Errors only

---

## Resetting FSM State

### Via Debug Command (Recommended)

1. Ensure `BOT_DEBUG=true` is set
2. Send `/debug` to the bot
3. Tap "🗑️ Сбросить FSM состояние"

### Via Database

```sql
-- Clear state for specific user
DELETE FROM bot_states WHERE telegram_user_id = 123456789;

-- Clear all states (use with caution!)
TRUNCATE TABLE bot_states;
```

### Via Script

```bash
python -c "
import asyncio
import asyncpg
import os

async def clear_state(telegram_id):
    conn = await asyncpg.connect(os.environ['DATABASE_URL'])
    await conn.execute('DELETE FROM bot_states WHERE telegram_user_id = $1', telegram_id)
    await conn.close()
    print(f'State cleared for user {telegram_id}')

asyncio.run(clear_state(123456789))
"
```

---

## Common Failures and Solutions

### 1. Bot Token Invalid

**Symptoms:**
- Bot fails to start
- Error: `Unauthorized`

**Causes:**
- Wrong `TELEGRAM_BOT_TOKEN`
- Token revoked in @BotFather

**Solutions:**
1. Verify token with:
   ```bash
   curl https://api.telegram.org/bot<TOKEN>/getMe
   ```
2. If invalid, regenerate in @BotFather

---

### 2. Webhook Misconfigured

**Symptoms:**
- Bot works locally but not in production
- Updates not received

**Causes:**
- `WEBHOOK_URL` not matching actual URL
- SSL certificate issues
- Firewall blocking incoming connections

**Solutions:**
1. Check current webhook:
   ```bash
   curl https://api.telegram.org/bot<TOKEN>/getWebhookInfo
   ```

2. Delete webhook for polling:
   ```bash
   curl https://api.telegram.org/bot<TOKEN>/deleteWebhook
   ```

3. Set webhook manually:
   ```bash
   curl -F "url=https://your-domain.com/webhook" \
        https://api.telegram.org/bot<TOKEN>/setWebhook
   ```

4. Verify SSL certificate is valid

---

### 3. Backend Unauthorized (Service Token)

**Symptoms:**
- API calls return 401
- Error: "Invalid service token"

**Causes:**
- `BOT_SERVICE_TOKEN` mismatch between bot and backend
- Token not set in backend environment

**Solutions:**
1. Verify both environments have the same token:
   ```bash
   # In bot container/process
   echo $BOT_SERVICE_TOKEN
   
   # In backend container/process
   echo $BOT_SERVICE_TOKEN
   ```

2. Restart both services after fixing

---

### 4. Database Connection Failed

**Symptoms:**
- Bot fails to start
- Error: "Cannot connect to PostgreSQL"

**Causes:**
- Wrong `DATABASE_URL`
- Database server down
- Network issues

**Solutions:**
1. Verify connection string:
   ```bash
   psql "$DATABASE_URL" -c "SELECT 1"
   ```

2. Check database server is running

3. Verify network connectivity

---

### 5. Supabase Storage Credentials Missing

**Symptoms:**
- Photo/document uploads fail
- Error in upload handler

**Causes:**
- Supabase credentials not configured
- Storage bucket not created

**Solutions:**
1. For development, uploads use placeholder URLs
2. For production, set Supabase environment variables:
   ```bash
   export SUPABASE_URL="https://xxx.supabase.co"
   export SUPABASE_KEY="your-service-key"
   export SUPABASE_BUCKET="documents"
   ```

---

### 6. Google OAuth Redirect Mismatch

**Symptoms:**
- Calendar connection fails
- Error: "redirect_uri_mismatch"

**Causes:**
- OAuth redirect URL not in Google Console whitelist
- Wrong domain

**Solutions:**
1. In Google Cloud Console, add redirect URI:
   - `https://your-domain.com/api/auth/google/callback`

2. Verify environment variable:
   ```bash
   echo $GOOGLE_OAUTH_REDIRECT_URI
   ```

---

### 7. FSM State Corruption

**Symptoms:**
- User stuck in wrong state
- Bot shows unexpected prompts

**Solutions:**
1. User can send `/start` to reset
2. Admin can clear via database (see above)
3. Enable debug mode for user to self-reset

---

### 8. Rate Limiting Active

**Symptoms:**
- Bot ignores button presses
- Callback queries not processed

**Causes:**
- User pressing buttons too quickly
- Default rate limit: 0.3 seconds between actions

**Solutions:**
1. This is expected behavior
2. Adjust rate limit in `bot.py` if needed:
   ```python
   ThrottlingMiddleware(rate_limit=0.5)  # 0.5 seconds
   ```

---

## Health Checks

### Bot Health Endpoint (Webhook Mode)

```bash
curl http://localhost:8443/health
```

Expected response:
```json
{"status": "ok", "bot": "running"}
```

### Backend Health

```bash
curl http://localhost:5000/health/db
```

### Smoke Test

```bash
cd apps/telegram_bot
python scripts/smoke.py
```

---

## Monitoring

### Key Metrics to Watch

1. **Request latency** — Should be <2s for most operations
2. **Error rate** — Track `[ERR]` and `[FATAL]` logs
3. **API call success rate** — Monitor backend availability
4. **FSM state distribution** — Identify stuck users

### Database Queries

```sql
-- Active users (last 24h)
SELECT COUNT(*) FROM bot_states 
WHERE updated_at > NOW() - INTERVAL '24 hours';

-- FSM state distribution
SELECT state, COUNT(*) 
FROM bot_states 
GROUP BY state 
ORDER BY COUNT(*) DESC;

-- Old states (potential cleanup)
SELECT COUNT(*) FROM bot_states 
WHERE updated_at < NOW() - INTERVAL '30 days';
```

---

## Testing

### Run Unit Tests

```bash
cd apps/telegram_bot
pytest tests/ -v
```

### Run Backend Contract Tests

```bash
cd backend
pytest tests/test_bot_endpoints.py -v
```

### Seed Test Users

```bash
cd apps/telegram_bot
python scripts/seed_test_users.py
```

---

## Deployment Checklist

### Before Deploying

- [ ] Run smoke tests
- [ ] Run unit tests
- [ ] Verify environment variables
- [ ] Check webhook URL (if using webhooks)
- [ ] Verify service token matches backend

### After Deploying

- [ ] Check health endpoints
- [ ] Send `/start` to bot
- [ ] Verify `/debug` shows correct backend URL
- [ ] Test one full flow (e.g., create service)
- [ ] Check logs for errors

---

## Emergency Procedures

### Bot Not Responding

1. Check if process is running
2. Check logs for errors
3. Restart bot process
4. If still failing, check backend health

### Mass FSM State Issues

```sql
-- Backup states first
CREATE TABLE bot_states_backup AS SELECT * FROM bot_states;

-- Clear all states (nuclear option)
TRUNCATE TABLE bot_states;
```

### Rolling Back

1. Stop current bot process
2. Deploy previous version
3. Start bot
4. Clear FSM states if needed

---

## Support Contacts

For issues not covered here:
- Check GitHub issues
- Contact development team
- Review application logs with correlation IDs

