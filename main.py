"""
WhatsApp Business API Bot
FastAPI app exposing webhook verification (GET) and message handler (POST).
"""

import logging

from fastapi import FastAPI, HTTPException, Query, Request, status
from fastapi.responses import PlainTextResponse

from app.config import settings
from app.handlers import handle_webhook
from app.notifications import OrderNotification, send_order_notification

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

app = FastAPI(
    title="WhatsApp Business Bot",
    description="Webhook receiver and outbound notification system for WhatsApp Cloud API.",
    version="1.0.0",
)


# ---------------------------------------------------------------------------
# Webhook verification (Meta requires a GET endpoint)
# ---------------------------------------------------------------------------

@app.get("/webhook", response_class=PlainTextResponse, tags=["webhook"])
async def verify_webhook(
    hub_mode: str = Query(alias="hub.mode", default=""),
    hub_verify_token: str = Query(alias="hub.verify_token", default=""),
    hub_challenge: str = Query(alias="hub.challenge", default=""),
) -> str:
    """
    Meta sends a GET request to verify the webhook URL.
    Return the challenge string when the verify_token matches.
    """
    if hub_mode == "subscribe" and hub_verify_token == settings.VERIFY_TOKEN:
        logging.info("Webhook verified successfully.")
        return hub_challenge
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Verification failed.")


# ---------------------------------------------------------------------------
# Incoming messages
# ---------------------------------------------------------------------------

@app.post("/webhook", status_code=status.HTTP_200_OK, tags=["webhook"])
async def receive_message(request: Request) -> dict:
    """
    Receive and process incoming WhatsApp messages.
    Meta requires a 200 response within 20 seconds — processing is fire-and-forget.
    """
    payload = await request.json()
    logging.info("Webhook payload received.")

    # Run handler without blocking the response
    import asyncio
    asyncio.create_task(handle_webhook(payload))

    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Outbound notification endpoint (internal use / called by your backend)
# ---------------------------------------------------------------------------

@app.post("/notify/order", tags=["notifications"])
async def notify_order(notif: OrderNotification) -> dict:
    """Send an order status notification to a customer via WhatsApp."""
    success = await send_order_notification(notif)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to send WhatsApp notification.",
        )
    return {"sent": True, "phone": notif.phone, "order_id": notif.order_id}


@app.get("/health", tags=["ops"])
async def health() -> dict:
    return {"status": "ok", "phone_id": settings.WHATSAPP_PHONE_ID}
