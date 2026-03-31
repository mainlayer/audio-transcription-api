import math
import os
from mainlayer import MainlayerClient

PRICE_PER_MINUTE: float = 1.0  # 1 credit per minute (partial minutes rounded up)

_client: MainlayerClient | None = None


def get_client() -> MainlayerClient:
    global _client
    if _client is None:
        _client = MainlayerClient(api_key=os.environ["MAINLAYER_API_KEY"])
    return _client


async def verify_payment(resource_id: str, token: str) -> bool:
    """Return True if the token grants access to the given resource."""
    client = get_client()
    access = await client.resources.verify_access(resource_id, token)
    return access.authorized


def calculate_credits(duration_seconds: float, price_per_minute: float = PRICE_PER_MINUTE) -> float:
    """
    Calculate credit cost based on audio duration.

    Partial minutes are rounded up (ceiling), matching industry standard billing.

    Args:
        duration_seconds: Length of the audio clip in seconds.
        price_per_minute: Cost per minute of audio.

    Returns:
        Total credit cost (float).
    """
    minutes = duration_seconds / 60.0
    return math.ceil(minutes) * price_per_minute
