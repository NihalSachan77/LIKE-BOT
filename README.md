# NXT Like Bot — Premium Edition

Telegram bot starter with a premium inline menu, free/premium daily limits, redeem keys, admin commands, multi-channel force join, SQLite storage, and Render worker configuration.

## Important limitation
No likes API was provided. `/nxtlike` intentionally returns a clear "API not configured" message until you set `LIKE_API_URL`. This project does not invent or simulate successful likes. Only integrate an API you are authorized to use and whose terms allow the requested operation. `/profile` is a placeholder until a separate profile endpoint is supplied.

## Setup
1. Create a bot using Telegram's official BotFather and copy its token.
2. Upload this folder to a private GitHub repository.
3. In Render, create a Background Worker from the repository.
4. Set environment variables:
   - `BOT_TOKEN`: your bot token
   - `ADMIN_IDS`: your numeric Telegram user ID (comma-separated for multiple admins)
   - `DEFAULT_CHANNEL`: defaults to `@trynexttime`
   - `LIKE_API_URL`: leave blank until you have a working authorized endpoint, e.g. a URL template containing `{uid}` and optionally `{region}`
5. Ensure the bot can inspect membership for every required channel. For reliable membership checks, add the bot as an administrator in each channel. For private channels, pass the channel ID and a valid invite URL with `/addchannel <channel_id> <invite_url>`.
6. Deploy and open the bot with `/start`.

## Commands
User:
- `/start`, `/help`, `/id`, `/mystatus`
- `/nxtlike <UID>` (requires `LIKE_API_URL`)
- `/profile <UID>` (placeholder until profile API is configured)
- `/redeem <CODE>`

Admin (IDs in `ADMIN_IDS`):
- `/addchannel @channel [invite_url]`
- `/removechannel @channel`
- `/channels`
- `/setchannel @channel`
- `/clearchannels`
- `/setjoin on|off`
- `/addpremium <user_id> <days>`
- `/removepremium <user_id>`
- `/genkey <days>`
- `/revokekey <key>`
- `/stats`
- `/broadcast <message>`

## Multiple channel examples
- Public: `/addchannel @mychannel`
- Private: `/addchannel -1001234567890 https://t.me/+inviteCode`
- Show channels: `/channels`
- Remove one: `/removechannel @mychannel`

The bot must be able to access/check channel membership. If channel checks fail, fix the channel ID/username and bot permissions before turning on force join.

## AutoLike
- Premium users can run `/autolike <UID>` to schedule one request per configured interval (default: every 24 hours).
- `/stopautolike` disables it; `/myautolike` shows status.
- Set `AUTOLIKE_INTERVAL_HOURS` to an integer of at least 1.
- AutoLike does nothing until `LIKE_API_URL` is configured. Use only a trusted API you are authorized to use; check the game's rules and API terms. Repeated requests may be rate-limited by the provider.
- The Render service uses a local SQLite database. Configure persistent storage if AutoLike schedules and subscriptions must survive redeploys.

## Security
- Never commit `.env` or bot tokens to GitHub.
- Rotate the token through BotFather if it leaks.
- SQLite is stored locally beside `database.py`; use persistent disk/storage on hosting if you need data to survive redeploys. The included Render worker configuration does not automatically provision persistent storage.
