from __future__ import annotations

import os

from fastapi import Header, HTTPException, status


async def require_api_key(x_api_key: str | None = Header(None)) -> None:
    expected = os.getenv("API_KEY")
    if not expected:
        return  # No key configured — endpoint is open
    if x_api_key != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key. Provide it via the X-Api-Key header.",
        )
