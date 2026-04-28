import pytest

from app.services.email_service import EmailService


@pytest.fixture
def configured_email_service(mocker):
    mocker.patch("app.services.email_service.settings.RESEND_API_KEY", "re_test_key")
    mocker.patch(
        "app.services.email_service.settings.EMAIL_FROM",
        "Acme <onboarding@resend.dev>",
    )
    return EmailService()


@pytest.fixture
def unconfigured_email_service(mocker):
    mocker.patch("app.services.email_service.settings.RESEND_API_KEY", None)
    mocker.patch("app.services.email_service.settings.EMAIL_FROM", None)
    return EmailService()


def test_is_configured_returns_true_when_api_key_and_email_from_exist(
    configured_email_service,
):
    assert configured_email_service.is_configured() is True


def test_is_configured_returns_false_when_values_are_missing(
    unconfigured_email_service,
):
    assert unconfigured_email_service.is_configured() is False


def test_send_password_reset_email_raises_when_service_is_not_configured(
    unconfigured_email_service,
):
    with pytest.raises(ValueError, match="no está configurado"):
        unconfigured_email_service.send_password_reset_email(
            to_email="shantipa95@gmail.com",
            reset_link="https://example.com/reset?token=abc123",
            username="shantipa95",
        )


def test_send_password_reset_email_calls_resend_with_expected_payload(
    configured_email_service,
    mocker,
):
    send_mock = mocker.patch(
        "app.services.email_service.resend.Emails.send",
        return_value={"id": "email_123"},
    )

    result = configured_email_service.send_password_reset_email(
        to_email="shantipa95@gmail.com",
        reset_link="https://example.com/reset?token=abc123",
        username="shantipa95",
    )

    assert result == {"id": "email_123"}
    assert configured_email_service.api_key == "re_test_key"

    send_mock.assert_called_once()
    sent_params = send_mock.call_args.args[0]

    assert sent_params["from"] == "Acme <onboarding@resend.dev>"
    assert sent_params["to"] == ["shantipa95@gmail.com"]
    assert sent_params["subject"] == "Restablecimiento de contraseña"
    assert "Hola, shantipa95." in sent_params["html"]
    assert "https://example.com/reset?token=abc123" in sent_params["html"]


def test_send_password_reset_email_uses_default_username_when_missing(
    configured_email_service,
    mocker,
):
    send_mock = mocker.patch(
        "app.services.email_service.resend.Emails.send",
        return_value={"id": "email_456"},
    )

    configured_email_service.send_password_reset_email(
        to_email="shantipa95@gmail.com",
        reset_link="https://example.com/reset?token=abc123",
    )

    send_mock.assert_called_once()
    sent_params = send_mock.call_args.args[0]

    assert "Hola, usuario." in sent_params["html"]
