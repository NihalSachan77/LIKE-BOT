# NXT Like Bot — Render setup

## Deploy on Render's free Web Service

This version exposes `/health` on `0.0.0.0:$PORT`, so it satisfies Render's Web Service port check. It runs Telegram polling in the same process.

1. Upload the contents of this folder to a **private GitHub repository**.
2. In Render choose **New + → Blueprint** and select the repository, or create a Python Web Service manually.
3. If creating manually, use:
   - Build command: `pip install -r requirements.txt`
   - Start command: `python main.py`
   - Health check path: `/health`
   - Instance type: Free (if offered for your account)
4. Set `BOT_TOKEN` to a fresh token from Telegram's official @BotFather.
5. Set `ADMIN_IDS` to your own numeric Telegram user ID.
6. Set `DEFAULT_CHANNEL` to your channel username, or leave the default.
7. Leave `LIKE_API_URL` blank until you have a trusted, working API endpoint authorized for this use.
8. Deploy and check Logs, then send `/start` to the bot.

## Important free-tier limitation

Render's free Web Services can spin down after a period without inbound web traffic. Since this bot uses Telegram polling, it may become temporarily unavailable when the service sleeps. A free service is not guaranteed to be always-on. If you need reliable 24/7 operation, use a hosting option that supports an always-on worker, or adapt the bot to a webhook architecture.

## Features and API limitation

This is a Telegram bot starter with daily limits, premium keys, channel membership checks, SQLite, and AutoLike scheduling. AutoLike runs once per day at the configured Asia/Kolkata (IST) time. It may run a few minutes after that time because the scheduler checks every five minutes. AutoLike and like commands do not actually deliver likes unless `LIKE_API_URL` is configured with a working API you are authorized to use. A successful scheduled job only means the scheduler ran; it does not prove that a like request succeeded.

## Environment variables

- `BOT_TOKEN`: required Telegram bot token.
- `ADMIN_IDS`: comma-separated numeric Telegram user IDs.
- `DEFAULT_CHANNEL`: channel used for the default join check.
- `LIKE_API_URL`: optional authorized API URL template using `{uid}` and optionally `{region}`.
- `FREE_DAILY_LIMIT`: default `3`.
- `PREMIUM_DAILY_LIMIT`: default `50`.
- `AUTOLIKE_TIME`: default daily run time `09:00` in Asia/Kolkata (IST). The admin command `/setautoliketime HH:MM` changes the daily run time, e.g. `/setautoliketime 21:30`.

## Security

Never commit `.env` files, bot tokens, or your live SQLite database to GitHub. The old uploaded project contained a hard-coded bot token; revoke it with @BotFather and use a newly generated token in Render Environment settings. Do not put the token into source code or share it in screenshots.

## Added admin commands

- `/addadmin <telegram_user_id>` — add an admin stored in SQLite.
- `/removeadmin <telegram_user_id>` — remove a database admin. The root admin configured in Render's `ADMIN_IDS` must be removed from Render Environment instead.
- `/admins` — list configured admin IDs.
- `/setautoliketime <hours>` — set the saved AutoLike interval (1–168 hours). This setting is stored in SQLite, so note that it may reset on redeploy/restart if you do not configure persistent storage.
- `/runautolike <user_id>` — immediately run the saved AutoLike request for that user's saved player UID. Requires `LIKE_API_URL` to be configured with a trusted, authorized endpoint.

The first/root admin must be listed in Render's `ADMIN_IDS` environment variable before using admin commands. Do not make an untrusted user an admin.
