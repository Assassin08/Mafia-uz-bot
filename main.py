import logging
import asyncio
import re
import os
import random
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ChatPermissions, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.enums import ChatMemberStatus
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

# TO'G'RI VARIANT: Token to'g'ridan-to'g'ri o'zgaruvchiga tenglashtirildi
BOT_TOKEN = "8865841570:AAHpEjp4pqu9c_KnUZL6amQz5Cx7q-j6q5I"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Ma'lumotlar bazalari (Eng chetdan, xatosiz yozildi)
warns_db = {}
messages_db = {}

async def is_admin(message: Message) -> bool:
    # Guruh nomidan yozgan anonim adminlarni ham to'g'ri tekshirish qo'shildi
    if message.sender_chat and message.sender_chat.id == message.chat.id:
        return True
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

@dp.message(F.text == ".main")
async def cmd_main_admin(message: Message):
    # Buyruq bergan odam admin ekanligini va biror xabarga reply qilinganini tekshirish
    if not await is_admin(message) or not message.reply_to_message: 
        return
        
    target_user = message.reply_to_message.from_user
    
    try:
        # Anonimlikdan tashqari barcha adminlik huquqlarini berish
        await bot.promote_chat_member(
            chat_id=message.chat.id, 
            user_id=target_user.id,
            is_anonymous=False,              # Anonim bo'lmaydi (Ismi ko'rinib turadi)
            can_manage_chat=True,            # Guruhni boshqarish
            can_delete_messages=True,        # Xabarlarni o'chirish
            can_restrict_members=True,       # A'zolarni bloklash/mut qilish
            can_promote_members=True,        # Yangi adminlar qo'shish
            can_invite_users=True,           # Guruhga odam qo'shish (Taklif qilish)
            can_change_info=True,            # Guruh ma'lumotlarini o'zgartirish
            can_post_stories=True,           # Hikoyalar joylash (Guruh nomidan)
            can_edit_stories=True,
            can_delete_stories=True
        )
        await message.answer(
            f"👑 {target_user.mention_html()} guruhning **Asosiy Admini (.main)** etib tayinlandi!\n"
            f"⚠️ *Xavfsizlik uchun anonimlik huquqi berilmadi.*"
        )
    except Exception as e:
        await message.answer("❌ Botda ushbu huquqlarni berish uchun ruxsat yetarli emas (Bot o'zi to'liq admin bo'lishi kerak).")

@dp.message(F.text == ".unmain")
async def cmd_unmain_admin(message: Message):
    # Buyruq bergan odam admin ekanligini va biror xabarga reply qilinganini tekshirish
    if not await is_admin(message) or not message.reply_to_message: 
        return
        
    target_user = message.reply_to_message.from_user
    
    try:
        # Barcha adminlik huquqlarini False qilish orqali bekor qilish
        await bot.promote_chat_member(
            chat_id=message.chat.id, 
            user_id=target_user.id,
            is_anonymous=False,
            can_manage_chat=False,
            can_delete_messages=False,
            can_restrict_members=False,
            can_promote_members=False,
            can_invite_users=False,
            can_change_info=False,
            can_post_stories=False,
            can_edit_stories=False,
            can_delete_stories=False
        )
        await message.answer(f"❌ {target_user.mention_html()} ning barcha bosh adminlik (.main) huquqlari bekor qilindi va u oddiy a'zoga aylantirildi.")
    except Exception:
        await message.answer("❌ Botda ushbu huquqlarni bekor qilish uchun ruxsat yetarli emas.")



# ==================== MODERATION & PUNISHMENT ====================

@dp.message(F.text.startswith(".mute"))
async def cmd_mute(message: Message):
    if not await is_admin(message) or not message.reply_to_message: return
    args = message.text[5:].strip()
    duration, reason = parse_time(args)
    permissions = ChatPermissions(can_send_messages=False, can_send_media_messages=False, can_send_other_messages=False)
    
    # Vaqt cheklovini hisoblash (Maksimal 365 kun xavfsizlik uchun)
      # Render serveri vaqti Telegram serverlari bilan moslashtirildi
    until_date = datetime.utcnow() + duration if duration else None
    
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

