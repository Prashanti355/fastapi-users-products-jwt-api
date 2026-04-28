from unittest.mock import MagicMock

from app.core import rate_limit


def test_rate_limit_key_func_uses_test_header_in_testing_environment(mocker):
    mocker.patch.object(rate_limit.settings, "ENVIRONMENT", "testing")

    request = MagicMock()
    request.headers = {
        "X-Test-RateLimit-Key": "login-user-1",
    }

    result = rate_limit.rate_limit_key_func(request)

    assert result == "test:login-user-1"


def test_rate_limit_key_func_falls_back_to_remote_address_in_testing_without_header(
    mocker,
):
    mocker.patch.object(rate_limit.settings, "ENVIRONMENT", "testing")
    mocker.patch(
        "app.core.rate_limit.get_remote_address",
        return_value="127.0.0.1",
    )

    request = MagicMock()
    request.headers = {}

    result = rate_limit.rate_limit_key_func(request)

    assert result == "127.0.0.1"


def test_rate_limit_key_func_uses_remote_address_outside_testing(mocker):
    mocker.patch.object(rate_limit.settings, "ENVIRONMENT", "development")
    mocker.patch(
        "app.core.rate_limit.get_remote_address",
        return_value="10.0.0.5",
    )

    request = MagicMock()
    request.headers = {
        "X-Test-RateLimit-Key": "should-not-be-used",
    }

    result = rate_limit.rate_limit_key_func(request)

    assert result == "10.0.0.5"


def test_limiter_uses_settings_values():
    assert rate_limit.limiter._key_func is rate_limit.rate_limit_key_func
    assert rate_limit.limiter._default_limits == rate_limit.settings.RATE_LIMIT_DEFAULTS
    assert (
        rate_limit.limiter._headers_enabled
        == rate_limit.settings.RATE_LIMIT_HEADERS_ENABLED
    )
    assert rate_limit.limiter._storage_uri == rate_limit.settings.RATE_LIMIT_STORAGE_URI
    assert rate_limit.limiter.enabled == rate_limit.settings.RATE_LIMIT_ENABLED
