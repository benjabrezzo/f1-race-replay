import builtins
import sys

import pytest
from fastf1.exceptions import F1AuthError
from fastf1.internals.f1account import get_token
from fastf1.internals.f1account import login as fastf1_login

import src.lib.f1_auth as f1_auth


class FakeTty:
    def isatty(self):
        return True


@pytest.fixture
def interactive_session_without_credentials(monkeypatch):
    monkeypatch.delenv("F1_USERNAME", raising=False)
    monkeypatch.delenv("F1_PASSWORD", raising=False)
    monkeypatch.delenv("FASTF1_AUTH_METHOD", raising=False)
    monkeypatch.setattr(sys, "stdin", FakeTty())
    # registers the restore of the function the hook is about to replace
    monkeypatch.setattr(
        fastf1_login,
        "_credentials_from_env_or_prompt",
        fastf1_login._credentials_from_env_or_prompt,
    )


def test_get_token_raises_f1_auth_error_instead_of_prompting(
    monkeypatch, interactive_session_without_credentials
):
    def fail_if_prompted(*args, **kwargs):
        raise AssertionError("the user was prompted for credentials")

    monkeypatch.setattr(builtins, "input", fail_if_prompted)
    monkeypatch.setattr("getpass.getpass", fail_if_prompted)

    f1_auth.install()

    with pytest.raises(F1AuthError):
        get_token(force_renew=True)


def test_login_request_is_recorded(interactive_session_without_credentials):
    f1_auth.install()

    with pytest.raises(F1AuthError):
        get_token(force_renew=True)

    assert f1_auth.login_was_requested()


def test_flag_is_false_when_login_was_not_requested(
    interactive_session_without_credentials,
):
    f1_auth.install()
    with pytest.raises(F1AuthError):
        get_token(force_renew=True)

    # a new load starts and, being cached, never asks for credentials
    f1_auth.install()

    assert not f1_auth.login_was_requested()


def test_credentials_from_environment_are_not_intercepted(
    monkeypatch, interactive_session_without_credentials
):
    monkeypatch.setenv("F1_USERNAME", "driver@example.com")
    monkeypatch.setenv("F1_PASSWORD", "secret")
    signed_in_with = []
    monkeypatch.setattr(
        fastf1_login,
        "login",
        lambda username, password: signed_in_with.append((username, password)),
    )

    # twice, as the selection window installs it before every load
    f1_auth.install()
    f1_auth.install()
    fastf1_login.default_login()

    assert signed_in_with == [("driver@example.com", "secret")]
    assert not f1_auth.login_was_requested()


def test_install_does_nothing_when_fastf1_function_is_missing(monkeypatch):
    # simulates a FastF1 release that no longer has the credentials prompt
    monkeypatch.delattr(fastf1_login, "_credentials_from_env_or_prompt")

    f1_auth.install()

    assert not hasattr(fastf1_login, "_credentials_from_env_or_prompt")
    assert not f1_auth.login_was_requested()