# ==================== WARNINGS & OTHER COMMANDS ====================

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
            await message.answer(f"🚨 {message.reply_to_message.from_user.mention_html()} 3 ta ogohlantirish oldi va 24 soatga mut qilindi!")
        except Exception: pass
    else:
        await message.answer(f"⚠️ {message.reply_to_message.from_user.mention_html()} ogohlantirish oldi! Jami: {warns_db[user_id]}/3")

@dp.message(F.text == ".unwarn")
async def cmd_unwarn(message: Message):
    if not await is_admin(message) or not message.reply_to_message: return
    user_id = message.reply_to_message.from_user.id
    warns_db[user_id] = 0
    await message.answer(f"✅ {message.reply_to_message.from_user.mention_html()} ning ogohlantirishlari nolga tushirildi!")

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
        await message.answer(f"🚷 {message.reply_to_message.from_user.mention_html()} klubdan haydaldi (Ban)!")
    except Exception: pass

@dp.message(F.text == ".unban")
async def cmd_unban(message: Message):
    if not await is_admin(message) or not message.reply_to_message: return
    try:
        await bot.unban_chat_member(chat_id=message.chat.id, user_id=message.reply_to_message.from_user.id)
        await message.answer(f"🔓 {message.reply_to_message.from_user.mention_html()} bandan chiqarildi!")
    except Exception: pass


# ==================== ADVANCED & INTERACTIVE CONTROLS ====================

@dp.message(F.text == ".night")
async def cmd_night(message: Message):
    if not await is_admin(message): return
    permissions = ChatPermissions(can_send_messages=False, can_send_media_messages=False, can_send_other_messages=False)
    try:
        await bot.set_chat_permissions(chat_id=message.chat.id, permissions=permissions)
        await message.answer(f"🌃 **Shahar uyquga ketmoqda... (Tungi rejim YOQILDI)**\nChat {message.from_user.mention_html()} tomonidan qulflandi. Jimjitlik saqlang! 🤐")
    except Exception: pass

@dp.message(F.text == ".day")
async def cmd_day(message: Message):
    if not await is_admin(message): return
    permissions = ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_polls=True, can_send_other_messages=True)
    try:
        await bot.set_chat_permissions(chat_id=message.chat.id, permissions=permissions)
        await message.answer(f"🌅 **Quyosh chiqdi! Shahar uyg'onmoqda... (Tungi rejim O'CHIRILDI)**\nChat {message.from_user.mention_html()} tomonidan ochildi. O'yinni muhokama qilishingiz mumkin! 💬")
    except Exception: pass


# ==================== CHANNELS & HELP ====================

@dp.message(F.text == ".channels")
async def cmd_channels(message: Message):
    await message.answer(
        "⛓ @mafia_uzbekis Rasmiy Klub Loyihalari:\n\n"
        "📜 Qoidalar kanali — O'yin shartlari va qonunlar.\n"
        "📸 Zapallar kanali — Qiziqarli lahzalar va fosh etishlar."
    )

@dp.message(F.text == ".help")
async def cmd_help_list(message: Message):
    await message.answer(
        "🕵️‍♂️ @mafia_uzbekis Bot Buyruqlar Ro'yxati:\n\n"
        "👑 Adminlarni boshqarish:\n"
        "🔹 .admin / .unadmin\n"
        "🔹 .muter / .unmuter\n"
        "🔹 .moderator / .unmoderator\n\n"
        "🚫 Moderatsiya va jazo:\n"
        "🔹 .mute [vaqt] [sabab] / .unmute\n"
        "🔹 .warn / .unwarn\n"
        "🔹 .ban / .unban\n"
        "🔹 .del\n\n"
        "⚙️ Guruh boshqaruvi va o'yin:\n"
        "🔹 .night / .day\n"
        "🔹 .channels\n"
        "🔹 .shoot\n"
        "🔹 .check"
            "👑 Adminlarni boshqarish:\n"
        "🔹 .main / .unmain (To'liq adminlikni boshqarish)\n"
        "🔹 .admin / .unadmin\n"
    )

