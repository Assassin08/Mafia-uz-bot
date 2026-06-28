import logging
import asyncio
import re
import os
import random
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ChatPermissions
from aiogram.enums import ChatMemberStatus
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

# Tokenni Render saytida xavfsiz o'qiydi
BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

warns_db = {}

async def is_admin(message: Message) -> bool:
    member = await message.chat.get_member(message.from_user.id)
    return member.status in [ChatMemberStatus.CREATOR, ChatMemberStatus.ADMINISTRATOR]

def parse_time(text: str):
    if not text:
        return None, ""
    match = re.search(r'(\d+)\s*([mhd])', text.lower())
    if not match:
        return None, text
    value = int(match.group(1))
    unit = match.group(2)
    if unit == 'm': duration = timedelta(minutes=value)
    elif unit == 'h': duration = timedelta(hours=value)
    elif unit == 'd': duration = timedelta(days=value)
    else: return None, text
    clean_reason = text.replace(match.group(0), "").strip()
    return duration, clean_reason

# ==================== ADMIN MANAGEMENT ====================

@dp.message(F.text == ".admin")
async def cmd_admin(message: Message):
    if not await is_admin(message) or not message.reply_to_message: return
    try:
        await bot.promote_chat_member(
            chat_id=message.chat.id, user_id=message.reply_to_message.from_user.id,
            can_manage_chat=True, can_delete_messages=True, can_restrict_members=True, can_invite_users=True
        )
        await message.answer(f"✅ {message.reply_to_message.from_user.mention_html()} has been promoted to Admin!")
    except Exception: pass

@dp.message(F.text == ".unadmin")
async def cmd_unadmin(message: Message):
    if not await is_admin(message) or not message.reply_to_message: return
    try:
        await bot.promote_chat_member(
            chat_id=message.chat.id, user_id=message.reply_to_message.from_user.id,
            can_manage_chat=False, can_delete_messages=False, can_restrict_members=False,
            can_promote_members=False, can_invite_users=False, can_change_info=False
        )
        await message.answer(f"❌ {message.reply_to_message.from_user.mention_html()} has been demoted to regular member.")
    except Exception: pass

@dp.message(F.text == ".muter")
async def cmd_muter(message: Message):
    if not await is_admin(message) or not message.reply_to_message: return
    try:
        await bot.promote_chat_member(
            chat_id=message.chat.id, user_id=message.reply_to_message.from_user.id,
            can_manage_chat=True, can_restrict_members=True
        )
        await message.answer(f"🤫 {message.reply_to_message.from_user.mention_html()} now has permission to mute players!")
    except Exception: pass

@dp.message(F.text == ".unmuter")
async def cmd_unmuter(message: Message):
    if not await is_admin(message) or not message.reply_to_message: return
    try:
        await bot.promote_chat_member(
            chat_id=message.chat.id, user_id=message.reply_to_message.from_user.id,
            can_restrict_members=False
        )
        await message.answer(f"❌ {message.reply_to_message.from_user.mention_html()}'s mute permission has been revoked.")
    except Exception: pass

@dp.message(F.text == ".moderator")
async def cmd_moderator(message: Message):
    if not await is_admin(message) or not message.reply_to_message: return
    try:
        await bot.promote_chat_member(
            chat_id=message.chat.id, user_id=message.reply_to_message.from_user.id,
            can_manage_chat=True, can_delete_messages=True, can_restrict_members=True,
            can_promote_members=True, can_invite_users=True, can_change_info=True
        )
        await message.answer(f"👑 {message.reply_to_message.from_user.mention_html()} has been appointed as Moderator!")
    except Exception: pass

@dp.message(F.text == ".unmoderator")
async def cmd_unmoderator(message: Message):
    if not await is_admin(message) or not message.reply_to_message: return
    try:
        await bot.promote_chat_member(
            chat_id=message.chat.id, user_id=message.reply_to_message.from_user.id,
            can_manage_chat=False, can_delete_messages=False, can_restrict_members=False,
            can_promote_members=False, can_invite_users=False, can_change_info=False
        )
        await message.answer(f"❌ {message.reply_to_message.from_user.mention_html()} lost moderator privileges.")
    except Exception: pass


