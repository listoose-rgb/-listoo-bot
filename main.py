#!/usr/bin/env python3
# Listoo Telegram Bot v7 - Multi photo + Save + Hidden contact
# @Listoo_se_bot

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, InputMediaPhoto
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ConversationHandler, filters, ContextTypes
)

TOKEN = "8818399192:AAEWVqY7kWipQgTgWw4iY66FjWFZcGATc7Y"
CHANNEL_ID = "@listoo_se"
ADMIN_ID = 7899749173

logging.basicConfig(level=logging.INFO)

(MAIN_MENU, GET_TITLE, GET_DESC, GET_PRICE, GET_LOCATION,
 GET_PHOTOS, GET_CONTACT, GET_DELETE_ID) = range(8)

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
        await update.message.reply_text("*" + categories[text] + "*\n\nSkriv en titel:", parse_mode="Markdown")
        return GET_TITLE
    elif "bort" in text:
        await update.message.reply_text("Skriv titeln på annonsen du vill ta bort:")
        return GET_DELETE_ID
    elif "Support" in text:
        await update.message.reply_text("*Support*\n\nE-post: info@listoo.se\nWebb: listoo.se", parse_mode="Markdown")
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
    ctx.user_data['photos'] = []
    await update.message.reply_text(
        "Skicka upp till 5 foton ett i taget\n\nNär du är klar, skriv /klar"
    )
    return GET_PHOTOS

