import os

from fastf1.exceptions import F1AuthError

try:
    from fastf1.internals.f1account import login
except ImportError:
    # FastF1 reorganised its internals: behave as if the hook did not exist
    login = None

_login_requested = False
_original_credentials = None


def _credentials_or_refuse():
    if os.environ.get(login.ENV_USERNAME) and os.environ.get(login.ENV_PASSWORD):
        return _original_credentials()
    global _login_requested
    _login_requested = True
    raise F1AuthError("F1 account credentials are not available")


def install():
    global _login_requested, _original_credentials
    _login_requested = False
    if login is None or not hasattr(login, "_credentials_from_env_or_prompt"):
        return
    if login._credentials_from_env_or_prompt is not _credentials_or_refuse:
        _original_credentials = login._credentials_from_env_or_prompt
    login._credentials_from_env_or_prompt = _credentials_or_refuse


def login_was_requested():
    return _login_requested
