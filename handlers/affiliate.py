from config import *
from utils import *
from functions import *
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, MessageHandler, filters, CommandHandler, CallbackQueryHandler


async def start_affiliate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    This is the handler to start affiliate options
    """
    user = UserClient.get_user(update.message)

    #  WRTIE A PROCESS TO CHECK ADMIN AND SEND REQUEST TO PROCESS WITH USER
    username = update.message.from_user.username
    if user["_id"] != ADMIN_ID or user["verified"] == False:
        await context.bot.send_message(
            chat_id=user["_id"],
            text=emoji.emojize(
                """
    :robot: Awaiting authorization from support. Contact @Telescrowbotsupport to pass screening process
                """,
            ),
        )

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"""
    User ID - {user['_id']} just attempted adding this bot to a group
            """,
            parse_mode="HTML",
        )

    else:

        question = await context.bot.send_message(
            chat_id=user["_id"],
            text=emoji.emojize(
                """
    :robot: To use escrow service on your group, I would need the following information.
                
    Please reply with the your Group Username :grey_question: (example -> @GetGroupIDRobot)
                """,
            ),
        )

        context.user_data["next_step"] = add_addresses


async def add_addresses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group_id = update.message.text
    try:
        chat = await context.bot.get_chat(group_id)
        
        if not chat.id:
            return await context.bot.send_message(chat_id=update.message.from_user.id, text="Invalid Group ID")

        agent = AgentAction().create_agent(update.message.from_user.id)
        # import pdb; pdb.set_t     race()
        affiliate = create_affiliate(agent, str(chat.id))
        print(affiliate)
        if affiliate != "Already Exists":
            await context.bot.send_message(
                chat_id=update.message.from_user.id,
                text=emoji.emojize(
                    ":+1: Congrats!! You can now add TeleEscrow Service(@tele_escrowbot) to your public group and receive your affiliate charge for trade performed by your members, selecting their roles on the group. Good Luck!!",
                ),
            )

        else:
            await context.bot.send_message(
                chat_id=update.message.from_user.id,
                text=emoji.emojize(
                    ":construction: This Group Is Already Registered",
                ),
            )
    except Exception as e:
        print(e)
        await context.bot.send_message(
            chat_id=update.message.from_user.id,
            text="Invalid Group ID or bot doesn't have access to the group"
        )


async def affiliate_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /affiliate command"""
    user_id = update.effective_user.id
    
    # Get user's affiliate code
    affiliate_code = get_affiliate_code(user_id)
    if not affiliate_code:
        # Generate new affiliate code if user doesn't have one
        affiliate_code = generate_affiliate_code(user_id)
    
    # Create affiliate link
    bot_username = (await context.bot.get_me()).username
    affiliate_link = f"https://t.me/{bot_username}?start={affiliate_code}"
    
    # Get affiliate stats
    stats = get_affiliate_stats(user_id)
    
    await update.message.reply_text(
        f"🎯 <b>Your Affiliate Program</b>\n\n"
        f"Your unique affiliate code: <code>{affiliate_code}</code>\n"
        f"Your affiliate link: {affiliate_link}\n\n"
        f"📊 <b>Statistics:</b>\n"
        f"Total referrals: {stats['total_referrals']}\n"
        f"Active referrals: {stats['active_referrals']}\n"
        f"Total earnings: ${stats['total_earnings']:.2f}\n\n"
        f"Share your affiliate link with others and earn a commission for each successful trade they complete!",
        parse_mode="html",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔗 Copy Link", callback_data=f"copy_link_{affiliate_link}"),
            InlineKeyboardButton("📊 View Stats", callback_data="affiliate_stats")
        ]])
    )


async def handle_affiliate_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle affiliate-related callback queries"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith("copy_link_"):
        link = data.replace("copy_link_", "")
        await query.edit_message_text(
            text=f"🔗 Here's your affiliate link:\n\n{link}\n\nCopy and share it with others!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back", callback_data="affiliate_menu")
            ]])
        )
    
    elif data == "affiliate_stats":
        user_id = query.from_user.id
        stats = get_affiliate_stats(user_id)
        
        await query.edit_message_text(
            text=f"📊 <b>Your Affiliate Statistics</b>\n\n"
                 f"Total referrals: {stats['total_referrals']}\n"
                 f"Active referrals: {stats['active_referrals']}\n"
                 f"Total earnings: ${stats['total_earnings']:.2f}\n\n"
                 f"Keep sharing your link to earn more!",
            parse_mode="html",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back", callback_data="affiliate_menu")
            ]])
        )
    
    elif data == "affiliate_menu":
        # Return to main affiliate menu
        await affiliate_handler(update, context)


def register_handlers(application):
    """Register handlers for the affiliate module"""
    application.add_handler(CommandHandler("affiliate", affiliate_handler))
    application.add_handler(CallbackQueryHandler(handle_affiliate_callback, pattern="^(copy_link_|affiliate_stats|affiliate_menu)"))

# Register handlers
application.add_handler(MessageHandler(filters.Regex("^Add Bot To Your Group"), start_affiliate))