async def get_photos(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        photos = ctx.user_data.get('photos', [])
        if len(photos) < 5:
            photos.append(update.message.photo[-1].file_id)
            ctx.user_data['photos'] = photos
            remaining = 5 - len(photos)
            if remaining > 0:
                await update.message.reply_text(
                    "Foto " + str(len(photos)) + " mottaget!\n\nSkicka fler eller skriv /klar"
                )
            else:
                await update.message.reply_text("Max 5 foton!\n\nSkriv /klar för att fortsätta")
        else:
            await update.message.reply_text("Max 5 foton uppnått. Skriv /klar")
    return GET_PHOTOS

async def done_photos(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Din e-post eller telefon:")
    return GET_CONTACT

async def get_delete_id(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    title = update.message.text
    user = update.message.from_user
    username = user.username or user.first_name
    keyboard = [[
        InlineKeyboardButton("Ta bort", callback_data="delete_" + str(user.id) + "_" + title[:15]),
        InlineKeyboardButton("Avbryt", callback_data="nodelet_" + str(user.id))
    ]]
    await ctx.bot.send_message(
        chat_id=ADMIN_ID,
        text="Borttagningsbegäran\n\n@" + username + "\n" + title,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    markup = ReplyKeyboardMarkup(MENU_KEYBOARD, resize_keyboard=True)
    await update.message.reply_text("Din begäran är skickad!", reply_markup=markup)
    return MAIN_MENU

async def get_contact(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data['contact'] = update.message.text
    d = ctx.user_data
    user_id = str(update.message.from_user.id)
    username = update.message.from_user.username or update.message.from_user.first_name

    cat = d.get('category', 'Övrigt')
    price_label = "Lön" if d['type'] == 'jobb' else "Pris"
    photos = d.get('photos', [])

    short_caption = "*" + d['title'] + "*\n" + price_label + ": " + d['price'] + " kr\n" + d['location']

    # Store ad data
    ctx.bot_data[user_id] = {
        'short': short_caption,
        'contact': d['contact'],
        'desc': d['desc'],
        'photos': photos,
        'title': d['title'],
        'price': d['price'],
        'location': d['location'],
        'price_label': price_label,
        'cat': cat
    }

    admin_text = (
        "Ny annons - " + cat + "\n"
        "@" + username + "\n\n"
        + d['title'] + "\n"
        + d['desc'] + "\n"
        + price_label + ": " + d['price'] + " kr\n"
        + d['location'] + "\n\n"
        + "Kontakt: " + d['contact'] + "\n"
        + "Antal foton: " + str(len(photos))
    )

    keyboard_admin = [[
        InlineKeyboardButton("Godkänn", callback_data="approve_" + user_id),
        InlineKeyboardButton("Neka", callback_data="reject_" + user_id)
    ]]

    try:
        if photos:
            if len(photos) == 1:
                await ctx.bot.send_photo(
                    chat_id=ADMIN_ID, photo=photos[0],
                    caption=admin_text,
                    reply_markup=InlineKeyboardMarkup(keyboard_admin)
                )
            else:
                media = [InputMediaPhoto(media=p) for p in photos]
                media[0] = InputMediaPhoto(media=photos[0], caption=admin_text)
                await ctx.bot.send_media_group(chat_id=ADMIN_ID, media=media)
                await ctx.bot.send_message(
                    chat_id=ADMIN_ID,
                    text="Godkänn annons ovan:",
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
            photos = ad.get('photos', [])
            keyboard_ch = [[
                InlineKeyboardButton("❤️ Spara", callback_data="save_" + ad_id),
                InlineKeyboardButton("📞 Kontakt", callback_data="contact_" + ad_id),
                InlineKeyboardButton("🟠 Listoo", url="https://listoo.se")
            ]]
            markup_ch = InlineKeyboardMarkup(keyboard_ch)
            try:
                if len(photos) > 1:
                    # Album med flera foton
                    media = [InputMediaPhoto(media=p) for p in photos]
                    media[0] = InputMediaPhoto(media=photos[0], caption=ad['short'], parse_mode="Markdown")
                    await ctx.bot.send_media_group(chat_id=CHANNEL_ID, media=media)
                    # Skicka knappar separat
                    await ctx.bot.send_message(
                        chat_id=CHANNEL_ID,
                        text=ad['short'],
                        parse_mode="Markdown",
                        reply_markup=markup_ch
                    )
                elif len(photos) == 1:
                    await ctx.bot.send_photo(
                        chat_id=CHANNEL_ID,
                        photo=photos[0],
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
                await ctx.bot.send_message(chat_id=int(ad_id), text="Din annons är publicerad!\n@listoo_se")
                await query.edit_message_text("Annons publicerad!")
            except Exception as e:
                logging.error(str(e))
                await query.edit_message_text("Fel: " + str(e))
        else:
            await query.edit_message_text("Fel: annons hittades inte.")

    elif data.startswith("reject_"):
        ad_id = data.replace("reject_", "")
        try:
            await ctx.bot.send_message(chat_id=int(ad_id), text="Din annons godkändes inte.\ninfo@listoo.se")
        except:
            pass
        await query.edit_message_text("Annons nekad.")

    elif data.startswith("contact_"):
        ad_id = data.replace("contact_", "")
        ad = ctx.bot_data.get(ad_id)
        if ad:
            # Send contact info privately to the user who clicked
            try:
                await ctx.bot.send_message(
                    chat_id=query.from_user.id,
                    text="Kontaktinfo för:\n*" + ad['title'] + "*\n\n📞 " + ad['contact'],
                    parse_mode="Markdown"
                )
                await query.answer("Kontaktinfo skickad till dig!", show_alert=True)
            except:
                await query.answer("Starta @Listoo_se_bot för att se kontaktinfo", show_alert=True)
        else:
            await query.answer("Info ej tillgänglig.", show_alert=True)

    elif data.startswith("save_"):
        ad_id = data.replace("save_", "")
        ad = ctx.bot_data.get(ad_id)
        if ad:
            saved_text = (
                "❤️ *Sparad annons*\n\n"
                + "*" + ad['title'] + "*\n"
                + ad['price_label'] + ": " + ad['price'] + " kr\n"
                + ad['location'] + "\n\n"
                + ad['desc'] + "\n\n"
                + "📞 Kontakt: " + ad['contact']
            )
            try:
                await ctx.bot.send_message(
                    chat_id=query.from_user.id,
                    text=saved_text,
                    parse_mode="Markdown"
                )
                await query.answer("Annons sparad!", show_alert=True)
            except:
                await query.answer("Starta @Listoo_se_bot för att spara", show_alert=True)
        else:
            await query.answer("Kan inte spara.", show_alert=True)

    elif data.startswith("delete_"):
        parts = data.split("_", 2)
        user_id = parts[1]
        try:
            await ctx.bot.send_message(chat_id=int(user_id), text="Din annons har tagits bort.")
        except:
            pass
        await query.edit_message_text("Borttagen. Ta bort manuellt från kanalen.")

    elif data.startswith("nodelet_"):
        user_id = data.replace("nodelet_", "")
        try:
            await ctx.bot.send_message(chat_id=int(user_id), text="Borttagningsbegäran nekad.")
        except:
            pass
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
            GET_PHOTOS: [
                MessageHandler(filters.PHOTO, get_photos),
                CommandHandler("klar", done_photos)
            ],
            GET_CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_contact)],
            GET_DELETE_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_delete_id)],
        },
        fallbacks=[CommandHandler("cancel", cancel), CommandHandler("start", start)],
        allow_reentry=True,
    )
    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(handle_approval))
    print("Listoo Bot v7 running...")
    app.run_polling()

if __name__ == "__main__":
    main()

