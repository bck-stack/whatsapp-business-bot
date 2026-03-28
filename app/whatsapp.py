"""
WhatsApp Cloud API client.
Sends text messages, template messages, and interactive reply buttons.
"""

import logging
from typing import Any, Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

GRAPH_API_URL = "https://graph.facebook.com/v19.0"


class WhatsAppClient:
    """Thin async wrapper around the Meta WhatsApp Cloud API."""

    def __init__(self) -> None:
        self._headers = {
            "Authorization": f"Bearer {settings.WHATSAPP_TOKEN}",
            "Content-Type": "application/json",
        }
        self._base = f"{GRAPH_API_URL}/{settings.WHATSAPP_PHONE_ID}/messages"

    async def _post(self, payload: dict[str, Any]) -> dict:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(self._base, json=payload, headers=self._headers)
            resp.raise_for_status()
            return resp.json()

    async def send_text(self, to: str, body: str) -> dict:
        """Send a plain text message."""
        return await self._post({
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {"preview_url": False, "body": body},
        })

    async def send_template(
        self,
        to: str,
        template_name: str,
        language_code: str = "en_US",
        components: Optional[list[dict]] = None,
    ) -> dict:
        """Send a pre-approved template message (required for outbound initiation)."""
        payload: dict[str, Any] = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language_code},
            },
        }
        if components:
            payload["template"]["components"] = components
        return await self._post(payload)

    async def send_buttons(
        self,
        to: str,
        body_text: str,
        buttons: list[dict[str, str]],
        header_text: Optional[str] = None,
        footer_text: Optional[str] = None,
    ) -> dict:
        """
        Send an interactive message with up to 3 reply buttons.
        buttons: [{"id": "btn_1", "title": "Yes"}, ...]
        """
        interactive: dict[str, Any] = {
            "type": "button",
            "body": {"text": body_text},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": b["id"], "title": b["title"]}}
                    for b in buttons[:3]
                ]
            },
        }
        if header_text:
            interactive["header"] = {"type": "text", "text": header_text}
        if footer_text:
            interactive["footer"] = {"text": footer_text}

        return await self._post({
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "interactive",
            "interactive": interactive,
        })

    async def mark_as_read(self, message_id: str) -> dict:
        """Mark an incoming message as read."""
        return await self._post({
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id,
        })


wa_client = WhatsAppClient()
