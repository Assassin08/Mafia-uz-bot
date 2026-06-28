import logging
import asyncio
import re
import os
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ChatPermissions
from aiogram.enums import ChatMemberStatus

# Tokenni Render saytida xavfsiz kiritamiz
BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

warns_db = {}

async def is_admin(message: Message) -> bool:
    member = await message.chat.get_member(message.from_user.id)
    return member.status in [ChatMemberStatus.CREATOR, ChatMemberStatus.ADMINISTRATOR]

def parse_time(text: str):
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

@dp.message(F.text == ".admin")
async def cmd_admin(message: Message):
    if not await is_admin(message) or not message.reply_to_message: return
    try:
        await bot.promote_chat_member(
            chat_id=message.chat.id, user_id=message.reply_to_message.from_user.id,
            can_manage_chat=True, can_delete_messages=True, can_restrict_members=True, can_invite_users=True
        )
        await message.answer(f"✅ {message.reply_to_message.from_user.mention_html()} admin qilindi!")
    except Exception: pass

@dp.message(F.text == ".muter")
async def cmd_muter(message: Message):
    if not await is_admin(message) or not message.reply_to_message: return
    try:
        await bot.promote_chat_member(
            chat_id=message.chat.id, user_id=message.reply_to_message.from_user.id,
            can_manage_chat=True, can_restrict_members=True
        )
        await message.answer(f"🤫 {message.reply_to_message.from_user.mention_html()} endi mute qila oladi!")
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
        await message.answer(f"👑 {message.reply_to_message.from_user.mention_html()} moderator qilindi!")
    except Exception: pass

@dp.message(F.text.in_([".unadmin", ".unmuter", ".unmoderator"]))
async def cmd_unadmin(message: Message):
    if not await is_admin(message) or not message.reply_to_message: return
    try:
        await bot.promote_chat_member(
            chat_id=message.chat.id, user_id=message.reply_to_message.from_user.id,
            can_manage_chat=False, can_delete_messages=False, can_restrict_members=False,
            can_promote_members=False, can_invite_users=False, can_change_info=False
        )
        await message.answer(f"❌ {message.reply_to_message.from_user.mention_html()} huquqlari olib tashlandi.")
    except Exception: pass

@dp.message(F.text.startswith(".mute"))
async def cmd_mute(message: Message):
    if not await is_admin(message) or not message.reply_to_message: return
    args = message.text[5:].strip()
    duration, reason = parse_time(args)
    permissions = ChatPermissions(can_send_messages=False, can_send_media_messages=False, can_send_other_messages=False)
    until_date = datetime.now() + duration if duration else None
    try:
        await bot.restrict_chat_member(chat_id=message.chat.id, user_id=message.reply_to_message.from_user.id, permissions=permissions, until_date=until_date)
        time_str = f"{duration}" if duration else "Abadiy"
        reason_str = f"\n📝 Sabab: {reason}" if reason else ""
        await message.answer(f"🤐 {message.reply_to_message.from_user.mention_html()} mute qilindi!\n⏱ Muddat: {time_str}{reason_str}")
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
            await message.answer(f"🚨 {message.reply_to_message.from_user.mention_html()} 3ta ogohlantirish bilan 24 soatga mute qilindi!")
        except Exception: pass
    else:
        await message.answer(f"⚠️ {message.reply_to_message.from_user.mention_html()} ogohlantirish oldi: {warns_db[user_id]}/3")

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
        await message.answer(f"🚷 {message.reply_to_message.from_user.mention_html()} BAN qilindi!")
    except Exception: pass

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
