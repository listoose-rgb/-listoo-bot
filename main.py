#!/usr/bin/env python3
# Listoo Telegram Bot v2 - با سیستم حذف آگهی
# @Listoo_se_bot

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ConversationHandler, filters, ContextTypes
)

TOKEN = "8818399192:AAEWVqY7kWipQgTgWw4iY66FjWFZcGATc7Y"
CHANNEL_ID = "@listoo_se"
ADMIN_ID = 7899749173

logging.basicConfig(level=logging.INFO)

(MAIN_MENU, GET_TITLE, GET_DESC, GET_PRICE, GET_LOCATION, GET_PHOTO, GET_CONTACT, GET_DELETE_ID) = range(8)

# ── START ──
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["📦 Lägg upp annons", "💼 Lägg upp jobb"],
        ["🗑️ Ta bort annons", "🔍 Sök annonser"],
        ["📞 Support"]
    ]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "🟠 Välkommen till *Listoo*!\n\n"
        "Köp, sälj och hitta jobb.\n\n"
        "Välj ett alternativ 👇",
        parse_mode="Markdown",
        reply_markup=markup
    )
    return MAIN_MENU

# ── MAIN MENU ──
async def main_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if "annons" in text and "bort" not in text:
        ctx.user_data['type'] = 'annons'
        await update.message.reply_text("📦 *Ny annons*\n\nSkriv en titel:", parse_mode="Markdown")
        return GET_TITLE
    elif "jobb" in text:
        ctx.user_data['type'] = 'jobb'
        await update.message.reply_text("💼 *Nytt jobb*\n\nSkriv jobbtiteln:", parse_mode="Markdown")
        return GET_TITLE
    elif "bort" in text or "Ta bort" in text:
        await update.message.reply_text(
            "🗑️ *Ta bort annons*\n\n"
            "Skriv titeln pa din annons som du vill ta bort:\n"
            "(Vi skickar en borttagningsbegaran till admin)",
            parse_mode="Markdown"
        )
        return GET_DELETE_ID
    elif "Sök" in text:
        await update.message.reply_text("🔍 Se alla annonser:\n👉 @listoo_se\n\nlistoo.se")
        return MAIN_MENU
    elif "Support" in text:
        await update.message.reply_text(
            "📞 *Support*\n\n"
            "📧 info@listoo.se\n"
            "🌐 listoo.se\n"
            "📢 @listoo_se\n\n"
            "Vi svarar inom 24 timmar!",
            parse_mode="Markdown"
        )
        return MAIN_MENU
    return MAIN_MENU

