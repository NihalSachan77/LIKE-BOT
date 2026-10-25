import os
import html
import logging
import asyncio
from datetime import datetime, timedelta, timezone
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, ContextTypes,
)
from telegram.error import TelegramError
import database as db
import requests

BOT_TOKEN = os.getenv("BOT_TOKEN", "8668815651:AAGC5ooqtmDtYHhiMVI7eXNPd4_RMUSPpms").strip()
ADMIN_IDS = {int(x) for x in os.getenv("ADMIN_IDS", "7360994054").replace(" ", "").split(",") if x.isdigit()}
DEFAULT_CHANNEL = os.getenv("DEFAULT_CHANNEL", "@trynexttime").strip()
LIKE_API_URL = os.getenv("LIKE_API_URL", "https://nihalviplike.vercel.app/like?uid={uid}&region={region}&key=Nihalsachan").strip()
FREE_DAILY_LIMIT = int(os.getenv("FREE_DAILY_LIMIT", "3"))
PREMIUM_DAILY_LIMIT = int(os.getenv("PREMIUM_DAILY_LIMIT", "50"))
AUTOLIKE_INTERVAL_HOURS = max(1, int(os.getenv("AUTOLIKE_INTERVAL_HOURS", "24")))
PORT = int(os.getenv("PORT", "10000"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("nxt-like-bot")

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❤️ Send Likes", callback_data="likes_help"),
         InlineKeyboardButton("👤 Player Profile", callback_data="profile_help")],
        [InlineKeyboardButton("💎 Premium Plans", callback_data="premium"),
         InlineKeyboardButton("📊 My Status", callback_data="status")],
        [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{DEFAULT_CHANNEL.lstrip('@')}")],
        [InlineKeyboardButton("🆘 Help", callback_data="help")]
    ])

