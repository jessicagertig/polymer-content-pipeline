"""Centralized Google API credentials.

The same OAuth client and refresh token inflow-ats and polymer-engagement-pipeline use for
the internal sheets (GOOGLE_INTERNAL_SHEETS_CLIENT_ID / _CLIENT_SECRET / _REFRESH_TOKEN).

That refresh token was granted the full `spreadsheets` scope. Google rejects a refresh
naming any scope outside the original grant, so Sheets calls request exactly that scope,
and Search Console (the `webmasters` scope) needs its own refresh token
(GOOGLE_SEARCH_CONSOLE_REFRESH_TOKEN). When that is empty, Google indexing is skipped.
"""

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

from config.settings import settings

SEARCH_CONSOLE_SCOPE = "https://www.googleapis.com/auth/webmasters"


def get_credentials(scopes: list[str]):
    refresh_token = (
        settings.google_search_console_refresh_token
        if SEARCH_CONSOLE_SCOPE in scopes
        else settings.google_internal_sheets_refresh_token
    )
    credentials = Credentials(
        token=None,
        refresh_token=refresh_token,
        client_id=settings.google_internal_sheets_client_id,
        client_secret=settings.google_internal_sheets_client_secret,
        token_uri="https://oauth2.googleapis.com/token",
        scopes=scopes,
    )
    credentials.refresh(Request())
    return credentials