# ── مراحل ثبت آگهی ──
async def get_title(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data['title'] = update.message.text
    await update.message.reply_text("✍️ Beskriv varan/jobbet:")
    return GET_DESC

async def get_desc(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data['desc'] = update.message.text
    label = "💰 Pris (kr):" if ctx.user_data.get('type') == 'annons' else "💰 Lon (kr/man):"
    await update.message.reply_text(label)
    return GET_PRICE

async def get_price(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data['price'] = update.message.text
    await update.message.reply_text("📍 Stad/ort:")
    return GET_LOCATION

async def get_location(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data['location'] = update.message.text
    await update.message.reply_text("📸 Skicka ett foto!\n(eller /skip)")
    return GET_PHOTO

async def get_photo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        ctx.user_data['photo'] = update.message.photo[-1].file_id
    else:
        ctx.user_data['photo'] = None
    await update.message.reply_text("📬 Din e-post eller telefon:")
    return GET_CONTACT

async def skip_photo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data['photo'] = None
    await update.message.reply_text("📬 Din e-post eller telefon:")
    return GET_CONTACT

# ── درخواست حذف آگهی ──
async def get_delete_id(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    title = update.message.text
    user = update.message.from_user
    username = user.username or user.first_name

    # ارسال درخواست به ادمین
    keyboard = [
        [
            InlineKeyboardButton("✅ حذف کن", callback_data=f"delete_{user.id}_{title[:20]}"),
            InlineKeyboardButton("❌ رد کن", callback_data=f"nodelet_{user.id}")
        ]
    ]
    markup = InlineKeyboardMarkup(keyboard)

    await ctx.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"🗑️ *درخواست حذف آگهی*\n\n"
             f"👤 کاربر: @{username}\n"
             f"📌 عنوان: *{title}*\n\n"
             f"آیا این آگهی رو از کانال حذف کنی؟",
        parse_mode="Markdown",
        reply_markup=markup
    )

    await update.message.reply_text(
        "✅ درخواست حذف ارسال شد!\n\n"
        "ادمین بررسی می‌کنه و آگهیت رو پاک می‌کنه.\n"
        "معمولاً در ۲۴ ساعت انجام میشه! 🟠"
    )
    return MAIN_MENU

# ── ارسال به ادمین برای تأیید ──
async def get_contact(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data['contact'] = update.message.text
    ctx.user_data['user_id'] = update.message.from_user.id
    ctx.user_data['username'] = update.message.from_user.username or update.message.from_user.first_name
    d = ctx.user_data

    ad_type = "📦 ANNONS" if d['type'] == 'annons' else "💼 JOBB"
    price_label = "💰 Pris" if d['type'] == 'annons' else "💰 Lon"

    caption = (
        f"🟠 *{ad_type} — Listoo*\n\n"
        f"📌 *{d['title']}*\n\n"
        f"📝 {d['desc']}\n\n"
        f"{price_label}: *{d['price']} kr*\n"
        f"📍 {d['location']}\n\n"
        f"📬 Kontakt: `{d['contact']}`\n\n"
        f"✅ listoo.se"
    )

    keyboard = [
        [
            InlineKeyboardButton("✅ تأیید و انتشار", callback_data=f"approve_{d['user_id']}"),
            InlineKeyboardButton("❌ رد کردن", callback_data=f"reject_{d['user_id']}")
        ]
    ]
    markup = InlineKeyboardMarkup(keyboard)

    ctx.bot_data[str(d['user_id'])] = {
        'caption': caption,
        'photo': d.get('photo'),
        'user_id': d['user_id']
    }

    admin_text = (
        f"⚠️ *آگهی جدید برای تأیید*\n\n"
        f"👤 کاربر: @{d['username']}\n\n"
        f"{caption}"
    )

    try:
        if d.get('photo'):
            await ctx.bot.send_photo(
                chat_id=ADMIN_ID,
                photo=d['photo'],
                caption=admin_text,
                parse_mode="Markdown",
                reply_markup=markup
            )
        else:
            await ctx.bot.send_message(
                chat_id=ADMIN_ID,
                text=admin_text,
                parse_mode="Markdown",
                reply_markup=markup
            )
    except Exception as e:
        logging.error(f"Error: {e}")

    await update.message.reply_text(
        "✅ *Tack! Din annons granskas.*\n\nVi publicerar den inom kort! 🟠",
        parse_mode="Markdown"
    )
    ctx.user_data.clear()
    return ConversationHandler.END

# ── ادمین تأیید یا رد می‌کنه ──
async def handle_approval(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("approve_") or data.startswith("reject_"):
        action, user_id = data.split('_', 1)
        ad = ctx.bot_data.get(user_id)

        if action == "approve" and ad:
            keyboard = [[InlineKeyboardButton("🌐 Listoo.se", url="https://listoo.se")]]
            markup = InlineKeyboardMarkup(keyboard)
            try:
                if ad.get('photo'):
                    await ctx.bot.send_photo(
                        chat_id=CHANNEL_ID,
                        photo=ad['photo'],
                        caption=ad['caption'],
                        parse_mode="Markdown",
                        reply_markup=markup
                    )
                else:
                    await ctx.bot.send_message(
                        chat_id=CHANNEL_ID,
                        text=ad['caption'],
                        parse_mode="Markdown",
                        reply_markup=markup
                    )
                await ctx.bot.send_message(
                    chat_id=int(user_id),
                    text="🎉 *آگهی شما تأیید و منتشر شد!*\n\n👉 @listoo_se",
                    parse_mode="Markdown"
                )
                await query.edit_message_text("✅ آگهی منتشر شد!")
            except Exception as e:
                logging.error(f"Error: {e}")

        elif action == "reject":
            await ctx.bot.send_message(
                chat_id=int(user_id),
                text="❌ *متأسفانه آگهی شما تأیید نشد.*\n\nبرای اطلاعات: info@listoo.se",
                parse_mode="Markdown"
            )
            await query.edit_message_text("❌ آگهی رد شد!")
        ctx.bot_data.pop(user_id, None)

    elif data.startswith("delete_"):
        parts = data.split('_', 2)
        user_id = parts[1]
        title = parts[2] if len(parts) > 2 else "نامشخص"
        await ctx.bot.send_message(
            chat_id=int(user_id),
            text=f"✅ آگهی *{title}* از کانال حذف شد!\n\nممنون از استفاده از Listoo 🟠",
            parse_mode="Markdown"
        )
        await query.edit_message_text(f"✅ درخواست حذف تأیید شد!\nعنوان: {title}\n\n⚠️ خودت باید پیام رو از کانال پاک کنی!")

    elif data.startswith("nodelet_"):
        user_id = data.split('_')[1]
        await ctx.bot.send_message(
            chat_id=int(user_id),
            text="❌ درخواست حذف رد شد.\n\nبرای اطلاعات بیشتر: info@listoo.se"
        )
        await query.edit_message_text("❌ درخواست حذف رد شد!")

# ── CANCEL ──
async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    await update.message.reply_text("❌ Avbröts. Skriv /start för att börja igen.")
    return ConversationHandler.END

# ── MAIN ──
def main():
    app = Application.builder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu)],
            GET_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_title)],
            GET_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_desc)],
            GET_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_price)],
            GET_LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_location)],
            GET_PHOTO: [
                MessageHandler(filters.PHOTO, get_photo),
                CommandHandler("skip", skip_photo)
            ],
            GET_CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_contact)],
            GET_DELETE_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_delete_id)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(handle_approval))

    print("🟠 Listoo Bot v2 در حال اجراست...")
    app.run_polling()

if __name__ == "__main__":
    main()
