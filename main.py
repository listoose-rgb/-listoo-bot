#!/usr/bin/env python3
# Listoo Telegram Bot v4
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

(MAIN_MENU, GET_TITLE, GET_DESC, GET_PRICE, GET_LOCATION,
 GET_PHOTO, GET_CONTACT, GET_DELETE_ID) = range(8)

MENU_KEYBOARD = [
    ["🏠 Bostad", "🚗 Fordon"],
    ["📱 Elektronik", "🛋️ Möbler"],
    ["💼 Jobb", "📦 Övrigt"],
    ["🗑️ Ta bort annons", "📞 Support"]
]

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    markup = ReplyKeyboardMarkup(MENU_KEYBOARD, resize_keyboard=True)
    await update.message.reply_text(
        "🟠 Välkommen till *Listoo*!\n\nKöp, sälj och hitta jobb.\n\nVälj en kategori 👇",
        parse_mode="Markdown",
        reply_markup=markup
    )
    return MAIN_MENU

async def main_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    categories = {
        "🏠 Bostad": "bostad",
        "🚗 Fordon": "fordon",
        "📱 Elektronik": "elektronik",
        "🛋️ Möbler": "möbler",
        "💼 Jobb": "jobb",
        "📦 Övrigt": "övrigt"
    }
    if text in categories:
        ctx.user_data['category'] = categories[text]
        ctx.user_data['type'] = 'jobb' if text == "💼 Jobb" else 'annons'
        await update.message.reply_text(
            text + "\n\nSkriv en titel för din annons:",
            parse_mode="Markdown"
        )
        return GET_TITLE
    elif "bort" in text:
        await update.message.reply_text("🗑️ Skriv titeln på annonsen du vill ta bort:")
        return GET_DELETE_ID
    elif "Support" in text:
        await update.message.reply_text(
            "📞 *Support*\n\n📧 info@listoo.se\n🌐 listoo.se\n📢 @listoo_se",
            parse_mode="Markdown"
        )
        return MAIN_MENU
    return MAIN_MENU

