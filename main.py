#!/usr/bin/env python3
# Listoo Telegram Bot v5
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
        "Välkommen till *Listoo*\nKöp, sälj och hitta jobb\n\nVälj kategori 👇",
        parse_mode="Markdown",
        reply_markup=markup
    )
    return MAIN_MENU

async def main_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    categories = {
        "🏠 Bostad": "Bostad",
        "🚗 Fordon": "Fordon",
        "📱 Elektronik": "Elektronik",
        "🛋️ Möbler": "Möbler",
        "💼 Jobb": "Jobb",
        "📦 Övrigt": "Övrigt"
    }
    if text in categories:
        ctx.user_data['category'] = categories[text]
        ctx.user_data['type'] = 'jobb' if text == "💼 Jobb" else 'annons'
        await update.message.reply_text(
            "*" + categories[text] + "*\n\nSkriv en titel:",
            parse_mode="Markdown"
        )
        return GET_TITLE
    elif "bort" in text:
        await update.message.reply_text("Skriv titeln på annonsen du vill ta bort:")
        return GET_DELETE_ID
    elif "Support" in text:
        await update.message.reply_text(
            "*Support*\n\nE-post: info@listoo.se\nWebb: listoo.se",
            parse_mode="Markdown"
        )
        return MAIN_MENU
    return MAIN_MENU

