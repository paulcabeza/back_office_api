"""
Email service using SendGrid for transactional emails.

When SENDGRID_ENABLED is False (default in dev), emails are logged
to console instead of sent. This allows development without an API key.
"""

import logging

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Email, Content, Mail, To

from app.config import settings

logger = logging.getLogger(__name__)


def _send_email(to_email: str, subject: str, html_content: str) -> bool:
    """Send an email via SendGrid. Returns True if sent, False otherwise."""
    if not settings.SENDGRID_ENABLED:
        logger.info(
            "Email (not sent - SendGrid disabled):\n"
            "  To: %s\n  Subject: %s\n  Body preview: %s...",
            to_email,
            subject,
            html_content[:200],
        )
        return False

    try:
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        from_email = Email(settings.SENDGRID_FROM_EMAIL, settings.SENDGRID_FROM_NAME)
        message = Mail(
            from_email=from_email,
            to_emails=To(to_email),
            subject=subject,
            html_content=Content("text/html", html_content),
        )
        response = sg.send(message)
        logger.info(
            "Email sent to %s (status %s)", to_email, response.status_code
        )
        return True
    except Exception:
        logger.exception("Failed to send email to %s", to_email)
        return False


def send_welcome_distributor(
    to_email: str,
    first_name: str,
    last_name: str,
    affiliate_code: str,
    kit_name: str,
    kit_price: str,
    sponsor_name: str | None = None,
) -> bool:
    """Send welcome email to newly enrolled distributor."""
    sponsor_line = (
        f"<p><strong>Tu patrocinador:</strong> {sponsor_name}</p>"
        if sponsor_name
        else ""
    )

    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #2d6a4f;">Bienvenido a Ganoherb</h2>
        <p>Hola <strong>{first_name} {last_name}</strong>,</p>
        <p>Tu inscripcion como distribuidor independiente ha sido registrada exitosamente.</p>

        <div style="background: #f0f7f4; padding: 16px; border-radius: 8px; margin: 16px 0;">
            <p style="margin: 4px 0;"><strong>Tu codigo de distribuidor:</strong>
                <span style="font-size: 1.2em; color: #2d6a4f; font-weight: bold;">{affiliate_code}</span>
            </p>
            <p style="margin: 4px 0;"><strong>Kit adquirido:</strong> {kit_name} (${kit_price})</p>
            {sponsor_line}
        </div>

        <p><strong>Tus credenciales de acceso:</strong></p>
        <ul>
            <li><strong>Email:</strong> {to_email}</li>
            <li><strong>Contrasena:</strong> La que proporcionaste durante la inscripcion.</li>
        </ul>

        <p>Tu orden de inscripcion esta pendiente de confirmacion de pago.
        Una vez confirmado, tu cuenta sera activada y podras acceder al portal.</p>

        <hr style="border: none; border-top: 1px solid #ddd; margin: 24px 0;">
        <p style="color: #888; font-size: 0.85em;">
            Este correo fue generado automaticamente. No responder a esta direccion.
        </p>
    </div>
    """

    return _send_email(
        to_email=to_email,
        subject=f"Bienvenido a Ganoherb — Tu codigo: {affiliate_code}",
        html_content=html,
    )


def send_enrollment_notification_admin(
    admin_email: str,
    admin_name: str,
    affiliate_code: str,
    affiliate_name: str,
    affiliate_email: str,
    kit_name: str,
    kit_price: str,
    order_number: str,
    placement_info: str | None = None,
) -> bool:
    """Send enrollment confirmation email to the admin who performed it."""
    placement_line = (
        f"<p><strong>Posicion en arbol:</strong> {placement_info}</p>"
        if placement_info
        else ""
    )

    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #2d6a4f;">Nuevo Distribuidor Inscrito</h2>
        <p>Hola <strong>{admin_name}</strong>,</p>
        <p>Se ha inscrito exitosamente un nuevo distribuidor en el sistema.</p>

        <div style="background: #f0f7f4; padding: 16px; border-radius: 8px; margin: 16px 0;">
            <p style="margin: 4px 0;"><strong>Codigo:</strong> {affiliate_code}</p>
            <p style="margin: 4px 0;"><strong>Nombre:</strong> {affiliate_name}</p>
            <p style="margin: 4px 0;"><strong>Email:</strong> {affiliate_email}</p>
            <p style="margin: 4px 0;"><strong>Kit:</strong> {kit_name} (${kit_price})</p>
            <p style="margin: 4px 0;"><strong>Orden:</strong> {order_number}</p>
            <p style="margin: 4px 0;"><strong>Estado:</strong> Pendiente de pago</p>
            {placement_line}
        </div>

        <hr style="border: none; border-top: 1px solid #ddd; margin: 24px 0;">
        <p style="color: #888; font-size: 0.85em;">
            Este correo fue generado automaticamente por el sistema Ganoherb Back Office.
        </p>
    </div>
    """

    return _send_email(
        to_email=admin_email,
        subject=f"Nuevo distribuidor inscrito — {affiliate_code}",
        html_content=html,
    )