async def get_title(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data['title'] = update.message.text
    await update.message.reply_text("✍️ Beskriv varan:")
    return GET_DESC

async def get_desc(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data['desc'] = update.message.text
    label = "💰 Lön (kr/mån):" if ctx.user_data.get('type') == 'jobb' else "💰 Pris (kr):"
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

async def get_delete_id(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    title = update.message.text
    user = update.message.from_user
    username = user.username or user.first_name
    keyboard = [[
        InlineKeyboardButton("✅ حذف کن", callback_data="delete_" + str(user.id) + "_" + title[:20]),
        InlineKeyboardButton("❌ رد کن", callback_data="nodelet_" + str(user.id))
    ]]
    await ctx.bot.send_message(
        chat_id=ADMIN_ID,
        text="🗑️ درخواست حذف\n\n👤 @" + username + "\n📌 " + title,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    markup = ReplyKeyboardMarkup(MENU_KEYBOARD, resize_keyboard=True)
    await update.message.reply_text(
        "✅ درخواست حذف ارسال شد!\nادمین بررسی می‌کنه. 🟠",
        reply_markup=markup
    )
    return MAIN_MENU

async def get_contact(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data['contact'] = update.message.text
    ctx.user_data['user_id'] = update.message.from_user.id
    ctx.user_data['username'] = update.message.from_user.username or update.message.from_user.first_name
    d = ctx.user_data

    cat = d.get('category', 'ovrigt').upper()
    cat_emojis = {
        'BOSTAD': '🏠', 'FORDON': '🚗', 'ELEKTRONIK': '📱',
        'MOBLER': '🛋️', 'JOBB': '💼', 'OVRIGT': '📦'
    }
    emoji = cat_emojis.get(cat, '📦')
    price_label = "💰 Lön" if d['type'] == 'jobb' else "💰 Pris"

    short_caption = emoji + " *" + d['title'] + "*\n" + price_label + ": *" + d['price'] + " kr*\n📍 " + d['location'] + "\n\n🟠 listoo.se"
    full_info = emoji + " *" + d['title'] + "*\n\n📝 " + d['desc'] + "\n\n" + price_label + ": *" + d['price'] + " kr*\n📍 " + d['location'] + "\n\n📬 Kontakt: `" + d['contact'] + "`\n\n✅ listoo.se"

    ad_id = str(d['user_id'])
    ctx.bot_data[ad_id] = {
        'caption': short_caption,
        'full_info': full_info,
        'photo': d.get('photo'),
        'user_id': d['user_id']
    }

    keyboard = [[
        InlineKeyboardButton("✅ تأیید", callback_data="approve_" + ad_id),
        InlineKeyboardButton("❌ رد", callback_data="reject_" + ad_id)
    ]]

    admin_text = "⚠️ آگهی جدید — " + emoji + " " + cat + "\n\n👤 @" + d['username'] + "\n\n" + full_info

    try:
        if d.get('photo'):
            await ctx.bot.send_photo(
                chat_id=ADMIN_ID, photo=d['photo'],
                caption=admin_text, parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await ctx.bot.send_message(
                chat_id=ADMIN_ID, text=admin_text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    except Exception as e:
        logging.error(str(e))

    markup = ReplyKeyboardMarkup(MENU_KEYBOARD, resize_keyboard=True)
    await update.message.reply_text(
        "✅ *Tack! Din annons granskas.*\n\nVi publicerar den inom kort! 🟠\n\nVälj kategori för ny annons 👇",
        parse_mode="Markdown",
        reply_markup=markup
    )
    ctx.user_data.clear()
    return MAIN_MENU

async def handle_approval(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("approve_"):
        user_id = data.replace("approve_", "")
        ad = ctx.bot_data.get(user_id)
        if ad:
            keyboard = [[
                InlineKeyboardButton("📋 Visa mer info", callback_data="info_" + user_id),
                InlineKeyboardButton("🌐 Listoo.se", url="https://listoo.se")
            ]]
            markup = InlineKeyboardMarkup(keyboard)
            try:
                if ad.get('photo'):
                    await ctx.bot.send_photo(
                        chat_id=CHANNEL_ID, photo=ad['photo'],
                        caption=ad['caption'], parse_mode="Markdown",
                        reply_markup=markup
                    )
                else:
                    await ctx.bot.send_message(
                        chat_id=CHANNEL_ID, text=ad['caption'],
                        parse_mode="Markdown", reply_markup=markup
                    )
                await ctx.bot.send_message(
                    chat_id=int(user_id),
                    text="🎉 آگهی شما منتشر شد!\n\n👉 @listoo_se",
                    parse_mode="Markdown"
                )
                await query.edit_message_text("✅ آگهی منتشر شد!")
            except Exception as e:
                logging.error(str(e))
        ctx.bot_data.pop(user_id, None)

    elif data.startswith("reject_"):
        user_id = data.replace("reject_", "")
        await ctx.bot.send_message(
            chat_id=int(user_id),
            text="❌ آگهی شما تأیید نشد.\n\nاطلاعات: info@listoo.se"
        )
        await query.edit_message_text("❌ آگهی رد شد!")
        ctx.bot_data.pop(user_id, None)

    elif data.startswith("info_"):
        user_id = data.replace("info_", "")
        ad = ctx.bot_data.get(user_id)
        if ad:
            await query.answer(ad.get('full_info', 'اطلاعات موجود نیست'), show_alert=True)
        else:
            await query.answer("اطلاعات در دسترس نیست", show_alert=True)

    elif data.startswith("delete_"):
        parts = data.split("_", 2)
        user_id = parts[1]
        title = parts[2] if len(parts) > 2 else "نامشخص"
        await ctx.bot.send_message(
            chat_id=int(user_id),
            text="✅ آگهی " + title + " حذف شد! 🟠"
        )
        await query.edit_message_text("✅ حذف تأیید شد!\n⚠️ خودت از کانال پاک کن!")

    elif data.startswith("nodelet_"):
        user_id = data.replace("nodelet_", "")
        await ctx.bot.send_message(
            chat_id=int(user_id),
            text="❌ درخواست حذف رد شد."
        )
        await query.edit_message_text("❌ درخواست رد شد!")

async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    markup = ReplyKeyboardMarkup(MENU_KEYBOARD, resize_keyboard=True)
    await update.message.reply_text("❌ Avbröts.", reply_markup=markup)
    return MAIN_MENU

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
        fallbacks=[CommandHandler("cancel", cancel), CommandHandler("start", start)],
        allow_reentry=True,
    )
    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(handle_approval))
    print("🟠 Listoo Bot v4 در حال اجراست...")
    app.run_polling()

if __name__ == "__main__":
    main()

