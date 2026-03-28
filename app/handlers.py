"""
Incoming message handler.
Parses webhook payload and dispatches to appropriate response logic.
"""

import logging
from typing import Any

from app.whatsapp import wa_client
from app.config import settings

logger = logging.getLogger(__name__)

# Simple in-memory session state (replace with Redis in production)
_sessions: dict[str, dict] = {}


async def handle_webhook(payload: dict[str, Any]) -> None:
    """Entry point — called by the webhook POST endpoint."""
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            messages = value.get("messages", [])
            for msg in messages:
                await _dispatch(msg)


async def _dispatch(msg: dict[str, Any]) -> None:
    """Route a single message object to the right handler."""
    from_number = msg.get("from", "")
    msg_id = msg.get("id", "")
    msg_type = msg.get("type", "")

    # Mark as read
    try:
        await wa_client.mark_as_read(msg_id)
    except Exception:
        pass

    if msg_type == "text":
        text = msg.get("text", {}).get("body", "").strip().lower()
        await _handle_text(from_number, text)

    elif msg_type == "interactive":
        reply_id = (
            msg.get("interactive", {})
            .get("button_reply", {})
            .get("id", "")
        )
        await _handle_button(from_number, reply_id)

    else:
        await wa_client.send_text(
            from_number,
            "I can only process text messages and button replies for now."
        )


async def _handle_text(to: str, text: str) -> None:
    """Process incoming text and respond based on keywords."""
    greetings = {"hi", "hello", "hey", "merhaba", "selam"}

    if text in greetings:
        await wa_client.send_buttons(
            to=to,
            header_text=f"Welcome to {settings.BUSINESS_NAME}",
            body_text="How can I help you today?",
            footer_text="Reply with a button or type your question.",
            buttons=[
                {"id": "track_order", "title": "Track Order"},
                {"id": "support",     "title": "Get Support"},
                {"id": "pricing",     "title": "Pricing"},
            ],
        )

    elif "order" in text or "track" in text:
        await wa_client.send_text(
            to,
            "Please share your order ID (e.g. ORD-1042) and I'll look it up for you.",
        )
        _sessions[to] = {"state": "awaiting_order_id"}

    elif text.startswith("ord-") or _sessions.get(to, {}).get("state") == "awaiting_order_id":
        order_id = text.upper()
        _sessions.pop(to, None)
        # In production, query your database here
        await wa_client.send_text(
            to,
            f"Order *{order_id}* — Status: *In Transit* 🚚\nExpected delivery: Tomorrow by 6 PM.",
        )

    elif "price" in text or "pricing" in text:
        await wa_client.send_text(
            to,
            "Our plans:\n\n• *Starter* — $29/mo\n• *Pro* — $79/mo\n• *Enterprise* — Contact us\n\nVisit our website for full details.",
        )

    elif "support" in text or "help" in text:
        await wa_client.send_text(
            to,
            "Our support team is available Mon–Fri 9AM–6PM.\nYou can also email us at support@example.com",
        )

    else:
        await wa_client.send_text(
            to,
            f"Thanks for your message! A team member will get back to you shortly.\n\nType *hi* to see the main menu.",
        )


async def _handle_button(to: str, reply_id: str) -> None:
    """Handle interactive button replies."""
    if reply_id == "track_order":
        await wa_client.send_text(to, "Please share your order ID (e.g. ORD-1042).")
        _sessions[to] = {"state": "awaiting_order_id"}

    elif reply_id == "support":
        await wa_client.send_text(
            to,
            "Support is available Mon–Fri 9AM–6PM.\nEmail: support@example.com",
        )

    elif reply_id == "pricing":
        await wa_client.send_text(
            to,
            "Our plans:\n\n• *Starter* — $29/mo\n• *Pro* — $79/mo\n• *Enterprise* — Contact us",
        )

    else:
        await wa_client.send_text(to, "Unknown option. Type *hi* to start over.")