# ==================== MODERATION & PUNISHMENT ====================

@dp.message(F.text.startswith(".mute"))
async def cmd_mute(message: Message):
    if not await is_admin(message) or not message.reply_to_message: return
    args = message.text[5:].strip()
    duration, reason = parse_time(args)
    permissions = ChatPermissions(can_send_messages=False, can_send_media_messages=False, can_send_other_messages=False)
    
    # Vaqt cheklovini hisoblash (Maksimal 365 kun xavfsizlik uchun)
    until_date = datetime.now() + duration if duration else None
    
    try:
        await bot.restrict_chat_member(chat_id=message.chat.id, user_id=message.reply_to_message.from_user.id, permissions=permissions, until_date=until_date)
        
        # Vaqt formatini xatosiz va chiroyli ajratib ko'rsatish
        match = re.search(r'(\d+\s*[mhd])', args.lower())
        time_str = match.group(1) if match else "Forever"
        reason_str = f"\n📝 Reason: {reason}" if reason else ""
        
        await message.answer(f"🤐 {message.reply_to_message.from_user.mention_html()} has been muted!\n⏱ Duration: {time_str}{reason_str}")
    except Exception: pass

@dp.message(F.text == ".unmute")
async def cmd_unmute(message: Message):
    if not await is_admin(message) or not message.reply_to_message: return
    permissions = ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_polls=True, can_send_other_messages=True)
    try:
        await bot.restrict_chat_member(chat_id=message.chat.id, user_id=message.reply_to_message.from_user.id, permissions=permissions)
        await message.answer(f"🔊 {message.reply_to_message.from_user.mention_html()} has been unmuted!")
    except Exception: pass

@dp.message(F.text == ".warn")
async def cmd_warn(message: Message):
    if not await is_admin(message) or not message.reply_to_message: return
    user_id = message.reply_to_message.from_user.id
    warns_db[user_id] = warns_db.get(user_id, 0) + 1
    if warns_db[user_id] >= 3:
        warns_db[user_id] = 0
        try:
            permissions = ChatPermissions(can_send_messages=False, can_send_media_messages=False)
            await bot.restrict_chat_member(chat_id=message.chat.id, user_id=user_id, permissions=permissions, until_date=datetime.now() + timedelta(days=1))
            await message.answer(f"🚨 {message.reply_to_message.from_user.mention_html()} reached 3 warns and has been muted for 24 hours!")
        except Exception: pass
    else:
        await message.answer(f"⚠️ {message.reply_to_message.from_user.mention_html()} received a warning! Total: {warns_db[user_id]}/3")

@dp.message(F.text == ".unwarn")
async def cmd_unwarn(message: Message):
    if not await is_admin(message) or not message.reply_to_message: return
    user_id = message.reply_to_message.from_user.id
    warns_db[user_id] = 0
    await message.answer(f"✅ Warnings for {message.reply_to_message.from_user.mention_html()} have been reset!")

@dp.message(F.text == ".del")
async def cmd_del(message: Message):
    if not await is_admin(message) or not message.reply_to_message: return
    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.reply_to_message.message_id)
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    except Exception: pass

@dp.message(F.text == ".ban")
async def cmd_ban(message: Message):
    if not await is_admin(message) or not message.reply_to_message: return
    try:
        await bot.ban_chat_member(chat_id=message.chat.id, user_id=message.reply_to_message.from_user.id)
        await message.answer(f"🚷 {message.reply_to_message.from_user.mention_html()} has been banned from the club!")
    except Exception: pass

@dp.message(F.text == ".unban")
async def cmd_unban(message: Message):
    if not await is_admin(message) or not message.reply_to_message: return
    try:
        await bot.unban_chat_member(chat_id=message.chat.id, user_id=message.reply_to_message.from_user.id)
        await message.answer(f"🔓 {message.reply_to_message.from_user.mention_html()} has been unbanned!")
    except Exception: pass


