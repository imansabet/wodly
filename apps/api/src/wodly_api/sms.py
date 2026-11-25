import logging
from typing import Protocol

logger = logging.getLogger(__name__)


class SmsSender(Protocol):
    async def send(self, phone: str, message: str) -> None: ...


class ConsoleSmsSender:
    """Dev-only sender: prints the message instead of sending an SMS."""

    async def send(self, phone: str, message: str) -> None:
        logger.warning("[DEV SMS] to=%s message=%s", phone, message)


def get_sms_sender() -> SmsSender:
    return ConsoleSmsSender()
