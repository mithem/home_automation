"""Helpers for home_automation's OAuth2 implementation."""
import google_auth_oauthlib.flow

from google.oauth2.credentials import Credentials
from home_automation.server.backend.state_manager import StateManager

GOOGLE_MAIL_SEND_SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


def get_oauth_flow() -> google_auth_oauthlib.flow.Flow:
    """Get the OAuth2 flow for Google's OAuth2."""
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        "client_secret.json", GOOGLE_MAIL_SEND_SCOPES
    )
    flow.redirect_uri = (
        "https://helix2.ddns.net:10000/backend/home_automation/oauth2/google/callback"
    )
    return flow


def get_google_oauth2_credentials(state_manager: StateManager) -> Credentials:
    """Get the credentials for Google's OAuth2."""
    credentials = state_manager.get_oauth2_credentials()
    hashmap = {}
    for key, value in credentials:
        hashmap[key] = value
    creds = Credentials(hashmap.get("access_token"))
    return creds


def clear_credentials(state_manager: StateManager):
    """Clear all OAuth2 credentials saved in the database."""
    state_manager.reset_oauth2()


def save_credentials(credentials: Credentials, state_manager: StateManager):
    """Save the access token provided by the OAuth2 credentials to the persistent database."""
    state_manager.update_oauth2_credentials("access_token", credentials.token)
