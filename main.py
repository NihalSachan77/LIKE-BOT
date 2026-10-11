#━━━━━━━━━━━━━━━━━━━
#𝗠𝗔𝗗𝗘 𝗕𝗬 NIHAL LIKE BOT
#𝗣𝗥𝗢𝗝𝗘𝗖𝗧𝗦 NXT
#𝗠𝗬 𝗨𝗦𝗘𝗥 : @itsnihal
#━━━━━━━━━━━━━━━━━━━
import json
import asyncio
import nest_asyncio
from datetime import datetime, timedelta
from pytz import timezone
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    ChatMemberHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
import logging
import os
import sys

# ✅ Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ================= 👑 CONFIG =================

CHANNEL_1 = "@trynexttime"
CHANNEL_2 = "@trynexttime"
BOT_TOKEN = "8668815651:AAGC5ooqtmDtYHhiMVI7eXNPd4_RMUSPpms"
OWNER_IDS = [7360994054,6515708509]  # Super Admins (Can't be removed)
BOT_ENABLED = True

ALLOWED_GROUP_IDS = [
    -1003943676726
]

REPORT_CHAT_ID = -1003943676726

API_URL = "https://nihalviplike.vercel.app/like?uid={uid}&region={region}&key=Nihalsachan"
DEMO_API_URL = "https://nihalviplike.vercel.app/like?uid={uid}&region={region}&key=Nihalsachan"

# ✅ FIXED: Auto-like time set to 4:00 AM
SEND_LIKE_TIME = "04:00 AM"
DATA_FILE = "autolike_data.json"
GROUP_DATA_FILE = "allowed_groups.json"
ADMIN_DATA_FILE = "admin_data.json"
TIMEZONE = timezone("Asia/Kolkata")

# USER DAILY LIMIT
USER_DAILY_LIMIT = 1
USER_USAGE = {}

# ================= 📁 ADMIN DATA MANAGEMENT =================

def load_admin_data():
    """Load admin data from file"""
    try:
        with open(ADMIN_DATA_FILE, "r") as f:
            data = json.load(f)
            return data
    except:
        return {"admins": [], "admin_limits": {}}