async def force_join_ok(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    if not db.get_setting("force_join", "on") == "on":
        return True
    channels = db.list_channels()
    if not channels:
        channels = [{"channel": DEFAULT_CHANNEL, "invite": f"https://t.me/{DEFAULT_CHANNEL.lstrip('@')}"}]
    for row in channels:
        channel = row["channel"]
        try:
            member = await context.bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status in ("left", "kicked"):
                return False
        except TelegramError:
            # A channel that the bot cannot inspect should not silently block every user.
            log.warning("Unable to verify membership for channel %s", channel)
            return False
    return True

async def require_join(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user = update.effective_user
    if not user:
        return False
    if await force_join_ok(context, user.id):
        return True
    rows = db.list_channels() or [{"channel": DEFAULT_CHANNEL, "invite": f"https://t.me/{DEFAULT_CHANNEL.lstrip('@')}"}]
    buttons = []
    for i, row in enumerate(rows, 1):
        link = row["invite"] or (f"https://t.me/{row['channel'].lstrip('@')}" if row["channel"].startswith("@") else "")
        if link:
            buttons.append([InlineKeyboardButton(f"📢 Join Channel {i}", url=link)])
    buttons.append([InlineKeyboardButton("✅ Verify Membership", callback_data="verify_join")])
    markup = InlineKeyboardMarkup(buttons)
    text = "╭━━━━━━━━━━━━━━━━━━━━━━╮\n┃ 📢 CHANNEL REQUIRED\n╰━━━━━━━━━━━━━━━━━━━━━━╯\n\nJoin all required channels, then tap Verify Membership."
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(text, reply_markup=markup)
    elif update.message:
        await update.message.reply_text(text, reply_markup=markup)
    return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.upsert_user(user.id, user.username or "", user.first_name or "")
    if not await require_join(update, context):
        return
    plan = db.plan_for(user.id)
    await update.message.reply_text(
        f"╭━━━━━━━━━━━━━━━━━━━━━━╮\n┃ 👑 NXT LIKE BOT\n┃ ⚡ PREMIUM EDITION\n╰━━━━━━━━━━━━━━━━━━━━━━╯\n\n"
        f"👤 User: {user.first_name or 'Player'}\n💎 Plan: {plan.upper()}\n🌍 Region: INDIA 🇮🇳\n\n"
        "Choose an option below. Like requests need a configured, working API.",
        reply_markup=main_menu()
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = ("🤖 NXT LIKE BOT COMMANDS\n\n"
        "/start — Open menu\n/like <region> <UID> — Send likes in a group (API required)\n"
        "/profile <UID> — Player lookup (API integration required)\n/autolike <UID> — Scheduled AutoLike (premium/API required)\n/stopautolike — Stop AutoLike\n/myautolike — AutoLike status\n"
        "/mystatus — Subscription status\n/redeem <CODE> — Redeem premium key\n"
        "/id — Your Telegram ID\n/help — Help\n\n"
        "Admin:\n/addchannel <@channel> [invite_url]\n/removechannel <@channel>\n/channels\n/setchannel <@channel>\n/clearchannels\n/setjoin on|off\n"
        "/addpremium <user_id> <days>\n/removepremium <user_id>\n/genkey <days>\n/revokekey <key>\n/stats\n/broadcast <message>")
    await update.message.reply_text(text)

async def id_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Your Telegram ID: `{update.effective_user.id}`", parse_mode="Markdown")

async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    used = db.usage_today(uid)
    plan = db.plan_for(uid)
    limit = PREMIUM_DAILY_LIMIT if plan == "premium" else FREE_DAILY_LIMIT
    expiry = db.premium_expiry(uid)
    await update.message.reply_text(f"📊 YOUR STATUS\nPlan: {plan.upper()}\nToday's usage: {used}/{limit}\nPremium expiry: {expiry or '—'}")

async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /redeem <CODE>")
        return
    result = db.redeem_key(update.effective_user.id, context.args[0].strip())
    await update.message.reply_text("✅ Premium activated!" if result else "❌ Invalid, expired, or already-used key.")

def like_result_card(payload: dict) -> tuple[str, bool]:
    """Build a premium-style success/failure card from the like API response."""
    if not isinstance(payload, dict):
        payload = {}
    status = payload.get("status")
    likes_added = payload.get("LikesGivenByAPI", 0)
    likes_before = payload.get("LikesbeforeCommand", payload.get("LikesBeforeCommand", "—"))
    likes_after = payload.get("LikesafterCommand", payload.get("LikesAfterCommand", "—"))
    nickname = html.escape(str(payload.get("PlayerNickname", "Unknown")))
    player_uid = html.escape(str(payload.get("UID", "—")))
    level = html.escape(str(payload.get("Level", "—")))
    region = html.escape(str(payload.get("Region", "IND")))
    reason = html.escape(str(payload.get("message") or payload.get("error") or "The API did not confirm that likes were delivered."))
    try:
        added_count = int(likes_added or 0)
    except (TypeError, ValueError):
        added_count = 0
    success = status == 1 and added_count > 0
    if success:
        text = (
            "💎 <b>ＮＸＴ  ＬＩＫＥ  ＢＯＴ</b>\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "🎉 <b>LIKES GIVEN SUCCESSFULLY</b>\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>Player:</b> <code>{nickname}</code>\n"
            f"🆔 <b>UID:</b> <code>{player_uid}</code>\n"
            f"🌍 <b>Region:</b> <code>{region}</code>  •  🎖️ <b>Level:</b> <code>{level}</code>\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "❤️ <b>LIKE STATISTICS</b>\n"
            f"▫️ Before: <code>{html.escape(str(likes_before))}</code>\n"
            f"🟢 Likes Given: <b>+{html.escape(str(likes_added))}</b>\n"
            f"💖 After: <code>{html.escape(str(likes_after))}</code>\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "⚡ <i>Powered by @itsnihal</i>"
        )
    else:
        text = (
            "💎 <b>ＮＸＴ  ＬＩＫＥ  ＢＯＴ</b>\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "❌ <b>LIKES FAILED</b>\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"🆔 <b>UID:</b> <code>{player_uid}</code>\n"
            f"🌍 <b>Region:</b> <code>{region}</code>\n"
            f"⚠️ <b>Reason:</b> {reason}\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "🔁 <i>Please try again later.</i>\n"
            "⚡ <i>Powered by @itsnihal</i>"
        )
    return text, success


async def send_like_failure(update: Update, title: str, detail: str):
    text = (
        "💎 <b>ＮＸＴ  ＬＩＫＥ  ＢＯＴ</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"❌ <b>{html.escape(title)}</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"⚠️ {html.escape(detail)}\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "🔁 <i>Please try again later.</i>"
    )
    await update.effective_message.reply_text(text, parse_mode="HTML")


async def like_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Like requests are intentionally available only in groups/supergroups.
    chat = update.effective_chat
    if not chat or chat.type not in ("group", "supergroup"):
        await send_like_failure(update, "GROUP ONLY", "Use this command in a Telegram group: /like <region> <UID>.")
        return

    user_id = update.effective_user.id
    if not await require_join(update, context):
        return
    if len(context.args) != 2:
        await send_like_failure(update, "INVALID FORMAT", "Use /like <region> <UID> — example: /like ind 15787042719.")
        return

    region = context.args[0].strip().lower()
    player_uid = context.args[1].strip()
    allowed_regions = {"ind", "br", "sg", "id", "th", "vn", "tw", "me", "cis", "eu", "na", "sac", "pk", "bd"}
    if region not in allowed_regions:
        await send_like_failure(update, "INVALID REGION", "Use a supported region code, for example: ind, br, sg, id, me, or eu.")
        return
    if not player_uid.isdigit():
        await send_like_failure(update, "INVALID UID", "The player UID must contain digits only.")
        return
    plan = db.plan_for(user_id)
    limit = PREMIUM_DAILY_LIMIT if plan == "premium" else FREE_DAILY_LIMIT
    if db.usage_today(user_id) >= limit:
        await send_like_failure(update, "DAILY LIMIT REACHED", f"You have used {limit} requests today. Try again tomorrow or redeem a premium key.")
        return
    if not LIKE_API_URL:
        await send_like_failure(update, "API NOT CONFIGURED", "The likes API is not configured.")
        return

    progress = await update.effective_message.reply_text(
        "💎 <b>ＮＸＴ  ＬＩＫＥ  ＢＯＴ</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "⏳ <b>PROCESSING LIKE REQUEST</b>\n"
        "🔎 Contacting the likes API…",
        parse_mode="HTML"
    )
    try:
        url = LIKE_API_URL.format(uid=player_uid, region=region)
        response = await asyncio.to_thread(requests.get, url, timeout=12)
        if response.status_code != 200:
            await progress.edit_text(
                "💎 <b>ＮＸＴ  ＬＩＫＥ  ＢＯＴ</b>\n"
                "━━━━━━━━━━━━━━━━━━\n"
                "❌ <b>LIKES FAILED</b>\n"
                f"⚠️ API returned HTTP <code>{response.status_code}</code>.\n"
                "🔁 Please try again later.",
                parse_mode="HTML"
            )
            return
        try:
            payload = response.json()
        except ValueError:
            await progress.edit_text(
                "💎 <b>ＮＸＴ  Ｌ𝗜𝗞𝗘 𝗕𝗢𝗧</b>\n"
                "━━━━━━━━━━━━━━━━━━\n"
                "❌ <b>LIKES FAILED</b>\n"
                "⚠️ The API returned an invalid response.\n"
                "🔁 Please try again later.",
                parse_mode="HTML"
            )
            return
        card, success = like_result_card(payload)
        if success:
            db.record_usage(user_id)
        await progress.edit_text(card, parse_mode="HTML")
    except Exception as exc:
        log.exception("Like API request failed")
        try:
            await progress.edit_text(
                "💎 <b>ＮＸＴ  ＬＩＫＥ  ＢＯＴ</b>\n"
                "━━━━━━━━━━━━━━━━━━\n"
                "❌ <b>LIKES FAILED</b>\n"
                f"⚠️ Request error: <code>{html.escape(type(exc).__name__)}</code>\n"
                "🔁 Please try again later.",
                parse_mode="HTML"
            )
        except TelegramError:
            await send_like_failure(update, "LIKES FAILED", f"Request error: {type(exc).__name__}")

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Usage: /profile <PLAYER_UID>")
        return
    await update.message.reply_text("⚠️ Player profile lookup is not configured. Add a trusted profile API endpoint before using this command.")

async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    data = q.data or ""
    if data == "verify_join":
        if await force_join_ok(context, q.from_user.id):
            await q.answer("Membership verified!", show_alert=True)
            await q.message.reply_text("✅ Verified. Send /start to open the menu.")
        else:
            await q.answer("Please join every required channel first.", show_alert=True)
    elif data == "likes_help":
        await q.answer()
        await q.message.reply_text("Use /like <region> <UID> in a Telegram group, for example /like ind 15787042719.")
    elif data == "profile_help":
        await q.answer()
        await q.message.reply_text("Use /profile <UID>. Profile API integration is not configured yet.")
    elif data == "premium":
        await q.answer()
        await q.message.reply_text("💎 Premium: higher daily request limit. Ask the bot administrator for a redeem key.")
    elif data == "status":
        await q.answer()
        await status_cmd_from_callback(q, context)
    elif data == "help":
        await q.answer()
        await q.message.reply_text("Commands: /like <region> <UID> (group only), /profile <UID>, /mystatus, /redeem <CODE>, /help")

async def status_cmd_from_callback(q, context):
    uid = q.from_user.id
    plan = db.plan_for(uid)
    used = db.usage_today(uid)
    limit = PREMIUM_DAILY_LIMIT if plan == "premium" else FREE_DAILY_LIMIT
    await q.message.reply_text(f"📊 Plan: {plan.upper()}\nToday's usage: {used}/{limit}")

def admin_only(update: Update) -> bool:
    return bool(update.effective_user and is_admin(update.effective_user.id))

async def addchannel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        await update.message.reply_text("⛔ Admin only."); return
    if not context.args:
        await update.message.reply_text("Usage: /addchannel @channel [invite_url]"); return
    channel = context.args[0]
    invite = context.args[1] if len(context.args) > 1 else (f"https://t.me/{channel.lstrip('@')}" if channel.startswith("@") else "")
    db.add_channel(channel, invite)
    await update.message.reply_text(f"✅ Added channel: {channel}")

async def removechannel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        await update.message.reply_text("⛔ Admin only."); return
    if not context.args:
        await update.message.reply_text("Usage: /removechannel @channel"); return
    db.remove_channel(context.args[0])
    await update.message.reply_text("✅ Channel removed if it existed.")

async def channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        await update.message.reply_text("⛔ Admin only."); return
    rows = db.list_channels()
    if not rows:
        await update.message.reply_text("No extra channels configured. Default channel is used.")
        return
    await update.message.reply_text("📢 Required channels:\n" + "\n".join(f"{i}. {r['channel']} — {r['invite'] or 'no invite link'}" for i, r in enumerate(rows, 1)))

async def setchannel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        await update.message.reply_text("⛔ Admin only."); return
    if not context.args or not context.args[0].startswith("@"):
        await update.message.reply_text("Usage: /setchannel @channel"); return
    global DEFAULT_CHANNEL
    DEFAULT_CHANNEL = context.args[0]
    db.set_setting("default_channel", DEFAULT_CHANNEL)
    if not db.list_channels():
        db.add_channel(DEFAULT_CHANNEL, f"https://t.me/{DEFAULT_CHANNEL.lstrip('@')}")
    await update.message.reply_text(f"✅ Default channel set to {DEFAULT_CHANNEL}")

async def clearchannels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        await update.message.reply_text("⛔ Admin only."); return
    db.clear_channels()
    await update.message.reply_text("✅ Extra channel list cleared. The default channel will be used.")

async def setjoin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        await update.message.reply_text("⛔ Admin only."); return
    if not context.args or context.args[0].lower() not in ("on", "off"):
        await update.message.reply_text("Usage: /setjoin on|off"); return
    db.set_setting("force_join", context.args[0].lower())
    await update.message.reply_text(f"✅ Force join {context.args[0].upper()}.")

async def addpremium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        await update.message.reply_text("⛔ Admin only."); return
    if len(context.args) != 2 or not all(x.isdigit() for x in context.args):
        await update.message.reply_text("Usage: /addpremium <user_id> <days>"); return
    db.grant_premium(int(context.args[0]), int(context.args[1]))
    await update.message.reply_text("✅ Premium granted.")

async def removepremium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        await update.message.reply_text("⛔ Admin only."); return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Usage: /removepremium <user_id>"); return
    db.remove_premium(int(context.args[0]))
    await update.message.reply_text("✅ Premium removed.")

async def genkey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        await update.message.reply_text("⛔ Admin only."); return
    if not context.args or not context.args[0].isdigit() or int(context.args[0]) < 1:
        await update.message.reply_text("Usage: /genkey <days>"); return
    key = db.generate_key(int(context.args[0]))
    await update.message.reply_text(f"🎟️ Premium redeem key:\n`{key}`", parse_mode="Markdown")

async def revokekey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        await update.message.reply_text("⛔ Admin only."); return
    if not context.args:
        await update.message.reply_text("Usage: /revokekey <KEY>"); return
    db.revoke_key(context.args[0])
    await update.message.reply_text("✅ Key revoked if it existed.")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        await update.message.reply_text("⛔ Admin only."); return
    await update.message.reply_text(f"📊 Users: {db.user_count()}\nActive premium: {db.premium_count()}\nChannels: {len(db.list_channels())}\nForce join: {db.get_setting('force_join', 'on')}")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        await update.message.reply_text("⛔ Admin only."); return
    message = update.message.text.partition(" ")[2].strip()
    if not message:
        await update.message.reply_text("Usage: /broadcast <message>"); return
    sent, failed = 0, 0
    for user_id in db.all_user_ids():
        try:
            await context.bot.send_message(user_id, message)
            sent += 1
        except TelegramError:
            failed += 1
    await update.message.reply_text(f"📢 Broadcast complete. Sent: {sent}; failed: {failed}")

async def autolike_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await require_join(update, context):
        return
    if not LIKE_API_URL:
        await update.message.reply_text("⚠️ AutoLike needs a working authorized likes API. Set LIKE_API_URL in Render first.")
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Usage: /autolike <PLAYER_UID>\nAutoLike sends a request on a scheduled interval; default is every 24 hours.")
        return
    if db.plan_for(user_id) != "premium":
        await update.message.reply_text("💎 AutoLike is a premium feature. Redeem a key or ask an admin for access.")
        return
    db.set_autolike(user_id, context.args[0])
    await update.message.reply_text(f"✅ AutoLike enabled for UID {context.args[0]}. The bot will make one API request every {AUTOLIKE_INTERVAL_HOURS} hour(s), while the API is configured. Use /stopautolike to stop it.")

async def stopautolike_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.stop_autolike(update.effective_user.id)
    await update.message.reply_text("🛑 AutoLike stopped (if it was enabled).")

async def myautolike_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    row = db.get_autolike(update.effective_user.id)
    if not row or not row["enabled"]:
        await update.message.reply_text("AutoLike is currently OFF. Use /autolike <UID> to enable it (premium required).")
    else:
        await update.message.reply_text(f"❤️ AutoLike: ON\nPlayer UID: {row['player_uid']}\nInterval: every {AUTOLIKE_INTERVAL_HOURS} hour(s)\nLast run: {row['last_run'] or 'Not run yet'}")

async def autolike_worker(context: ContextTypes.DEFAULT_TYPE):
    if not LIKE_API_URL:
        return
    now = datetime.now(timezone.utc)
    for row in db.active_autolikes():
        try:
            # Only premium users can keep an AutoLike schedule active.
            if db.plan_for(row["user_id"]) != "premium":
                db.stop_autolike(row["user_id"])
                continue
            last = row.get("last_run")
            if last:
                try:
                    if now - datetime.fromisoformat(last) < timedelta(hours=AUTOLIKE_INTERVAL_HOURS):
                        continue
                except ValueError:
                    pass
            url = LIKE_API_URL.format(uid=row["player_uid"], region="ind")
            response = await asyncio.to_thread(requests.get, url, timeout=12)
            if response.status_code == 200:
                db.record_usage(row["user_id"])
                db.mark_autolike_run(row["user_id"])
            else:
                log.warning("AutoLike API returned HTTP %s for user %s", response.status_code, row["user_id"])
        except Exception:
            log.exception("AutoLike worker failed for user %s", row["user_id"])

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    log.exception("Unhandled bot exception", exc_info=context.error)

def main():
    if not BOT_TOKEN:
        raise SystemExit("Set BOT_TOKEN in environment variables.")
    db.init_db()
    if DEFAULT_CHANNEL and not db.list_channels():
        db.add_channel(DEFAULT_CHANNEL, f"https://t.me/{DEFAULT_CHANNEL.lstrip('@')}")
    app = Application.builder().token(BOT_TOKEN).build()
    handlers = [
        CommandHandler("start", start), CommandHandler("help", help_cmd),
        CommandHandler("id", id_cmd), CommandHandler("mystatus", status_cmd),
        CommandHandler("redeem", redeem), CommandHandler("like", like_cmd),
        CommandHandler("profile", profile), CommandHandler("autolike", autolike_cmd),
        CommandHandler("stopautolike", stopautolike_cmd), CommandHandler("myautolike", myautolike_cmd),
        CommandHandler("addchannel", addchannel),
        CommandHandler("removechannel", removechannel), CommandHandler("channels", channels),
        CommandHandler("setchannel", setchannel), CommandHandler("clearchannels", clearchannels),
        CommandHandler("setjoin", setjoin), CommandHandler("addpremium", addpremium),
        CommandHandler("removepremium", removepremium), CommandHandler("genkey", genkey),
        CommandHandler("revokekey", revokekey), CommandHandler("stats", stats),
        CommandHandler("broadcast", broadcast), CallbackQueryHandler(callback),
    ]
    for h in handlers:
        app.add_handler(h)
    app.add_error_handler(error_handler)
    app.job_queue.run_repeating(autolike_worker, interval=300, first=30, name="autolike-worker")
    log.info("Starting NXT Like Bot polling")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