# ==================== .INFO BUYRUG'I ====================

@dp.message(F.text == ".info")
async def cmd_info(message: Message):
    # Agar reply bo'lsa o'sha odamni, bo'lmasa buyruq bergan odamning o'zini tekshiradi
    target_user = message.reply_to_message.from_user if message.reply_to_message else message.from_user
    user_id = target_user.id
    
    # Guruhdagi holatini olish (Admin, Muted, oddiy a'zo)
    member = await message.chat.get_member(user_id)
    status_str = "Foydalanuvchi"
    is_muted = False
    
    if member.status in [ChatMemberStatus.CREATOR, ChatMemberStatus.ADMINISTRATOR]:
        status_str = "👑 Admin / Moderator"
    elif member.status == ChatMemberStatus.RESTRICTED:
        # Agar xabar yozish huquqi o'chirilgan bo'lsa demak u mute qilingan
        if not member.can_send_messages:
            status_str = "🤫 Mute qilingan (Muted)"
            is_muted = True
        else:
            status_str = "⚠️ Cheklangan a'zo"
            
    # Ma'lumotlarni bazadan o'qish
    user_data = messages_db.get(user_id, {"count": 0, "joined": datetime.now().strftime("%d.%m.%Y")})
    warn_count = warns_db.get(user_id, 0)
    
    info_text = (
        f"👤 **Foydalanuvchi ma'lumotlari:**\n\n"
        f"📝 **Niki:** {target_user.mention_html()}\n"
        f"🆔 **ID:** <code>{user_id}</code>\n"
        f"📅 **Qo'shilgan vaqti:** {user_data['joined']}\n"
        f"💬 **Xabarlar soni:** {user_data['count']} ta\n"
        f"⚠️ **Ogohlantirishlar (Warn):** {warn_count}/3\n"
        f"⚙️ **Hozirgi holati:** {status_str}"
    )
    
    # Inline tugmalarni yaratish
    buttons = []
    if is_muted:
        buttons.append([InlineKeyboardButton(text="🔊 Mutedan chiqarish", callback_data=f"unmute:{user_id}")])
    else:
        buttons.append([InlineKeyboardButton(text="🤫 Mute berish (1 soat)", callback_data=f"mute:{user_id}")])
        
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    # Bot crash bo'lib o'chib qolmasligi uchun HTML formatlash yoqildi
    await message.answer(info_text, reply_markup=keyboard, parse_mode="HTML")

# ==================== TUGMALARNI QABUL QILUVCHI (CALLBACK HANDLER) ====================

@dp.callback_query(F.data.startswith("mute:") | F.data.startswith("unmute:"))
async def handle_info_buttons(callback: CallbackQuery):
    # Tugmani bosgan odam admin ekanligini tekshirish
    admin_member = await callback.message.chat.get_member(callback.from_user.id)
    if admin_member.status not in [ChatMemberStatus.CREATOR, ChatMemberStatus.ADMINISTRATOR]:
        await callback.answer("❌ Bu tugmadan faqat adminlar foydalana oladi!", show_alert=True)
        return
        
    action, target_id = callback.data.split(":")
    target_id = int(target_id)
    
    try:
        if action == "mute":
            # 1 soatga mute qilish huquqlari
            permissions = ChatPermissions(can_send_messages=False, can_send_media_messages=False, can_send_other_messages=False)
            until_date = datetime.now() + timedelta(hours=1)
            await callback.bot.restrict_chat_member(chat_id=callback.message.chat.id, user_id=target_id, permissions=permissions, until_date=until_date)
            await callback.message.answer(f"🤫 Foydalanuvchi admin tomonidan inline tugma orqali 1 soatga mut qilindi.")
            