def save_admin_data(data):
    """Save admin data to file"""
    with open(ADMIN_DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def is_admin(user_id):
    """Check if user is an admin (including owner)"""
    if user_id in OWNER_IDS:
        return True
    admin_data = load_admin_data()
    return user_id in admin_data.get("admins", [])

def get_admin_limit(user_id):
    """Get admin's daily limit"""
    if user_id in OWNER_IDS:
        return 999999
    admin_data = load_admin_data()
    limits = admin_data.get("admin_limits", {})
    return limits.get(str(user_id), USER_DAILY_LIMIT)

def set_admin_limit(user_id, limit):
    """Set admin's daily limit"""
    admin_data = load_admin_data()
    if "admin_limits" not in admin_data:
        admin_data["admin_limits"] = {}
    admin_data["admin_limits"][str(user_id)] = limit
    save_admin_data(admin_data)

def add_admin(user_id):
    """Add a new admin"""
    admin_data = load_admin_data()
    if user_id not in admin_data["admins"]:
        admin_data["admins"].append(user_id)
        save_admin_data(admin_data)
        return True
    return False

def remove_admin(user_id):
    """Remove an admin"""
    if user_id in OWNER_IDS:
        return False
    admin_data = load_admin_data()
    if user_id in admin_data["admins"]:
        admin_data["admins"].remove(user_id)
        save_admin_data(admin_data)
        return True
    return False

def get_all_admins():
    """Get list of all admins with details"""
    admin_data = load_admin_data()
    admins = []
    
    for owner_id in OWNER_IDS:
        admins.append({
            "id": owner_id,
            "type": "👑 Owner",
            "limit": "∞",
            "can_autolike": True
        })
    
    for admin_id in admin_data.get("admins", []):
        limit = admin_data.get("admin_limits", {}).get(str(admin_id), USER_DAILY_LIMIT)
        admins.append({
            "id": admin_id,
            "type": "🛡️ Admin",
            "limit": limit,
            "can_autolike": True
        })
    
    return admins

# ================= 📁 GROUP DATA MANAGEMENT =================

def load_group_data():
    """Load allowed groups from file"""
    try:
        with open(GROUP_DATA_FILE, "r") as f:
            data = json.load(f)
            return data.get("groups", [])
    except:
        return []

def save_group_data(groups):
    """Save allowed groups to file"""
    with open(GROUP_DATA_FILE, "w") as f:
        json.dump({"groups": groups}, f, indent=4)

def sync_allowed_groups():
    """Sync ALLOWED_GROUP_IDS with saved data"""
    global ALLOWED_GROUP_IDS
    saved_groups = load_group_data()
    if saved_groups:
        ALLOWED_GROUP_IDS = saved_groups
    return ALLOWED_GROUP_IDS

# ================= ⚙ BASIC =================

async def is_owner(update: Update):
    return update.effective_user.id in OWNER_IDS

async def is_admin_or_owner(update: Update):
    """Check if user is admin or owner"""
    user_id = update.effective_user.id
    return user_id in OWNER_IDS or is_admin(user_id)

def parse_time_str(t):
    dt = datetime.strptime(t.strip().upper(), "%I:%M %p")
    return dt.hour, dt.minute

SEND_HOUR, SEND_MINUTE = parse_time_str(SEND_LIKE_TIME)

def today_str():
    return datetime.now(TIMEZONE).strftime("%Y-%m-%d")
    
def hide_uid(uid):
    uid = str(uid)
    if len(uid) <= 7:
        return uid
    return uid[:4] + "****" + uid[-3:]

def is_group_allowed(chat_id):
    """Check if group ID is in allowed list"""
    if chat_id in ALLOWED_GROUP_IDS:
        return True
    if chat_id < 0 and abs(chat_id) in ALLOWED_GROUP_IDS:
        return True
    if chat_id > 0 and -chat_id in ALLOWED_GROUP_IDS:
        return True
    return False

# ================= 💾 DATA =================

def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
    except:
        data = {}
    data.setdefault("last_run_date", None)
    data.setdefault("uids", [])
    data.setdefault("total_likes_given", 0)
    for entry in data["uids"]:
        if "tg_id" not in entry:
            entry["tg_id"] = None
        if "likes_given" not in entry:
            entry["likes_given"] = 0
    return data

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# ================= 🔒 GROUP LOCK & AUTO-LEAVE =================

async def group_only(update: Update):
    """Check if command is from allowed group"""
    chat = update.effective_chat
    
    if chat.type == "private":
        if update.message and update.message.text:
            command = update.message.text.split()[0].lower()
            if command in ["/help", "/start", "/getid", "/mygroups", "/addgroup", "/removegroup", "/groupstats", "/autolikeinfo", "/admins", "/addadmin", "/removeadmin", "/setadminlimit"]:
                return True
        await update.message.reply_text(
            "🚫 This bot works only in the official group.\n\n👉 Join here:\nhttps://t.me/+Kv1fDgTnuVU5YTBl"
        )
        return False
    
    chat_id = chat.id
    print(f"📌 Command from group: {chat_id} ({chat.title})")
    
    if not is_group_allowed(chat_id):
        await update.message.reply_text(
            f"⛔ This bot is not allowed in this group.\n\n"
            f"📌 Your Group ID: {chat_id}\n"
            f"👑 Official Group:\nhttps://t.me/+Kv1fDgTnuVU5YTBl"
        )
        return False
    
    return True

async def auto_leave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Leave groups that are not in the allowed list"""
    try:
        if not update.my_chat_member:
            return
            
        new_status = update.my_chat_member.new_chat_member.status
        old_status = update.my_chat_member.old_chat_member.status
        
        if (old_status in ["left", "kicked", "restricted"] and 
            new_status in ["member", "administrator"]):
            
            chat = update.effective_chat
            
            if chat.type in ["group", "supergroup"]:
                if not is_group_allowed(chat.id):
                    try:
                        await context.bot.send_message(
                            chat_id=chat.id,
                            text="⛔ This bot is not allowed in this group.\n\n👉 Official Group:\nhttps://t.me/trynexttime\n\n👑 NIHAL LIKE BOT"
                        )
                    except:
                        pass
                    
                    await asyncio.sleep(1)
                    await context.bot.leave_chat(chat.id)
                    print(f"🚪 Left unauthorized group: {chat.id} ({chat.title})")
                else:
                    print(f"✅ Bot added to allowed group: {chat.id} ({chat.title})")
    except Exception as e:
        print(f"⚠️ Auto-leave error: {e}")

# ✅ MESSAGE DELETION COMPLETELY DISABLED
async def delete_non_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """⚠️ DELETION DISABLED - This function does nothing now"""
    return

# ================= 🌐 API =================

async def call_api(session, uid, region, api_url=None):
    """Call API with optional custom URL"""
    if api_url is None:
        api_url = API_URL
    try:
        async with session.get(api_url.format(uid=uid, region=region), timeout=35) as r:
            return await r.json()
    except Exception as e:
        print(f"API Error: {e}")
        return None

# ================= ❤️ SEND LIKE (FULLY FIXED) =================

async def send_like(app, session, entry, remaining):
    uid = entry["uid"]
    region = entry["region"]
    tg_id = entry.get("tg_id")

    print(f"📤 Sending like to UID: {uid} (Region: {region})")
    
    js = await call_api(session, uid, region)

    if not js:
        fail_msg = f"❌ AUTO LIKE FAILED\n\nUID : {hide_uid(uid)}\n\nRegion : {region.upper()}\n\n👑 NIHAL LIKE BOT"
        try:
            await app.bot.send_message(chat_id=REPORT_CHAT_ID, text=fail_msg)
        except:
            pass
        if tg_id:
            try:
                await app.bot.send_message(chat_id=tg_id, text=fail_msg)
            except:
                pass
        return False

    likes_given = int(js.get("LikesGivenByAPI", 0))
    after = int(js.get("LikesafterCommand", 0))
    before = int(js.get("LikesbeforeCommand", after - likes_given))
    status = js.get("status", "N/A")
    name = js.get("PlayerNickname", "N/A")

    expire_dt = datetime.fromisoformat(entry["expire"])
    days_left = max(0, (expire_dt - datetime.now(TIMEZONE)).days)

    total_days = entry.get("days", 60)
    remaining = f"{remaining}/60"
    used_days = max(0, total_days - days_left)

    if likes_given > 0:
        entry["likes_given"] = entry.get("likes_given", 0) + likes_given
        print(f"✅ Success: {likes_given} likes given to {uid}")
    else:
        print(f"❌ Failed: No likes given to {uid}")

    if likes_given > 0:
        msg = (
            f"AUTO LIKE SUCCESS ({SEND_LIKE_TIME})\n\n"
            f"Player: {name}\n"
            f"UID: {hide_uid(uid)}\n"
            f"Region: {region.upper()}\n\n"
            f"Like Before: {before}\n"
            f"Like After: {after}\n"
            f"Like Given: {likes_given}\n\n"
            f"Status: {status}\n"
            f"Plan: {total_days} Days\n"
            f"Used: {used_days} Days\n"
            f"Remaining: {remaining}\n\n"
            f"👑 NIHAL LIKE BOT (@itsnihal)"
        )
    else:
        msg = (
            f"LIKE LIMIT / FAILED\n\n"
            f"Player: {name}\n"
            f"UID: {hide_uid(uid)}\n"
            f"Region: {region.upper()}\n"
            f"Current: {after}\n"
            f"Status: {status}\n\n"
            f"👑 NIHAL LIKE BOT (@itsnihal)"
        )

    keyboard = [
        [
            InlineKeyboardButton("💰 Buy Autolike", url="https://t.me/itsnihal"),
            InlineKeyboardButton("📢 Join Channel", url="https://t.me/trynexttime")
        ]
    ]

    # ✅ Send to report chat with error handling
    try:
        await app.bot.send_message(
            chat_id=REPORT_CHAT_ID,
            text=msg,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        print(f"Report send error: {e}")
        try:
            await app.bot.send_message(
                chat_id=REPORT_CHAT_ID,
                text=msg
            )
        except:
            pass
    
    # ✅ Send to user with error handling
    if tg_id:
        try:
            await app.bot.send_message(
                chat_id=tg_id,
                text=msg,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as e:
            print(f"User send error: {e}")
            try:
                await app.bot.send_message(
                    chat_id=tg_id,
                    text=msg
                )
            except:
                pass

    return likes_given > 0

# ================= ⏰ AUTO PROCESS =================

async def perform_auto_like(app, manual=False):
    print("🔄 perform_auto_like started (manual=" + str(manual) + ")")
    data = load_data()
    today = today_str()

    if not manual and data.get("last_run_date") == today:
        print("✅ Already ran today, skipping")
        return

    if not data["uids"]:
        print("📭 No UIDs in database")
        try:
            await app.bot.send_message(
                chat_id=REPORT_CHAT_ID,
                text="📭 No auto-like entries found. Add some using /autolike"
            )
        except:
            pass
        return

    total = success = failed = 0
    expired = 0
    total_likes = 0
    customer = 1
    valid = []
    now = datetime.now(TIMEZONE)

    print(f"📊 Total UIDs to process: {len(data['uids'])}")

    async with aiohttp.ClientSession() as session:
        for entry in data["uids"]:
            expire_date = datetime.fromisoformat(entry["expire"])
            if now > expire_date:
                expired += 1
                print(f"⏰ UID {entry['uid']} expired")
                continue
            valid.append(entry)
            result = await send_like(app, session, entry, customer)
            customer += 1
            total += 1
            success += int(result)
            failed += int(not result)
            if result:
                total_likes += entry.get("likes_given", 0)
            await asyncio.sleep(3)

    data["uids"] = valid

    if not manual:
        data["last_run_date"] = today

    data["total_likes_given"] = data.get("total_likes_given", 0) + total_likes

    save_data(data)

    summary = (
        f"AUTO LIKE COMPLETED\n\n"
        f"Total : {total}\n"
        f"Success : {success}\n"
        f"Failed : {failed}\n"
        f"Expired Today : {expired}\n"
        f"Total Likes Given : {data['total_likes_given']}\n"
        f"Remaining : {len(valid)} active\n\n"
        f"👑 NIHAL LIKE BOT"
    )
    keyboard = [
        [
            InlineKeyboardButton("💰 Buy Autolike", url="https://t.me/itsnihal"),
            InlineKeyboardButton("📢 Join Channel", url="https://t.me/trynexttime")
        ]
    ]

    try:
        await app.bot.send_message(
            chat_id=REPORT_CHAT_ID,
            text=summary,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        print(f"Summary send error: {e}")
        try:
            await app.bot.send_message(
                chat_id=REPORT_CHAT_ID,
                text=summary
            )
        except:
            pass
            
    print(summary)

# ================= /runall =================

async def runall_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await group_only(update):
        return
    if not await is_owner(update):
        await update.message.reply_text("🚫 Owner Only")
        return

    await update.message.reply_text("🔄 Manual auto-like triggered...")
    await perform_auto_like(context.application, manual=True)

# ================= /autolike =================

async def autolike_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await group_only(update):
        return
    if not await is_owner(update):
        await update.message.reply_text("🚫 Owner Only")
        return

    if len(context.args) != 4:
        await update.message.reply_text(
            "❌ Usage: /autolike <region> <uid> <days> <tg_id>\n\nExample: /autolike me 1234567890 30 7520194195"
        )
        return

    region, uid, days_str, tg_id_str = context.args

    try:
        days = int(days_str)
        if days <= 0 or days > 3650:
            raise ValueError
    except:
        await update.message.reply_text("❌ Days must be a positive integer (1 to 3650)")
        return

    try:
        tg_id = int(tg_id_str)
    except:
        await update.message.reply_text("❌ TG ID must be a valid integer")
        return

    wait_msg = await update.message.reply_text("🔄 Verifying UID...")

    data = load_data()
    for x in data["uids"]:
        if x["uid"] == uid:
            await wait_msg.edit_text("⚠️ UID Already Added")
            return

    async with aiohttp.ClientSession() as session:
        js = await call_api(session, uid, region)

    if not js:
        await wait_msg.edit_text(f"❌ UID Verification Failed\n\nUID: {uid}\nRegion: {region.upper()}")
        return

    player_name = js.get('PlayerNickname', 'N/A')
    expire_date = datetime.now(TIMEZONE) + timedelta(days=days)

    user_name = str(tg_id)
    try:
        chat = await context.bot.get_chat(tg_id)
        user_name = chat.first_name or chat.username or str(tg_id)
        if chat.last_name:
            user_name = f"{chat.first_name} {chat.last_name}".strip()
    except Exception as e:
        print(f"Could not fetch name for {tg_id}: {e}")

    data["uids"].append({
        "uid": uid,
        "region": region.lower(),
        "expire": expire_date.isoformat(),
        "days": days,
        "tg_id": tg_id,
        "likes_given": 0
    })
    save_data(data)

    keyboard = [
        [
            InlineKeyboardButton("💰 Buy Autolike", url="https://t.me/itsnihal"),
            InlineKeyboardButton("📢 Join Channel", url="https://t.me/trynexttime")
        ]
    ]

    await wait_msg.edit_text(
        f"✅ AUTO LIKE ADDED\n\n"
        f"Player : {player_name}\n"
        f"UID : {hide_uid(uid)}\n"
        f"Region : {region.upper()}\n"
        f"Days : {days}\n"
        f"Name : {user_name}\n\n"
        f"Auto-like will run daily at {SEND_LIKE_TIME}\n\n"
        f"👑 NIHAL LIKE BOT",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    dm_text = (
        f"✅ YOUR AUTO-LIKE HAS BEEN ACTIVATED ✅\n\n"
        f"Player : {player_name}\n"
        f"UID : {hide_uid(uid)}\n"
        f"Region : {region.upper()}\n"
        f"Days : {days}\n"
        f"Expiry : {expire_date.strftime('%Y-%m-%d')}\n\n"
        f"The bot will like your UID every day at {SEND_LIKE_TIME}.\n\n"
        f"👑 NIHAL LIKE BOT"
    )
    try:
        keyboard = [
            [InlineKeyboardButton("💰 Buy Autolike", url="https://t.me/itsnihal")]
        ]

        await context.bot.send_message(
            chat_id=tg_id,
            text=dm_text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        print(f"Failed to send DM to {tg_id}: {e}")

# ================= /extend =================

async def extend_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await group_only(update):
        return
    if not await is_owner(update):
        await update.message.reply_text("🚫 Owner Only")
        return
    if len(context.args) != 2:
        await update.message.reply_text("Usage: /extend <uid> <additional_days>")
        return

    uid, days_str = context.args
    try:
        extra_days = int(days_str)
        if extra_days <= 0:
            raise ValueError
    except:
        await update.message.reply_text("❌ Days must be a positive integer")
        return

    data = load_data()
    found = None
    for entry in data["uids"]:
        if entry["uid"] == uid:
            found = entry
            break
    if not found:
        await update.message.reply_text("❌ UID not found in database.")
        return

    old_expire = datetime.fromisoformat(found["expire"])
    new_expire = old_expire + timedelta(days=extra_days)
    found["expire"] = new_expire.isoformat()
    save_data(data)

    await update.message.reply_text(f"✅ Extended UID {uid} by {extra_days} days.\nNew expiry: {new_expire.strftime('%Y-%m-%d')}")

    tg_id = found.get("tg_id")
    if tg_id:
        try:
            await context.bot.send_message(
                chat_id=tg_id,
                text=f"🔔 Your auto-like for UID {uid} has been extended by {extra_days} days.\nNew expiry: {new_expire.strftime('%Y-%m-%d')}\n\n👑 NIHAL LIKE BOT "
            )
        except Exception as e:
            print(f"Failed to DM {tg_id}: {e}")

# ================= /extendall =================

async def extendall_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await group_only(update):
        return
    if not await is_owner(update):
        await update.message.reply_text("🚫 Owner Only")
        return
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /extendall <days>\n\nExample: /extendall 1  (adds 1 day to all active UIDs and notifies them)")
        return

    days_str = context.args[0]
    try:
        extra_days = int(days_str)
        if extra_days <= 0:
            raise ValueError
    except:
        await update.message.reply_text("❌ Days must be a positive integer (1, 2, 3, ...)")
        return

    data = load_data()
    now = datetime.now(TIMEZONE)
    updated_entries = []

    for entry in data["uids"]:
        expire_dt = datetime.fromisoformat(entry["expire"])
        if expire_dt > now:
            old_expire = expire_dt
            new_expire = expire_dt + timedelta(days=extra_days)
            entry["expire"] = new_expire.isoformat()
            updated_entries.append({
                "uid": entry["uid"],
                "region": entry["region"],
                "new_expire": new_expire,
                "tg_id": entry.get("tg_id"),
                "old_expire": old_expire
            })

    if not updated_entries:
        await update.message.reply_text("⚠️ No active UIDs found to extend.")
        return

    save_data(data)

    await update.message.reply_text(
        f"✅ Extended {len(updated_entries)} active UID(s) by {extra_days} day(s).\nNow notifying each user via DM..."
    )

    notify_success = 0
    for entry in updated_entries:
        tg_id = entry["tg_id"]
        if tg_id:
            try:
                await context.bot.send_message(
                    chat_id=tg_id,
                    text=(
                        f"🔔 Your Auto-Like has been extended!\n\n"
                        f"UID: {hide_uid(entry['uid'])}\n"
                        f"Region: {entry['region'].upper()}\n"
                        f"Old Expiry: {entry['old_expire'].strftime('%Y-%m-%d')}\n"
                        f"New Expiry: {entry['new_expire'].strftime('%Y-%m-%d')}\n"
                        f"Added: {extra_days} day(s)\n\n"
                        f"👑 NIHAL LIKE BOT"
                    )
                )
                notify_success += 1
                await asyncio.sleep(0.5)
            except Exception as e:
                print(f"Failed to notify tg_id {tg_id}: {e}")

    await update.message.reply_text(
        f"📨 Notified {notify_success} / {len(updated_entries)} users successfully.\n\n👑 NIHAL LIKE BOT "
    )

# ================= /state =================

async def state_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await group_only(update):
        return
    if not await is_owner(update):
        await update.message.reply_text("🚫 Owner Only")
        return

    data = load_data()
    if not data["uids"]:
        await update.message.reply_text("📭 No Active Entries")
        return

    now = datetime.now(TIMEZONE)
    msg = "📋 ACTIVE AUTO LIKE STATE\n\n"
    count = 0
    for entry in data["uids"]:
        expire_dt = datetime.fromisoformat(entry["expire"])
        if now > expire_dt:
            continue
        count += 1
        days_left = max(0, (expire_dt - now).days)
        tg_name = "Unknown"
        try:
            tg_id = entry.get("tg_id")
            if tg_id:
                chat = await context.bot.get_chat(tg_id)
                tg_name = f"@{chat.username}" if chat.username else (chat.first_name or "Unknown")
        except:
            pass
        msg += f"{count}. UID : {hide_uid(entry['uid'])}\n   Region : {entry['region'].upper()}\n   Days Left : {days_left}\n   User : {tg_name}\n\n"
    msg += "👑 NIHAL LIKE BOT (@itsnihal)"
    await update.message.reply_text(msg)

# ================= /list =================

async def list_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await group_only(update):
        return
    if not await is_owner(update):
        await update.message.reply_text("🚫 Owner Only")
        return
    data = load_data()
    if not data["uids"]:
        await update.message.reply_text("📭 No active auto likes")
        return
    now = datetime.now(TIMEZONE)
    msg = "📋 ACTIVE AUTO LIKE LIST\n\n"
    count = 0
    for entry in data["uids"]:
        expire_dt = datetime.fromisoformat(entry["expire"])
        if now > expire_dt:
            continue
        count += 1
        days_left = max(0, (expire_dt - now).days)
        msg += f"{count}. UID : {hide_uid(entry['uid'])}\n   {entry['region'].upper()}\n   Days Left : {days_left}\n\n"
    msg += "👑 NIHAL LIKE BOT (@itsnihal)"
    await update.message.reply_text(msg)

# ================= /remove =================

async def remove_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await group_only(update):
        return
    if not await is_owner(update):
        await update.message.reply_text("🚫 Owner Only")
        return
    if not context.args:
        await update.message.reply_text("Usage: /remove <uid>")
        return
    uid = context.args[0]
    data = load_data()
    data["uids"] = [x for x in data["uids"] if x["uid"] != uid]
    save_data(data)
    await update.message.reply_text(f"🗑 Removed: {uid}")

# ================= 📱 /like COMMAND =================

async def like_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Demo like command - Same as /vip but uses different API"""
    if not BOT_ENABLED:
        await update.message.reply_text(
            "🔴 Bot is currently OFF.\n\nPlease wait until the owner turns it ON."
        )
        return
    
    if not await group_only(update):
        return
    
    user_id = update.effective_user.id
    is_admin_user = await is_admin_or_owner(update)
    
    if not is_admin_user:
        try:
            m1 = await context.bot.get_chat_member(CHANNEL_1, user_id)
            m2 = await context.bot.get_chat_member(CHANNEL_2, user_id)

            ok1 = m1.status in ["member", "administrator", "creator"]
            ok2 = m2.status in ["member", "administrator", "creator"]

            if not (ok1 and ok2):
                keyboard = [
                    [InlineKeyboardButton("📢 Join Channel 1", url="https://t.me/trynexttime")],
                    [InlineKeyboardButton("📢 Join Channel 2", url="https://t.me/trynexttime")]
                ]

                await update.message.reply_text(
                    "🔒 You must join both channels first!",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return

        except Exception:
            await update.message.reply_text(
                "⚠️ Bot must be admin in both channels."
            )
            return

    if not is_admin_user:
        today = today_str()
        
        if user_id not in USER_USAGE:
            USER_USAGE[user_id] = {
                "date": today,
                "count": 0
            }

        if USER_USAGE[user_id]["date"] != today:
            USER_USAGE[user_id] = {
                "date": today,
                "count": 0
            }

        if USER_USAGE[user_id]["count"] >= USER_DAILY_LIMIT:
            await update.message.reply_text(
                f"❌ Daily limit finished!\n\nYour limit: {USER_DAILY_LIMIT} / day"
            )
            return
    else:
        admin_limit = get_admin_limit(user_id)
        if admin_limit != 999999:
            today = today_str()
            if user_id not in USER_USAGE:
                USER_USAGE[user_id] = {
                    "date": today,
                    "count": 0
                }
            if USER_USAGE[user_id]["date"] != today:
                USER_USAGE[user_id] = {
                    "date": today,
                    "count": 0
                }
            if USER_USAGE[user_id]["count"] >= admin_limit:
                await update.message.reply_text(
                    f"❌ Admin daily limit finished!\n\nYour admin limit: {admin_limit} / day"
                )
                return

    if len(context.args) != 2:
        await update.message.reply_text(
            "❌ Usage: /like <region> <uid>\n\n"
            "📌 Example: /like me 1234567890\n\n"
            "💡 This is a demo command same as /vip"
        )
        return

    region, uid = context.args
    wait_msg = await update.message.reply_text("🔄 Testing UID, Please Wait...")

    async with aiohttp.ClientSession() as session:
        js = await call_api(session, uid, region, DEMO_API_URL)

    if not js:
        await wait_msg.edit_text(
            f"❌ API FAILED / INVALID UID\n\n"
            f"UID : {hide_uid(uid)}\n"
            f"Region : {region.upper()}\n\n"
            f"👑 NIHAL LIKE BOT (@trynexttime)"
        )        
        return

    likes_given = int(js.get("LikesGivenByAPI", 0))
    after = int(js.get("LikesafterCommand", 0))
    before = int(js.get("LikesbeforeCommand", after - likes_given))
    status = js.get("status", "N/A")
    name = js.get("PlayerNickname", "N/A")

    if likes_given == 0:
        msg = (
            f"⚠️🚫 LIKE LIMIT REACHED 🚫⚠️\n\n"
            f"Player : {name}\n"
            f"UID : {hide_uid(uid)}\n"
            f"Region : {region.upper()}\n\n"
            f"Current Likes : {after}\n"
            f"Status : {status}\n\n"
            f"Reason : Daily Like Max / Server Limit\n\n"
            f"👑 NIHAL LIKE BOT (@itsnihal)"
        )
    else:
        msg = (
            f"🧪 DEMO API TEST SUCCESS\n\n"
            f"Player : {name}\n"
            f"UID : {hide_uid(uid)}\n"
            f"Region : {region.upper()}\n\n"
            f"Like Before Command : {before}\n"
            f"Like After Command : {after}\n"
            f"Like Given By Bot : {likes_given}\n\n"
            f"Status : {status}\n\n"
            f"👑 NIHAL LIKE BOT (@itsnihal)"
        )
        
    if user_id not in OWNER_IDS:
        if user_id not in USER_USAGE:
            USER_USAGE[user_id] = {"date": today_str(), "count": 0}
        USER_USAGE[user_id]["count"] = USER_USAGE[user_id].get("count", 0) + 1
        
    keyboard = [
        [
            InlineKeyboardButton("💰 Buy Autolike", url="https://t.me/itsnihal"),
            InlineKeyboardButton("📢 Join Channel", url="https://t.me/trynexttime")
        ]
    ]

    await wait_msg.edit_text(
        msg,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ================= /vip (Original Test Command) =================

async def test_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not BOT_ENABLED:
        await update.message.reply_text(
            "🔴 Bot is currently OFF.\n\nPlease wait until the owner turns it ON."
        )
        return
    
    if not await group_only(update):
        return
    
    user_id = update.effective_user.id
    is_admin_user = await is_admin_or_owner(update)
    
    if not is_admin_user:
        try:
            m1 = await context.bot.get_chat_member(CHANNEL_1, user_id)
            m2 = await context.bot.get_chat_member(CHANNEL_2, user_id)

            ok1 = m1.status in ["member", "administrator", "creator"]
            ok2 = m2.status in ["member", "administrator", "creator"]

            if not (ok1 and ok2):
                keyboard = [
                    [InlineKeyboardButton("📢 Join Channel 1", url="https://t.me/trynexttime")],
                    [InlineKeyboardButton("📢 Join Channel 2", url="https://t.me/trynexttime")]
                ]

                await update.message.reply_text(
                    "🔒 You must join both channels first!",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return

        except Exception:
            await update.message.reply_text(
                "⚠️ Bot must be admin in both channels."
            )
            return

    if not is_admin_user:
        today = today_str()

        if user_id not in USER_USAGE:
            USER_USAGE[user_id] = {
                "date": today,
                "count": 0
            }

        if USER_USAGE[user_id]["date"] != today:
            USER_USAGE[user_id] = {
                "date": today,
                "count": 0
            }

        if USER_USAGE[user_id]["count"] >= USER_DAILY_LIMIT:
            await update.message.reply_text(
                f"❌ Daily limit finished!\n\nYour limit: {USER_DAILY_LIMIT} / day"
            )
            return
    else:
        admin_limit = get_admin_limit(user_id)
        if admin_limit != 999999:
            today = today_str()
            if user_id not in USER_USAGE:
                USER_USAGE[user_id] = {
                    "date": today,
                    "count": 0
                }
            if USER_USAGE[user_id]["date"] != today:
                USER_USAGE[user_id] = {
                    "date": today,
                    "count": 0
                }
            if USER_USAGE[user_id]["count"] >= admin_limit:
                await update.message.reply_text(
                    f"❌ Admin daily limit finished!\n\nYour admin limit: {admin_limit} / day"
                )
                return

    if len(context.args) != 2:
        await update.message.reply_text("❌ Usage: /vip <region> <uid>\n\nExample : /vip me 1234567890")
        return

    region, uid = context.args
    wait_msg = await update.message.reply_text("🔄 Testing UID, Please Wait...")

    async with aiohttp.ClientSession() as session:
        js = await call_api(session, uid, region)

    if not js:
        await wait_msg.edit_text(f"❌ API FAILED / INVALID UID\n\nUID : {hide_uid(uid)}\nRegion : {region.upper()}\n\n👑 NIHAL LIKE BOT (@itsnihal)")        
        return

    likes_given = int(js.get("LikesGivenByAPI", 0))
    after = int(js.get("LikesafterCommand", 0))
    before = int(js.get("LikesbeforeCommand", after - likes_given))
    status = js.get("status", "N/A")
    name = js.get("PlayerNickname", "N/A")

    if likes_given == 0:
        msg = f"⚠️🚫 LIKE LIMIT REACHED 🚫⚠️\n\nPlayer : {name}\nUID : {hide_uid(uid)}\nRegion : {region.upper()}\n\nCurrent Likes : {after}\nStatus : {status}\n\nReason : Daily Like Max / Server Limit\n\n👑 NIHAL LIKE BOT (@itsnihal)"
    else:
        msg = f"🧪 API TEST SUCCESS\n\nPlayer : {name}\nUID : {hide_uid(uid)}\nRegion : {region.upper()}\n\nLike Before Command : {before}\nLike After Command : {after}\nLike Given By Bot : {likes_given}\n\nStatus : {status}\n\n👑 NIHAL LIKE BOT (@itsnihal)"
        
    if user_id not in OWNER_IDS:
        if user_id not in USER_USAGE:
            USER_USAGE[user_id] = {"date": today_str(), "count": 0}
        USER_USAGE[user_id]["count"] = USER_USAGE[user_id].get("count", 0) + 1
        
    keyboard = [
        [
            InlineKeyboardButton("💰 Buy Autolike", url="https://t.me/itsnihal"),
            InlineKeyboardButton("📢 Join Channel", url="https://t.me/trynexttime")
        ]
    ]

    await wait_msg.edit_text(
        msg,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ================= 👑 ADMIN MANAGEMENT COMMANDS =================

async def admins_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show all admins"""
    if not await is_owner(update):
        await update.message.reply_text("🚫 Owner Only")
        return
    
    admins = get_all_admins()
    
    if not admins:
        await update.message.reply_text("📭 No admins found.")
        return
    
    msg = "👑 ADMIN LIST\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    for idx, admin in enumerate(admins, 1):
        try:
            chat = await context.bot.get_chat(admin["id"])
            name = chat.first_name or chat.username or str(admin["id"])
            username = f"@{chat.username}" if chat.username else "N/A"
        except:
            name = str(admin["id"])
            username = "N/A"
        
        msg += f"{idx}. {name}\n"
        msg += f"   ID: {admin['id']}\n"
        msg += f"   Type: {admin['type']}\n"
        msg += f"   Limit: {admin['limit']}/day\n"
        msg += f"   Username: {username}\n\n"
    
    msg += "━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "👑 NIHAL LIKE BOT"
    
    keyboard = [
        [InlineKeyboardButton("➕ Add Admin", callback_data="add_admin")],
        [InlineKeyboardButton("➖ Remove Admin", callback_data="remove_admin")],
        [InlineKeyboardButton("📊 Set Limit", callback_data="set_admin_limit")]
    ]
    
    await update.message.reply_text(
        msg,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def addadmin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add a new admin"""
    if not await is_owner(update):
        await update.message.reply_text("🚫 Owner Only")
        return
    
    if not context.args:
        await update.message.reply_text(
            "📝 Usage:\n"
            "/addadmin <user_id>\n\n"
            "📌 Example:\n"
            "/addadmin 1234567890\n\n"
            "💡 Use /getid to get user ID."
        )
        return
    
    try:
        user_id = int(context.args[0])
    except:
        await update.message.reply_text("❌ Invalid User ID. Please enter a valid number.")
        return
    
    if user_id in OWNER_IDS:
        await update.message.reply_text("👑 This user is already an Owner (Super Admin).")
        return
    
    if is_admin(user_id):
        await update.message.reply_text(f"⚠️ User {user_id} is already an admin.")
        return
    
    if add_admin(user_id):
        try:
            chat = await context.bot.get_chat(user_id)
            name = chat.first_name or chat.username or str(user_id)
        except:
            name = str(user_id)
        
        await update.message.reply_text(
            f"✅ Admin Added Successfully!\n\n"
            f"Name: {name}\n"
            f"ID: {user_id}\n\n"
            f"This user can now:\n"
            f"• Use /vip and /like commands\n"
            f"• Has higher daily limit\n"
            f"• No channel verification needed"
        )
        
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text="🎉 You have been promoted to Admin!\n\n"
                     "Your new permissions:\n"
                     "• Use /vip and /like commands\n"
                     "• Higher daily limit (can be set by owner)\n"
                     "• No channel verification needed\n\n"
                     "👑 Powered By NIHAL LIKE BOT"
            )
        except:
            pass
    else:
        await update.message.reply_text("❌ Failed to add admin. Please try again.")

async def removeadmin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove an admin"""
    if not await is_owner(update):
        await update.message.reply_text("🚫 Owner Only")
        return
    
    if not context.args:
        await update.message.reply_text(
            "📝 Usage:\n"
            "/removeadmin <user_id>\n\n"
            "📌 Example:\n"
            "/removeadmin 1234567890\n\n"
            "💡 Use /admins to see all admin IDs."
        )
        return
    
    try:
        user_id = int(context.args[0])
    except:
        await update.message.reply_text("❌ Invalid User ID. Please enter a valid number.")
        return
    
    if user_id in OWNER_IDS:
        await update.message.reply_text("❌ Cannot remove Owner (Super Admin).")
        return
    
    if not is_admin(user_id):
        await update.message.reply_text(f"⚠️ User {user_id} is not an admin.")
        return
    
    if remove_admin(user_id):
        try:
            chat = await context.bot.get_chat(user_id)
            name = chat.first_name or chat.username or str(user_id)
        except:
            name = str(user_id)
        
        await update.message.reply_text(
            f"✅ Admin Removed Successfully!\n\n"
            f"Name: {name}\n"
            f"ID: {user_id}\n\n"
            f"This user no longer has admin privileges."
        )
        
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text="🔴 You have been removed from Admin!\n\n"
                     "Your admin privileges have been revoked.\n\n"
                     "👑 Powered By NIHAL LIKE BOT"
            )
        except:
            pass
    else:
        await update.message.reply_text("❌ Failed to remove admin. Please try again.")

async def setadminlimit_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set admin's daily limit"""
    if not await is_owner(update):
        await update.message.reply_text("🚫 Owner Only")
        return
    
    if len(context.args) != 2:
        await update.message.reply_text(
            "📝 Usage:\n"
            "/setadminlimit <user_id> <limit>\n\n"
            "📌 Example:\n"
            "/setadminlimit 1234567890 10\n\n"
            "💡 Use 0 for unlimited (only for owners)\n"
            "💡 Use /admins to see all admin IDs."
        )
        return
    
    try:
        user_id = int(context.args[0])
        limit = int(context.args[1])
    except:
        await update.message.reply_text("❌ Invalid input. Please enter valid numbers.")
        return
    
    if user_id not in OWNER_IDS and not is_admin(user_id):
        await update.message.reply_text(f"⚠️ User {user_id} is not an admin.")
        return
    
    if limit < 0:
        await update.message.reply_text("❌ Limit cannot be negative.")
        return
    
    if user_id in OWNER_IDS:
        await update.message.reply_text("👑 Owners have unlimited limit by default.")
        return
    
    set_admin_limit(user_id, limit)
    
    try:
        chat = await context.bot.get_chat(user_id)
        name = chat.first_name or chat.username or str(user_id)
    except:
        name = str(user_id)
    
    limit_text = "∞ (Unlimited)" if limit == 0 else f"{limit} / day"
    
    await update.message.reply_text(
        f"✅ Admin Limit Set!\n\n"
        f"Name: {name}\n"
        f"ID: {user_id}\n"
        f"New Limit: {limit_text}\n\n"
        f"This admin can now use /vip and /like {limit_text}."
    )
    
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=f"📊 Your Admin Limit Has Been Updated!\n\n"
                 f"New Limit: {limit_text}\n\n"
                 f"👑 Powered By NIHAL LIKE BOT"
        )
    except:
        pass

# ================= /setlimit (For normal users) =================

async def setlimit_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global USER_DAILY_LIMIT

    if not await is_owner(update):
        await update.message.reply_text("🚫 Owner Only")
        return

    if not context.args:
        await update.message.reply_text(
            "❌ Use: /setlimit <number>\nExample: /setlimit 5"
        )
        return

    try:
        limit = int(context.args[0])
        if limit <= 0:
            raise ValueError
    except:
        await update.message.reply_text(
            "❌ Please enter a valid number"
        )
        return

    USER_DAILY_LIMIT = limit
    await update.message.reply_text(f"✅ User daily limit set to {limit}")

# ================= /start =================

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📢 Join Channel 1", url="https://t.me/trynexttime")],
        [InlineKeyboardButton("📢 Join Channel 2", url="https://t.me/trynexttime")],
        [InlineKeyboardButton("✅ Verify Membership", callback_data="verify_join")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    text = (
        "🎮 FREE FIRE LIKE BOT\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🔒 To use this bot, you must join both channels.\n\n"
        "✅ Step 1: Join Channel 1\n"
        "✅ Step 2: Join Channel 2\n"
        "✅ Step 3: Press Verify Membership\n\n"
        "❤️ After verification you can use all commands."
    )

    try:
        await update.message.reply_text(
            text,
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Start command error: {e}")
        await update.message.reply_text(
            "🎮 FREE FIRE LIKE BOT\n\nPlease use /help for commands."
        )

# ================= VERIFY =================

async def verify_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    try:
        m1 = await context.bot.get_chat_member(CHANNEL_1, user_id)
        m2 = await context.bot.get_chat_member(CHANNEL_2, user_id)

        ok1 = m1.status in ["member", "administrator", "creator"]
        ok2 = m2.status in ["member", "administrator", "creator"]

        if ok1 and ok2:
            await query.edit_message_text(
                "╔══════════════════════════════════════════╗\n"
                "║      👑 𝐅𝐑𝐄𝐄 𝐅𝐈𝐑𝐄 𝐕𝐈𝐏 𝐀𝐔𝐓𝐎 𝐋𝐈𝐊𝐄 👑      ║\n"
                "╠══════════════════════════════════════════╣\n"
                "║                                          ║\n"
                "║  ❤️ 100 𝐑𝐄𝐀𝐋 𝐋𝐈𝐊𝐄𝐒 𝐄𝐕𝐄𝐑𝐘 𝐃𝐀𝐘         ║\n"
                "║  ⚡ 𝐀𝐔𝐓𝐎𝐌𝐀𝐓𝐈𝐂 𝐃𝐄𝐋𝐈𝐕𝐄𝐑𝐘                 ║\n"
                "║  ⏰ 𝐃𝐀𝐈𝐋𝐘 𝐀𝐓 𝟒:𝟎𝟎 𝐀𝐌 (𝐈𝐒𝐓)               ║\n"
                "║  🆔 𝐎𝐍𝐋𝐘 𝐅𝐅 𝐔𝐈𝐃 𝐑𝐄𝐐𝐔𝐈𝐑𝐄𝐃                ║\n"
                "║  🇮🇳 𝐈𝐍𝐃𝐈𝐀 𝐒𝐄𝐑𝐕𝐄𝐑                     ║\n"
                "║  🔒 𝐅𝐀𝐒𝐓 • 𝐄𝐀𝐒𝐘 • 𝐑𝐄𝐋𝐈𝐀𝐁𝐋𝐄             ║\n"
                "║                                          ║\n"
                "╠══════════════════════════════════════════╣\n"
                "║           💎 𝐕𝐈𝐏 𝐋𝐈𝐊𝐄 𝐏𝐋𝐀𝐍𝐒             ║\n"
                "╠══════════════════════════════════════════╣\n"
                "║                                          ║\n"
                "║  💸 𝟏 𝐃𝐀𝐘    ➜ ₹𝟏𝟎                    ║\n"
                "║  ❤️ 𝟏𝟎𝟎 𝐋𝐈𝐊𝐄𝐒 ➜ 👍🏻                    ║\n"
                "║                                          ║\n"
                "║  💸 𝟕 𝐃𝐀𝐘𝐒   ➜ ₹𝟕𝟎                    ║\n"
                "║  ❤️ 𝟕𝟎𝟎 𝐋𝐈𝐊𝐄𝐒 ➜ 👍🏻                    ║\n"
                "║                                          ║\n"
                "║  💸 𝟏𝟓 𝐃𝐀𝐘𝐒  ➜ ₹𝟏𝟓𝟎                   ║\n"
                "║  ❤️ 𝟏,𝟓𝟎𝟎 𝐋𝐈𝐊𝐄𝐒 ➜ 👍🏻                  ║\n"
                "║                                          ║\n"
                "║  💸 𝟑𝟎 𝐃𝐀𝐘𝐒  ➜ ₹𝟑𝟎𝟎                   ║\n"
                "║  ❤️ 𝟑,𝟎𝟎𝟎 𝐋𝐈𝐊𝐄𝐒 ➜ 👍🏻                  ║\n"
                "║                                          ║\n"
                "║  💸 𝟔𝟎 𝐃𝐀𝐘𝐒  ➜ ₹𝟔𝟎𝟎                   ║\n"
                "║  ❤️ 𝟔,𝟎𝟎𝟎 𝐋𝐈𝐊𝐄𝐒 ➜ 👍🏻                  ║\n"
                "║                                          ║\n"
                "║  💸 𝟏𝟐𝟎 𝐃𝐀𝐘𝐒 ➜ ₹𝟏,𝟐𝟎𝟎                 ║\n"
                "║  ❤️ 𝟏𝟐,𝟎𝟎𝟎 𝐋𝐈𝐊𝐄𝐒 ➜ 👍🏻                ║\n"
                "║                                          ║\n"
                "║  💸 𝟏𝟖𝟎 𝐃𝐀𝐘𝐒 ➜ ₹𝟏,𝟖𝟎𝟎                 ║\n"
                "║  ❤️ 𝟏𝟖,𝟎𝟎𝟎 𝐋𝐈𝐊𝐄𝐒 ➜ 👍🏻                ║\n"
                "║                                          ║\n"
                "║  💸 𝟑𝟔𝟓 𝐃𝐀𝐘𝐒 ➜ ₹𝟑,𝟔𝟓𝟎                 ║\n"
                "║  ❤️ 𝟑𝟔,𝟓𝟎𝟎 𝐋𝐈𝐊𝐄𝐒 ➜ 👍🏻                ║\n"
                "║                                          ║\n"
                "╠══════════════════════════════════════════╣\n"
                "║        🎯 𝐂𝐔𝐒𝐓𝐎𝐌 𝐏𝐋𝐀𝐍 𝐀𝐕𝐀𝐈𝐋𝐀𝐁𝐋𝐄        ║\n"
                "╠══════════════════════════════════════════╣\n"
                "║                                          ║\n"
                "║  📅 अपने हिसाब से 𝐂𝐔𝐒𝐓𝐎𝐌 𝐃𝐀𝐘𝐒 चुनें      ║\n"
                "║  ❤️ 𝟏𝟎𝟎 𝐋𝐈𝐊𝐄𝐒 / 𝐃𝐀𝐘                   ║\n"
                "║  💰 ₹𝟏𝟎 × 𝐍𝐔𝐌𝐁𝐄𝐑 𝐎𝐅 𝐃𝐀𝐘𝐒              ║\n"
                "║                                          ║\n"
                "║  👉 𝟏𝟎 𝐃𝐀𝐘𝐒  = ₹𝟏𝟎𝟎  = 𝟏,𝟎𝟎𝟎 ❤️        ║\n"
                "║  👉 𝟐𝟎 𝐃𝐀𝐘𝐒  = ₹𝟐𝟎𝟎  = 𝟐,𝟎𝟎𝟎 ❤️        ║\n"
                "║  👉 𝟒𝟓 𝐃𝐀𝐘𝐒  = ₹𝟒𝟓𝟎  = 𝟒,𝟓𝟎𝟎 ❤️        ║\n"
                "║  👉 𝟗𝟎 𝐃𝐀𝐘𝐒  = ₹𝟗𝟎𝟎  = 𝟗,𝟎𝟎𝟎 ❤️        ║\n"
                "║                                          ║\n"
                "║  📩 𝐂𝐔𝐒𝐓𝐎𝐌 𝐏𝐋𝐀𝐍 𝐊𝐄 𝐋𝐈𝐘𝐄 𝐃𝐌 𝐊𝐀𝐑𝐄𝐍     ║\n"
                "║                                          ║\n"
                "╠══════════════════════════════════════════╣\n"
                "║         🔥 𝐒𝐄𝐑𝐕𝐈𝐂𝐄 𝐅𝐄𝐀𝐓𝐔𝐑𝐄𝐒 🔥         ║\n"
                "╠══════════════════════════════════════════╣\n"
                "║                                          ║\n"
                "║  ✅ 𝟏𝟎𝟎 𝐋𝐈𝐊𝐄𝐒 𝐃𝐀𝐈𝐋𝐘                  ║\n"
                "║  ✅ 𝐀𝐔𝐓𝐎𝐌𝐀𝐓𝐈𝐂 𝐃𝐄𝐋𝐈𝐕𝐄𝐑𝐘                 ║\n"
                "║  ✅ 𝐃𝐀𝐈𝐋𝐘 𝐀𝐓 𝟒:𝟎𝟎 𝐀𝐌 (𝐈𝐒𝐓)              ║\n"
                "║  ✅ 🇮🇳 𝐈𝐍𝐃𝐈𝐀 𝐒𝐄𝐑𝐕𝐄𝐑                    ║\n"
                "║  ✅ 𝐎𝐍𝐋𝐘 𝐅𝐅 𝐔𝐈𝐃 𝐑𝐄𝐐𝐔𝐈𝐑𝐄𝐃                ║\n"
                "║  ✅ 𝐍𝐎 𝐏𝐀𝐒𝐒𝐖𝐎𝐑𝐃 𝐑𝐄𝐐𝐔𝐈𝐑𝐄𝐃 🔐            ║\n"
                "║  ✅ 𝐅𝐋𝐄𝐗𝐈𝐁𝐋𝐄 𝐏𝐋𝐀𝐍𝐒                   ║\n"
                "║  ✅ 𝐂𝐔𝐒𝐓𝐎𝐌 𝐃𝐀𝐘𝐒 𝐀𝐕𝐀𝐈𝐋𝐀𝐁𝐋𝐄             ║\n"
                "║                                          ║\n"
                "╠══════════════════════════════════════════╣\n"
                "║              📩 𝐎𝐑𝐃𝐄𝐑 𝐍𝐎𝐖              ║\n"
                "║                                          ║\n"
                "║  👤 𝐓𝐄𝐋𝐄𝐆𝐑𝐀𝐌: @itsnihal         ║\n"
                "║                                          ║\n"
                "║  ❤️ 𝐓𝐇𝐀𝐍𝐊 𝐘𝐎𝐔 𝐅𝐎𝐑 𝐂𝐇𝐎𝐎𝐒𝐈𝐍𝐆 𝐔𝐒 ❤️     ║\n"
                "║  🔥 𝐅𝐀𝐒𝐓 • 𝐒𝐈𝐌𝐏𝐋𝐄 • 𝐏𝐑𝐄𝐌𝐈𝐔𝐌 🔥         ║\n"
                "╚══════════════════════════════════════════╝"
            )
        else:
            await query.answer(
                "❌ Please join both channels first!",
                show_alert=True
            )

    except Exception as e:
        logger.error(f"Verify error: {e}")
        await query.answer(
            "⚠️ Verification failed.",
            show_alert=True
        )

# ================= /off =================

async def off_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global BOT_ENABLED

    if not await is_owner(update):
        await update.message.reply_text("🚫 Owner Only")
        return

    BOT_ENABLED = False
    await update.message.reply_text(
        "🔴 Bot has been turned OFF.\n\nOnly the owner can turn it ON again."
    )
    
# ================= /on =================

async def on_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global BOT_ENABLED

    if not await is_owner(update):
        await update.message.reply_text("🚫 Owner Only")
        return

    BOT_ENABLED = True
    await update.message.reply_text(
        "🟢 Bot has been turned ON.\n\nAll commands are working now."
    )
        
# ================= 📢 TEXT SMS BROADCAST =================

async def vipsms_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send text message to all users (Owner Only)"""
    if not await group_only(update):
        return

    if not await is_owner(update):
        await update.message.reply_text("🚫 Owner Only")
        return

    if not context.args:
        await update.message.reply_text(
            "📝 Usage:\n/vipsms <message>\n\n📌 Example:\n/vipsms Hello everyone!"
        )
        return

    message = " ".join(context.args)
    data = load_data()

    if not data["uids"]:
        await update.message.reply_text("📭 No users to send message.")
        return

    status_msg = await update.message.reply_text(
        f"📤 Sending message to {len(data['uids'])} users..."
    )

    sent = 0
    failed = 0
    total = len(data["uids"])

    for entry in data["uids"]:
        tg_id = entry.get("tg_id")
        
        if not tg_id:
            failed += 1
            continue

        try:
            await context.bot.send_message(
                chat_id=tg_id,
                text=f"📢 VIP NOTICE\n\n{message}\n\n👑 NIHAL LIKE BOT"
            )
            sent += 1
            await asyncio.sleep(0.3)
        except Exception:
            failed += 1

    await status_msg.edit_text(
        f"📨 SMS Broadcast Completed\n\n"
        f"👥 Total Users : {total}\n"
        f"✅ Delivered : {sent}\n"
        f"❌ Failed : {failed}\n\n"
        f"👑 NIHAL LIKE BOT"
    )

# ================= 🎵 VOICE MESSAGE BROADCAST =================

async def vipvoice_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send voice message to all users (Owner Only)"""
    if not await group_only(update):
        return

    if not await is_owner(update):
        await update.message.reply_text("🚫 Owner Only")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text(
            "🎵 Usage:\nReply to a voice message with /vipvoice\n\n"
            "📌 How to use:\n"
            "1️⃣ Send a voice message to the bot\n"
            "2️⃣ Reply to that voice message with /vipvoice\n"
            "3️⃣ Bot will forward it to all users"
        )
        return

    voice_msg = update.message.reply_to_message
    if not voice_msg.voice:
        await update.message.reply_text(
            "❌ Please reply to a voice message only!"
        )
        return

    data = load_data()
    if not data["uids"]:
        await update.message.reply_text("📭 No users to send voice message.")
        return

    status_msg = await update.message.reply_text(
        f"🎵 Sending voice message to {len(data['uids'])} users..."
    )

    sent = 0
    failed = 0
    total = len(data["uids"])
    
    voice_file_id = voice_msg.voice.file_id

    for entry in data["uids"]:
        tg_id = entry.get("tg_id")
        
        if not tg_id:
            failed += 1
            continue

        try:
            await context.bot.send_voice(
                chat_id=tg_id,
                voice=voice_file_id,
                caption="🎵 VIP VOICE NOTICE\n\n👑 NIHAL LIKE BOT"
            )
            sent += 1
            await asyncio.sleep(0.5)
        except Exception:
            failed += 1

    await status_msg.edit_text(
        f"🎵 Voice Broadcast Completed\n\n"
        f"👥 Total Users : {total}\n"
        f"✅ Delivered : {sent}\n"
        f"❌ Failed : {failed}\n\n"
        f"👑 NIHAL LIKE BOT"
    )

# ================= 📊 AUTO LIKE INFO COMMAND =================

async def autolikeinfo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show complete auto-like statistics"""
    if not await is_owner(update):
        await update.message.reply_text("🚫 Owner Only")
        return
    
    data = load_data()
    now = datetime.now(TIMEZONE)
    
    active = 0
    expired = 0
    total_days = 0
    total_likes = data.get("total_likes_given", 0)
    user_details = []
    
    for entry in data["uids"]:
        expire_dt = datetime.fromisoformat(entry["expire"])
        if now > expire_dt:
            expired += 1
            continue
        active += 1
        days_left = max(0, (expire_dt - now).days)
        total_days += days_left
        
        tg_name = "Unknown"
        tg_id = entry.get("tg_id")
        if tg_id:
            try:
                chat = await context.bot.get_chat(tg_id)
                tg_name = f"@{chat.username}" if chat.username else (chat.first_name or "Unknown")
            except:
                pass
        
        likes = entry.get("likes_given", 0)
        
        user_details.append({
            "uid": entry["uid"],
            "region": entry["region"].upper(),
            "name": tg_name,
            "days_left": days_left,
            "likes": likes,
            "expire": expire_dt
        })
    
    user_details.sort(key=lambda x: x["days_left"])
    
    msg = "📊 AUTO LIKE INFO\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    msg += f"📌 Total UIDs: {len(data['uids'])}\n"
    msg += f"✅ Active: {active}\n"
    msg += f"❌ Expired: {expired}\n"
    msg += f"🎯 Total Likes Given: {total_likes}\n"
    msg += f"📅 Total Days Active: {total_days}\n\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━\n"
    
    if user_details:
        msg += "👥 Active Users:\n\n"
        for idx, user in enumerate(user_details, 1):
            msg += f"{idx}. {user['name']}\n"
            msg += f"   UID: {hide_uid(user['uid'])}\n"
            msg += f"   Region: {user['region']}\n"
            msg += f"   Days Left: {user['days_left']}\n"
            msg += f"   Likes Given: {user['likes']}\n\n"
    else:
        msg += "📭 No active users.\n"
    
    msg += "━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "👑 NIHAL LIKE BOT"
    
    keyboard = [
        [InlineKeyboardButton("📢 Join Channel", url="https://t.me/trynexttime")],
        [InlineKeyboardButton("💰 Buy Autolike", url="https://t.me/itsnihal")]
    ]
    
    try:
        await update.message.reply_text(
            msg,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except:
        await update.message.reply_text(
            msg.replace("*", "").replace("_", ""),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# ================= 📊 GROUP MANAGEMENT COMMANDS =================

async def mygroups_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show all groups where bot is added and allowed"""
    if not await is_owner(update):
        await update.message.reply_text("🚫 Owner Only")
        return
    
    sync_allowed_groups()
    
    if not ALLOWED_GROUP_IDS:
        await update.message.reply_text("📭 No groups added yet.")
        return
    
    msg = "📊 MY GROUPS\n━━━━━━━━━━━━━━━━━━━━━\n\n"
    msg += f"📌 Total Groups: {len(ALLOWED_GROUP_IDS)}\n\n"
    
    for idx, group_id in enumerate(ALLOWED_GROUP_IDS, 1):
        try:
            chat = await context.bot.get_chat(group_id)
            title = chat.title or "Unknown"
            msg += f"{idx}. {title}\n"
            msg += f"   ID: {group_id}\n"
            msg += f"   Type: {chat.type}\n\n"
        except:
            msg += f"{idx}. ID: {group_id}\n"
            msg += "   ⚠️ Can't fetch info (bot may not be in group)\n\n"
    
    msg += "━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "👑 NIHAL LIKE BOT"
    
    keyboard = [
        [InlineKeyboardButton("➕ Add Group", callback_data="add_group")],
        [InlineKeyboardButton("➖ Remove Group", callback_data="remove_group")]
    ]
    
    await update.message.reply_text(
        msg,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def addgroup_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add a new group to allowed list"""
    if not await is_owner(update):
        await update.message.reply_text("🚫 Owner Only")
        return
    
    if not context.args:
        await update.message.reply_text(
            "📝 Usage:\n"
            "/addgroup <group_id>\n\n"
            "📌 Example:\n"
            "/addgroup -1001234567890\n\n"
            "💡 Tip: Use /getid in the group to get its ID."
        )
        return
    
    try:
        group_id = int(context.args[0])
    except:
        await update.message.reply_text("❌ Invalid Group ID. Please enter a valid number.")
        return
    
    sync_allowed_groups()
    
    if group_id in ALLOWED_GROUP_IDS:
        await update.message.reply_text(f"⚠️ Group {group_id} is already in the list.")
        return
    
    try:
        chat = await context.bot.get_chat(group_id)
        title = chat.title or "Unknown"
    except:
        await update.message.reply_text(
            f"❌ Can't access group {group_id}.\n\n"
            f"💡 Make sure:\n"
            f"1. Bot is added to the group\n"
            f"2. Group ID is correct\n"
            f"3. Bot is admin in the group"
        )
        return
    
    ALLOWED_GROUP_IDS.append(group_id)
    save_group_data(ALLOWED_GROUP_IDS)
    
    await update.message.reply_text(
        f"✅ Group Added Successfully!\n\n"
        f"Name: {title}\n"
        f"ID: {group_id}\n"
        f"Type: {chat.type}\n\n"
        f"Bot will now work in this group."
    )
    
    try:
        await context.bot.send_message(
            chat_id=group_id,
            text="🎉 Bot Activated!\n\n"
                 "This bot is now active in this group.\n\n"
                 "Use /help to see all commands.\n\n"
                 "👑 Powered By NIHAL LIKE BOT"
        )
    except:
        pass

async def removegroup_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove a group from allowed list"""
    if not await is_owner(update):
        await update.message.reply_text("🚫 Owner Only")
        return
    
    if not context.args:
        await update.message.reply_text(
            "📝 Usage:\n"
            "/removegroup <group_id>\n\n"
            "📌 Example:\n"
            "/removegroup -1001234567890\n\n"
            "💡 Use /mygroups to see all group IDs."
        )
        return
    
    try:
        group_id = int(context.args[0])
    except:
        await update.message.reply_text("❌ Invalid Group ID. Please enter a valid number.")
        return
    
    sync_allowed_groups()
    
    if group_id not in ALLOWED_GROUP_IDS:
        await update.message.reply_text(f"⚠️ Group {group_id} is not in the list.")
        return
    
    ALLOWED_GROUP_IDS.remove(group_id)
    save_group_data(ALLOWED_GROUP_IDS)
    
    try:
        chat = await context.bot.get_chat(group_id)
        title = chat.title or "Unknown"
    except:
        title = "Unknown"
    
    await update.message.reply_text(
        f"✅ Group Removed Successfully!\n\n"
        f"Name: {title}\n"
        f"ID: {group_id}\n\n"
        f"Bot will no longer work in this group."
    )
    
    try:
        await context.bot.send_message(
            chat_id=group_id,
            text="🔴 Bot Deactivated!\n\n"
                 "This bot is no longer active in this group.\n\n"
                 "👑 Powered By NIHAL LIKE BOT"
        )
        await asyncio.sleep(1)
        await context.bot.leave_chat(group_id)
    except:
        pass

async def groupstats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show detailed statistics about groups"""
    if not await is_owner(update):
        await update.message.reply_text("🚫 Owner Only")
        return
    
    sync_allowed_groups()
    
    total_groups = len(ALLOWED_GROUP_IDS)
    active_groups = 0
    inactive_groups = 0
    group_details = []
    
    for group_id in ALLOWED_GROUP_IDS:
        try:
            chat = await context.bot.get_chat(group_id)
            title = chat.title or "Unknown"
            active_groups += 1
            group_details.append({
                "id": group_id,
                "title": title,
                "status": "✅ Active"
            })
        except:
            inactive_groups += 1
            group_details.append({
                "id": group_id,
                "title": "Unknown",
                "status": "❌ Inactive"
            })
    
    msg = "📊 GROUP STATISTICS\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━\n\n"
    msg += f"📌 Total Groups: {total_groups}\n"
    msg += f"✅ Active: {active_groups}\n"
    msg += f"❌ Inactive: {inactive_groups}\n\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "📋 Group Details:\n\n"
    
    for idx, group in enumerate(group_details, 1):
        msg += f"{idx}. {group['title']}\n"
        msg += f"   ID: {group['id']}\n"
        msg += f"   {group['status']}\n\n"
    
    msg += "━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "👑 NIHAL LIKE BOT"
    
    await update.message.reply_text(msg)

async def group_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle group management callbacks"""
    query = update.callback_query
    await query.answer()
    
    if not await is_owner(update):
        await query.edit_message_text("🚫 Owner Only")
        return
    
    if query.data == "add_group":
        await query.edit_message_text(
            "📝 Add Group\n\n"
            "To add a group, use:\n"
            "/addgroup <group_id>\n\n"
            "📌 Example:\n"
            "/addgroup -1001234567890\n\n"
            "💡 Use /getid in the group to get its ID."
        )
    
    elif query.data == "remove_group":
        await query.edit_message_text(
            "📝 Remove Group\n\n"
            "To remove a group, use:\n"
            "/removegroup <group_id>\n\n"
            "📌 Example:\n"
            "/removegroup -1001234567890\n\n"
            "💡 Use /mygroups to see all group IDs."
        )

# ================= ADMIN CALLBACK HANDLERS =================

async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin management callbacks"""
    query = update.callback_query
    await query.answer()
    
    if not await is_owner(update):
        await query.edit_message_text("🚫 Owner Only")
        return
    
    if query.data == "add_admin":
        await query.edit_message_text(
            "📝 Add Admin\n\n"
            "To add an admin, use:\n"
            "/addadmin <user_id>\n\n"
            "📌 Example:\n"
            "/addadmin 1234567890\n\n"
            "💡 Use /getid to get user ID."
        )
    
    elif query.data == "remove_admin":
        await query.edit_message_text(
            "📝 Remove Admin\n\n"
            "To remove an admin, use:\n"
            "/removeadmin <user_id>\n\n"
            "📌 Example:\n"
            "/removeadmin 1234567890\n\n"
            "💡 Use /admins to see all admin IDs."
        )
    
    elif query.data == "set_admin_limit":
        await query.edit_message_text(
            "📝 Set Admin Limit\n\n"
            "To set admin limit, use:\n"
            "/setadminlimit <user_id> <limit>\n\n"
            "📌 Example:\n"
            "/setadminlimit 1234567890 10\n\n"
            "💡 Use 0 for unlimited."
        )

# ================= 📖 HELP COMMAND =================

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command - Shows different content for users vs owners"""
    is_user_owner = await is_owner(update)
    is_user_admin = await is_admin_or_owner(update)
    
    user_commands = """
👤 USER COMMANDS

/vip <region> <uid> - Test like on your UID
/like <region> <uid> - Demo like command
/start - Start the bot and verify membership
/help - Show this help message

Example:
/vip me 1234567890
/like me 1234567890

Join Channel: @trynexttime
"""
    
    admin_commands = """
━━━━━━━━━━━━━━━━━━━━━
🛡️ ADMIN COMMANDS

(Admins have higher limits and bypass channel check)
"""
    
    owner_commands = """
━━━━━━━━━━━━━━━━━━━━━
👑 OWNER COMMANDS

Manage Auto-Like:
/autolike <region> <uid> <days> <tg_id> - Add new auto-like
/extend <uid> <days> - Extend specific UID
/extendall <days> - Extend all active UIDs
/remove <uid> - Remove UID from database

View Data:
/state - View detailed status
/list - View list of active UIDs
/autolikeinfo - Complete auto-like statistics

Bot Control:
/runall - Manually trigger auto-like
/on - Turn bot ON
/off - Turn bot OFF
/setlimit <number> - Set user daily limit

Broadcast:
/vipsms <message> - Send text message to all users
/vipvoice - Reply to voice message to broadcast

👑 Admin Management:
/admins - Show all admins
/addadmin <id> - Add new admin
/removeadmin <id> - Remove admin
/setadminlimit <id> <limit> - Set admin daily limit

Group Management:
/mygroups - Show all allowed groups
/addgroup <id> - Add a new group
/removegroup <id> - Remove a group
/groupstats - Show group statistics

Debug:
/debug - Check bot status
/getid - Get current group ID
"""
    
    if is_user_owner:
        help_text = f"""
📖 AUTO LIKE BOT HELP
━━━━━━━━━━━━━━━━━━━━━

{user_commands}
{admin_commands}
{owner_commands}
━━━━━━━━━━━━━━━━━━━━━
⏰ Auto Time: {SEND_LIKE_TIME}
📊 Daily Limit: {USER_DAILY_LIMIT} likes/user

👑 Powered By NIHAL LIKE BOT
📢 Join: @trynexttime
"""
    elif is_user_admin:
        admin_limit = get_admin_limit(update.effective_user.id)
        help_text = f"""
📖 AUTO LIKE BOT HELP
━━━━━━━━━━━━━━━━━━━━━

{user_commands}
{admin_commands}
━━━━━━━━━━━━━━━━━━━━━
⏰ Auto Time: {SEND_LIKE_TIME}
📊 Your Admin Limit: {admin_limit}/day

👑 Powered By NIHAL LIKE BOT
📢 Join: @trynexttime
"""
    else:
        help_text = f"""
📖 AUTO LIKE BOT HELP
━━━━━━━━━━━━━━━━━━━━━

{user_commands}
━━━━━━━━━━━━━━━━━━━━━
⏰ Auto Time: {SEND_LIKE_TIME}
📊 Daily Limit: {USER_DAILY_LIMIT} likes/user

👑 Powered By NIHAL LIKE BOT
📢 Join: @trynexttime
"""
    
    keyboard = [
        [InlineKeyboardButton("📢 Join Channel", url="https://t.me/trynexttime")],
        [InlineKeyboardButton("💰 Buy Autolike", url="https://t.me/itsnihal")],
        [InlineKeyboardButton("👑 Owner Contact", url="https://t.me/itsnihal")]
    ]
    
    try:
        await update.message.reply_text(
            help_text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"Help command error: {e}")
        await update.message.reply_text(
            "📖 AUTO LIKE BOT HELP\n\nUse /vip or /like for testing likes.\nUse /start to verify membership."
        )

# ================= 🔍 DEBUG COMMANDS =================

async def debug_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Debug command to check everything"""
    if not await is_owner(update):
        await update.message.reply_text("🚫 Owner Only")
        return
    
    chat = update.effective_chat
    chat_id = chat.id
    
    sync_allowed_groups()
    
    msg = f"""
🔍 DEBUG INFO

Chat ID: {chat_id}
Type: {chat.type}
Title: {chat.title or 'N/A'}
Is Owner: {await is_owner(update)}
Is Admin: {await is_admin_or_owner(update)}

Allowed Groups ({len(ALLOWED_GROUP_IDS)}):
"""
    
    for idx, aid in enumerate(ALLOWED_GROUP_IDS[:10], 1):
        msg += f"{idx}. {aid}\n"
    
    if len(ALLOWED_GROUP_IDS) > 10:
        msg += f"... and {len(ALLOWED_GROUP_IDS) - 10} more\n"
    
    msg += f"\nGroup Allowed: {is_group_allowed(chat_id)}"
    
    try:
        bot_member = await context.bot.get_chat_member(chat_id, context.bot.id)
        msg += f"\nBot Status: {bot_member.status}"
        msg += f"\nBot Admin: {bot_member.status in ['administrator', 'creator']}"
    except:
        msg += "\nCan't get bot status"
    
    await update.message.reply_text(msg)

async def getid_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get current chat ID"""
    chat = update.effective_chat
    chat_id = chat.id
    
    msg = f"""
📌 Chat Information

Name: {chat.title or 'Private Chat'}
ID: {chat_id}
Type: {chat.type}
Your ID: {update.effective_user.id}
"""
    
    if chat.type != "private":
        msg += f"\nGroup Allowed: {is_group_allowed(chat_id)}"
    
    await update.message.reply_text(msg)

# ================= 🚀 SCHEDULER =================

async def scheduler(app):
    """Run auto-like at scheduled time"""
    print("=" * 50)
    print("⏰ SCHEDULER STARTED!")
    print(f"📅 Auto-like will run daily at {SEND_LIKE_TIME}")
    print(f"🕐 Current time: {datetime.now(TIMEZONE).strftime('%I:%M %p')}")
    print("=" * 50)
    
    last_run_date = None
    
    while True:
        try:
            now = datetime.now(TIMEZONE)
            current_time = now.strftime("%I:%M %p")
            today = now.strftime("%Y-%m-%d")
            
            if now.hour == SEND_HOUR and now.minute == SEND_MINUTE:
                if last_run_date != today:
                    print(f"⏰ TIME TO RUN AUTO-LIKE! ({current_time})")
                    print("🔄 Starting auto-like process...")
                    
                    try:
                        await perform_auto_like(app)
                        last_run_date = today
                        print("✅ Auto-like completed successfully!")
                        
                        try:
                            for owner_id in OWNER_IDS:
                                await app.bot.send_message(
                                    chat_id=owner_id,
                                    text=f"✅ AUTO-LIKE COMPLETED AT {current_time}\n\n📅 Date: {today}\n👑 NIHAL LIKE BOT"
                                )
                        except:
                            pass
                            
                    except Exception as e:
                        print(f"❌ Auto-like error: {e}")
                        try:
                            for owner_id in OWNER_IDS:
                                await app.bot.send_message(
                                    chat_id=owner_id,
                                    text=f"❌ AUTO-LIKE FAILED AT {current_time}\n\nError: {str(e)[:100]}\n👑 NIH LIKE BOT"
                                )
                        except:
                            pass
                    
                    await asyncio.sleep(120)
                else:
                    if now.second == 0:
                        print(f"⏰ Already ran today at {SEND_LIKE_TIME}, waiting for tomorrow...")
                    await asyncio.sleep(60)
                    
            else:
                if now.minute % 5 == 0 and now.second == 0:
                    hours_left = 0
                    minutes_left = 0
                    if now.hour < SEND_HOUR:
                        hours_left = SEND_HOUR - now.hour - 1
                        minutes_left = 60 - now.minute + SEND_MINUTE
                    elif now.hour == SEND_HOUR and now.minute < SEND_MINUTE:
                        minutes_left = SEND_MINUTE - now.minute
                    else:
                        hours_left = 24 - now.hour + SEND_HOUR - 1
                        minutes_left = 60 - now.minute + SEND_MINUTE
                    
                    if minutes_left >= 60:
                        hours_left += 1
                        minutes_left -= 60
                    
                    print(f"⏰ Waiting for {SEND_LIKE_TIME}... ({hours_left}h {minutes_left}m left) Current: {current_time}")
                
                await asyncio.sleep(30)
                
        except Exception as e:
            print(f"❌ Scheduler error: {e}")
            await asyncio.sleep(60)

# ================= 👑 MAIN =================

async def main():
    # Sync groups on startup
    sync_allowed_groups()
    
    print("=" * 50)
    print("🤖 BOT STARTING...")
    print("=" * 50)
    print(f"⏰ Auto-like Time: {SEND_LIKE_TIME}")
    print(f"👑 Owners: {OWNER_IDS}")
    print(f"📊 Allowed Groups: {ALLOWED_GROUP_IDS}")
    print("=" * 50)
    
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # ✅ ALL COMMANDS REGISTERED
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("vip", test_cmd))
    app.add_handler(CommandHandler("like", like_cmd))
    app.add_handler(CommandHandler("autolike", autolike_cmd))
    app.add_handler(CommandHandler("extend", extend_cmd))
    app.add_handler(CommandHandler("extendall", extendall_cmd))
    app.add_handler(CommandHandler("runall", runall_cmd))
    app.add_handler(CommandHandler("state", state_cmd))
    app.add_handler(CommandHandler("list", list_cmd))
    app.add_handler(CommandHandler("remove", remove_cmd))
    app.add_handler(CommandHandler("setlimit", setlimit_cmd))
    app.add_handler(CommandHandler("vipsms", vipsms_cmd))
    app.add_handler(CommandHandler("vipvoice", vipvoice_cmd))
    app.add_handler(CommandHandler("on", on_cmd))
    app.add_handler(CommandHandler("off", off_cmd))
    app.add_handler(CommandHandler("debug", debug_cmd))
    app.add_handler(CommandHandler("getid", getid_cmd))
    app.add_handler(CommandHandler("autolikeinfo", autolikeinfo_cmd))
    
    # ✅ Admin Management Commands
    app.add_handler(CommandHandler("admins", admins_cmd))
    app.add_handler(CommandHandler("addadmin", addadmin_cmd))
    app.add_handler(CommandHandler("removeadmin", removeadmin_cmd))
    app.add_handler(CommandHandler("setadminlimit", setadminlimit_cmd))
    
    # ✅ Group Management Commands
    app.add_handler(CommandHandler("mygroups", mygroups_cmd))
    app.add_handler(CommandHandler("addgroup", addgroup_cmd))
    app.add_handler(CommandHandler("removegroup", removegroup_cmd))
    app.add_handler(CommandHandler("groupstats", groupstats_cmd))
    
    # Callback handlers
    app.add_handler(CallbackQueryHandler(verify_join, pattern="verify_join"))
    app.add_handler(CallbackQueryHandler(group_callback_handler, pattern="add_group"))
    app.add_handler(CallbackQueryHandler(group_callback_handler, pattern="remove_group"))
    app.add_handler(CallbackQueryHandler(admin_callback_handler, pattern="add_admin"))
    app.add_handler(CallbackQueryHandler(admin_callback_handler, pattern="remove_admin"))
    app.add_handler(CallbackQueryHandler(admin_callback_handler, pattern="set_admin_limit"))
    
    app.add_handler(ChatMemberHandler(auto_leave, ChatMemberHandler.MY_CHAT_MEMBER))
    
    # ✅ Start scheduler as a background task
    asyncio.create_task(scheduler(app))

    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    
    print("=" * 50)
    print("✅ BOT STARTED SUCCESSFULLY!")
    print("=" * 50)
    print(f"⏰ Auto-like will run at: {SEND_LIKE_TIME}")
    print(f"👑 Owners: {OWNER_IDS}")
    print(f"📊 Allowed Groups: {len(ALLOWED_GROUP_IDS)} groups")
    for gid in ALLOWED_GROUP_IDS:
        print(f"   - {gid}")
    print("=" * 50)
    print("✅ Commands Registered:")
    print("   /start, /help, /vip, /like, /autolike, /extend")
    print("   /extendall, /runall, /state, /list, /remove")
    print("   /setlimit, /vipsms, /vipvoice, /on, /off")
    print("   /debug, /getid, /mygroups, /addgroup")
    print("   /removegroup, /groupstats, /autolikeinfo")
    print("   /admins, /addadmin, /removeadmin, /setadminlimit")
    print("=" * 50)
    print("🔴 MESSAGE DELETION IS DISABLED")
    print("🎯 Bot is ready to use!")
    print("=" * 50)
    
    await asyncio.Event().wait()

if __name__ == "__main__":
    nest_asyncio.apply()
    asyncio.run(main())
