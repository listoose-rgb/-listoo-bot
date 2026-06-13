#!/usr/bin/env python3
# Listoo Telegram Bot v3 - با دسته‌بندی
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

# ── START ──
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["🏠 Bostad", "🚗 Fordon"],
        ["📱 Elektronik", "🛋️ Möbler"],
        ["💼 Jobb", "📦 Övrigt"],
        ["🗑️ Ta bort annons", "📞 Support"]
    ]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "🟠 Välkommen till *Listoo*!\n\n"
        "Köp, sälj och hitta jobb.\n\n"
        "Välj en kategori 👇",
        parse_mode="Markdown",
        reply_markup=markup
    )
    return MAIN_MENU

# ── MAIN MENU ──
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
        
        emoji = text.split()[0]
        cat_name = text
        
        await update.message.reply_text(
            f"{emoji} *{cat_name}*\n\nSkriv en titel för din annons:",
            parse_mode="Markdown"
        )
        return GET_TITLE

    elif "bort" in text:
        await update.message.reply_text(
            "🗑️ *Ta bort annons*\n\n"
            "Skriv titeln på din annons:",
            parse_mode="Markdown"
        )
        return GET_DELETE_ID

    elif "Support" in text:
        await update.message.reply_text(
            "📞 *Support*\n\n"
            "📧 info@listoo.se\n"
            "🌐 listoo.se\n"
            "📢 @listoo_se",
            parse_mode="Markdown"
        )
        return MAIN_MENU

    return MAIN_MENU

# ── مراحل ثبت آگهی ──
async def get_title(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data['title'] = update.message.text
    await update.message.reply_text("✍️ Beskriv varan:")
    return GET_DESC

async def get_desc(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data['desc'] = update.message.text
    label = "💰 Lon (kr/man):" if ctx.user_data.get('type') == 'jobb' else "💰 Pris (kr):"
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

# ── درخواست حذف ──
async def get_delete_id(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    title = update.message.text
    user = update.message.from_user
    username = user.username or user.first_name

    keyboard = [[
        InlineKeyboardButton("✅ حذف کن", callback_data=f"delete_{user.id}_{title[:20]}"),
        InlineKeyboardButton("❌ رد کن", callback_data=f"nodelet_{user.id}")
    ]]
    markup = InlineKeyboardMarkup(keyboard)

    await ctx.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"🗑️ *درخواست حذف آگهی*\n\n"
             f"👤 کاربر: @{username}\n"
             f"📌 عنوان: *{title}*",
        parse_mode="Markdown",
        reply_markup=markup
    )

    await update.message.reply_text(
        "✅ درخواست حذف ارسال شد!\n\n"
        "ادمین بررسی می‌کنه و آگهیت رو پاک می‌کنه.\n"
        "معمولاً در ۲۴ ساعت انجام میشه! 🟠"
    )
    return MAIN_MENU

# ── ارسال به ادمین ──
async def get_contact(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data['contact'] = update.message.text
    ctx.user_data['user_id'] = update.message.from_user.id
    ctx.user_data['username'] = update.message.from_user.username or update.message.from_user.first_name
    d = ctx.user_data

    cat = d.get('category', 'övrigt').upper()
    cat_emojis = {
        'BOSTAD': '🏠', 'FORDON': '🚗', 'ELEKTRONIK': '📱',
        'MÖBLER': '🛋️', 'JOBB': '💼', 'ÖVRIGT': '📦'
    }
    emoji = cat_emojis.get(cat, '📦')
    price_label = "💰 Lon" if d['type'] == 'jobb' else "💰 Pris"

    caption = (
        f"🟠 *{emoji} {cat} — Listoo*\n\n"
        f"📌 *{d['title']}*\n\n"
        f"📝 {d['desc']}\n\n"
        f"{price_label}: *{d['price']} kr*\n"
        f"📍 {d['location']}\n\n"
        f"📬 Kontakt: `{d['contact']}`\n\n"
        f"✅ listoo.se"
    )

    keyboard = [[
        InlineKeyboardButton("✅ تأیید", callback_data=f"approve_{d['user_id']}"),
        InlineKeyboardButton("❌ رد", callback_data=f"reject_{d['user_id']}")
    ]]
    markup = InlineKeyboardMarkup(keyboard)

    ctx.bot_data[str(d['user_id'])] = {
        'caption': caption,
        'photo': d.get('photo'),
        'user_id': d['user_id']
    }

    admin_text = f"⚠️ *آگهی جدید — {emoji} {cat}*\n\n👤 @{d['username']}\n\n{caption}"

    try:
        if d.get('photo'):
            await ctx.bot.send_photo(
                chat_id=ADMIN_ID, photo=d['photo'],
                caption=admin_text, parse_mode="Markdown", reply_markup=markup
            )
        else:
            await ctx.bot.send_message(
                chat_id=ADMIN_ID, text=admin_text,
                parse_mode="Markdown", reply_markup=markup
            )
    except Exception as e:
        logging.error(f"Error: {e}")

    keyboard = [
        ["🏠 Bostad", "🚗 Fordon"],
        ["📱 Elektronik", "🛋️ Möbler"],
        ["💼 Jobb", "📦 Övrigt"],
        ["🗑️ Ta bort annons", "📞 Support"]
    ]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "✅ *Tack! Din annons granskas.*\n\nVi publicerar den inom kort! 🟠\n\nVill du lägga upp en ny annons? Välj kategori 👇",
        parse_mode="Markdown",
        reply_markup=markup
    )
    ctx.user_data.clear()
    return MAIN_MENU

# ── تأیید/رد ادمین ──
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
                        chat_id=CHANNEL_ID, photo=ad['photo'],
                        caption=ad['caption'], parse_mode="Markdown", reply_markup=markup
                    )
                else:
                    await ctx.bot.send_message(
                        chat_id=CHANNEL_ID, text=ad['caption'],
                        parse_mode="Markdown", reply_markup=markup
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
                text="❌ *آگهی شما تأیید نشد.*\n\nبرای اطلاعات: info@listoo.se",
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
            text=f"✅ آگهی *{title}* حذف شد! 🟠",
            parse_mode="Markdown"
        )
        await query.edit_message_text(f"✅ حذف تأیید شد!\n⚠️ خودت از کانال پاک کن!")

    elif data.startswith("nodelet_"):
        user_id = data.split('_')[1]
        await ctx.bot.send_message(
            chat_id=int(user_id),
            text="❌ درخواست حذف رد شد.\n\nبرای اطلاعات: info@listoo.se"
        )
        await query.edit_message_text("❌ درخواست رد شد!")

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
            MAIN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu), CommandHandler("start", start)],
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

    print("🟠 Listoo Bot v3 در حال اجراست...")
    app.run_polling()

if __name__ == "__main__":
    main()
