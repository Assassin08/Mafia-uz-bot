# ==================== CHANNELS ====================

@dp.message(F.text == ".channels")
async def cmd_channels(message: Message):
    await message.answer(
        "⛓ @mafia_uzbekis Official Club Projects:\n\n"
        "📜 Qoidalar kanali — O'yin qoidalari va qonunlar.\n"
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


# ==================== SERVER CONNECTION ====================

async def on_startup(bot: Bot):
    await bot.delete_webhook(drop_pending_updates=True)
    asyncio.create_task(dp.start_polling(bot))


def main():
    app = web.Application()

    SimpleRequestHandler(
        dispatcher=dp,
        bot=bot
    ).register(app, path="/webhook")

    setup_application(app, dp, bot=bot)

    app.on_startup.append(
        lambda _: on_startup(bot)
    )

    port = int(os.getenv("PORT", 10000))

    web.run_app(
        app,
        host="0.0.0.0",
        port=port
    )


if __name__ == "__main__":
    main()
