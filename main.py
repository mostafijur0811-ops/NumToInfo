"""Number To Country Info Bot — entry point.

A Telegram bot that identifies a country (and its public information) from
a phone number's international calling code. It never reveals or attempts
to find any personal, subscriber, carrier, or location data — only public,
country-level facts derived from the dialing code.
"""

from __future__ import annotations

import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from config import BOT_TOKEN, logger
from country import CountryLookupError, get_country_info, parse_phone_number
from keyboard import back_to_menu_keyboard, main_menu_keyboard, maps_keyboard
from utils import RateLimiter, extract_number_candidate, format_country_message

rate_limiter = RateLimiter()

WELCOME_TEXT = (
    "👋 <b>Welcome to Number To Country Info Bot!</b>\n\n"
    "📱 Send me any phone number (with or without <code>+</code>) and I'll tell you "
    "which country it belongs to, along with public country information.\n\n"
    "Example:\n<code>+8801712345678</code>\n\n"
    "⚠️ This bot <b>only</b> identifies the country from the dialing code. "
    "It never reveals the owner's identity, location, or any personal data."
)

HELP_TEXT = (
    "ℹ <b>How to use this bot</b>\n\n"
    "1️⃣ Send a phone number, e.g. <code>+919876543210</code>\n"
    "2️⃣ The bot detects the international calling code\n"
    "3️⃣ You get public country info: capital, currency, timezone, etc.\n\n"
    "<b>Commands</b>\n"
    "/start — Show the welcome menu\n"
    "/help — Show this help message\n"
    "/about — About this bot\n\n"
    "🔒 <i>No personal or subscriber data is ever accessed or stored.</i>"
)

ABOUT_TEXT = (
    "📚 <b>About Number To Country Info Bot</b>\n\n"
    "This bot uses a phone number's international calling code to look up "
    "publicly available country information via the REST Countries API.\n\n"
    "🔧 <b>Built with</b>\n"
    "• python-telegram-bot v21+\n"
    "• phonenumbers\n"
    "• pycountry\n"
    "• pytz\n\n"
    "🔒 <b>Privacy</b>: no owner name, carrier, IMEI, address, or location "
    "data is ever retrieved — only public, country-level information."
)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command."""
    if update.message is None:
        return
    await update.message.reply_text(
        WELCOME_TEXT, parse_mode=ParseMode.HTML, reply_markup=main_menu_keyboard()
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /help command."""
    if update.message is None:
        return
    await update.message.reply_text(
        HELP_TEXT, parse_mode=ParseMode.HTML, reply_markup=back_to_menu_keyboard()
    )


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /about command."""
    if update.message is None:
        return
    await update.message.reply_text(
        ABOUT_TEXT, parse_mode=ParseMode.HTML, reply_markup=back_to_menu_keyboard()
    )


async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline button presses from the main menu / navigation keyboards."""
    query = update.callback_query
    if query is None or query.data is None:
        return
    await query.answer()

    if query.data == "search_number":
        await query.edit_message_text(
            "🔎 <b>Send me a phone number now</b>\n\n"
            "Example: <code>+8801712345678</code>",
            parse_mode=ParseMode.HTML,
            reply_markup=back_to_menu_keyboard(),
        )
    elif query.data == "help":
        await query.edit_message_text(
            HELP_TEXT, parse_mode=ParseMode.HTML, reply_markup=back_to_menu_keyboard()
        )
    elif query.data == "about":
        await query.edit_message_text(
            ABOUT_TEXT, parse_mode=ParseMode.HTML, reply_markup=back_to_menu_keyboard()
        )
    elif query.data == "main_menu":
        await query.edit_message_text(
            WELCOME_TEXT, parse_mode=ParseMode.HTML, reply_markup=main_menu_keyboard()
        )


async def handle_number_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle a plain text message expected to contain a phone number."""
    if (
        update.message is None
        or update.message.text is None
        or update.effective_user is None
    ):
        return

    user_id = update.effective_user.id
    allowed, wait_seconds = rate_limiter.check(user_id)
    if not allowed:
        await update.message.reply_text(
            f"⏳ Please wait {wait_seconds}s before sending another number."
        )
        return

    raw_text = update.message.text
    candidate = extract_number_candidate(raw_text)

    if not candidate:
        await update.message.reply_text("❌ Invalid phone number.")
        return

    try:
        parsed = parse_phone_number(candidate)
        info = get_country_info(parsed)
    except ValueError:
        await update.message.reply_text("❌ Invalid phone number.")
        return
    except CountryLookupError as exc:
        logger.warning("Country lookup failed for %s: %s", candidate, exc)
        await update.message.reply_text(f"⚠️ {exc}")
        return
    except Exception:  # noqa: BLE001 - never let an unexpected error crash the bot
        logger.exception("Unexpected error while processing number: %s", candidate)
        await update.message.reply_text(
            "⚠️ Something went wrong while looking up this number. Please try again later."
        )
        return

    message = format_country_message(parsed, info)
    await update.message.reply_text(
        message,
        parse_mode=ParseMode.HTML,
        reply_markup=maps_keyboard(info.maps_url),
        disable_web_page_preview=True,
    )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Global error handler — logs the error and never lets the bot crash."""
    logger.error(
        "Unhandled exception while processing update: %s",
        context.error,
        exc_info=context.error,
    )


def build_application() -> Application:
    """Construct and configure the Telegram Application with all handlers."""
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about_command))
    application.add_handler(CallbackQueryHandler(menu_callback))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_number_message)
    )
    application.add_error_handler(error_handler)

    return application


class _HealthCheckHandler(BaseHTTPRequestHandler):
    """Minimal HTTP handler that just replies 200 OK on any request.

    This exists only so that hosting platforms which require an open HTTP
    port for "Web Service" deployments (e.g. Render) see the app as healthy.
    It has nothing to do with the bot's actual functionality.
    """

    def do_GET(self) -> None:  # noqa: N802 - required method name
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Number To Country Info Bot is running.")

    def log_message(self, format: str, *args) -> None:  # noqa: A002 - silence default logging
        pass


def _start_health_check_server() -> None:
    """Start a background HTTP server bound to $PORT, if one is provided.

    Render (and similar platforms) inject a PORT environment variable and
    expect the process to listen on it. This is only started when PORT is
    set, so local runs and Background Worker deployments are unaffected.
    """
    port_str = os.getenv("PORT")
    if not port_str:
        return
    try:
        port = int(port_str)
    except ValueError:
        logger.warning("Invalid PORT value %r; skipping health check server.", port_str)
        return

    server = HTTPServer(("0.0.0.0", port), _HealthCheckHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    logger.info("Health check HTTP server listening on port %s", port)


def main() -> None:
    """Run the bot with long polling."""
    logger.info("Starting Number To Country Info Bot...")
    _start_health_check_server()
    application = build_application()
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
