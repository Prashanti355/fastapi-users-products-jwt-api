from __future__ import annotations

from typing import Optional

import resend

from app.core.config import settings


class EmailService:
    def __init__(self):
        self.api_key = settings.RESEND_API_KEY
        self.email_from = settings.EMAIL_FROM

    def is_configured(self) -> bool:
        return bool(self.api_key and self.email_from)

    def send_password_reset_email(
        self,
        *,
        to_email: str,
        reset_link: str,
        username: Optional[str] = None,
    ) -> dict:
        if not self.is_configured():
            raise ValueError("El servicio de correo no está configurado.")

        resend.api_key = self.api_key

        greeting = username if username else "usuario"

        html = f"""
        <div style="font-family: Arial, sans-serif; line-height: 1.5;">
            <h2>Recuperación de contraseña</h2>
            <p>Hola, {greeting}.</p>
            <p>Recibimos una solicitud para restablecer tu contraseña.</p>
            <p>
                <a href="{reset_link}" style="display:inline-block;padding:10px 16px;background:#111;color:#fff;text-decoration:none;border-radius:6px;">
                    Restablecer contraseña
                </a>
            </p>
            <p>Si no solicitaste este cambio, puedes ignorar este correo.</p>
        </div>
        """

        params: resend.Emails.SendParams = {
            "from": self.email_from,
            "to": [to_email],
            "subject": "Restablecimiento de contraseña",
            "html": html,
        }

        return resend.Emails.send(params)