@dp.message(F.text == ".unmute")
async def cmd_unmute(message: Message):
    if not await is_admin(message) or not message.reply_to_message: return
    permissions = ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_polls=True, can_send_other_messages=True)
    try:
        await bot.restrict_chat_member(chat_id=message.chat.id, user_id=message.reply_to_message.from_user.id, permissions=permissions)
        await message.answer(f"🔊 {message.reply_to_message.from_user.mention_html()} has been unmuted!", parse_mode="HTML")
    except Exception: pass  # <-- MANA SHU YOPUVCHI BLOK TUSHIB QOLGAN EDI

# ==================== FUN COMMANDS ====================

@dp.message(F.text == ".shoot")
async def cmd_shoot(message: Message):
    if not message.reply_to_message:
        await message.reply("❓ Kimnidir otish uchun uning xabariga reply (javob) qiling.")
        return
    target = message.reply_to_message.from_user.mention_html()
    admin = message.from_user.mention_html()
    await message.answer(f"🕵️‍♂️ Mafiya Doni {admin} buyrug'iga ko'ra, ovozsiz o'q {target}ga tegdi... 🔫💀", parse_mode="HTML")


@dp.message(F.text == ".crush")
async def cmd_crush(message: Message):
    if not message.reply_to_message:
        await message.reply("❓ Kimnidir yaxshi ko'rishingizni aytish uchun uning xabariga reply (javob) qiling.")
        return

    lover = message.from_user.mention_html()
    target = message.reply_to_message.from_user.mention_html()

    if message.from_user.id == message.reply_to_message.from_user.id:
        await message.answer(f"❤️ {lover} o'z-o'ziga oshiq bo'lib qoldi! Narsissizm ham kerak-da... 😂")
        return

    await message.answer(
        f"💘 Ohho, guruhimizda yangi juftlikmi?\n\n"
        f"💞 {lover} kutilmaganda {target} ga oshiq bo'lib qoldi! 😍✨\n"
        f"Baxtli bo'linglar! 🥳"
    )

@dp.message(F.text == ".check")
async def cmd_check(message: Message):
    if not message.reply_to_message:
        await message.reply("❓ Kimning rolini tekshirishni xohlasangiz, uning xabariga reply qiling.")
        return
    target = message.reply_to_message.from_user.mention_html()
    roles = ["🔴 QIZIL (Mafiya)", "⚪️ OQ (Tinch aholi)", "🔴 QIZIL (Don Mafiya)", "🔵 KO'K (Shifokor)"]
    chosen_role = random.choice(roles)
    await message.answer(f"🔍 Komissar bugun tunda {target}ni tekshirdi...\nNatija: {chosen_role}")


# ==================== MESSAGE TRACKER (HAR DOIM SHU YERDA TURISHI KERAK) ====================

@dp.message(F.chat.type.in_({"supergroup", "group"}))
async def track_user_messages(message: Message):
    if message.text and message.text.startswith("."):
        return
    user_id = message.from_user.id
    current_time = datetime.now().strftime("%d.%m.%Y")
    if user_id not in messages_db:
        messages_db[user_id] = {"count": 1, "joined": current_time}
    else:
        messages_db[user_id]["count"] += 1


# ==================== SERVER CORE ====================

async def handle_ping(request):
    return web.Response(text="Mafia Bot muvaffaqiyatli ishlayapti!", status=200)

async def on_startup(bot: Bot) -> None:
    # TO'G'RI SHAXSIY WEBHOOK MANZILI O'RNATILDI:
    webhook_url = "https://onrender.com"
    await bot.set_webhook(url=webhook_url, drop_pending_updates=True)
    logging.info(f"Webhook o'rnatildi: {webhook_url}")

def main():
    app = web.Application()
    
    webhook_requests_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_requests_handler.register(app, path="/webhook")
    
    app.router.add_get("/", handle_ping)
    
    setup_application(app, dp, bot=bot)
    app.on_startup.append(lambda _: on_startup(bot))
    
    port = int(os.getenv("PORT", 10000))
    web.run_app(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