# ==================== ADVANCED & INTERACTIVE CONTROLS ====================

@dp.message(F.text == ".night")
async def cmd_night(message: Message):
    if not await is_admin(message): return
    permissions = ChatPermissions(can_send_messages=False, can_send_media_messages=False, can_send_other_messages=False)
    try:
        await bot.set_chat_permissions(chat_id=message.chat.id, permissions=permissions)
        await message.answer(f"🌃 **The city falls asleep... (Night Mode ON)**\nChat locked by {message.from_user.mention_html()}. Keep silence! 🤐")
    except Exception: pass

@dp.message(F.text == ".day")
async def cmd_day(message: Message):
    if not await is_admin(message): return
    permissions = ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_polls=True, can_send_other_messages=True)
    try:
        await bot.set_chat_permissions(chat_id=message.chat.id, permissions=permissions)
        await message.answer(f"🌅 **The sun rises! The city wakes up... (Night Mode OFF)**\nChat opened by {message.from_user.mention_html()}. Discuss the game! 💬")
    except Exception: pass

# ==================== CHANNELS ====================

@dp.message(F.text == ".channels")
async def cmd_channels(message: Message):
    await message.answer(
        "⛓ @mafia_uzbekis Official Club Projects:\n\n"
        "📜 Qoidalar kanali — O'yin shartlari va qonunlar.\n"
        "📸 Zapallar kanali — Qiziqarli lahzalar va fosh etishlar."
    )


# ==================== HELP ====================

@dp.message(F.text == ".help")
async def cmd_help_list(message: Message):
    await message.answer(
        "🕵️‍♂️ @mafia_uzbekis Bot Commands List:\n\n"
        "👑 Admin Management:\n"
        "🔹 .admin / .unadmin\n"
        "🔹 .muter / .unmuter\n"
        "🔹 .moderator / .unmoderator\n\n"
        "🚫 Moderation & Punishment:\n"
        "🔹 .mute [time] [reason] / .unmute\n"
        "🔹 .warn / .unwarn\n"
        "🔹 .ban / .unban\n"
        "🔹 .del\n\n"
        "⚙️ Group Controls & Fun:\n"
        "🔹 .night / .day\n"
        "🔹 .channels\n"
        "🔹 .shoot\n"
        "🔹 .check"
    )


# ==================== FUN COMMANDS ====================

@dp.message(F.text == ".shoot")
async def cmd_shoot(message: Message):
    if not message.reply_to_message:
        await message.reply(
            "❓ Reply to someone's message to shoot them."
        )
        return

    target = message.reply_to_message.from_user.mention_html()
    admin = message.from_user.mention_html()

    await message.answer(
        f"🕵️‍♂️ By the order of Mafia Don {admin}, "
        f"a silent bullet hit {target}... 🔫💀"
    )


@dp.message(F.text == ".check")
async def cmd_check(message: Message):
    if not message.reply_to_message:
        await message.reply(
            "❓ Reply to someone's message to investigate their role."
        )
        return

    target = message.reply_to_message.from_user.mention_html()

    roles = [
        "🔴 BLACK (Mafia)",
        "⚪️ WHITE (Citizen)",
        "🔴 BLACK (Don Mafia)",
        "🔵 BLUE (Doctor)"
    ]

    chosen_role = random.choice(roles)

    await message.answer(
        f"🔍 Detective investigated {target} tonight...\n"
        f"Result: {chosen_role}"
    )


# ==================== SERVER ====================

async def on_startup(bot: Bot) -> None:
    await bot.delete_webhook(drop_pending_updates=True)
    asyncio.create_task(dp.start_polling(bot))

def main():
    app = web.Application()
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path="/webhook")
    setup_application(app, dp, bot=bot)
    app.on_startup.append(lambda _: on_startup(bot))

    port = int(os.getenv("PORT", 10000))
    web.run_app(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
