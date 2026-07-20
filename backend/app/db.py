"""
db.py – Supabase client singleton.

Call `init_supabase()` once at application startup and `get_supabase()` anywhere
a database handle is needed.  Both helpers are safe to import at module level;
the client is created lazily inside `init_supabase()` so tests that never call
that function do not require real credentials.
"""

import logging
import os
from typing import Optional

from supabase import Client, create_client

logger = logging.getLogger(__name__)

_client: Optional[Client] = None


def init_supabase() -> None:
    """Initialise the module-level Supabase client.

    Reads SUPABASE_URL and SUPABASE_KEY from the environment (loaded by
    python-dotenv in main.py before this is called).

    Raises:
        RuntimeError: If either environment variable is missing.
    """
    global _client

    url = os.environ.get("SUPABASE_URL", "").strip()
    key = os.environ.get("SUPABASE_KEY", "").strip()

    if not url:
        raise RuntimeError(
            "SUPABASE_URL is not set. Add it to your .env file and restart."
        )
    if not key:
        raise RuntimeError(
            "SUPABASE_KEY is not set. Add it to your .env file and restart."
        )

    _client = create_client(url, key)
    logger.info("Supabase client initialised (url=%s…)", url[:40])


def get_supabase() -> Client:
    """Return the shared Supabase client.

    Raises:
        RuntimeError: If `init_supabase()` has not been called yet.
    """
    if _client is None:
        raise RuntimeError(
            "Supabase client has not been initialised. "
            "Ensure init_supabase() is called during application startup."
        )
    return _client
