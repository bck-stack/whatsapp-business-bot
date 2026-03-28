"""
Outbound notification helpers.
Used for sending order confirmations, alerts, and status updates
proactively to customers.
"""

import logging
from dataclasses import dataclass

from app.whatsapp import wa_client

logger = logging.getLogger(__name__)


@dataclass
class OrderNotification:
    phone: str          # E.164 format: +905551234567
    order_id: str
    customer_name: str
    status: str         # confirmed | shipped | delivered | cancelled
    detail: str = ""


STATUS_MESSAGES = {
    "confirmed": "Your order *{order_id}* has been confirmed! We'll notify you when it ships.",
    "shipped": "Great news! Order *{order_id}* is on its way 🚚\n{detail}",
    "delivered": "Your order *{order_id}* has been delivered! Enjoy 🎉\nTap below to leave a review.",
    "cancelled": "Order *{order_id}* has been cancelled.\n{detail}\nContact us if you have questions.",
}


async def send_order_notification(notif: OrderNotification) -> bool:
    """
    Send an order status update to a customer.
    Returns True on success, False on failure.
    """
    template = STATUS_MESSAGES.get(notif.status)
    if not template:
        logger.error("Unknown status: %s", notif.status)
        return False

    body = template.format(order_id=notif.order_id, detail=notif.detail)
    greeting = f"Hi {notif.customer_name}! 👋\n\n"

    try:
        await wa_client.send_text(notif.phone, greeting + body)
        logger.info(
            "Notification sent to %s — order=%s status=%s",
            notif.phone, notif.order_id, notif.status,
        )
        return True
    except Exception as exc:
        logger.error("Failed to send notification to %s: %s", notif.phone, exc)
        return False
