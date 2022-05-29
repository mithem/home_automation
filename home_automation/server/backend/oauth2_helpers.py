import google_auth_oauthlib.flow
from home_automation.server.backend import state_manager
from google.oauth2.credentials import Credentials

GOOGLE_MAIL_SEND_SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    # "https://www.googleapis.com/auth/gmail.readonly"
]

def get_oauth_flow() -> google_auth_oauthlib.flow.Flow:
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file("client_secret.json", GOOGLE_MAIL_SEND_SCOPES)
    flow.redirect_uri = "https://helix2.ddns.net:10000/backend/home_automation/oauth2/google/callback"
    return flow

def get_google_oauth2_credentials(state_manager: state_manager.StateManager) -> Credentials:
    credentials = state_manager.get_oauth2_credentials()
    hashmap = {}
    for key, value in credentials:
        hashmap[key] = value
    creds = Credentials(hashmap.get("access_token"))
    return creds

def clear_credentials(state_manager: state_manager.StateManager):
    state_manager.reset_oauth2()

def save_credentials(credentials: Credentials, state_manager: state_manager.StateManager):
    state_manager.update_oauth2_credentials("access_token", credentials.token)