async def get_title(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data['title'] = update.message.text
    await update.message.reply_text("Beskriv varan:")
    return GET_DESC

async def get_desc(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data['desc'] = update.message.text
    label = "Lön (kr/mån):" if ctx.user_data.get('type') == 'jobb' else "Pris (kr):"
    await update.message.reply_text(label)
    return GET_PRICE

async def get_price(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data['price'] = update.message.text
    await update.message.reply_text("Ort/stad:")
    return GET_LOCATION

async def get_location(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data['location'] = update.message.text
    await update.message.reply_text("Skicka ett foto\n(eller /skip för att hoppa över)")
    return GET_PHOTO

async def get_photo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        ctx.user_data['photo'] = update.message.photo[-1].file_id
    else:
        ctx.user_data['photo'] = None
    await update.message.reply_text("Din e-post eller telefon:")
    return GET_CONTACT

async def skip_photo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data['photo'] = None
    await update.message.reply_text("Din e-post eller telefon:")
    return GET_CONTACT

async def get_delete_id(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    title = update.message.text
    user = update.message.from_user
    username = user.username or user.first_name
    keyboard = [[
        InlineKeyboardButton("Ta bort", callback_data="delete_" + str(user.id) + "_" + title[:20]),
        InlineKeyboardButton("Avbryt", callback_data="nodelet_" + str(user.id))
    ]]
    await ctx.bot.send_message(
        chat_id=ADMIN_ID,
        text="Borttagningsbegäran\n\nAnvändare: @" + username + "\nTitel: " + title,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    markup = ReplyKeyboardMarkup(MENU_KEYBOARD, resize_keyboard=True)
    await update.message.reply_text("Din begäran är skickad!", reply_markup=markup)
    return MAIN_MENU

async def get_contact(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data['contact'] = update.message.text
    ctx.user_data['user_id'] = update.message.from_user.id
    ctx.user_data['username'] = update.message.from_user.username or update.message.from_user.first_name
    d = ctx.user_data

    cat = d.get('category', 'Övrigt')
    price_label = "Lön" if d['type'] == 'jobb' else "Pris"

    # Blocket-style short caption - clean and minimal
    short_caption = (
        "*" + d['title'] + "*\n"
        + price_label + ": " + d['price'] + " kr\n"
        + d['location']
    )

    # Full info stored in callback_data style - encoded in button
    full_text = (
        d['title'] + "\n\n"
        + d['desc'] + "\n\n"
        + price_label + ": " + d['price'] + " kr\n"
        + "Ort: " + d['location'] + "\n\n"
        + "Kontakt: " + d['contact']
    )

    # Store full info
    ad_id = str(d['user_id'])
    ctx.bot_data[ad_id] = {
        'short': short_caption,
        'full': full_text,
        'photo': d.get('photo'),
        'user_id': d['user_id'],
        'cat': cat
    }

    keyboard_admin = [[
        InlineKeyboardButton("Godkänn", callback_data="approve_" + ad_id),
        InlineKeyboardButton("Neka", callback_data="reject_" + ad_id)
    ]]

    admin_text = (
        "Ny annons - " + cat + "\n"
        + "Användare: @" + d['username'] + "\n\n"
        + full_text
    )

    try:
        if d.get('photo'):
            await ctx.bot.send_photo(
                chat_id=ADMIN_ID, photo=d['photo'],
                caption=admin_text,
                reply_markup=InlineKeyboardMarkup(keyboard_admin)
            )
        else:
            await ctx.bot.send_message(
                chat_id=ADMIN_ID, text=admin_text,
                reply_markup=InlineKeyboardMarkup(keyboard_admin)
            )
    except Exception as e:
        logging.error(str(e))

    markup = ReplyKeyboardMarkup(MENU_KEYBOARD, resize_keyboard=True)
    await update.message.reply_text(
        "Tack! Din annons granskas och publiceras inom kort.\n\nVälj kategori för ny annons 👇",
        reply_markup=markup
    )
    ctx.user_data.clear()
    return MAIN_MENU

async def handle_approval(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("approve_"):
        ad_id = data.replace("approve_", "")
        ad = ctx.bot_data.get(ad_id)
        if ad:
            # Blocket-style channel post
            keyboard_ch = [[
                InlineKeyboardButton("Kontaktinfo", callback_data="info_" + ad_id),
                InlineKeyboardButton("listoo.se", url="https://listoo.se")
            ]]
            markup_ch = InlineKeyboardMarkup(keyboard_ch)
            try:
                if ad.get('photo'):
                    await ctx.bot.send_photo(
                        chat_id=CHANNEL_ID,
                        photo=ad['photo'],
                        caption=ad['short'],
                        parse_mode="Markdown",
                        reply_markup=markup_ch
                    )
                else:
                    await ctx.bot.send_message(
                        chat_id=CHANNEL_ID,
                        text=ad['short'],
                        parse_mode="Markdown",
                        reply_markup=markup_ch
                    )
                await ctx.bot.send_message(
                    chat_id=int(ad_id),
                    text="Din annons är nu publicerad!\n\n@listoo_se"
                )
                await query.edit_message_text("Annons publicerad!")
            except Exception as e:
                logging.error(str(e))

    elif data.startswith("reject_"):
        ad_id = data.replace("reject_", "")
        ad = ctx.bot_data.get(ad_id)
        if ad:
            await ctx.bot.send_message(
                chat_id=int(ad_id),
                text="Din annons godkändes inte.\nKontakta oss: info@listoo.se"
            )
        await query.edit_message_text("Annons nekad.")
        ctx.bot_data.pop(ad_id, None)

    elif data.startswith("info_"):
        ad_id = data.replace("info_", "")
        ad = ctx.bot_data.get(ad_id)
        if ad:
            await query.answer(ad.get('full', 'Info ej tillgänglig'), show_alert=True)
        else:
            await query.answer("Info ej tillgänglig längre.", show_alert=True)

    elif data.startswith("delete_"):
        parts = data.split("_", 2)
        user_id = parts[1]
        title = parts[2] if len(parts) > 2 else ""
        await ctx.bot.send_message(chat_id=int(user_id), text="Din annons har tagits bort.")
        await query.edit_message_text("Annons borttagen. Ta bort manuellt från kanalen.")

    elif data.startswith("nodelet_"):
        user_id = data.replace("nodelet_", "")
        await ctx.bot.send_message(chat_id=int(user_id), text="Borttagningsbegäran nekad.")
        await query.edit_message_text("Nekad.")

async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    markup = ReplyKeyboardMarkup(MENU_KEYBOARD, resize_keyboard=True)
    await update.message.reply_text("Avbröts.", reply_markup=markup)
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
    print("Listoo Bot v5 running...")
    app.run_polling()

if __name__ == "__main__":
    main()

