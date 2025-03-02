from telegram import Update
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, filters, \
    CallbackQueryHandler, ApplicationBuilder

from bot.service import PHOTO, photo, start, language, LANGUAGE, fullname, FULLNAME, \
    regenerate, PHOTO_TO_REGENERATE, photo_regenerate, error_handler, admin_response, cancel, leave_group, alll, \
    capture_rejection_reason, search, receive_number, NUMBER, AGE, age, WORK, work, GMAIL, gmail, HUDUD, hudud, DIRECTION, direction, OFFERS, offers
from config import BOT_TOKEN, GROUP_CHAT_ID


def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = ApplicationBuilder().token(BOT_TOKEN).read_timeout(300).write_timeout(300).build()

    application.add_handler(MessageHandler(~filters.ChatType.PRIVATE & ~filters.Chat(GROUP_CHAT_ID), leave_group))

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANGUAGE: [CallbackQueryHandler(language)],
            NUMBER: [CommandHandler('cancel', cancel), MessageHandler(filters.CONTACT, receive_number)],
            FULLNAME: [CommandHandler('cancel', cancel), MessageHandler(filters.TEXT, fullname)],
            AGE: [CommandHandler('cancel', cancel), MessageHandler(filters.TEXT, age)],
            WORK: [CommandHandler('cancel', cancel), MessageHandler(filters.TEXT, work)],
            GMAIL: [CommandHandler('cancel', cancel), MessageHandler(filters.TEXT, gmail)],
            HUDUD: [CommandHandler('cancel', cancel), MessageHandler(filters.TEXT, hudud)],
            DIRECTION: [CommandHandler('cancel', cancel), MessageHandler(filters.TEXT, direction)],
            OFFERS: [CommandHandler('cancel', cancel), MessageHandler(filters.TEXT, offers)],
            PHOTO: [MessageHandler(filters.PHOTO, photo)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        per_message=False
    )

    application.add_handler(CallbackQueryHandler(admin_response, pattern="\d"))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Chat(GROUP_CHAT_ID), capture_rejection_reason))

    application.add_handler(CommandHandler("all", alll))
    application.add_handler(CommandHandler("search", search))


    application.add_handler(conv_handler)
    application.add_error_handler(error_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
