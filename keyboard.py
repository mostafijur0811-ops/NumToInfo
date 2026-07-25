"""Inline keyboard layouts used by the bot."""

from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Return the main menu inline keyboard shown on /start."""
    buttons = [
        [InlineKeyboardButton("🔎 Search Number", callback_data="search_number")],
        [
            InlineKeyboardButton("ℹ Help", callback_data="help"),
            InlineKeyboardButton("📚 About", callback_data="about"),
        ],
    ]
    return InlineKeyboardMarkup(buttons)


def back_to_menu_keyboard() -> InlineKeyboardMarkup:
    """Return a simple 'back to menu' keyboard."""
    buttons = [[InlineKeyboardButton("⬅ Back to Menu", callback_data="main_menu")]]
    return InlineKeyboardMarkup(buttons)


def maps_keyboard(maps_url: str | None) -> InlineKeyboardMarkup | None:
    """Return a keyboard with a Google Maps link button, if a URL is available."""
    if not maps_url:
        return None
    buttons = [[InlineKeyboardButton("🗺 Open in Google Maps", url=maps_url)]]
    return InlineKeyboardMarkup(buttons)
