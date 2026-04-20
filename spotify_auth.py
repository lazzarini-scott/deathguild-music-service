"""
One-time script to obtain a Spotify refresh token for the dedicated app account.
Run once, copy the printed refresh token into .env as SPOTIFY_REFRESH_TOKEN.

Usage:
    python spotify_auth.py
"""
import asyncio
import webbrowser
from urllib.parse import urlencode, urlparse, parse_qs

import httpx
from aiohttp import web

from core.config import settings

SCOPES = "playlist-modify-public user-read-private"
AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"

_code_future: asyncio.Future = None


async def _callback(request: web.Request) -> web.Response:
    code = request.query.get("code")
    error = request.query.get("error")
    if error or not code:
        _code_future.set_exception(RuntimeError(f"Spotify auth error: {error}"))
        return web.Response(text="Auth failed. Check terminal.")
    _code_future.set_result(code)
    return web.Response(text="Auth complete. You can close this tab.")


async def main():
    global _code_future
    loop = asyncio.get_event_loop()
    _code_future = loop.create_future()

    params = urlencode({
        "client_id": settings.spotify_client_id,
        "response_type": "code",
        "redirect_uri": settings.spotify_redirect_uri,
        "scope": SCOPES,
    })
    auth_url = f"{AUTH_URL}?{params}"
    print(f"Opening Spotify login in browser...\nIf it doesn't open, visit:\n{auth_url}\n")
    webbrowser.open(auth_url)

    app = web.Application()
    parsed = urlparse(settings.spotify_redirect_uri)
    app.router.add_get(parsed.path, _callback)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, parsed.hostname, parsed.port)
    await site.start()

    code = await _code_future
    await runner.cleanup()

    async with httpx.AsyncClient() as client:
        response = await client.post(
            TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.spotify_redirect_uri,
            },
            auth=(settings.spotify_client_id, settings.spotify_client_secret),
        )
        response.raise_for_status()
        tokens = response.json()

    print("\n--- SUCCESS ---")
    print(f"Add this to your .env file:\n")
    print(f"SPOTIFY_REFRESH_TOKEN={tokens['refresh_token']}")


if __name__ == "__main__":
    asyncio.run(main())
