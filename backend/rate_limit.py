"""
Shared slowapi Limiter instance.

Defined here (not in main.py) so routers can import it without circular deps.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

from config import settings

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[settings.generate_rate_limit],
)
